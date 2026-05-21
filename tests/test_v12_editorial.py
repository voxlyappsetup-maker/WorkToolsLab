"""Tests for v1.2 editorial relevance rules."""

from linkops.content_model import ContentItem
from linkops.suggestion_engine import (
    classify_page_type,
    detect_primary_clusters,
    detect_secondary_clusters,
    generate_suggestions,
    is_core_page,
)


def _item(
    item_id: int,
    url: str,
    title: str,
    plain: str,
    slug: str,
    links: list | None = None,
    content_html: str | None = None,
) -> ContentItem:
    html = content_html if content_html is not None else f"<p>{plain}</p>"
    return ContentItem(
        id=item_id,
        type="post",
        title=title,
        url=url,
        slug=slug,
        content_html=html,
        excerpt_html="",
        modified="2024-01-01",
        existing_internal_links=links or [],
        word_count=len(plain.split()),
        plain_text=plain,
    )


def _target_catalog(extra: list[ContentItem] | None = None) -> list[ContentItem]:
    target_url = "https://worktoolslab.com/best-communication-tools-for-remote-teams/"
    target = _item(
        10,
        target_url,
        "Best Communication Tools for Remote Teams",
        (
            "communication tools for remote teams slack zoom google meet video chat messaging. "
            "Also compare asana monday project management task management workflow automation."
        ),
        "best-communication-tools-for-remote-teams",
    )
    catalog = [target]
    if extra:
        catalog.extend(extra)
    return catalog, target_url


def test_communication_target_primary_cluster_is_communication_only():
    target_url = "https://worktoolslab.com/best-communication-tools-for-remote-teams/"
    catalog, _ = _target_catalog()
    report = generate_suggestions(
        catalog,
        target_url=target_url,
        target_keyword="remote work communication tools",
        max_suggestions=8,
    )
    assert report.target_primary_cluster == "communication"
    assert "project_management" not in report.target_clusters
    assert "task_management" not in report.target_clusters
    assert "workflow_management" not in report.target_clusters


def test_communication_target_does_not_pick_pm_task_workflow_from_full_content():
    content = (
        "asana monday clickup trello project management tasks kanban workflow automation "
        "milestones roadmap planning recurring process approval handoff"
    )
    primary = detect_primary_clusters(
        "Best Communication Tools for Remote Teams",
        "best-communication-tools-for-remote-teams",
        "remote work communication tools",
    )
    secondary = detect_secondary_clusters(content, primary)
    assert "communication" in primary
    assert "project_management" not in primary
    assert "task_management" not in primary
    assert "workflow_management" not in primary
    assert "project_management" not in secondary
    assert "task_management" not in secondary
    assert "workflow_management" not in secondary


def test_core_pages_excluded_by_default():
    catalog, target_url = _target_catalog(
        [
            _item(1, "https://worktoolslab.com/", "Home", "welcome to worktoolslab", "home"),
            _item(2, "https://worktoolslab.com/blog/", "Blog", "latest articles", "blog"),
            _item(
                3,
                "https://worktoolslab.com/contact/",
                "Contact",
                "contact us form email",
                "contact",
            ),
            _item(
                4,
                "https://worktoolslab.com/about/",
                "About",
                "about our editorial team",
                "about",
            ),
            _item(
                5,
                "https://worktoolslab.com/slack-review/",
                "Slack Review",
                "slack chat messaging communication remote video calls",
                "slack-review",
            ),
        ]
    )
    report = generate_suggestions(
        catalog,
        target_url=target_url,
        target_keyword="remote work communication tools",
        max_suggestions=8,
    )
    titles = [s.source_title for s in report.suggestions]
    assert "Home" not in titles
    assert "Blog" not in titles
    assert "Contact" not in titles
    assert "About" not in titles
    assert "Home" in report.core_pages_excluded or any(
        r.source_title == "Home" for r in report.rejected
    )


def test_include_core_pages_allows_core_pages_but_not_low_risk():
    catalog, target_url = _target_catalog(
        [
            _item(
                1,
                "https://worktoolslab.com/about/",
                "About",
                "about our team communication remote work editorial",
                "about",
            ),
        ]
    )
    report = generate_suggestions(
        catalog,
        target_url=target_url,
        target_keyword="remote work communication tools",
        max_suggestions=8,
        include_core_pages=True,
        include_high_risk=True,
    )
    about_suggestions = [s for s in report.suggestions if s.source_title == "About"]
    if about_suggestions:
        assert all(s.risk_level != "low" for s in about_suggestions)
        assert all(s.strength != "strong" for s in about_suggestions)


def test_monday_vs_asana_rejected_for_communication_target():
    catalog, target_url = _target_catalog(
        [
            _item(
                1,
                "https://worktoolslab.com/monday-com-vs-asana/",
                "Monday.com vs Asana",
                (
                    "monday.com vs asana project management planning roadmap timeline milestones. "
                    "Teams can use communication features in both tools for remote work."
                ),
                "monday-com-vs-asana",
            ),
        ]
    )
    report = generate_suggestions(
        catalog,
        target_url=target_url,
        target_keyword="remote work communication tools",
        max_suggestions=8,
    )
    titles = [s.source_title for s in report.suggestions]
    assert "Monday.com vs Asana" not in titles
    rejected = [r for r in report.rejected if r.source_title == "Monday.com vs Asana"]
    assert rejected
    assert any("communication" in r.reason.lower() or "unrelated" in r.reason.lower() for r in rejected)


