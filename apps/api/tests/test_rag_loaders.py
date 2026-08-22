"""Document loaders dispatch by extension and fail loudly on bad JSONL
(app/rag/loaders.py).

Text/JSONL paths run everywhere; PDF/HTML tests skip when the optional parser is
not installed (they are lazily imported in the loader).
"""

from __future__ import annotations

import json

import pytest

from app.rag import loaders


def test_text_files_become_rawdocs(tmp_path):
    (tmp_path / "note.md").write_text("# Heading\n\nBody text.", encoding="utf-8")
    (tmp_path / "plain.txt").write_text("just text", encoding="utf-8")

    docs = {d.source: d for d in loaders.load_documents([tmp_path])}

    assert docs["note"].text.startswith("# Heading")
    assert docs["note"].meta["doc_type"] == "md"
    assert docs["plain"].meta["doc_type"] == "txt"
    assert docs["plain"].meta["path"].endswith("plain.txt")


def test_jsonl_records_are_parsed_with_meta(tmp_path):
    path = tmp_path / "corpus.jsonl"
    path.write_text(
        json.dumps({"content": "Standard A", "source": "NGSS", "meta": {"code": "X-1"}})
        + "\n\n"  # blank line is skipped
        + json.dumps({"content": "Standard B", "source": "CCSS", "meta": {"code": "Y-2"}})
        + "\n",
        encoding="utf-8",
    )

    docs = list(loaders.load_documents([path]))

    assert [d.text for d in docs] == ["Standard A", "Standard B"]
    assert docs[0].source == "NGSS"
    assert docs[0].meta == {"code": "X-1"}


def test_jsonl_invalid_json_reports_line(tmp_path):
    path = tmp_path / "bad.jsonl"
    path.write_text('{"content": "ok"}\nnot json\n', encoding="utf-8")
    with pytest.raises(ValueError, match=r"bad\.jsonl:2"):
        list(loaders.load_documents([path]))


def test_jsonl_missing_content_raises(tmp_path):
    path = tmp_path / "empty.jsonl"
    path.write_text(json.dumps({"source": "NGSS", "meta": {}}) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing non-empty 'content'"):
        list(loaders.load_documents([path]))


def test_iter_supported_recurses_sorts_and_skips_unsupported(tmp_path):
    (tmp_path / "a.md").write_text("a", encoding="utf-8")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.txt").write_text("b", encoding="utf-8")
    (tmp_path / "ignore.csv").write_text("x,y", encoding="utf-8")  # unsupported

    found = [p.name for p in loaders.iter_supported([tmp_path])]

    assert found == ["a.md", "b.txt"]  # recursive + sorted, .csv skipped


def test_html_text_extraction_strips_script_and_style(tmp_path):
    pytest.importorskip("bs4")
    path = tmp_path / "page.html"
    path.write_text(
        "<html><body><h1>Title</h1><script>var x=1;</script>"
        "<p>Hello</p><style>.a{color:red}</style></body></html>",
        encoding="utf-8",
    )

    (doc,) = list(loaders.load_documents([path]))

    assert doc.meta["doc_type"] == "html"
    assert "Title" in doc.text and "Hello" in doc.text
    assert "var x" not in doc.text and "color:red" not in doc.text


def test_pdf_path_is_wired(tmp_path):
    pypdf = pytest.importorskip("pypdf")
    path = tmp_path / "doc.pdf"
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=72, height=72)
    with path.open("wb") as fh:
        writer.write(fh)

    (doc,) = list(loaders.load_documents([path]))

    assert doc.source == "doc"
    assert doc.meta["doc_type"] == "pdf"
    assert isinstance(doc.text, str)  # blank page → "", but the loader still yields a RawDoc
