"""Tests for v1.3.1 GSC intent matching, overrides, and report fields."""

import json
from pathlib import Path

import pytest

from linkops.content_model import ContentItem
from linkops.gsc_intent import (
    ACTION_OLD_URL,
    ACTION_TITLE_META_CTR,
    INTENT_BROAD_BEST,
    PAGE_COMPARISON,
    PAGE_REVIEW,
    PAGE_ROUNDUP,
    detect_gsc_page_type,
    detect_query_intent,
)
from linkops.gsc_model import GscCache, GscQueryRow, STATUS_OLD_URL
from linkops.opportunity_engine import _best_catalog_match, analyze_opportunities, build_catalog_index
from linkops.query_overrides import load_query_target_overrides


def _page(
    slug: str,
    title: str,
    extra_plain: str = "",
    links: list | None = None,
) -> ContentItem:
    url = f"https://worktoolslab.com/{slug}/"
    plain = f"{title} {slug.replace('-', ' ')} {extra_plain}"
    return ContentItem(
        id=hash(slug) % 10000,
        type="post",
        title=title,
        url=url,
        slug=slug,
        content_html=f"<h1>{title}</h1><p>{plain}</p>",
        excerpt_html="",
        modified="2024-01-01",
        existing_internal_links=links or [],
        word_count=len(plain.split()),
        plain_text=plain,
    )


def _full_catalog() -> list[ContentItem]:
    links = [
        {
            "href": "https://worktoolslab.com/other/",
            "normalized_url": "https://worktoolslab.com/other",
            "anchor_text": "other",
        }
    ] * 4
    return [
        _page(
            "best-project-management-tools-for-small-teams",
            "Best Project Management Tools for Small Teams",
            "project management software tools platforms apps for small teams and small business",
        ),
        _page(
            "best-project-management-tools-for-freelancers",
            "Best Project Management Tools for Freelancers",
            "freelance project management tools solo client work",
        ),
        _page(
            "monday-com-review-for-small-teams",
            "Monday.com Review for Small Teams",
            "monday.com project management software review planning roadmap",
        ),
        _page(
            "task-management-vs-project-management",
            "Task Management vs Project Management: What Is the Difference?",
            "task management vs project management comparison guide",
        ),
        _page(
            "clickup-vs-trello-for-small-teams",
            "ClickUp vs Trello for Small Teams",
            "clickup trello comparison kanban tasks",
        ),
        _page(
            "trello-review-for-freelancers",
            "Trello Review for Freelancers",
            "trello review kanban board freelancers",
            links=links,
        ),
        _page(
            "best-communication-tools-for-small-businesses",
            "Best Communication Tools for Small Businesses",
            "business communication tools slack zoom messaging",
        ),
        _page(
            "best-communication-tools-for-remote-teams",
            "Best Communication Tools for Remote Teams",
            "remote work communication tools slack zoom video chat messaging",
        ),
    ]


@pytest.mark.parametrize(
    "query,expected_slug_part",
    [
        ("project management software for small teams", "best-project-management-tools-for-small-teams"),
        ("project management tools for small business", "best-project-management-tools-for-small-teams"),
        ("best project management tools small business", "best-project-management-tools-for-small-teams"),
        ("freelance project management tools", "best-project-management-tools-for-freelancers"),
        ("clickup vs trello", "clickup-vs-trello"),
        ("trello vs clickup", "clickup-vs-trello"),
    ],
)
def test_broad_and_comparison_queries_map_correctly(query, expected_slug_part):
    catalog = _full_catalog()
    index = build_catalog_index(catalog)
    match = _best_catalog_match(query, index, overrides={})
    assert match.in_catalog
    assert expected_slug_part in match.url.replace("_", "-")


def test_broad_query_prefers_roundup_over_review():
    catalog = _full_catalog()
    index = build_catalog_index(catalog)
    match = _best_catalog_match(
        "project management software for small teams",
        index,
        overrides={},
    )
    assert detect_query_intent("project management software for small teams") == INTENT_BROAD_BEST
    assert detect_gsc_page_type(match.item) == PAGE_ROUNDUP
    assert "monday" not in match.url


def test_broad_query_prefers_roundup_over_comparison():
    catalog = _full_catalog()
    index = build_catalog_index(catalog)
    match = _best_catalog_match(
        "project management tools for small business",
        index,
        overrides={},
    )
    assert detect_gsc_page_type(match.item) == PAGE_ROUNDUP
    assert "task-management-vs-project" not in match.url