def test_webex_and_google_workspace_accepted_if_not_already_linking():
    catalog, target_url = _target_catalog(
        [
            _item(
                1,
                "https://worktoolslab.com/webex-review-for-small-businesses/",
                "Webex Review for Small Businesses",
                "webex video meetings remote communication calls conferencing",
                "webex-review-for-small-businesses",
            ),
            _item(
                2,
                "https://worktoolslab.com/google-workspace-for-small-teams/",
                "Google Workspace for Small Teams",
                "google workspace collaboration chat meet video communication remote teams",
                "google-workspace-for-small-teams",
            ),
        ]
    )
    report = generate_suggestions(
        catalog,
        target_url=target_url,
        target_keyword="remote work communication tools",
        max_suggestions=8,
    )
    titles = [s.source_title for s in report.suggestions]
    assert "Webex Review for Small Businesses" in titles
    assert "Google Workspace for Small Teams" in titles
    strong_titles = {s.source_title for s in report.strong}
    assert "Webex Review for Small Businesses" in strong_titles or any(
        s.source_title == "Webex Review for Small Businesses" and s.risk_level == "low"
        for s in report.suggestions
    )


def test_seven_plus_related_pages_limits_recommendations():
    target_url = "https://worktoolslab.com/best-communication-tools-for-remote-teams/"
    target = _item(
        10,
        target_url,
        "Best Communication Tools for Remote Teams",
        "communication tools for remote teams slack zoom google meet video chat messaging",
        "best-communication-tools-for-remote-teams",
    )
    related_pages = [
        _item(
            i,
            f"https://worktoolslab.com/related-{i}/",
            f"Remote Communication Guide {i}",
            "slack zoom remote communication video meetings chat messaging",
            f"remote-communication-guide-{i}",
            links=[
                {
                    "href": target_url,
                    "anchor_text": "communication tools",
                    "normalized_url": target_url,
                    "surrounding_text": "",
                }
            ],
        )
        for i in range(1, 10)
    ]
    optional = [
        _item(
            100,
            "https://worktoolslab.com/webex-review-for-small-businesses/",
            "Webex Review for Small Businesses",
            "webex video meetings remote communication calls conferencing",
            "webex-review-for-small-businesses",
        ),
        _item(
            101,
            "https://worktoolslab.com/google-workspace-for-small-teams/",
            "Google Workspace for Small Teams",
            "google workspace collaboration chat meet video communication remote teams",
            "google-workspace-for-small-teams",
        ),
    ]
    catalog = [target, *related_pages, *optional]
    report = generate_suggestions(
        catalog,
        target_url=target_url,
        target_keyword="remote work communication tools",
        max_suggestions=8,
    )
    assert report.strict_mode is True
    assert len(report.related_already_linking) >= 7
    assert len(report.suggestions) <= 2
    assert "Additional links may not be necessary" in report.already_linking_quality_note


def test_report_includes_no_new_links_needed_when_appropriate():
    target_url = "https://worktoolslab.com/best-communication-tools-for-remote-teams/"
    target = _item(
        10,
        target_url,
        "Best Communication Tools for Remote Teams",
        "communication tools for remote teams slack zoom google meet video chat messaging",
        "best-communication-tools-for-remote-teams",
    )
    related_pages = [
        _item(
            i,
            f"https://worktoolslab.com/related-{i}/",
            f"Remote Communication Guide {i}",
            "slack zoom remote communication video meetings chat messaging",
            f"remote-communication-guide-{i}",
            links=[
                {
                    "href": target_url,
                    "anchor_text": "communication tools",
                    "normalized_url": target_url,
                    "surrounding_text": "",
                }
            ],
        )
        for i in range(1, 10)
    ]
    catalog = [target, *related_pages]
    report = generate_suggestions(
        catalog,
        target_url=target_url,
        target_keyword="remote work communication tools",
        max_suggestions=8,
    )
    assert report.final_recommendation == "No new links needed"


def test_classify_page_type_core_and_policy():
    assert classify_page_type(_item(1, "https://worktoolslab.com/", "Home", "", "home")) == "core_page"
    assert classify_page_type(
        _item(2, "https://worktoolslab.com/privacy-policy/", "Privacy Policy", "", "privacy-policy")
    ) == "policy_legal"
    assert is_core_page(_item(3, "https://worktoolslab.com/blog/", "Blog", "", "blog"))


def test_strict_mode_optional_link_recommendation():
    target_url = "https://worktoolslab.com/best-communication-tools-for-remote-teams/"
    target = _item(
        10,
        target_url,
        "Best Communication Tools for Remote Teams",
        "communication tools for remote teams slack zoom google meet video chat messaging",
        "best-communication-tools-for-remote-teams",
    )
    related_pages = [
        _item(
            i,
            f"https://worktoolslab.com/related-{i}/",
            f"Remote Communication Guide {i}",
            "slack zoom remote communication video meetings chat messaging",
            f"remote-communication-guide-{i}",
            links=[
                {
                    "href": target_url,
                    "anchor_text": "communication tools",
                    "normalized_url": target_url,
                    "surrounding_text": "",
                }
            ],
        )
        for i in range(1, 10)
    ]
    optional = [
        _item(
            100,
            "https://worktoolslab.com/webex-review-for-small-businesses/",
            "Webex Review for Small Businesses",
            "webex video meetings remote communication calls conferencing",
            "webex-review-for-small-businesses",
        ),
        _item(
            101,
            "https://worktoolslab.com/google-workspace-for-small-teams/",
            "Google Workspace for Small Teams",
            "google workspace collaboration chat meet video communication remote teams",
            "google-workspace-for-small-teams",
        ),
    ]
    catalog = [target, *related_pages, *optional]
    report = generate_suggestions(
        catalog,
        target_url=target_url,
        target_keyword="remote work communication tools",
        max_suggestions=8,
    )
    assert "No new links are necessary unless you want one optional link from" in report.final_recommendation
