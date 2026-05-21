"""Tests for read-only content optimization analysis."""

import pytest

from linkops.content_model import ContentItem
from linkops.content_optimization_model import (
    ALIGNMENT_ALIGNED,
    ALIGNMENT_MISALIGNED,
    COVERAGE_EXACT,
    COVERAGE_MISSING,
    REC_CONTENT,
    REC_REVIEW_MANUAL,
    REC_MONITOR,
    REC_NO_CHANGE,
    REC_TITLE_META,
)
from linkops.content_optimizer import (
    analyze_content_optimization,
    classify_coverage,
    classify_heading_coverage,
    compute_intent_alignment,
    find_item_by_url,
    smart_title_case,
)
from linkops.gsc_model import GscQueryPageRow
from linkops.gsc_intent import INTENT_BROAD_BEST, PAGE_REVIEW, PAGE_ROUNDUP
from linkops.gsc_model import GscCache, GscQueryRow


def _page(
    slug: str,
    title: str,
    body_html: str,
    plain: str | None = None,
    links: list | None = None,
) -> ContentItem:
    url = f"https://worktoolslab.com/{slug}/"
    plain_text = plain if plain is not None else body_html
    return ContentItem(
        id=abs(hash(slug)) % 100000,
        type="post",
        title=title,
        url=url,
        slug=slug,
        content_html=body_html,
        excerpt_html="",
        modified="2024-01-01",
        existing_internal_links=links or [],
        word_count=len(plain_text.split()),
        plain_text=plain_text,
    )


def _pm_roundup_page() -> ContentItem:
    intro = (
        "Small teams need project management tools that improve visibility and reduce confusion. "
        "The best tool is not always the one with the most features."
    )
    body = (
        f"<h1>Best Project Management Tools for Small Teams</h1>"
        f"<p>{intro}</p>"
        "<h2>Top Tools Compared</h2>"
        "<h2>How to Choose a Platform</h2>"
        "<h3>What should small teams look for?</h3>"
    )
    return _page(
        "best-project-management-tools-for-small-teams",
        "Best Project Management Tools for Small Teams",
        body,
        plain=intro + " Top tools compared how to choose a platform.",
    )


def _webex_review_page() -> ContentItem:
    intro = (
        "Webex review for small businesses starts with a simple question about fit. "
        "This guide covers pricing, meetings, and alternatives."
    )
    body = (
        f"<h1>Webex Review for Small Businesses</h1><p>{intro}</p>"
        "<h2>Is Webex Good for Small Businesses?</h2>"
    )
    return _page(
        "webex-review-for-small-businesses",
        "Webex Review for Small Businesses",
        body,
        plain=intro,
    )


def _review_page_misaligned() -> ContentItem:
    return _page(
        "monday-com-review",
        "Monday.com Review for Small Teams",
        "<h1>Monday.com Review</h1><p>Monday.com review pricing features.</p>",
        plain="Monday.com review pricing features for teams.",
    )


def test_exact_keyword_detected_in_title():
    status, _ = classify_coverage(
        "Best Project Management Tools for Small Teams",
        "Best Project Management Tools for Small Teams",
    )
    assert status == COVERAGE_EXACT


def test_exact_keyword_missing_from_intro():
    catalog = [_pm_roundup_page()]
    report = analyze_content_optimization(
        catalog,
        "https://worktoolslab.com/best-project-management-tools-for-small-teams/",
        "project management software for small teams",
    )
    intro_field = next(c for c in report.coverage if c.field_name == "first_150_words")
    assert intro_field.status in (COVERAGE_MISSING, "partial_match", "weak")
    assert report.intro.needs_direct_sentence or not report.intro.exact_keyword_early


def test_heading_suggestions_generated():
    report = analyze_content_optimization(
        [_pm_roundup_page()],
        "https://worktoolslab.com/best-project-management-tools-for-small-teams/",
        "project management software for small teams",
        max_heading_suggestions=3,
    )
    assert len(report.headings.suggestions) >= 1
    assert any("project management" in s.lower() or "Best" in s for s in report.headings.suggestions)


def test_faq_suggestions_broad_tools_query():
    report = analyze_content_optimization(
        [_pm_roundup_page()],
        "https://worktoolslab.com/best-project-management-tools-for-small-teams/",
        "project management software for small teams",
        max_faq_suggestions=5,
    )
    assert len(report.faq.suggestions) >= 3
    assert any("small teams" in s.lower() for s in report.faq.suggestions)


