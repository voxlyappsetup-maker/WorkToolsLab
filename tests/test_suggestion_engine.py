"""Tests for suggestion scoring (v1.1/v1.2)."""

from linkops.content_model import ContentItem
from linkops.suggestion_engine import (
    DOMAIN_STOPWORDS,
    detect_clusters,
    generate_suggestions,
    item_links_to_target,
)


def _item(
    item_id: int,
    url: str,
    title: str,
    plain: str,
    slug: str,
    links: list | None = None,
) -> ContentItem:
    return ContentItem(
        id=item_id,
        type="post",
        title=title,
        url=url,
        slug=slug,
        content_html=f"<p>{plain}</p>",
        excerpt_html="",
        modified="2024-01-01",
        existing_internal_links=links or [],
        word_count=len(plain.split()),
        plain_text=plain,
    )


def test_communication_target_prefers_related_over_unrelated():
    target_url = "https://worktoolslab.com/best-video-meeting-tools/"
    catalog = [
        _item(
            10,
            target_url,
            "Best Video Meeting Tools",
            "zoom google meet remote communication video meetings chat",
            "best-video-meeting-tools",
        ),
        _item(
            1,
            "https://worktoolslab.com/slack-vs-microsoft-teams/",
            "Slack vs Microsoft Teams",
            "slack microsoft teams communication collaboration chat messaging",
            "slack-vs-microsoft-teams",
        ),
        _item(
            2,
            "https://worktoolslab.com/asana-review/",
            "Asana Review",
            "asana project management tasks gantt planning roadmap",
            "asana-review",
        ),
        _item(
            3,
            "https://worktoolslab.com/best-accounting-software/",
            "Best Accounting Software",
            "accounting bookkeeping invoices taxes",
            "best-accounting-software",
        ),
    ]
    report = generate_suggestions(
        catalog,
        target_url=target_url,
        target_keyword="communication remote zoom",
        max_suggestions=5,
    )
    assert len(report.suggestions) >= 1
    titles = [s.source_title for s in report.suggestions]
    assert "Slack vs Microsoft Teams" in titles
    scores = {s.source_title: s.score for s in report.suggestions}
    assert scores.get("Slack vs Microsoft Teams", 0) > scores.get("Best Accounting Software", 0)


def test_communication_target_ranks_tool_pages_above_project_management():
    target_url = "https://worktoolslab.com/best-communication-tools-for-remote-teams/"
    catalog = [
        _item(
            10,
            target_url,
            "Best Communication Tools for Remote Teams",
            "communication tools for remote teams slack zoom google meet video chat messaging",
            "best-communication-tools-for-remote-teams",
        ),
        _item(
            1,
            "https://worktoolslab.com/slack-review/",
            "Slack Review",
            "slack chat messaging communication remote teams video calls",
            "slack-review",
        ),
        _item(
            2,
            "https://worktoolslab.com/zoom-review/",
            "Zoom Review",
            "zoom video meetings remote communication calls web conferencing",
            "zoom-review",
        ),
        _item(
            3,
            "https://worktoolslab.com/google-meet-review/",
            "Google Meet Review",
            "google meet video meetings remote communication calls",
            "google-meet-review",
        ),
        _item(
            4,
            "https://worktoolslab.com/webex-review/",
            "Webex Review",
            "webex video meetings remote communication calls conferencing",
            "webex-review",
        ),
        _item(
            5,
            "https://worktoolslab.com/asana-review/",
            "Asana Review",
            "asana project management planning roadmap timeline milestones",
            "asana-review",
        ),
        _item(
            6,
            "https://worktoolslab.com/clickup-review/",
            "ClickUp Review",
            "clickup task management kanban backlog priority due date",
            "clickup-review",
        ),
    ]
    report = generate_suggestions(
        catalog,
        target_url=target_url,
        target_keyword="communication tools remote teams",
        max_suggestions=8,
    )
    titles = [s.source_title for s in report.suggestions]
    comm_tools = {"Slack Review", "Zoom Review", "Google Meet Review", "Webex Review"}
    pm_tools = {"Asana Review", "ClickUp Review"}

    assert comm_tools & set(titles), "Expected communication tool pages in suggestions"
    for pm in pm_tools:
        if pm in titles:
            pm_score = next(s.score for s in report.suggestions if s.source_title == pm)
            comm_scores = [
                s.score for s in report.suggestions if s.source_title in comm_tools
            ]
            assert pm_score < max(comm_scores), f"{pm} should rank below communication pages"

    pm_in_strong = [s for s in report.strong if s.source_title in pm_tools]
    assert not pm_in_strong, "Project management pages should not be strong suggestions"


