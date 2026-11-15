#!/usr/bin/env python3
"""Batch downloader for official Nigerian Educational Research and Development Council (NERDC) curricula.

Downloads official national curriculum PDFs directly from the NERDC portal
into the LessonForge `knowledge/nerdc/` directory for RAG ingestion.

Usage:
    # Dry-run: list all subjects and PDF URLs
    python3 scripts/download_nerdc.py --dry-run

    # Download 2 sample subjects per grade level for quick RAG testing
    python3 scripts/download_nerdc.py --limit 2

    # Download all primary school curricula
    python3 scripts/download_nerdc.py --level primary

    # Download all JSS (Junior Secondary) curricula
    python3 scripts/download_nerdc.py --level jss

    # Download all SSS (Senior Secondary) curricula
    python3 scripts/download_nerdc.py --level sss

    # Download full national curriculum catalog
    python3 scripts/download_nerdc.py --all
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

BASE_LMIS = "https://lmis.nerdcportals.com.ng"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# All level paths available across the NERDC portal
CATALOG_SECTIONS = [
    # Primary (Basic 1-6)
    {"level_key": "pry_1", "category": "primary", "grade": "Primary 1", "path": "pry_1/"},
    {"level_key": "pry_2", "category": "primary", "grade": "Primary 2", "path": "pry_2/"},
    {"level_key": "pry_3", "category": "primary", "grade": "Primary 3", "path": "pry_3/"},
    {"level_key": "pry_4", "category": "primary", "grade": "Primary 4", "path": "pry_4/"},
    {"level_key": "pry_5", "category": "primary", "grade": "Primary 5", "path": "pry_5/"},
    {"level_key": "pry_6", "category": "primary", "grade": "Primary 6", "path": "pry_6/"},
    # Junior Secondary (Basic 7-9)
    {"level_key": "jss_1", "category": "jss", "grade": "JSS 1", "path": "jss_1/"},
    {"level_key": "jss_2", "category": "jss", "grade": "JSS 2", "path": "jss_2/"},
    {"level_key": "jss_3", "category": "jss", "grade": "JSS 3", "path": "jss_3/"},
    # Senior Secondary 1
    {"level_key": "sss_1", "category": "sss", "grade": "SSS 1 Core", "path": "s1_core/"},
    {"level_key": "sss_1", "category": "sss", "grade": "SSS 1 Science", "path": "s1_science/"},
    {"level_key": "sss_1", "category": "sss", "grade": "SSS 1 Humanities", "path": "s1_humanities/"},
    {"level_key": "sss_1", "category": "sss", "grade": "SSS 1 Business", "path": "s1_business/"},
    {"level_key": "sss_1", "category": "sss", "grade": "SSS 1 Trades", "path": "s1_trades/"},
    # Senior Secondary 2
    {"level_key": "sss_2", "category": "sss", "grade": "SSS 2 Core", "path": "s2_core/"},
    {"level_key": "sss_2", "category": "sss", "grade": "SSS 2 Science", "path": "s2_science/"},
    {"level_key": "sss_2", "category": "sss", "grade": "SSS 2 Humanities", "path": "s2_humanities/"},
    {"level_key": "sss_2", "category": "sss", "grade": "SSS 2 Business", "path": "s2_business/"},
    {"level_key": "sss_2", "category": "sss", "grade": "SSS 2 Trades", "path": "s2_trades/"},
]


@dataclass
class CurriculumItem:
    grade: str
    category: str
    level_key: str
    subject_id: str
    subject_name: str
    pdf_url: str
    filename: str


def slugify(text: str) -> str:
    """Normalize subject string for safe filenames."""
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "_", s)
    return s.strip("_")


def fetch_html(url: str, timeout: int = 15) -> str:
    """Fetch HTML with custom user-agent, gracefully handling 403 response bodies."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as exc:
        # Portal returns 403 with the full table HTML in response body
        return exc.read().decode("utf-8", errors="ignore")
    except Exception as exc:
        print(f"  [!] Failed fetching {url}: {exc}")
        return ""


