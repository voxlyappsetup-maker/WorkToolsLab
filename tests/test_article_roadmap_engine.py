"""Tests for v1.7.0 new-article roadmap engine and report writer."""

from __future__ import annotations

import pytest

from linkops.article_roadmap_engine import build_article_roadmap_report
from linkops.article_roadmap_model import (
    ARTICLE_COMPARISON,
    ARTICLE_GUIDE,
    ARTICLE_REVIEW,
    ARTICLE_ROUNDUP,
    PRIORITY_HIGH,
    PRIORITY_LOW,
    PRIORITY_MANUAL,
    PRIORITY_MEDIUM,
)
from linkops.article_roadmap_report_writer import write_article_roadmap_reports
from linkops.content_model import ContentItem
from linkops.gsc_model import GscCache, GscQueryRow


def _page(slug: str, title: str, extra: str = "") -> ContentItem:
    plain = f"{title} {slug.replace('-', ' ')} {extra}"
    return ContentItem(
        id=abs(hash(slug)) % 100000,
        type="post",
        title=title,
        url=f"https://worktoolslab.com/{slug}/",
        slug=slug,
        content_html=f"<h1>{title}</h1><p>{plain}</p>",
        excerpt_html="",
        modified="2024-01-01",
        existing_internal_links=[],
        word_count=len(plain.split()),
        plain_text=plain,
    )


def _catalog_full() -> list[ContentItem]:
    return [
        _page(
            "clickup-vs-trello-for-small-teams",
            "ClickUp vs Trello for Small Teams",
            "clickup vs trello comparison for small teams",
        ),
        _page(
            "asana-vs-clickup-for-small-teams",
            "Asana vs ClickUp for Small Teams",
            "asana vs clickup comparison",
        ),
        _page(
            "best-project-management-tools-for-small-teams",
            "Best Project Management Tools for Small Teams",
            "best project management software tools planning",
        ),
        _page(
            "best-productivity-tools-for-small-teams",
            "Best Productivity Tools for Small Teams",
            "team productivity tools apps software",
        ),
        _page(
            "webex-review-for-small-businesses",
            "Webex Review for Small Businesses",
            "webex review video meetings",
        ),
        _page(
            "how-to-choose-project-management-software",
            "How to Choose Project Management Software",
            "how to choose project management software for small teams guide",
        ),
    ]


def _cache(queries: list[tuple[str, int, int, float]]) -> GscCache:
    return GscCache(
        imported_at="2026-05-29T12:00:00Z",
        queries=[
            GscQueryRow(q, clicks, imp, 0.0, pos) for q, clicks, imp, pos in queries
        ],
    )


def _find_candidate(report, keyword: str):
    key = keyword.lower()
    for c in report.all_candidates:
        if key in c.primary_keyword.lower():
            return c
        if any(key in s.lower() for s in c.secondary_queries):
            return c
    return None


def test_teamwork_vs_asana_candidate():
    report = build_article_roadmap_report(
        _cache([("teamwork vs asana", 0, 55, 32.0)]),
        _catalog_full(),
        min_impressions=10,
        max_candidates=20,
        include_manual_review=True,
    )
    c = _find_candidate(report, "teamwork vs asana")
    assert c is not None
    assert c.suggested_title == "Teamwork vs Asana for Small Teams"
    assert c.article_type == ARTICLE_COMPARISON
    assert "asana-vs-clickup" not in c.suggested_slug
    assert c.priority in (PRIORITY_HIGH, PRIORITY_MEDIUM)
    assert "teamwork" in c.target_gap_reason.lower() or "branded" in c.target_gap_reason.lower()
    assert "Asana vs ClickUp" in " ".join(c.editorial_notes) or "not Asana" in " ".join(
        c.editorial_notes
    ).lower() or "teamwork" in c.target_gap_reason.lower()


def test_vague_query_manual_or_low():
    report = build_article_roadmap_report(
        _cache([("small business teams", 0, 45, 40.0)]),
        _catalog_full(),
        min_impressions=10,
        include_manual_review=True,
    )
    c = _find_candidate(report, "small business teams")
    if c:
        assert c.priority in (PRIORITY_MANUAL, PRIORITY_LOW)
        assert "vague" in " ".join(c.editorial_notes).lower() or c.priority == PRIORITY_MANUAL
    else:
        excluded = [e for e in report.excluded_queries if "small business teams" in e.query]
        assert excluded
        assert excluded[0].category in ("vague", "unclear_intent", "already_covered") or "vague" in excluded[
            0
        ].exclusion_reason.lower()