def test_project_management_not_low_risk_for_communication_without_context():
    target_url = "https://worktoolslab.com/best-communication-tools-for-remote-teams/"
    catalog = [
        _item(
            10,
            target_url,
            "Best Communication Tools for Remote Teams",
            "communication tools for remote teams slack zoom google meet video chat",
            "best-communication-tools-for-remote-teams",
        ),
        _item(
            1,
            "https://worktoolslab.com/asana-review/",
            "Asana Review",
            "asana project management planning roadmap timeline milestones",
            "asana-review",
        ),
        _item(
            2,
            "https://worktoolslab.com/trello-review/",
            "Trello Review",
            "trello kanban boards project planning milestones timeline",
            "trello-review",
        ),
    ]
    report = generate_suggestions(
        catalog,
        target_url=target_url,
        target_keyword="communication tools remote teams",
        max_suggestions=5,
    )
    for s in report.suggestions:
        if s.source_title in ("Asana Review", "Trello Review"):
            assert s.risk_level != "low", "PM pages should not be low-risk for communication target"


def test_generic_words_do_not_dominate_scoring():
    target_url = "https://worktoolslab.com/best-communication-tools-for-remote-teams/"
    catalog = [
        _item(
            10,
            target_url,
            "Best Communication Tools for Remote Teams",
            "communication tools for remote teams slack zoom video chat messaging",
            "best-communication-tools-for-remote-teams",
        ),
        _item(
            1,
            "https://worktoolslab.com/best-small-business-tools/",
            "Best Small Business Tools",
            "best tools for small teams business software review guide comparison",
            "best-small-business-tools",
        ),
        _item(
            2,
            "https://worktoolslab.com/slack-review/",
            "Slack Review",
            "slack chat messaging communication remote video calls",
            "slack-review",
        ),
    ]
    report = generate_suggestions(
        catalog,
        target_url=target_url,
        target_keyword="communication tools remote teams",
        max_suggestions=5,
    )
    titles = [s.source_title for s in report.suggestions]
    assert "Slack Review" in titles
    generic_only = [
        r for r in report.rejected
        if r.source_title == "Best Small Business Tools"
    ]
    accepted_generic = [s for s in report.suggestions if s.source_title == "Best Small Business Tools"]
    if accepted_generic:
        slack_score = next(s.score for s in report.suggestions if s.source_title == "Slack Review")
        assert accepted_generic[0].score < slack_score
    else:
        assert generic_only or "Best Small Business Tools" not in titles


def test_domain_stopwords_excluded_from_meaningful_tokens():
    tokens = DOMAIN_STOPWORDS
    assert "best" in tokens
    assert "tools" in tokens
    assert "teams" in tokens
    assert "small" in tokens


def test_high_risk_excluded_by_default():
    target_url = "https://worktoolslab.com/best-communication-tools-for-remote-teams/"
    catalog = [
        _item(
            10,
            target_url,
            "Best Communication Tools for Remote Teams",
            "communication tools for remote teams slack zoom video chat",
            "best-communication-tools-for-remote-teams",
        ),
        _item(
            1,
            "https://worktoolslab.com/best-small-business-tools/",
            "Best Small Business Tools",
            "best tools for small teams business software review guide",
            "best-small-business-tools",
        ),
    ]
    report = generate_suggestions(
        catalog,
        target_url=target_url,
        target_keyword="communication tools remote teams",
        max_suggestions=8,
        include_high_risk=False,
    )
    high_risk_titles = {s.source_title for s in report.suggestions if s.risk_level == "high"}
    assert not high_risk_titles
    rejected_high = [
        r for r in report.rejected if "Best Small Business Tools" in r.source_title
    ]
    assert rejected_high or "Best Small Business Tools" not in [
        s.source_title for s in report.suggestions
    ]


def test_include_high_risk_flag():
    target_url = "https://worktoolslab.com/best-communication-tools-for-remote-teams/"
    catalog = [
        _item(
            10,
            target_url,
            "Best Communication Tools for Remote Teams",
            "communication tools for remote teams slack zoom video chat",
            "best-communication-tools-for-remote-teams",
        ),
        _item(
            1,
            "https://worktoolslab.com/best-small-business-tools/",
            "Best Small Business Tools",
            "best tools for small teams business software review guide",
            "best-small-business-tools",
        ),
    ]
    report_with = generate_suggestions(
        catalog,
        target_url=target_url,
        target_keyword="communication tools remote teams",
        max_suggestions=8,
        include_high_risk=True,
    )
    # With flag, weak pages may appear if they pass minimum score; at minimum no crash.
    assert report_with.rejected is not None


def test_item_links_to_target_normalized_url():
    target = "https://worktoolslab.com/best-communication-tools-for-remote-teams/"
    item = _item(
        1,
        "https://worktoolslab.com/related-1/",
        "Related",
        "slack zoom remote communication",
        "related-1",
        links=[
            {
                "href": target,
                "anchor_text": "communication tools",
                "normalized_url": target,
                "surrounding_text": "",
            }
        ],
    )
    assert item_links_to_target(item, target)


def test_item_links_to_target_href_only():
    target = "https://worktoolslab.com/zoom-review/"
    item = _item(
        1,
        "https://worktoolslab.com/slack-guide/",
        "Slack Guide",
        "slack chat",
        "slack-guide",
        links=[{"href": target, "anchor_text": "Zoom", "surrounding_text": ""}],
    )
    assert item_links_to_target(item, target)


