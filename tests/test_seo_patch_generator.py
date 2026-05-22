"""Tests for paste-ready SEO patch generation."""

import pytest

from linkops.content_model import ContentItem
from linkops.content_optimization_model import REC_FAQ_OPTIMIZATION, REC_MONITOR, REC_NO_CHANGE
from linkops.seo_patch_generator import (
    determine_patch_type,
    generate_seo_patch,
)
from linkops.seo_patch_model import PATCH_FAQ, PATCH_MONITOR


def _page(slug: str, title: str, html: str, plain: str, links: list | None = None) -> ContentItem:
    return ContentItem(
        id=abs(hash(slug)) % 100000,
        type="post",
        title=title,
        url=f"https://worktoolslab.com/{slug}/",
        slug=slug,
        content_html=html,
        excerpt_html="",
        modified="2024-01-01",
        existing_internal_links=links or [],
        word_count=len(plain.split()),
        plain_text=plain,
    )


def _clickup_trello_strong_page() -> ContentItem:
    intro = ("ClickUp vs Trello helps small teams compare tools. " * 12) + "clickup vs trello "
    html = (
        "<h1>ClickUp vs Trello for Small Teams</h1>"
        f"<p>{intro}</p>"
        "<h2>ClickUp vs Trello: Quick Verdict</h2>"
        "<h2>FAQ</h2>"
        "<h3>Is ClickUp Better Than Trello?</h3>"
        "<h3>Is Trello Easier to Use Than ClickUp?</h3>"
        "<h3>Which Is Better for Small Teams, ClickUp or Trello?</h3>"
        "<h3>What Is the Main Difference Between ClickUp and Trello?</h3>"
        "<h3>Should a Small Business Use ClickUp or Trello?</h3>"
    )
    return _page("clickup-vs-trello-for-small-teams", "ClickUp vs Trello for Small Teams", html, intro)


def _collaboration_strong_faq_page() -> ContentItem:
    kw = "best collaboration tools for small teams"
    intro = f"{kw} help teams work together. " * 15
    html = (
        f"<h1>Best Collaboration Tools for Small Teams</h1><p>{intro}</p>"
        "<h2>FAQ</h2>"
        "<h3>What are the best collaboration tools for small teams?</h3>"
        "<h3>What should small teams look for in collaboration tools?</h3>"
        "<h3>Do small teams need collaboration tools?</h3>"
        "<h3>What is the easiest collaboration tool for small teams?</h3>"
        "<h3>What is the difference between collaboration tools and communication tools?</h3>"
    )
    return _page(
        "best-collaboration-tools-for-small-teams",
        "Best Collaboration Tools for Small Teams",
        html,
        intro,
    )


def _pm_weak_faq_page() -> ContentItem:
    kw = "project management software for small teams"
    intro = "Small teams need visibility. " * 20
    html = f"<h1>Best PM Tools</h1><p>{intro}</p><h2>Top Tools</h2>"
    return _page(
        "best-project-management-tools-for-small-teams",
        "Best Project Management Tools for Small Teams",
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


def test_monitor_only_no_unnecessary_additions():
    patch = generate_seo_patch(
        [_clickup_trello_strong_page(), *_linkers("clickup-vs-trello-for-small-teams", 5)],
        "https://worktoolslab.com/clickup-vs-trello-for-small-teams/",
        "clickup vs trello",
    )
    assert patch.patch_type == PATCH_MONITOR
    assert patch.seo_title == "No SEO title change needed."
    assert patch.meta_description == "No meta description change needed."
    assert patch.faq_patch == "No FAQ additions needed."
    assert patch.intro_addition == "No intro addition needed."
    assert "Best ClickUp" not in patch.seo_title
    assert "Clickup" not in patch.seo_title


def test_faq_optimization_creates_faq_patch_only():
    patch = generate_seo_patch(
        [_pm_weak_faq_page(), *_linkers("best-project-management-tools-for-small-teams", 5)],
        "https://worktoolslab.com/best-project-management-tools-for-small-teams/",
        "project management software for small teams",
    )
    assert patch.patch_type in (PATCH_FAQ, "combined_light_patch")
    assert patch.faq_questions or "project management" in patch.faq_patch.lower()
    assert patch.seo_title == "No SEO title change needed."
    assert "Best Best" not in patch.faq_patch


def test_clickup_brand_capitalization_in_patch():
    patch = generate_seo_patch(
        [_clickup_trello_strong_page(), *_linkers("clickup-vs-trello-for-small-teams", 5)],
        "https://worktoolslab.com/clickup-vs-trello-for-small-teams/",
        "clickup vs trello",
    )
    blob = patch.seo_title + patch.faq_patch + patch.editorial_decision
    if patch.seo_title != "No SEO title change needed.":
        assert "ClickUp" in blob
    assert "Clickup" not in blob
    assert "Trello" in blob or patch.patch_type == PATCH_MONITOR


def test_no_best_clickup_vs_trello_title():
    patch = generate_seo_patch(
        [_clickup_trello_strong_page()],
        "https://worktoolslab.com/clickup-vs-trello-for-small-teams/",
        "clickup vs trello",
    )
    assert "Best ClickUp vs Trello" not in patch.seo_title
    assert "Best ClickUp" not in patch.faq_patch


def test_collaboration_faq_templates_not_pm():
    patch = generate_seo_patch(
        [_collaboration_strong_faq_page(), *_linkers("best-collaboration-tools-for-small-teams", 5)],
        "https://worktoolslab.com/best-collaboration-tools-for-small-teams/",
        "best collaboration tools for small teams",
    )
    if patch.faq_questions:
        for q in patch.faq_questions:
            assert "collaboration" in q.lower()
            assert "project management software for small teams" not in q.lower()
    else:
        assert patch.faq_patch == "No FAQ additions needed."


def test_meta_under_160_when_title_meta_patch():
    from linkops.content_optimization_model import REC_TITLE_META
    from linkops.gsc_model import GscCache, GscQueryRow

    page = _pm_weak_faq_page()
    gsc = GscCache(
        imported_at="2026-01-01",
        queries=[
            GscQueryRow(
                query="project management software for small teams",
                clicks=0,
                impressions=50,
                ctr=0.0,
                position=12.0,
            )
        ],
    )
    patch = generate_seo_patch(
        [page],
        "https://worktoolslab.com/best-project-management-tools-for-small-teams/",
        "project management software for small teams",
        gsc_cache=gsc,
    )
    if patch.patch_type == "title_meta_patch" or patch.overall_recommendation == REC_TITLE_META:
        assert len(patch.meta_description) <= 160


def test_strong_faq_no_additions():
    patch = generate_seo_patch(
        [_collaboration_strong_faq_page(), *_linkers("best-collaboration-tools-for-small-teams", 5)],
        "https://worktoolslab.com/best-collaboration-tools-for-small-teams/",
        "best collaboration tools for small teams",
    )
    assert patch.faq_patch == "No FAQ additions needed."


def test_slug_keep_current_in_do_not_change():
    patch = generate_seo_patch(
        [_clickup_trello_strong_page()],
        "https://worktoolslab.com/clickup-vs-trello-for-small-teams/",
        "clickup vs trello",
    )
    checklist = " ".join(patch.do_not_change).lower()
    assert "slug" in checklist
    assert "keep current" in checklist or "do not change the published url slug" in checklist


def test_missing_target_raises():
    with pytest.raises(ValueError, match="not found"):
        generate_seo_patch(
            [_clickup_trello_strong_page()],
            "https://worktoolslab.com/does-not-exist/",
            "clickup vs trello",
        )