def crawl_section(section: dict) -> list[CurriculumItem]:
    """Crawl a portal level and return list of CurriculumItem targets."""
    url = f"{BASE_LMIS}/{section['path']}"
    html = fetch_html(url)
    if not html:
        return []

    items: list[CurriculumItem] = []
    # Match table rows: <td>Subject Name</td> ... viewer/{level}/{id}
    matches = re.findall(
        r"<td>([^<]+)</td>\s*<td><a href=\"[^\"]*viewer/([^\"]+)/([0-9]+)\"",
        html,
    )

    for subj, lvl, sid in matches:
        clean_subj = subj.strip()
        if not clean_subj or clean_subj.lower() == "click to view":
            continue

        pdf_url = f"{BASE_LMIS}/{lvl}/necurrdc/{sid}.pdf"
        grade_slug = slugify(section["grade"])
        subj_slug = slugify(clean_subj)
        filename = f"{grade_slug}_{subj_slug}.pdf"

        items.append(
            CurriculumItem(
                grade=section["grade"],
                category=section["category"],
                level_key=lvl,
                subject_id=sid,
                subject_name=clean_subj,
                pdf_url=pdf_url,
                filename=filename,
            )
        )

    return items


def download_file(item: CurriculumItem, out_dir: Path, retries: int = 3) -> bool:
    """Download a single curriculum PDF idempotently with automatic retry."""
    dest = out_dir / item.filename
    if dest.exists() and dest.stat().st_size > 1024:
        print(f"  [✓ Cached] {item.filename} ({dest.stat().st_size // 1024} KB)")
        return True

    temp_dest = dest.with_suffix(".tmp")
    req = urllib.request.Request(item.pdf_url, headers={"User-Agent": USER_AGENT})

    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()

            # Check for valid PDF magic bytes
            if not data.startswith(b"%PDF-"):
                print(f"  [✗ Error] {item.filename}: Remote server did not return a valid PDF")
                return False

            temp_dest.write_bytes(data)
            temp_dest.rename(dest)
            print(f"  [✓ Downloaded] {item.filename} ({len(data) // 1024} KB)")
            return True
        except Exception as exc:
            if attempt < retries:
                print(f"  [↻ Retry {attempt}/{retries}] {item.filename}: {exc}")
            else:
                print(f"  [✗ Failed] {item.filename} ({item.pdf_url}): {exc}")
            if temp_dest.exists():
                temp_dest.unlink(missing_ok=True)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Download official NERDC curricula into knowledge/")
    parser.add_argument(
        "--level",
        type=str,
        default="all",
        choices=["all", "primary", "jss", "sss", "pry_1", "pry_2", "pry_3", "pry_4", "pry_5", "pry_6", "jss_1", "jss_2", "jss_3"],
        help="Select educational category or specific level (default: all)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Download all curricula across all categories",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of PDFs per section (useful for quick seeding)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Crawl and list available PDFs without downloading",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="knowledge/nerdc",
        help="Destination directory (default: knowledge/nerdc)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Concurrent download threads (default: 4)",
    )

    args = parser.parse_args()
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Filter target sections
    selected_sections = CATALOG_SECTIONS
    if not args.all and args.level != "all":
        selected_sections = [
            s for s in CATALOG_SECTIONS
            if s["category"] == args.level or s["level_key"] == args.level
        ]

    print("=" * 70)
    print("NERDC National Curriculum Downloader for LessonForge")
    print(f"Target Directory: {out_dir.resolve()}")
    print(f"Sections selected: {len(selected_sections)}")
    print("=" * 70)

    # 1. Crawl all selected sections
    all_items: list[CurriculumItem] = []
    for sec in selected_sections:
        print(f"Scanning {sec['grade']}…")
        items = crawl_section(sec)
        if args.limit and args.limit > 0:
            items = items[: args.limit]
        all_items.extend(items)
        print(f"  Found {len(items)} subject(s)")

    print(f"\nTotal Curriculum PDFs Discovered: {len(all_items)}\n")

    if args.dry_run:
        print("[Dry Run] Discovered Curriculum Items:")
        for it in all_items:
            print(f"  - {it.grade:<18} | {it.subject_name:<30} -> {it.pdf_url}")
        return 0

    if not all_items:
        print("No curriculum items found. Check internet connectivity.")
        return 1

    # 2. Download in parallel
    print(f"Downloading {len(all_items)} curricula with {args.workers} workers…")
    success_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(download_file, it, out_dir): it for it in all_items}
        for future in concurrent.futures.as_completed(futures):
            if future.result():
                success_count += 1

    # 3. Write catalog index metadata
    catalog_path = out_dir / "catalog.json"
    catalog_data = [asdict(it) for it in all_items]
    catalog_path.write_text(json.dumps(catalog_data, indent=2), encoding="utf-8")

    print("\n" + "=" * 70)
    print(f"Download complete: {success_count}/{len(all_items)} PDFs ready in {out_dir}")
    print(f"Catalog index generated at: {catalog_path}")
    print("Next step: Ingest into LessonForge RAG store:")
    print("  make ingest")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
