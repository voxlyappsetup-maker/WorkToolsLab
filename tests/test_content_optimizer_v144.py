"""Tests for v1.4.4 comparison FAQ coverage scoring."""

from linkops.content_model import ContentItem
from linkops.content_optimization_model import COVERAGE_STRONG, REC_FAQ_OPTIMIZATION, REC_MONITOR, REC_NO_CHANGE
from linkops.content_optimizer import (
    analyze_content_optimization,
    classify_faq_coverage,
    count_strong_comparison_faqs,
    extract_comparison_entities,
    _comparison_faq_pattern_types,
    _generate_faq_suggestions,
)
from linkops.gsc_intent import INTENT_COMPARISON


def _clickup_trello_faq_page() -> ContentItem:
    intro = (
        "ClickUp vs Trello is a common comparison for small teams. "
        "ClickUp vs Trello helps teams compare project management options."
    ) * 5
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
    return ContentItem(
        id=201,
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


def _linking_pages(count: int = 5) -> list[ContentItem]:
    pages = []
    for i in range(count):
        p = ContentItem(
            id=300 + i,
            type="post",
            title=f"Linker {i}",
            url=f"https://worktoolslab.com/linker-{i}/",
            slug=f"linker-{i}",
            content_html="<p>text</p>",
            excerpt_html="",
            modified="2024-01-01",
            existing_internal_links=[
                {
                    "href": "https://worktoolslab.com/clickup-vs-trello-for-small-teams/",
                    "anchor_text": "ClickUp vs Trello",
                    "normalized_url": "https://worktoolslab.com/clickup-vs-trello-for-small-teams",
                }
            ],
            word_count=1,
            plain_text="text",
        )
        pages.append(p)
    return pages


def test_extract_comparison_entities():
    assert extract_comparison_entities("clickup vs trello") == ("ClickUp", "Trello")
    assert extract_comparison_entities("monday.com vs asana") == ("Monday.com", "Asana")
    assert extract_comparison_entities("asana vs clickup") == ("Asana", "ClickUp")


def test_five_comparison_faqs_score_strong():
    page = _clickup_trello_faq_page()
    faq_items = [
        "Is ClickUp Better Than Trello?",
        "Is Trello Easier to Use Than ClickUp?",
        "Which Is Better for Small Teams, ClickUp or Trello?",
        "What Is the Main Difference Between ClickUp and Trello?",
        "Should a Small Business Use ClickUp or Trello?",
    ]
    assert count_strong_comparison_faqs(faq_items, "ClickUp", "Trello") >= 5
    status, detail = classify_faq_coverage("clickup vs trello", INTENT_COMPARISON, faq_items)
    assert status == COVERAGE_STRONG
    assert "strong comparison" in detail.lower()


def test_strong_comparison_faq_not_faq_optimization():
    report = analyze_content_optimization(
        [_clickup_trello_faq_page(), *_linking_pages(5)],
        "https://worktoolslab.com/clickup-vs-trello-for-small-teams/",
        "clickup vs trello",
    )
    faq_field = next(c for c in report.coverage if c.field_name == "faq")
    assert faq_field.status == COVERAGE_STRONG
    assert report.overall_recommendation in (REC_NO_CHANGE, REC_MONITOR)
    assert report.overall_recommendation != REC_FAQ_OPTIMIZATION
    assert "Improve FAQ coverage only" not in " ".join(report.content_gaps)


def test_no_missing_faq_when_semantically_covered():
    existing = [
        "Is ClickUp Better Than Trello?",
        "Is Trello Easier to Use Than ClickUp?",
        "Which Is Better for Small Teams, ClickUp or Trello?",
        "What Is the Main Difference Between ClickUp and Trello?",
        "Should a Small Business Use ClickUp or Trello?",
    ]
    suggestions = _generate_faq_suggestions(
        "clickup vs trello",
        INTENT_COMPARISON,
        "project_management",
        existing,
        5,
    )
    assert suggestions == []


def test_which_better_variants_equivalent_for_dedupe():
    left, right = "ClickUp", "Trello"
    a = _comparison_faq_pattern_types(
        "Which Is Better for Small Teams, ClickUp or Trello?", left, right
    )
    b = _comparison_faq_pattern_types(
        "ClickUp vs Trello: Which Is Better for Small Teams?", left, right
    )
    assert "which_better" in a
    assert "which_better" in b


def test_report_includes_strong_comparison_coverage_note():
    report = analyze_content_optimization(
        [_clickup_trello_faq_page(), *_linking_pages(5)],
        "https://worktoolslab.com/clickup-vs-trello-for-small-teams/",
        "clickup vs trello",
    )
    assert report.faq.coverage_note == "strong comparison coverage detected"
    assert not report.faq.suggestions
