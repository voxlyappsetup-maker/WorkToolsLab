"""Tests for v1.5.2 informational and mixed project/task paste-ready patches."""

import re

import pytest

from linkops.content_model import ContentItem
from linkops.informational_topics import (
    is_mixed_project_task_topic,
    mixed_project_task_faq_answer,
)
from linkops.seo_patch_faq import PASTE_READY_FORBIDDEN_SUBSTRINGS, UNSAFE_ANSWER_SUBSTRINGS
from linkops.seo_patch_generator import generate_seo_patch
from linkops.seo_patch_model import PATCH_COMBINED, PATCH_MONITOR
from linkops.seo_patch_report_writer import write_seo_patch_reports

KEYWORD = "project and task management"
TARGET = "https://worktoolslab.com/best-task-management-tools-for-small-teams/"
SLUG = "best-task-management-tools-for-small-teams"


def _page(slug: str, title: str, html: str, plain: str) -> ContentItem:
    return ContentItem(
        id=abs(hash(slug)) % 100000,
        type="post",
        title=title,
        url=f"https://worktoolslab.com/{slug}/",
        slug=slug,
        content_html=html,
        excerpt_html="",
        modified="2024-01-01",
        existing_internal_links=[],
        word_count=len(plain.split()),
        plain_text=plain,
    )


def _task_mgmt_page() -> ContentItem:
    intro = "Small teams need better task visibility and ownership. " * 18
    html = (
        "<h1>Best Task Management Tools for Small Teams</h1>"
        f"<p>{intro}</p>"
        "<h2>Top Task Management Tools</h2>"
        "<h2>How to Choose a Task Manager</h2>"
    )
    return _page(
        SLUG,
        "Best Task Management Tools for Small Teams",
        html,
        intro,
    )


def _related_comparison_page() -> ContentItem:
    intro = "Task management vs project management explained for small teams. " * 12
    html = (
        "<h1>Task Management vs Project Management</h1>"
        f"<p>{intro}</p>"
        "<h2>Key Differences</h2>"
    )
    return _page(
        "task-management-vs-project-management",
        "Task Management vs Project Management",
        html,
        intro,
    )


def _linkers(target_slug: str, n: int = 5) -> list[ContentItem]:
    pages = []
    for i in range(n):
        p = _page(f"link-{i}", f"L{i}", "<p>x</p>", "x")
        p.existing_internal_links = [
            {
                "href": f"https://worktoolslab.com/{target_slug}/",
                "anchor_text": "target",
                "normalized_url": f"https://worktoolslab.com/{target_slug}",
            }
        ]
        pages.append(p)
    return pages


def _catalog() -> list[ContentItem]:
    return [_task_mgmt_page(), _related_comparison_page(), *_linkers(SLUG, 5)]


def _paste_ready_section(md: str) -> str:
    start = md.find("## Paste-Ready Changes")
    end = md.find("## Manual Review Needed")
    assert start >= 0 and end > start
    return md[start:end]


def test_mixed_topic_detection():
    assert is_mixed_project_task_topic("project and task management")
    assert is_mixed_project_task_topic("project management and task management")
    assert is_mixed_project_task_topic("task vs project management")


@pytest.fixture
def mixed_patch():
    return generate_seo_patch(_catalog(), TARGET, KEYWORD)


def test_no_best_project_and_task_management_heading(mixed_patch):
    assert "Best Project and Task Management" not in mixed_patch.heading_addition
    assert "Best Project and Task Management: Overview" not in mixed_patch.heading_addition


def test_no_unnatural_faq_questions(mixed_patch):
    blob = mixed_patch.faq_patch.lower()
    assert "what is the best project and task management" not in blob
    assert "who is best project and task management best for" not in blob


def test_no_guillemets_or_generic_phrases_in_paste_ready(tmp_path, monkeypatch, mixed_patch):
    import linkops.seo_patch_report_writer as writer_mod

    monkeypatch.setattr(writer_mod, "REPORTS_DIR", tmp_path)
    md_path, _ = write_seo_patch_reports(mixed_patch, slug="mixed", ts="20260522_140000")
    section = _paste_ready_section(md_path.read_text(encoding="utf-8")).lower()
    assert "«" not in section and "»" not in section
    for banned in (*PASTE_READY_FORBIDDEN_SUBSTRINGS, *UNSAFE_ANSWER_SUBSTRINGS):
        assert banned not in section


def test_natural_heading_and_intro(mixed_patch):
    assert "Project and Task Management: What Small Teams Should Know" in mixed_patch.heading_addition
    assert "project management and task management" in mixed_patch.intro_addition.lower()
    assert "larger goals" in mixed_patch.intro_addition.lower()


def test_mixed_faq_questions_and_answers(mixed_patch):
    assert "difference between project management and task management" in mixed_patch.faq_patch.lower()
    assert "Do small teams need both" in mixed_patch.faq_patch
    assert mixed_project_task_faq_answer(
        "What is the difference between project management and task management?"
    ) in mixed_patch.faq_patch
    assert len(mixed_patch.faq_questions) >= 3


def test_combined_light_patch_when_multiple_gaps(mixed_patch):
    assert mixed_patch.patch_type == PATCH_COMBINED


def test_title_meta_unchanged(mixed_patch):
    assert mixed_patch.seo_title == "No SEO title change needed."
    assert mixed_patch.meta_description == "No meta description change needed."


def test_internal_link_note_when_related_page_in_cache(mixed_patch):
    manual = " ".join(mixed_patch.manual_review_needed).lower()
    assert "task management vs project management" in manual
    assert "task-management-vs-project-management" in manual


def test_monitor_only_regression_clickup():
    from tests.test_seo_patch_generator import _clickup_trello_strong_page, _linkers as linkers

    patch = generate_seo_patch(
        [_clickup_trello_strong_page(), *linkers("clickup-vs-trello-for-small-teams", 5)],
        "https://worktoolslab.com/clickup-vs-trello-for-small-teams/",
        "clickup vs trello",
    )
    assert patch.patch_type == PATCH_MONITOR


def test_webex_no_placeholder_regression(tmp_path, monkeypatch):
    from tests.test_seo_patch_v151 import _linkers as linkers, _webex_weak_faq_page

    patch = generate_seo_patch(
        [_webex_weak_faq_page(), *linkers("webex-review-for-small-businesses", 5)],
        "https://worktoolslab.com/webex-review-for-small-businesses/",
        "Webex review for small businesses",
    )
    import linkops.seo_patch_report_writer as writer_mod

    monkeypatch.setattr(writer_mod, "REPORTS_DIR", tmp_path)
    md_path, _ = write_seo_patch_reports(patch, slug="webex", ts="20260522_140001")
    section = _paste_ready_section(md_path.read_text(encoding="utf-8")).lower()
    assert "add a concise answer after editorial review" not in section