def test_item_links_to_target_trailing_slash_equivalent():
    target_no_slash = "https://worktoolslab.com/zoom-review"
    target_with_slash = "https://worktoolslab.com/zoom-review/"
    item = _item(
        1,
        "https://worktoolslab.com/slack-guide/",
        "Slack Guide",
        "slack chat",
        "slack-guide",
        links=[
            {
                "href": target_with_slash,
                "anchor_text": "Zoom",
                "normalized_url": target_with_slash,
                "surrounding_text": "",
            }
        ],
    )
    assert item_links_to_target(item, target_no_slash)
    assert item_links_to_target(item, target_with_slash)


def test_already_linking_excluded_from_suggestions():
    target = "https://worktoolslab.com/zoom-review/"
    catalog = [
        _item(1, target, "Zoom Review", "zoom video meeting remote communication", "zoom-review"),
        _item(
            2,
            "https://worktoolslab.com/slack-guide/",
            "Slack Guide",
            "slack chat messaging communication",
            "slack-guide",
            links=[
                {
                    "href": target,
                    "anchor_text": "Zoom",
                    "normalized_url": target,
                    "surrounding_text": "",
                },
            ],
        ),
    ]
    report = generate_suggestions(catalog, target_url=target, max_suggestions=8)
    assert item_links_to_target(catalog[1], target)
    assert all(s.source_title != "Slack Guide" for s in report.suggestions)


def test_excludes_already_linked():
    target = "https://worktoolslab.com/zoom-review/"
    catalog = [
        _item(1, target, "Zoom Review", "zoom video meeting remote communication", "zoom-review"),
        _item(
            2,
            "https://worktoolslab.com/slack-guide/",
            "Slack Guide",
            "slack chat messaging communication",
            "slack-guide",
            [
                {
                    "href": target,
                    "anchor_text": "Zoom",
                    "normalized_url": "https://worktoolslab.com/zoom-review",
                    "surrounding_text": "",
                },
            ],
        ),
        _item(
            3,
            "https://worktoolslab.com/teams-guide/",
            "Teams Guide",
            "microsoft teams video communication chat",
            "teams-guide",
        ),
    ]
    report = generate_suggestions(catalog, target_url=target, max_suggestions=8)
    assert len(report.already_linking) == 1
    assert report.already_linking[0].title == "Slack Guide"
    assert all("Slack Guide" not in s.source_title for s in report.suggestions)


def test_fewer_than_max_when_only_good_matches_exist():
    target_url = "https://worktoolslab.com/best-communication-tools-for-remote-teams/"
    catalog = [
        _item(
            10,
            target_url,
            "Best Communication Tools for Remote Teams",
            "communication tools for remote teams slack zoom video chat messaging",
            "best-communication-tools-for-remote-teams",
        ),
        _item(
            1,
            "https://worktoolslab.com/slack-review/",
            "Slack Review",
            "slack chat messaging communication remote video calls",
            "slack-review",
        ),
        _item(
            2,
            "https://worktoolslab.com/best-small-business-tools/",
            "Best Small Business Tools",
            "best tools for small teams business software review guide",
            "best-small-business-tools",
        ),
        _item(
            3,
            "https://worktoolslab.com/random-topic/",
            "Random Topic",
            "unrelated content about gardening and cooking recipes",
            "random-topic",
        ),
    ]
    report = generate_suggestions(
        catalog,
        target_url=target_url,
        target_keyword="communication tools remote teams",
        max_suggestions=8,
    )
    assert len(report.suggestions) < 8
    assert len(report.suggestions) >= 1


def test_detect_clusters_ignores_generic_terms_alone():
    clusters = detect_clusters(
        "best tools for small teams business software review guide",
        title="Best Tools for Small Teams",
        slug="best-tools-for-small-teams",
    )
    assert "communication" not in clusters
    assert "project_management" not in clusters


def test_detect_clusters_finds_communication_from_specific_terms():
    clusters = detect_clusters(
        "slack chat messaging video meetings remote communication",
        title="Slack Review",
        slug="slack-review",
    )
    assert "communication" in clusters


def test_target_clusters_in_report():
    target_url = "https://worktoolslab.com/best-communication-tools-for-remote-teams/"
    catalog = [
        _item(
            10,
            target_url,
            "Best Communication Tools for Remote Teams",
            "communication tools for remote teams slack zoom video chat messaging",
            "best-communication-tools-for-remote-teams",
        ),
        _item(
            1,
            "https://worktoolslab.com/slack-review/",
            "Slack Review",
            "slack chat messaging communication remote video calls",
            "slack-review",
        ),
    ]
    report = generate_suggestions(
        catalog,
        target_url=target_url,
        target_keyword="communication tools remote teams",
        max_suggestions=5,
    )
    assert "communication" in report.target_clusters
    assert report.target_primary_cluster == "communication"