def test_clickup_vs_trello_not_new_article():
    report = build_article_roadmap_report(
        _cache([("clickup vs trello", 0, 80, 28.0)]),
        _catalog_full(),
        min_impressions=10,
        exclude_existing_covered=True,
    )
    c = _find_candidate(report, "clickup vs trello")
    assert c is None
    excluded = [e for e in report.excluded_queries if e.query == "clickup vs trello"]
    assert excluded
    assert excluded[0].category == "already_covered"


def test_review_gap_candidate():
    report = build_article_roadmap_report(
        _cache([("smartsheet review for small business", 0, 42, 35.0)]),
        _catalog_full(),
        min_impressions=10,
        max_candidates=20,
    )
    c = _find_candidate(report, "smartsheet")
    assert c is not None
    assert c.article_type == ARTICLE_REVIEW
    assert "Smartsheet" in c.suggested_title
    assert "Review" in c.suggested_title


def test_roundup_ai_productivity_gap():
    report = build_article_roadmap_report(
        _cache([("best ai productivity tools for small teams", 0, 50, 30.0)]),
        _catalog_full(),
        min_impressions=10,
        max_candidates=20,
    )
    c = _find_candidate(report, "ai productivity")
    assert c is not None
    assert c.article_type == ARTICLE_ROUNDUP
    assert c.topic == "AI/productivity"
    assert "Productivity" in c.suggested_title or "productivity" in c.suggested_title.lower()


def test_guide_gap_not_forced_roundup():
    report = build_article_roadmap_report(
        _cache(
            [
                (
                    "how to choose project management software for small teams",
                    0,
                    38,
                    33.0,
                )
            ]
        ),
        [_page("best-task-tools", "Best Task Tools", "task tools list")],
        min_impressions=10,
        max_candidates=20,
        exclude_existing_covered=False,
    )
    c = _find_candidate(report, "how to choose")
    assert c is not None
    assert c.article_type == ARTICLE_GUIDE
    assert c.article_type != ARTICLE_ROUNDUP


def test_internal_link_plan_fields():
    report = build_article_roadmap_report(
        _cache([("teamwork vs asana", 0, 55, 32.0)]),
        _catalog_full(),
        min_impressions=10,
    )
    c = _find_candidate(report, "teamwork")
    assert c is not None
    assert isinstance(c.existing_related_pages, list)
    assert isinstance(c.suggested_internal_links_from, list)
    assert isinstance(c.suggested_internal_links_to, list)


def test_report_writer_sections_and_csv_columns(tmp_path, monkeypatch):
    import linkops.article_roadmap_report_writer as writer_mod

    monkeypatch.setattr(writer_mod, "REPORTS_DIR", tmp_path)
    report = build_article_roadmap_report(
        _cache(
            [
                ("teamwork vs asana", 0, 55, 32.0),
                ("smartsheet review for small business", 0, 42, 35.0),
            ]
        ),
        _catalog_full(),
        min_impressions=10,
        include_manual_review=True,
        include_low_priority=True,
    )
    md_path, csv_path = write_article_roadmap_reports(report, ts="test_roadmap")
    md = md_path.read_text(encoding="utf-8")
    for section in (
        "## Executive Summary",
        "## High-Priority New Article Opportunities",
        "## Medium-Priority Opportunities",
        "## Low-Priority / Monitor",
        "## Manual Review Queries",
        "## Suggested Content Calendar",
        "### Week 1",
        "## Internal Link Plan for New Articles",
        "## Excluded / Rejected Queries",
        "## Suggested LinkOps Commands",
    ):
        assert section in md
    import pandas as pd

    df = pd.read_csv(csv_path)
    for col in (
        "suggested_title",
        "suggested_slug",
        "article_type",
        "primary_keyword",
        "topic",
        "priority",
        "priority_score",
        "total_impressions",
        "target_gap_reason",
        "suggested_internal_links_from",
        "recommended_next_step",
    ):
        assert col in df.columns
