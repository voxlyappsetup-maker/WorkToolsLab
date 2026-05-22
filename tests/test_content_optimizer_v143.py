"""Tests for v1.4.3 comparison query titles and brand capitalization."""

from dataclasses import asdict

from linkops.content_model import ContentItem
from linkops.content_optimizer import (
    analyze_content_optimization,
    capitalize_brand,
    comparison_seo_titles,
    format_comparison_phrase,
    is_comparison_query,
)
from linkops.gsc_intent import INTENT_COMPARISON


def _comparison_page() -> ContentItem:
    kw = "clickup vs trello"
    intro = (
        "ClickUp vs Trello is a common comparison for small teams choosing project management software. "
        "Both tools help teams organize work, but they take different approaches."
    )
    html = (
        "<h1>ClickUp vs Trello for Small Teams</h1>"
        f"<p>{intro}</p>"
        "<h2>ClickUp vs Trello: Quick Verdict</h2>"
        "<h2>FAQ</h2>"
        "<h3>Which tool is better for small teams?</h3>"
    )
    return ContentItem(
        id=101,
        type="post",
        title="ClickUp vs Trello for Small Teams",
        url="https://worktoolslab.com/clickup-vs-trello-for-small-teams/",
        slug="clickup-vs-trello-for-small-teams",
        content_html=html,
        excerpt_html="",
        modified="2024-01-01",
        existing_internal_links=[],
        word_count=len(intro.split()),
        plain_text=intro,
    )


def _report_blob(report) -> str:
    return str(asdict(report)).lower()


def test_capitalize_brand_clickup_and_trello():
    assert capitalize_brand("clickup") == "ClickUp"
    assert capitalize_brand("trello") == "Trello"
    assert capitalize_brand("monday.com") == "Monday.com"


def test_format_comparison_phrase():
    assert format_comparison_phrase("clickup vs trello") == "ClickUp vs Trello"
    assert format_comparison_phrase("monday.com vs asana") == "Monday.com vs Asana"


def test_is_comparison_query():
    assert is_comparison_query("clickup vs trello", INTENT_COMPARISON)
    assert is_comparison_query("monday.com vs asana", "")


def test_seo_title_not_best_prefix():
    titles = comparison_seo_titles("clickup vs trello")
    assert not titles[0].lower().startswith("best ")
    assert "ClickUp vs Trello" in titles[0]


def test_seo_title_preserves_brand_casing():
    report = analyze_content_optimization(
        [_comparison_page()],
        "https://worktoolslab.com/clickup-vs-trello-for-small-teams/",
        "clickup vs trello",
    )
    title = report.title_meta.seo_title
    assert "ClickUp" in title
    assert "Trello" in title
    assert "Clickup" not in title
    assert not title.startswith("Best ")


def test_comparison_faq_specific_not_broad_best():
    report = analyze_content_optimization(
        [_comparison_page()],
        "https://worktoolslab.com/clickup-vs-trello-for-small-teams/",
        "clickup vs trello",
        max_faq_suggestions=5,
    )
    assert report.query_intent == INTENT_COMPARISON
    for s in report.faq.suggestions:
        low = s.lower()
        assert "clickup" in low or "trello" in low
        assert "best collaboration" not in low
        assert "best project management software for small teams" not in low
    assert any("better than" in s.lower() or "difference between" in s.lower() for s in report.faq.suggestions)


def test_heading_suggestions_no_best_prefix():
    report = analyze_content_optimization(
        [_comparison_page()],
        "https://worktoolslab.com/clickup-vs-trello-for-small-teams/",
        "clickup vs trello",
        max_heading_suggestions=5,
    )
    for h in report.headings.suggestions:
        assert not h.lower().startswith("best clickup")
        assert "ClickUp vs Trello" in h


def test_meta_description_under_160_with_brands():
    report = analyze_content_optimization(
        [_comparison_page()],
        "https://worktoolslab.com/clickup-vs-trello-for-small-teams/",
        "clickup vs trello",
    )
    meta = report.title_meta.meta_description
    assert len(meta) <= 160
    assert "clickup" in meta.lower() or "ClickUp" in meta
    assert "trello" in meta.lower() or "Trello" in meta


def test_no_best_best_in_comparison_report():
    report = analyze_content_optimization(
        [_comparison_page()],
        "https://worktoolslab.com/clickup-vs-trello-for-small-teams/",
        "clickup vs trello",
    )
    assert "best clickup" not in _report_blob(report)
    assert "best best" not in _report_blob(report)
