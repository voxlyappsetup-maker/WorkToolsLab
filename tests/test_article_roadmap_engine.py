"""Tests for v1.7.0+ new-article roadmap engine and report writer."""

from __future__ import annotations

import pytest

from linkops.article_roadmap_engine import (
    build_article_roadmap_report,
    collect_displayed_candidates,
    filter_high_quality_link_sources,
    find_existing_brand_review_page,
    is_branded_product_query,
    is_brand_mismatch_page,
    normalize_candidate_intent_key,
    page_matches_query_brand,
    safe_manual_review_title,
)
from linkops.article_roadmap_model import (
    ACTION_CREATE_NEW_ARTICLE,
    ACTION_MANUAL_REVIEW,
    ACTION_UPDATE_EXISTING_PAGE,
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


def _catalog_v172() -> list[ContentItem]:
    return _catalog_full() + [
        _page(
            "best-video-meeting-tools-for-small-businesses",
            "Best Video Meeting Tools for Small Businesses",
            "video meeting apps zoom teams webex meeting software",
        ),
        _page(
            "best-collaboration-tools-for-small-teams",
            "Best Collaboration Tools for Small Teams",
            "collaboration tools software for small teams",
        ),
        _page("blog", "Blog", "blog articles news"),
        _page("about", "About", "about worktoolslab"),
        _page("contact", "Contact", "contact us"),
        _page(
            "trello-review-for-small-businesses",
            "Trello Review for Small Businesses",
            "trello review kanban",
        ),
        _page(
            "trello-review-for-freelancers",
            "Trello Review for Freelancers",
            "trello review freelancers kanban board",
        ),
        _page(
            "microsoft-teams-review-for-small-businesses",
            "Microsoft Teams Review for Small Businesses",
            "microsoft teams review video meeting small business",
        ),
    ]


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
            "team productivity tools apps software team productivity software",
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
        blob = " ".join(
            [c.primary_keyword, *c.secondary_queries, *c.merged_queries]
        ).lower()
        if key in blob:
            return c
    return None


def test_productivity_intent_key_normalization():
    k1 = normalize_candidate_intent_key("team productivity tools", ARTICLE_ROUNDUP, "productivity")
    k2 = normalize_candidate_intent_key("team productivity software", ARTICLE_ROUNDUP, "productivity")
    assert k1 == k2 == "roundup:productivity"


def test_productivity_queries_consolidated_to_one_candidate():
    report = build_article_roadmap_report(
        _cache(
            [
                ("team productivity tools", 0, 40, 30.0),
                ("team productivity software", 0, 35, 32.0),
            ]
        ),
        _catalog_full(),
        min_impressions=10,
        max_candidates=20,
    )
    productivity_updates = [
        c
        for c in report.all_candidates
        if "productivity" in c.query_group_label or "productivity" in c.topic.lower()
    ]
    assert len(productivity_updates) == 1
    c = productivity_updates[0]
    assert "team productivity tools" in c.merged_queries
    assert "team productivity software" in c.merged_queries


def test_productivity_routes_to_existing_page_update():
    report = build_article_roadmap_report(
        _cache(
            [
                ("team productivity tools", 0, 45, 28.0),
                ("team productivity software", 0, 30, 30.0),
            ]
        ),
        _catalog_full(),
        min_impressions=10,
        max_candidates=20,
    )
    c = _find_candidate(report, "team productivity tools")
    assert c is not None
    assert c.action_type == ACTION_UPDATE_EXISTING_PAGE
    assert "best-productivity-tools-for-small-teams" in c.recommended_existing_url
    assert c.action_type != ACTION_CREATE_NEW_ARTICLE
    assert "Update:" in c.suggested_title
    assert "patch" in c.recommended_next_step.lower() or "optimize" in c.recommended_next_step.lower()


def test_medium_cannibalization_blocks_high_priority_create():
    """Create candidate with medium cannibalization should not be high priority."""
    from linkops.article_roadmap_engine import (
        _build_create_candidate_from_rows,
        calculate_cannibalization_adjusted_priority,
    )

    rows = [GscQueryRow("obscure niche tools xyz", 0, 50, 0.0, 35.0)]
    c = _build_create_candidate_from_rows(
        rows,
        catalog=_catalog_full(),
        gap_reason="No strong matching published page in WordPress cache.",
        query_group_label="roundup:niche",
        merged_queries=["obscure niche tools xyz"],
    )
    if c.cannibalization_risk == "medium" and c.action_type == ACTION_CREATE_NEW_ARTICLE:
        assert c.priority != PRIORITY_HIGH


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
    assert "asana-vs-clickup" not in (c.recommended_existing_url or c.suggested_slug)
    assert c.action_type in (ACTION_CREATE_NEW_ARTICLE, ACTION_MANUAL_REVIEW)
    assert c.priority in (PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_MANUAL)


def test_vague_query_manual_or_low():
    report = build_article_roadmap_report(
        _cache([("small business teams", 0, 45, 40.0)]),
        _catalog_full(),
        min_impressions=10,
        include_manual_review=True,
    )
    c = _find_candidate(report, "small business teams")
    assert c is not None
    assert c.priority == PRIORITY_MANUAL
    assert c.suggested_title.startswith("Manual Review:")
    assert "How to Small Business Teams" not in c.suggested_title


def test_meeting_apps_not_high_priority_create():
    report = build_article_roadmap_report(
        _cache([("best meeting apps for small business", 0, 55, 32.0)]),
        _catalog_v172(),
        min_impressions=10,
        max_candidates=20,
    )
    c = _find_candidate(report, "meeting apps")
    assert c is not None
    assert c.action_type in (ACTION_UPDATE_EXISTING_PAGE, ACTION_MANUAL_REVIEW)
    assert c.priority != PRIORITY_HIGH or c.action_type != ACTION_CREATE_NEW_ARTICLE
    assert c not in report.create_new_high
    if c.action_type == ACTION_UPDATE_EXISTING_PAGE:
        assert "video-meeting" in c.recommended_existing_url


def test_collaboration_small_business_not_confident_create():
    report = build_article_roadmap_report(
        _cache([("best collaboration tools for small business", 0, 48, 30.0)]),
        _catalog_v172(),
        min_impressions=10,
        max_candidates=20,
    )
    c = _find_candidate(report, "collaboration tools for small business")
    assert c is not None
    assert c.action_type in (ACTION_UPDATE_EXISTING_PAGE, ACTION_MANUAL_REVIEW)
    assert c.action_type != ACTION_CREATE_NEW_ARTICLE or c.priority != PRIORITY_HIGH


def test_job_management_ambiguous_manual_or_low():
    report = build_article_roadmap_report(
        _cache([("job management software for small teams", 0, 40, 35.0)]),
        _catalog_v172(),
        min_impressions=10,
        max_candidates=20,
        include_manual_review=True,
    )
    c = _find_candidate(report, "job management")
    assert c is not None
    assert c.priority != PRIORITY_HIGH
    assert c.action_type in (ACTION_MANUAL_REVIEW, ACTION_CREATE_NEW_ARTICLE)
    if c.action_type == ACTION_MANUAL_REVIEW:
        assert c.suggested_title.startswith("Manual Review:")
    else:
        assert any("job" in n.lower() or "scheduling" in n.lower() for n in c.editorial_notes)


def test_safe_manual_review_title():
    title, slug = safe_manual_review_title("small business teams")
    assert title == "Manual Review: small business teams"
    assert slug.startswith("manual-review-")


def test_summary_count_consistency(tmp_path, monkeypatch):
    import linkops.article_roadmap_report_writer as writer_mod

    monkeypatch.setattr(writer_mod, "REPORTS_DIR", tmp_path)
    report = build_article_roadmap_report(
        _cache(
            [
                ("team productivity tools", 0, 40, 30.0),
                ("best meeting apps for small business", 0, 55, 32.0),
                ("teamwork vs asana", 0, 55, 32.0),
            ]
        ),
        _catalog_v172(),
        min_impressions=10,
        max_candidates=5,
        include_manual_review=True,
    )
    displayed = report.displayed_roadmap_counts["total"]
    assert displayed == len(report.all_candidates)
    md_path, _ = write_article_roadmap_reports(report, ts="count_test")
    md = md_path.read_text(encoding="utf-8")
    assert f"**Total roadmap items:** {displayed}" in md
    assert f"{displayed} roadmap item(s) displayed" in report.executive_summary


def test_internal_link_filter_excludes_blog_when_topical_exists():
    catalog = _catalog_v172()
    urls = [
        "https://worktoolslab.com/blog/",
        "https://worktoolslab.com/best-productivity-tools-for-small-teams/",
        "https://worktoolslab.com/trello-review-for-small-businesses/",
    ]
    filtered = filter_high_quality_link_sources(
        urls,
        catalog,
        query="team productivity tools",
        topic="productivity",
        action_type=ACTION_CREATE_NEW_ARTICLE,
        limit=3,
    )
    assert "https://worktoolslab.com/blog/" not in filtered
    assert "https://worktoolslab.com/trello-review-for-small-businesses/" not in filtered
    assert "https://worktoolslab.com/best-productivity-tools-for-small-teams/" in filtered


def test_productivity_update_excludes_trello_freelancers_review():
    report = build_article_roadmap_report(
        _cache(
            [
                ("team productivity tools", 0, 45, 28.0),
                ("team productivity software", 0, 30, 30.0),
            ]
        ),
        _catalog_v172(),
        min_impressions=10,
        max_candidates=20,
    )
    c = _find_candidate(report, "team productivity tools")
    assert c is not None
    assert c.action_type == ACTION_UPDATE_EXISTING_PAGE
    links = " ".join(c.suggested_internal_links_from).lower()
    assert "trello-review-for-freelancers" not in links
    assert "trello-review-for-small-businesses" not in links


def test_productivity_update_related_pages_exclude_blog_and_trello():
    report = build_article_roadmap_report(
        _cache(
            [
                ("team productivity tools", 0, 45, 28.0),
                ("team productivity software", 0, 30, 30.0),
            ]
        ),
        _catalog_v172(),
        min_impressions=10,
        max_candidates=20,
    )
    c = _find_candidate(report, "team productivity tools")
    assert c is not None
    assert c.action_type == ACTION_UPDATE_EXISTING_PAGE
    related = " ".join(c.existing_related_pages).lower()
    assert "/blog" not in related
    assert "trello-review-for-freelancers" not in related
    assert "trello-review-for-small-businesses" not in related


def test_productivity_update_excludes_blog_from_link_from():
    report = build_article_roadmap_report(
        _cache([("team productivity tools", 0, 45, 28.0)]),
        _catalog_v172(),
        min_impressions=10,
        max_candidates=20,
    )
    c = _find_candidate(report, "team productivity tools")
    assert c is not None
    assert c.action_type == ACTION_UPDATE_EXISTING_PAGE
    assert not any("/blog" in u.lower() for u in c.suggested_internal_links_from)


def test_weak_only_link_sources_empty_for_productivity_update():
    catalog = [
        _page(
            "best-productivity-tools-for-small-teams",
            "Best Productivity Tools for Small Teams",
            "team productivity tools apps software",
        ),
        _page("blog", "Blog", "blog articles"),
        _page(
            "trello-review-for-freelancers",
            "Trello Review for Freelancers",
            "trello review freelancers",
        ),
    ]
    urls = [
        "https://worktoolslab.com/blog/",
        "https://worktoolslab.com/trello-review-for-freelancers/",
    ]
    filtered = filter_high_quality_link_sources(
        urls,
        catalog,
        query="team productivity tools",
        topic="productivity",
        action_type=ACTION_UPDATE_EXISTING_PAGE,
        target_url="https://worktoolslab.com/best-productivity-tools-for-small-teams/",
        limit=3,
    )
    assert filtered == []


def test_microsoft_teams_gap_reason_does_not_mention_webex():
    catalog = _catalog_v172() + [
        _page(
            "webex-review-for-small-businesses",
            "Webex Review for Small Businesses",
            "webex review video meetings microsoft teams zoom",
        ),
    ]
    report = build_article_roadmap_report(
        _cache([("microsoft teams for small business", 0, 25, 40.0)]),
        catalog,
        min_impressions=10,
        max_candidates=20,
        include_manual_review=True,
    )
    c = _find_candidate(report, "microsoft teams")
    assert c is not None
    assert c.action_type == ACTION_UPDATE_EXISTING_PAGE
    blob = " ".join(
        [
            c.target_gap_reason,
            c.update_reason,
            c.suggested_title,
            c.recommended_next_step,
            c.recommended_existing_url or "",
        ]
    ).lower()
    assert "webex" not in blob
    assert "microsoft teams" in c.target_gap_reason.lower()
    assert "microsoft-teams-review-for-small-businesses" in (
        c.recommended_existing_url or ""
    )


def test_branded_update_candidate_fields_are_consistent():
    catalog = _catalog_v172()
    report = build_article_roadmap_report(
        _cache([("microsoft teams for small business", 0, 30, 38.0)]),
        catalog,
        min_impressions=10,
        max_candidates=20,
    )
    c = _find_candidate(report, "microsoft teams")
    assert c is not None
    assert c.action_type == ACTION_UPDATE_EXISTING_PAGE
    assert "Microsoft Teams Review" in c.suggested_title
    assert "Microsoft Teams Review" in c.target_gap_reason
    assert c.recommended_existing_url.rstrip("/").endswith(
        "microsoft-teams-review-for-small-businesses"
    )
    assert "microsoft-teams-review-for-small-businesses" in c.recommended_next_step
    assert c.recommended_existing_url.rstrip("/") in c.recommended_next_step


def test_microsoft_teams_routes_to_microsoft_teams_review_not_webex():
    catalog = _catalog_v172() + [
        _page(
            "webex-review-for-small-businesses",
            "Webex Review for Small Businesses",
            "webex review video meetings microsoft teams zoom",
        ),
    ]
    report = build_article_roadmap_report(
        _cache([("microsoft teams for small business", 0, 25, 40.0)]),
        catalog,
        min_impressions=10,
        max_candidates=20,
        include_manual_review=True,
    )
    c = _find_candidate(report, "microsoft teams")
    assert c is not None
    assert c.action_type == ACTION_UPDATE_EXISTING_PAGE
    assert "microsoft-teams-review" in (c.recommended_existing_url or "")
    assert "webex-review" not in (c.recommended_existing_url or "")
    assert "How to Microsoft Teams" not in c.suggested_title


def test_microsoft_teams_manual_when_review_page_missing():
    catalog = [
        _page(
            "webex-review-for-small-businesses",
            "Webex Review for Small Businesses",
            "webex review microsoft teams mention",
        ),
    ]
    report = build_article_roadmap_report(
        _cache([("microsoft teams for small business", 0, 25, 40.0)]),
        catalog,
        min_impressions=10,
        include_manual_review=True,
    )
    c = _find_candidate(report, "microsoft teams")
    assert c is not None
    assert c.action_type == ACTION_MANUAL_REVIEW
    assert c.suggested_title.startswith("Manual Review:")
    assert "webex-review" not in (c.recommended_existing_url or "")


def test_webex_query_does_not_route_to_microsoft_teams_review():
    catalog = _catalog_v172() + [
        _page(
            "webex-review-for-small-businesses",
            "Webex Review for Small Businesses",
            "webex review video meetings",
        ),
    ]
    report = build_article_roadmap_report(
        _cache([("webex for small business", 0, 30, 35.0)]),
        catalog,
        min_impressions=10,
        max_candidates=20,
        include_manual_review=True,
    )
    c = _find_candidate(report, "webex")
    assert c is not None
    if c.action_type == ACTION_UPDATE_EXISTING_PAGE:
        assert "webex-review" in (c.recommended_existing_url or "")
        assert "microsoft-teams-review" not in (c.recommended_existing_url or "")


def test_brand_mismatch_guard_blocks_cross_brand_review():
    webex = _page(
        "webex-review-for-small-businesses",
        "Webex Review for Small Businesses",
        "webex video meetings",
    )
    ms = _page(
        "microsoft-teams-review-for-small-businesses",
        "Microsoft Teams Review for Small Businesses",
        "microsoft teams review",
    )
    assert is_brand_mismatch_page("microsoft teams for small business", webex)
    assert not is_brand_mismatch_page("microsoft teams for small business", ms)
    assert page_matches_query_brand("microsoft teams for small business", ms)
    upd = find_existing_brand_review_page("microsoft teams for small business", [webex, ms])
    assert upd is not None
    assert "microsoft-teams-review" in upd[0].url


def test_microsoft_teams_routes_to_review_update_or_manual():
    assert is_branded_product_query("microsoft teams for small business")
    catalog = _catalog_v172() + [
        _page(
            "webex-review-for-small-businesses",
            "Webex Review for Small Businesses",
            "webex review video meetings microsoft teams",
        ),
    ]
    report = build_article_roadmap_report(
        _cache([("microsoft teams for small business", 0, 25, 40.0)]),
        catalog,
        min_impressions=10,
        max_candidates=20,
        include_manual_review=True,
    )
    c = _find_candidate(report, "microsoft teams")
    assert c is not None
    assert "How to Microsoft Teams for Small Business for Small Teams" not in c.suggested_title
    assert c.action_type in (ACTION_UPDATE_EXISTING_PAGE, ACTION_MANUAL_REVIEW)
    if c.action_type == ACTION_UPDATE_EXISTING_PAGE:
        assert "microsoft-teams-review" in (c.recommended_existing_url or "")
        assert "webex-review" not in (c.recommended_existing_url or "")
    else:
        assert c.suggested_title.startswith("Manual Review:")


def test_executive_top_items_exclude_hidden_low_create():
    report = build_article_roadmap_report(
        _cache(
            [
                ("team productivity tools", 0, 45, 28.0),
                ("microsoft teams for small business", 0, 12, 55.0),
                ("teamwork vs asana", 0, 55, 32.0),
            ]
        ),
        _catalog_v172(),
        min_impressions=10,
        max_candidates=5,
        include_low_priority=False,
        include_manual_review=True,
    )
    displayed = collect_displayed_candidates(
        {
            "create_high": report.create_new_high,
            "create_medium": report.create_new_medium,
            "create_low": report.create_new_low,
            "update_high": report.update_existing_high,
            "update_medium": report.update_existing_medium,
            "update_low": report.update_existing_low,
            "manual": report.manual_review,
        },
        include_low=False,
        include_manual=True,
    )
    displayed_titles = {c.suggested_title for c in displayed}
    assert report.displayed_roadmap_counts.get("create", 0) == len(
        report.create_new_high
    ) + len(report.create_new_medium) + len(report.create_new_low)
    for c in report.top_candidates:
        assert c.suggested_title in displayed_titles
    assert "How to Microsoft Teams for Small Business for Small Teams" not in (
        report.executive_summary
    )
    if "Top items:" in report.executive_summary:
        top_section = report.executive_summary.split("Top items:", 1)[1]
        assert "How to Microsoft Teams" not in top_section


def test_top_items_match_visible_candidates():
    report = build_article_roadmap_report(
        _cache([("team productivity tools", 0, 45, 28.0)]),
        _catalog_v172(),
        min_impressions=10,
        max_candidates=10,
    )
    assert len(report.top_candidates) <= 5
    assert len(report.top_candidates) <= len(report.all_candidates)
    for c in report.top_candidates:
        assert c in report.all_candidates


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
    assert c.action_type == ACTION_CREATE_NEW_ARTICLE
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


def test_report_writer_v171_sections_and_csv(tmp_path, monkeypatch):
    import linkops.article_roadmap_report_writer as writer_mod

    monkeypatch.setattr(writer_mod, "REPORTS_DIR", tmp_path)
    report = build_article_roadmap_report(
        _cache(
            [
                ("team productivity tools", 0, 40, 30.0),
                ("team productivity software", 0, 35, 32.0),
                ("teamwork vs asana", 0, 55, 32.0),
            ]
        ),
        _catalog_full(),
        min_impressions=10,
        include_manual_review=True,
    )
    md_path, csv_path = write_article_roadmap_reports(report, ts="test_roadmap_v171")
    md = md_path.read_text(encoding="utf-8")
    for section in (
        "## Executive Summary",
        "## Create New Article Opportunities",
        "## Existing Page Update Opportunities",
        "## Consolidated / Merged Query Groups",
        "## Manual Review Queries",
        "## Excluded / Already Covered Queries",
        "## Suggested LinkOps Commands",
    ):
        assert section in md
    assert "patch --target-url" in md or "optimize --target-url" in md
    import pandas as pd

    df = pd.read_csv(csv_path)
    for col in (
        "action_type",
        "recommended_existing_url",
        "update_reason",
        "merged_queries",
        "content_gap_to_add",
        "query_group_label",
    ):
        assert col in df.columns