def test_trello_review_query_prefers_review_page():
    catalog = _full_catalog()
    index = build_catalog_index(catalog)
    match = _best_catalog_match("trello review", index, overrides={})
    assert detect_gsc_page_type(match.item) == PAGE_REVIEW
    assert "trello-review" in match.url


def test_page_type_detection():
    item = _page("best-project-management-tools-for-small-teams", "Best PM Tools for Small Teams")
    assert detect_gsc_page_type(item) == PAGE_ROUNDUP
    review = _page("monday-com-review", "Monday.com Review")
    assert detect_gsc_page_type(review) == PAGE_REVIEW
    comp = _page("clickup-vs-trello", "ClickUp vs Trello")
    assert detect_gsc_page_type(comp) == PAGE_COMPARISON


def test_query_intent_broad_commercial():
    assert detect_query_intent("project management software for small teams") == INTENT_BROAD_BEST
    assert detect_query_intent("clickup vs trello") == "comparison"
    assert detect_query_intent("trello review") == "specific_review"


def test_override_file_forces_target(tmp_path, monkeypatch):
    override_file = tmp_path / "overrides.json"
    override_file.write_text(
        json.dumps(
            {
                "project management software for small teams": (
                    "https://worktoolslab.com/best-project-management-tools-for-small-teams/"
                ),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "linkops.opportunity_engine.load_query_target_overrides",
        lambda: load_query_target_overrides(override_file),
    )
    catalog = [_page("monday-com-review", "Monday.com Review", "monday project management")]
    cache = GscCache(
        imported_at="2024-01-01",
        queries=[GscQueryRow("project management software for small teams", 0, 50, 0.0, 40.0)],
    )
    report = analyze_opportunities(cache, catalog, min_impressions=20, max_clicks=0)
    opp = report.opportunities[0]
    assert opp.override_used is True
    assert "best-project-management-tools-for-small-teams" in opp.target_url


def test_missing_override_file_does_not_crash(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "linkops.opportunity_engine.load_query_target_overrides",
        lambda: load_query_target_overrides(tmp_path / "missing.json"),
    )
    catalog = _full_catalog()
    cache = GscCache(
        imported_at="2024-01-01",
        queries=[GscQueryRow("freelance project management tools", 0, 40, 0.0, 35.0)],
    )
    report = analyze_opportunities(cache, catalog, min_impressions=20, max_clicks=0)
    assert report.opportunities


def test_invalid_override_target_reported_safely(monkeypatch):
    monkeypatch.setattr(
        "linkops.opportunity_engine.load_query_target_overrides",
        lambda: {
            "unknown widget tools": "https://worktoolslab.com/no-such-article-slug-here/",
        },
    )
    catalog = _full_catalog()
    cache = GscCache(
        imported_at="2024-01-01",
        queries=[GscQueryRow("unknown widget tools", 0, 30, 0.0, 40.0)],
    )
    report = analyze_opportunities(cache, catalog, min_impressions=20, max_clicks=0)
    opp = report.opportunities[0]
    assert opp.override_used is True
    assert "no-such-article" in opp.target_url
    assert "override" in opp.reason.lower() or "override" in opp.target_selection_reason.lower()


def test_action_type_title_meta_ctr():
    links = [
        {
            "href": "https://worktoolslab.com/other/",
            "normalized_url": "https://worktoolslab.com/other",
            "anchor_text": "x",
        }
    ] * 4
    catalog = [
        _page(
            "best-communication-tools-for-remote-teams",
            "Best Communication Tools for Remote Teams",
            "remote work communication tools slack zoom",
            links=links,
        ),
    ]
    cache = GscCache(
        imported_at="2024-01-01",
        queries=[GscQueryRow("remote work communication tools", 0, 100, 0.0, 12.0)],
    )
    report = analyze_opportunities(cache, catalog, min_impressions=20, max_clicks=0)
    opp = report.opportunities[0]
    assert opp.action_type == ACTION_TITLE_META_CTR


def test_action_type_old_url_monitor():
    catalog = _full_catalog()
    cache = GscCache(
        imported_at="2024-01-01",
        queries=[GscQueryRow("remote work communication tools", 0, 80, 0.0, 30.0)],
        query_pages=[],
    )
    from linkops.gsc_model import GscQueryPageRow

    cache.query_pages = [
        GscQueryPageRow(
            "remote work communication tools",
            "http://worktoolslab.com/best-communication-tools-for-remote-teams/",
            0,
            80,
            0.0,
            30.0,
        ),
    ]
    report = analyze_opportunities(cache, catalog, min_impressions=20, max_clicks=0)
    opp = next(o for o in report.opportunities if o.status == STATUS_OLD_URL)
    assert opp.action_type == ACTION_OLD_URL