def test_faq_suggestions_webex_review_query():
    report = analyze_content_optimization(
        [_webex_review_page()],
        "https://worktoolslab.com/webex-review-for-small-businesses/",
        "Webex review for small businesses",
        max_faq_suggestions=4,
    )
    assert len(report.faq.suggestions) >= 2
    assert any("webex" in s.lower() for s in report.faq.suggestions)
    assert any("small business" in s.lower() for s in report.faq.suggestions)


def test_seo_title_contains_keyword_or_variant():
    report = analyze_content_optimization(
        [_pm_roundup_page()],
        "https://worktoolslab.com/best-project-management-tools-for-small-teams/",
        "project management software for small teams",
    )
    blob = (
        report.title_meta.seo_title
        + report.title_meta.focus_keyword
        + report.title_meta.meta_description
    ).lower()
    assert "project management" in blob or "small teams" in blob


def test_meta_description_under_160_characters():
    report = analyze_content_optimization(
        [_webex_review_page()],
        "https://worktoolslab.com/webex-review-for-small-businesses/",
        "Webex review for small businesses",
    )
    assert len(report.title_meta.meta_description) <= 160


def test_intent_alignment_aligned():
    alignment = compute_intent_alignment(INTENT_BROAD_BEST, PAGE_ROUNDUP)
    assert alignment == ALIGNMENT_ALIGNED


def test_intent_mismatch_detected():
    report = analyze_content_optimization(
        [_review_page_misaligned()],
        "https://worktoolslab.com/monday-com-review/",
        "project management software for small teams",
    )
    assert report.intent_alignment == ALIGNMENT_MISALIGNED
    assert report.overall_recommendation == REC_REVIEW_MANUAL


def test_action_type_title_meta_ctr_near_page_one():
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
    # Page with strong coverage so recommendation can be title_meta
    strong = _page(
        "best-project-management-tools-for-small-teams",
        "project management software for small teams",
        (
            "<h1>project management software for small teams</h1>"
            "<p>project management software for small teams helps small teams plan work. "
            "project management software for small teams should be simple.</p>"
            "<h2>project management software for small teams FAQ</h2>"
            "<h3>What is the best project management software for small teams?</h3>"
        ),
        plain=(
            "project management software for small teams " * 30
            + " FAQ best tools software small teams"
        ),
    )
    report = analyze_content_optimization(
        [strong],
        "https://worktoolslab.com/best-project-management-tools-for-small-teams/",
        "project management software for small teams",
        gsc_cache=gsc,
    )
    assert report.overall_recommendation == REC_TITLE_META


def test_missing_target_url_raises():
    with pytest.raises(ValueError, match="not found"):
        analyze_content_optimization(
            [_pm_roundup_page()],
            "https://worktoolslab.com/does-not-exist/",
            "test query",
        )


def test_find_item_by_url():
    item = find_item_by_url(
        [_pm_roundup_page()],
        "https://worktoolslab.com/best-project-management-tools-for-small-teams",
    )
    assert item is not None
    assert item.slug == "best-project-management-tools-for-small-teams"


def _pm_page_exact_headings() -> ContentItem:
    kw = "project management software for small teams"
    body = (
        f"<h1>Best Project Management Tools for Small Teams</h1>"
        f"<p>{kw} helps small teams stay organized. {kw} should be easy to adopt.</p>"
        f"<h2>{kw}</h2>"
        f"<h3>What is the best {kw}?</h3>"
    )
    return _page(
        "best-project-management-tools-for-small-teams",
        "Best Project Management Tools for Small Teams",
        body,
        plain=f"{kw} " * 40,
    )


def test_exact_keyword_in_headings_prevents_heading_gap():
    report = analyze_content_optimization(
        [_pm_page_exact_headings()],
        "https://worktoolslab.com/best-project-management-tools-for-small-teams/",
        "project management software for small teams",
    )
    headings_field = next(c for c in report.coverage if c.field_name == "headings")
    assert headings_field.status == COVERAGE_EXACT
    assert report.headings.keyword_in_h2_recommended is False
    assert not report.headings.missing_opportunities
    assert not any("H2" in g for g in report.content_gaps)


