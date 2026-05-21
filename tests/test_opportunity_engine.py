"""Tests for GSC opportunity scoring and status detection."""

from linkops.content_model import ContentItem
from linkops.gsc_model import (
    GscCache,
    GscQueryPageRow,
    GscQueryRow,
    STATUS_CANNIBALIZATION,
    STATUS_CONTENT_OPTIMIZATION,
    STATUS_CORRECT_PAGE,
    STATUS_INTERNAL_LINKS,
    STATUS_NO_TARGET,
    STATUS_OLD_URL,
)
from linkops.opportunity_engine import (
    _best_catalog_match,
    _is_old_or_duplicate_url,
    analyze_opportunities,
    build_catalog_index,
)


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


def _catalog() -> list[ContentItem]:
    return [
        _page(
            "best-project-management-tools-for-small-teams",
            "Best Project Management Tools for Small Teams",
            "project management software planning roadmap milestones for small teams",
        ),
        _page(
            "best-project-management-tools-for-freelancers",
            "Best Project Management Tools for Freelancers",
            "freelance project management tools solo client work",
        ),
        _page(
            "clickup-vs-trello-for-small-teams",
            "ClickUp vs Trello for Small Teams",
            "clickup trello comparison kanban tasks",
        ),
        _page(
            "notion-vs-trello-vs-clickup-which-one-is-best-for-your-workflow",
            "Notion vs Trello vs ClickUp: Which One Is Best for Your Workflow?",
            "notion trello clickup workflow documentation",
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


def test_query_matches_expected_pages():
    catalog = _catalog()
    index = build_catalog_index(catalog)
    m1 = _best_catalog_match("project management software for small teams", index)
    assert m1.in_catalog
    assert "small-teams" in m1.url
    m2 = _best_catalog_match("freelance project management tools", index)
    assert m2.in_catalog
    assert "freelancers" in m2.url
    m3 = _best_catalog_match("trello vs clickup", index)
    assert m3.in_catalog
    assert "clickup-vs-trello" in m3.url
    m4 = _best_catalog_match("business communication tools", index)
    assert m4.in_catalog
    assert "small-businesses" in m4.url
    m5 = _best_catalog_match("remote work communication tools", index)
    assert m5.in_catalog
    assert "remote-teams" in m5.url


def test_old_url_detection():
    catalog = _catalog()
    index = build_catalog_index(catalog)
    assert _is_old_or_duplicate_url(
        "https://worktoolslab.com/best-communication-tools-for-remote-teams-2/",
        index,
    )
    assert _is_old_or_duplicate_url(
        "http://worktoolslab.com/best-communication-tools-for-remote-teams/",
        index,
    )


def test_cannibalization_detection():
    catalog = _catalog()
    cache = GscCache(
        imported_at="2024-01-01",
        queries=[
            GscQueryRow("trello vs clickup", 0, 90, 0.0, 35.0),
        ],
        query_pages=[
            GscQueryPageRow(
                "trello vs clickup",
                "https://worktoolslab.com/clickup-vs-trello-for-small-teams/",
                0,
                50,
                0.0,
                35.0,
            ),
            GscQueryPageRow(
                "trello vs clickup",
                "https://worktoolslab.com/notion-vs-trello-vs-clickup-which-one-is-best-for-your-workflow/",
                0,
                40,
                0.0,
                42.0,
            ),
        ],
    )
    report = analyze_opportunities(cache, catalog, min_impressions=20, max_clicks=0)
    cannibal = [o for o in report.opportunities if o.status == STATUS_CANNIBALIZATION]
    assert cannibal
    assert "trello vs clickup" in cannibal[0].query.lower()


def test_no_target_query(monkeypatch):
    monkeypatch.setattr(
        "linkops.opportunity_engine.load_query_target_overrides",
        lambda: {},
    )
    catalog = _catalog()
    cache = GscCache(
        imported_at="2024-01-01",
        queries=[
            GscQueryRow("flibbertigibbet zq99 quantum flute calibration", 0, 50, 0.0, 45.0),
        ],
    )
    report = analyze_opportunities(cache, catalog, min_impressions=20, max_clicks=0)
    assert report.opportunities
    no_target = [o for o in report.opportunities if o.status == STATUS_NO_TARGET]
    assert no_target


def test_correct_page_with_gsc_alignment():
    catalog = _catalog()
    cache = GscCache(
        imported_at="2024-01-01",
        queries=[
            GscQueryRow("remote work communication tools", 0, 100, 0.0, 28.0),
        ],
        query_pages=[
            GscQueryPageRow(
                "remote work communication tools",
                "https://worktoolslab.com/best-communication-tools-for-remote-teams/",
                0,
                100,
                0.0,
                28.0,
            ),
        ],
    )
    report = analyze_opportunities(cache, catalog, min_impressions=20, max_clicks=0)
    opp = report.opportunities[0]
    assert opp.status in (STATUS_CORRECT_PAGE, STATUS_CONTENT_OPTIMIZATION, STATUS_INTERNAL_LINKS)
    assert "remote-teams" in opp.target_url


def test_old_url_status_in_report():
    catalog = _catalog()
    cache = GscCache(
        imported_at="2024-01-01",
        queries=[GscQueryRow("remote work communication tools", 0, 80, 0.0, 30.0)],
        query_pages=[
            GscQueryPageRow(
                "remote work communication tools",
                "http://worktoolslab.com/best-communication-tools-for-remote-teams/",
                0,
                80,
                0.0,
                30.0,
            ),
        ],
    )
    report = analyze_opportunities(cache, catalog, min_impressions=20, max_clicks=0)
    old = [o for o in report.opportunities if o.status == STATUS_OLD_URL]
    assert old


def test_content_optimization_when_query_missing_from_headings():
    links = [
        {
            "href": "https://worktoolslab.com/other/",
            "normalized_url": "https://worktoolslab.com/other",
            "anchor_text": "other",
        }
    ] * 4
    catalog = [
        _page(
            "best-project-management-tools-for-small-teams",
            "Best Project Management Tools for Small Teams",
            (
                "project management software planning roadmap milestones for small teams. "
                "waterfall methodology critical path resource leveling techniques."
            ),
            links=links,
        ),
    ]
    cache = GscCache(
        imported_at="2024-01-01",
        queries=[
            GscQueryRow(
                "waterfall methodology critical path resource leveling",
                0,
                60,
                0.0,
                40.0,
            ),
        ],
        query_pages=[
            GscQueryPageRow(
                "waterfall methodology critical path resource leveling",
                "https://worktoolslab.com/best-project-management-tools-for-small-teams/",
                0,
                60,
                0.0,
                40.0,
            ),
        ],
    )
    report = analyze_opportunities(cache, catalog, min_impressions=20, max_clicks=0)
    statuses = {o.status for o in report.opportunities}
    assert STATUS_CONTENT_OPTIMIZATION in statuses or STATUS_CORRECT_PAGE in statuses
