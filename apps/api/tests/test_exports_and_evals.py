"""Unit tests for Export rendering (Phase 4) and Evals rubrics (Phase 5)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.services.export import render_export, render_html, render_markdown
from evals.evaluator import evaluate_lesson

SAMPLE_LESSON = {
    "title": "Earth Systems & Water Cycle",
    "grade": "5",
    "subject": "Science",
    "duration_minutes": 60,
    "objectives": [{"id": "obj-1", "text": "Model condensation and evaporation", "assessment_ids": ["a1"]}],
    "standards": [{"code": "NGSS 5-ESS2-1", "description": "Earth systems", "evidence": ["Hydrosphere interaction"]}],
    "sections": [
        {
            "id": "s1",
            "title": "Engage & Explore",
            "duration_minutes": 30,
            "teacher_actions": ["Introduce diagram"],
            "student_actions": ["Analyze water states"],
            "materials": ["Diagram sheet"],
        },
        {
            "id": "s2",
            "title": "Explain & Elaborate",
            "duration_minutes": 30,
            "teacher_actions": ["Facilitate review"],
            "student_actions": ["Complete exit ticket"],
            "materials": ["Exit slip"],
        },
    ],
    "differentiation": {
        "ell": ["Bilingual vocabulary card"],
        "iep": ["Visual aids and extended time"],
        "gifted": ["Design closed-loop condensation terrarium"],
    },
    "assessments": [
        {
            "id": "a1",
            "type": "Formative Exit Ticket",
            "questions": ["Explain how evaporation leads to cloud formation"],
            "success_criteria": ["Correctly identifies role of temperature drop"],
        }
    ],
    "review": {"review_passed": True, "score": 0.95, "issues": []},
}


def test_render_markdown():
    md = render_markdown(SAMPLE_LESSON)
    assert "# Earth Systems & Water Cycle" in md
    assert "NGSS 5-ESS2-1" in md
    assert "Engage & Explore (30 min)" in md
    assert "English Language Learners (ELL)" in md


def test_render_html():
    html_text = render_html(SAMPLE_LESSON)
    assert "<!DOCTYPE html>" in html_text
    assert "<h1>Earth Systems & Water Cycle</h1>" in html_text
    assert "NGSS 5-ESS2-1" in html_text


def test_render_export_formats():
    data_md, ext_md, mime_md = render_export(SAMPLE_LESSON, "markdown")
    assert ext_md == "md"
    assert mime_md == "text/markdown"
    assert b"Earth Systems" in data_md

    data_json, ext_json, mime_json = render_export(SAMPLE_LESSON, "json")
    assert ext_json == "json"
    assert mime_json == "application/json"
    assert b"NGSS 5-ESS2-1" in data_json

    data_html, ext_html, mime_html = render_export(SAMPLE_LESSON, "pdf")
    assert ext_html == "html"
    assert mime_html == "text/html"


def test_evaluator_rubrics():
    req = {
        "id": "test-req",
        "duration_minutes": 60,
        "standards": ["NGSS 5-ESS2-1"],
    }
    report = evaluate_lesson(SAMPLE_LESSON, req)
    assert report.overall_passed is True
    assert report.overall_score >= 0.9
    assert len(report.results) == 5