def test_no_change_needed_has_no_contradictory_content_gap():
    linking_pages = [
        _page(f"linker-{i}", f"Linker {i}", "<p>text</p>", links=[])
        for i in range(6)
    ]
    for p in linking_pages:
        p.existing_internal_links = [
            {
                "href": "https://worktoolslab.com/best-project-management-tools-for-small-teams/",
                "anchor_text": "PM tools",
                "normalized_url": "https://worktoolslab.com/best-project-management-tools-for-small-teams",
            }
        ]
    strong = _pm_page_exact_headings()
    gsc = GscCache(
        imported_at="2026-01-01",
        queries=[
            GscQueryRow(
                query="project management software for small teams",
                clicks=2,
                impressions=100,
                ctr=2.0,
                position=8.0,
            )
        ],
    )
    report = analyze_content_optimization(
        [strong, *linking_pages],
        "https://worktoolslab.com/best-project-management-tools-for-small-teams/",
        "project management software for small teams",
        gsc_cache=gsc,
    )
    assert report.overall_recommendation in (REC_NO_CHANGE, REC_MONITOR)
    assert report.content_gaps == [] or "No urgent" in " ".join(report.content_gaps).lower() or not report.content_gaps


def test_existing_relevant_slug_returns_keep_current_slug():
    report = analyze_content_optimization(
        [_pm_roundup_page()],
        "https://worktoolslab.com/best-project-management-tools-for-small-teams/",
        "project management software for small teams",
    )
    assert report.title_meta.slug_recommendation == "Keep current slug"


def test_title_case_keeps_for_lowercase():
    assert smart_title_case("best project management software for small teams") == (
        "Best Project Management Software for Small Teams"
    )
    assert " for " in smart_title_case("How to Choose Project Management Software for a Small Team")


def test_gsc_related_query_enrichment_when_exact_missing():
    gsc = GscCache(
        imported_at="2026-01-01",
        queries=[
            GscQueryRow(
                query="best project management tools small business",
                clicks=0,
                impressions=26,
                ctr=0.0,
                position=65.0,
            ),
        ],
        query_pages=[
            GscQueryPageRow(
                query="best project management tools small business",
                page="https://worktoolslab.com/best-project-management-tools-for-small-teams/",
                clicks=0,
                impressions=26,
                ctr=0.0,
                position=65.0,
            ),
        ],
    )
    report = analyze_content_optimization(
        [_pm_roundup_page()],
        "https://worktoolslab.com/best-project-management-tools-for-small-teams/",
        "project management software for small teams",
        gsc_cache=gsc,
    )
    assert report.gsc_metrics is not None
    assert report.gsc_metrics.available
    assert "related query" in (report.gsc_metrics.match_note or "").lower() or report.gsc_metrics.matched_via == "related"


def test_strong_coverage_and_links_returns_no_change_or_monitor():
    linking = []
    for i in range(5):
        p = _page(f"src-{i}", f"Source {i}", "<p>x</p>")
        p.existing_internal_links = [
            {
                "href": "https://worktoolslab.com/best-project-management-tools-for-small-teams/",
                "anchor_text": "pm",
                "normalized_url": "https://worktoolslab.com/best-project-management-tools-for-small-teams",
            }
        ]
        linking.append(p)
    gsc = GscCache(
        imported_at="2026-01-01",
        queries=[
            GscQueryRow(
                query="project management software for small teams",
                clicks=0,
                impressions=67,
                ctr=0.0,
                position=72.0,
            )
        ],
    )
    report = analyze_content_optimization(
        [_pm_page_exact_headings(), *linking],
        "https://worktoolslab.com/best-project-management-tools-for-small-teams/",
        "project management software for small teams",
        gsc_cache=gsc,
    )
    assert report.overall_recommendation in (REC_NO_CHANGE, REC_MONITOR)


def test_webex_long_tail_gsc_enrichment():
    gsc = GscCache(
        imported_at="2026-01-01",
        queries=[
            GscQueryRow(
                query="is webex good for small business video meetings and calling",
                clicks=0,
                impressions=40,
                ctr=0.0,
                position=55.0,
            ),
            GscQueryRow(
                query="webex for small business",
                clicks=0,
                impressions=30,
                ctr=0.0,
                position=48.0,
            ),
        ],
        query_pages=[
            GscQueryPageRow(
                query="webex for small business",
                page="https://worktoolslab.com/webex-review-for-small-businesses/",
                clicks=0,
                impressions=30,
                ctr=0.0,
                position=48.0,
            ),
        ],
    )
    report = analyze_content_optimization(
        [_webex_review_page()],
        "https://worktoolslab.com/webex-review-for-small-businesses/",
        "Webex review for small businesses",
        gsc_cache=gsc,
    )
    assert report.gsc_metrics is not None
    assert report.gsc_metrics.available
    assert "webex" in report.gsc_metrics.query.lower()
