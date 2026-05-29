"""Tests for v1.6.2 paste-ready patch relevance guardrails."""

import re

import pytest

from linkops.content_model import ContentItem
from linkops.patch_relevance_guardrails import (
    PatchContext,
    block_incompatible_patch_suggestion,
    classify_patch_context,
    filter_patch_faqs,
    is_concept_comparison,
    is_misrouted_branded_comparison,
    is_software_comparison,
    is_teamwork_vs_asana_query,
)
from linkops.seo_patch_generator import generate_seo_patch
from linkops.seo_patch_model import PATCH_MANUAL


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


def _concept_page() -> ContentItem:
    intro = "Project vs task management for small teams explained. " * 12
    html = (
        "<h1>Task Management vs Project Management</h1>"
        f"<p>{intro}</p><h2>Definitions</h2>"
    )
    return _page("task-management-vs-project-management", "Task Management vs Project Management", html, intro)


def _trello_review_page() -> ContentItem:
    intro = "Trello review for freelancers covers boards, client work, and Kanban. " * 12
    html = f"<h1>Trello Review for Freelancers</h1><p>{intro}</p><h2>Overview</h2>"
    return _page("trello-review-for-freelancers", "Trello Review for Freelancers", html, intro)


def _productivity_page() -> ContentItem:
    intro = "Team productivity tools help with tasks, docs, and communication. " * 15
    html = (
        "<h1>Best Productivity Tools for Small Teams</h1>"
        f"<p>{intro}</p><h2>Top Tools</h2>"
    )
    return _page(
        "best-productivity-tools-for-small-teams",
        "Best Productivity Tools for Small Teams",
        html,
        intro,
    )


def _clickup_page() -> ContentItem:
    intro = ("ClickUp vs Trello for small teams. " * 20) + "clickup vs trello "
    html = (
        "<h1>ClickUp vs Trello for Small Teams</h1>"
        f"<p>{intro}</p>"
        "<h2>FAQ</h2>"
        "<h3>Is ClickUp Better Than Trello?</h3>"
        "<h3>Is Trello Easier to Use Than ClickUp?</h3>"
        "<h3>Which Is Better for Small Teams, ClickUp or Trello?</h3>"
        "<h3>What Is the Main Difference Between ClickUp and Trello?</h3>"
        "<h3>Should a Small Business Use ClickUp or Trello?</h3>"
    )
    return _page("clickup-vs-trello-for-small-teams", "ClickUp vs Trello for Small Teams", html, intro)


def _webex_page() -> ContentItem:
    intro = "Webex review for small businesses video meetings. " * 20
    html = f"<h1>Webex Review for Small Businesses</h1><p>{intro}</p>"
    return _page("webex-review-for-small-businesses", "Webex Review for Small Businesses", html, intro)


def _video_meeting_page() -> ContentItem:
    intro = "Best video meeting tools for small businesses. " * 15
    html = f"<h1>Best Video Meeting Tools for Small Businesses</h1><p>{intro}</p>"
    return _page(
        "best-video-meeting-tools-for-small-businesses",
        "Best Video Meeting Tools for Small Businesses",
        html,
        intro,
    )


def _asana_clickup_page() -> ContentItem:
    intro = "Asana vs ClickUp comparison for small teams. " * 15
    html = f"<h1>Asana vs ClickUp for Small Teams</h1><p>{intro}</p>"
    return _page("asana-vs-clickup-for-small-teams", "Asana vs ClickUp for Small Teams", html, intro)


def _paste_section(blob: str) -> str:
    start = blob.find("## Paste-Ready Changes")
    end = blob.find("## Manual Review Needed")
    if start < 0:
        return blob.lower()
    if end < 0:
        return blob[start:].lower()
    return blob[start:end].lower()


def test_concept_comparison_detection():
    assert is_concept_comparison("project vs task")
    assert is_concept_comparison("task management vs project management")
    assert not is_concept_comparison("clickup vs trello")
    assert not is_concept_comparison("teamwork vs asana")


def test_concept_comparison_patch_no_fake_product_faq():
    patch = generate_seo_patch(
        [_concept_page()],
        "https://worktoolslab.com/task-management-vs-project-management/",
        "project vs task",
    )
    section = _paste_section(patch.faq_patch + patch.intro_addition + patch.heading_addition)
    assert "is project better than task" not in section
    assert "is task easier to use than project" not in section
    assert (
        "difference between a project and a task" in section
        or "project vs task" in section
        or "project management vs task management" in section
    )


def test_trello_review_no_video_meeting_templates():
    patch = generate_seo_patch(
        [_trello_review_page()],
        "https://worktoolslab.com/trello-review-for-freelancers/",
        "trello review",
    )
    section = _paste_section(
        patch.faq_patch + patch.intro_addition + patch.meta_description
    ).lower()
    assert "video meeting" not in section
    assert "calling" not in section or "business calling" not in section
    if patch.faq_patch and patch.faq_patch != "No FAQ additions needed.":
        assert "trello" in section or "freelancer" in section or "kanban" in section


def test_productivity_no_forced_pm_software_wording():
    patch = generate_seo_patch(
        [_productivity_page()],
        "https://worktoolslab.com/best-productivity-tools-for-small-teams/",
        "team productivity tools",
    )
    blob = (
        patch.intro_addition
        + patch.faq_patch
        + patch.heading_addition
    ).lower()
    assert "best project management software for small teams" not in blob
    if patch.intro_addition != "No intro addition needed.":
        assert "productivity" in patch.intro_addition.lower()


def test_teamwork_vs_asana_misroute_manual_review():
    assert is_teamwork_vs_asana_query("teamwork vs asana")
    page = _asana_clickup_page()
    assert is_misrouted_branded_comparison("teamwork vs asana", page)
    patch = generate_seo_patch(
        [page],
        "https://worktoolslab.com/asana-vs-clickup-for-small-teams/",
        "teamwork vs asana",
    )
    assert patch.patch_type == PATCH_MANUAL
    assert "Teamwork" in " ".join(patch.manual_review_needed)
    assert "Asana vs ClickUp" in " ".join(patch.manual_review_needed)
    assert patch.faq_patch in ("No FAQ additions needed.", "No paste-ready FAQ additions available.")


def test_clickup_software_comparison_regression():
    patch = generate_seo_patch(
        [_clickup_page()],
        "https://worktoolslab.com/clickup-vs-trello-for-small-teams/",
        "clickup vs trello",
    )
    assert is_software_comparison("clickup vs trello", "comparison")
    if patch.faq_patch not in ("No FAQ additions needed.", "No paste-ready FAQ additions available."):
        assert "clickup" in patch.faq_patch.lower()
        assert "trello" in patch.faq_patch.lower()


def test_webex_allows_video_wording():
    patch = generate_seo_patch(
        [_webex_page()],
        "https://worktoolslab.com/webex-review-for-small-businesses/",
        "Webex review for small businesses",
    )
    ctx = classify_patch_context(
        "Webex review for small businesses",
        item=_webex_page(),
    )
    assert ctx.allow_video_meeting_templates is True


def test_video_meeting_roundup_topic():
    ctx = classify_patch_context(
        "best video meeting tools",
        item=_video_meeting_page(),
    )
    assert ctx.topic == "video_meeting"
    assert ctx.allow_video_meeting_templates is True


def test_block_incompatible_productivity_pm_phrase():
    ctx = PatchContext(
        keyword="team productivity tools",
        comparison_kind="none",
        page_kind="roundup",
        topic="productivity",
        allow_pm_software_wording=False,
    )
    assert block_incompatible_patch_suggestion(
        "What is the best project management software for small teams?",
        ctx,
    )
