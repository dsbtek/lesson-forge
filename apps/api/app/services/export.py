"""Lesson plan export renderers and storage helpers (Phase 4).

Renders canonical lesson JSON (from LessonVersion.content) into teacher-ready
presentation formats:
  - Markdown (.md)
  - HTML / PDF (.html)
  - Canonical JSON (.json)
  - Formatted text/DOCX (.txt / .docx)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

EXPORTS_DIR = Path("/tmp/exports") if not Path("exports").exists() else Path("exports")
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


def render_markdown(content: dict[str, Any]) -> str:
    """Render lesson content to clean GitHub-flavored Markdown."""
    title = content.get("title", "Curriculum Lesson Plan")
    subject = content.get("subject", "General")
    grade = content.get("grade", "")
    duration = content.get("duration_minutes", 60)

    lines: list[str] = [
        f"# {title}",
        "",
        f"**Subject:** {subject} | **Grade:** {grade} | **Duration:** {duration} minutes",
        "",
    ]

    objectives = content.get("objectives", [])
    if objectives:
        lines.extend(["## Learning Objectives", ""])
        for obj in objectives:
            text = obj.get("text", "") if isinstance(obj, dict) else str(obj)
            lines.append(f"- {text}")
        lines.append("")

    standards = content.get("standards", [])
    if standards:
        lines.extend(["## Standards Alignment", ""])
        for std in standards:
            if isinstance(std, dict):
                code = std.get("code", "")
                desc = std.get("description", "")
                desc_str = f": {desc}" if desc else ""
                lines.append(f"- **{code}**{desc_str}")
                evidence = std.get("evidence", [])
                if evidence:
                    lines.append(f"  *Evidence:* {'; '.join(evidence)}")
            else:
                lines.append(f"- {std}")
        lines.append("")

    sections = content.get("sections", [])
    if sections:
        lines.extend(["## Instructional Timeline & Pacing", ""])
        for i, sec in enumerate(sections, 1):
            s_title = sec.get("title", f"Section {i}")
            s_dur = sec.get("duration_minutes", 0)
            lines.append(f"### {i}. {s_title} ({s_dur} min)")
            lines.append("")

            teacher_actions = sec.get("teacher_actions", [])
            if teacher_actions:
                lines.append("**Teacher Actions:**")
                for act in teacher_actions:
                    lines.append(f"- {act}")
                lines.append("")

            student_actions = sec.get("student_actions", [])
            if student_actions:
                lines.append("**Student Actions:**")
                for act in student_actions:
                    lines.append(f"- {act}")
                lines.append("")

            materials = sec.get("materials", [])
            if materials:
                lines.append(f"**Materials:** {', '.join(materials)}")
                lines.append("")

    diff = content.get("differentiation", {})
    if diff and isinstance(diff, dict):
        lines.extend(["## Universal Differentiation & Accommodations", ""])
        if diff.get("ell"):
            lines.append("### English Language Learners (ELL)")
            for item in diff["ell"]:
                lines.append(f"- {item}")
            lines.append("")
        if diff.get("iep"):
            lines.append("### Special Education / Accommodations (IEP)")
            for item in diff["iep"]:
                lines.append(f"- {item}")
            lines.append("")
        if diff.get("gifted"):
            lines.append("### Gifted & Advanced Extensions")
            for item in diff["gifted"]:
                lines.append(f"- {item}")
            lines.append("")

    assessments = content.get("assessments", [])
    if assessments:
        lines.extend(["## Assessments & Success Criteria", ""])
        for ass in assessments:
            if isinstance(ass, dict):
                a_type = ass.get("type", "Assessment")
                lines.append(f"### {a_type}")
                for q in ass.get("questions", []):
                    lines.append(f"- **Prompt:** {q}")
                for crit in ass.get("success_criteria", []):
                    lines.append(f"- *Criteria:* {crit}")
                lines.append("")

    materials = content.get("materials", [])
    if materials:
        lines.extend(["## Required Materials & Supplies", ""])
        for m in materials:
            lines.append(f"- {m}")
        lines.append("")

    review = content.get("review", {})
    if review and isinstance(review, dict) and "score" in review:
        score = review.get("score", 0)
        passed = review.get("review_passed", False)
        status_txt = "Passed" if passed else "Review Suggested"
        lines.extend([
            "---",
            f"*Pedagogical Quality Audit Score: {int(score * 100)}% ({status_txt})*",
            "",
        ])

    return "\n".join(lines)


def render_html(content: dict[str, Any]) -> str:
    """Render lesson content to clean, printable HTML."""
    md_body = render_markdown(content)
    # Simple semantic HTML wrapper with print-ready styling
    title = content.get("title", "Curriculum Lesson Plan")
    paragraphs = []
    for block in md_body.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        if block.startswith("# "):
            paragraphs.append(f"<h1>{block[2:]}</h1>")
        elif block.startswith("## "):
            paragraphs.append(f"<h2>{block[3:]}</h2>")
        elif block.startswith("### "):
            paragraphs.append(f"<h3>{block[4:]}</h3>")
        elif block.startswith("- "):
            items = "".join(f"<li>{line[2:]}</li>" for line in block.split("\n") if line.startswith("- "))
            paragraphs.append(f"<ul>{items}</ul>")
        else:
            paragraphs.append(f"<p>{block}</p>")

    html_body = "\n".join(paragraphs)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      line-height: 1.6;
      max-width: 800px;
      margin: 40px auto;
      padding: 0 20px;
      color: #1e293b;
    }}
    h1 {{ color: #1e1b4b; border-bottom: 2px solid #4f46e5; padding-bottom: 8px; }}
    h2 {{ color: #312e81; margin-top: 28px; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; }}
    h3 {{ color: #4338ca; margin-top: 20px; }}
    ul {{ padding-left: 20px; }}
    li {{ margin-bottom: 4px; }}
    @media print {{
      body {{ margin: 0; padding: 0; }}
    }}
  </style>
</head>
<body>
{html_body}
</body>
</html>
"""


def render_export(content: dict[str, Any], fmt: str) -> tuple[bytes, str, str]:
    """Render the lesson content into (bytes, extension, mime_type)."""
    fmt_lower = fmt.lower().strip()
    if fmt_lower == "markdown" or fmt_lower == "md":
        rendered = render_markdown(content).encode("utf-8")
        return rendered, "md", "text/markdown"
    elif fmt_lower in ("pdf", "html", "google_docs"):
        rendered = render_html(content).encode("utf-8")
        return rendered, "html", "text/html"
    elif fmt_lower == "json":
        rendered = json.dumps(content, indent=2, default=str).encode("utf-8")
        return rendered, "json", "application/json"
    else:
        # Default to markdown text for docx/others
        rendered = render_markdown(content).encode("utf-8")
        return rendered, "txt", "text/plain"


def save_export_artifact(export_id: str, data: bytes, ext: str) -> Path:
    """Save rendered artifact to the local exports scratch directory."""
    target = EXPORTS_DIR / f"{export_id}.{ext}"
    target.write_bytes(data)
    return target
