"""Tests for grouped next-actions engine and worklog."""

import json
from pathlib import Path

import pytest

from linkops.content_model import ContentItem
from linkops.gsc_model import GscCache, GscQueryRow, STATUS_NO_TARGET
from linkops.next_actions_engine import (
    build_next_actions_report,
    classify_no_target_recommendation,
    weighted_average_position,
)
from linkops.next_actions_model import NO_TARGET_MANUAL
from linkops.next_actions_report_writer import write_next_actions_reports
from linkops.gsc_model import Opportunity
from linkops.worklog import Worklog, canonical_worklog_url, load_worklog


def _page(slug: str, title: str, extra: str = "") -> ContentItem:
    plain = f"{title} {slug.replace('-', ' ')} {extra}"
    return ContentItem(
        id=hash(slug) % 10000,
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


def _catalog() -> list[ContentItem]:
    return [
        _page(
            "best-project-management-tools-for-small-teams",
            "Best Project Management Tools for Small Teams",
            "project management software planning for small teams",
        ),
        _page(
            "clickup-vs-trello-for-small-teams",
            "ClickUp vs Trello for Small Teams",
            "clickup trello comparison",
        ),
    ]


def _gsc_cache() -> GscCache:
    return GscCache(
        imported_at="2026-05-20T12:00:00Z",
        queries=[
            GscQueryRow("project management software for small teams", 0, 80, 0.0, 25.0),
            GscQueryRow("best project management tools for small teams", 0, 40, 0.0, 35.0),
            GscQueryRow("small business teams", 0, 60, 0.0, 45.0),
            GscQueryRow("clickup vs trello", 0, 50, 0.0, 30.0),
        ],
    )


def test_weighted_average_position():
    base = dict(
        target_url="https://worktoolslab.com/x/",
        target_title="T",
        status="Correct page",
        reason="r",
        recommended_action="a",
        next_command="",
        request_indexing_urls=[],
    )
    opps = [
        Opportunity(
            priority_rank=1,
            query="a",
            clicks=0,
            impressions=100,
            ctr=0.0,
            position=10.0,
            **base,
        ),
        Opportunity(
            priority_rank=2,
            query="b",
            clicks=0,
            impressions=50,
            ctr=0.0,
            position=40.0,
            **base,
        ),
    ]
    assert weighted_average_position(opps) == pytest.approx(20.0)


def test_grouping_queries_by_target_url():
    report = build_next_actions_report(_gsc_cache(), _catalog(), Worklog())
    pm_clusters = [
        c
        for c in report.unresolved_clusters + report.handled_clusters
        if "project-management" in c.target_url
    ]
    assert len(pm_clusters) == 1
    cluster = pm_clusters[0]
    assert cluster.query_count >= 2
    assert cluster.total_impressions == 120
    assert any("project management software" in q for q in cluster.queries)
    assert "best project management tools" in " ".join(cluster.queries).lower()


def test_worklog_missing_returns_empty(tmp_path, monkeypatch):
    import linkops.worklog as wl_mod

    missing = tmp_path / "no_worklog.json"
    monkeypatch.setattr(wl_mod, "WORKLOG_PATH", missing)
    assert load_worklog().pages == {}


def test_worklog_trailing_slash_matches_lookup(tmp_path, monkeypatch):
    import linkops.worklog as wl_mod

    path = tmp_path / "worklog.json"
    path.write_text(
        json.dumps(
            {
                "pages": {
                    "https://worktoolslab.com/clickup-vs-trello-for-small-teams/": {
                        "status": "monitor_only",
                        "note": "Reviewed",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(wl_mod, "WORKLOG_PATH", path)
    wl = load_worklog()
    canon = canonical_worklog_url(
        "https://worktoolslab.com/clickup-vs-trello-for-small-teams"
    )
    assert canon in wl.pages
    assert wl.entry_for_url(
        "https://worktoolslab.com/clickup-vs-trello-for-small-teams"
    ) is not None
    assert wl.entry_for_url(
        "https://worktoolslab.com/clickup-vs-trello-for-small-teams/"
    ) is not None
    assert wl.entry_for_url(
        "https://worktoolslab.com/clickup-vs-trello-for-small-teams"
    ).status == "monitor_only"


def test_worklog_no_trailing_slash_key_matches_target_with_slash(tmp_path, monkeypatch):
    import linkops.worklog as wl_mod

    path = tmp_path / "worklog.json"
    path.write_text(
        json.dumps(
            {
                "pages": {
                    "https://worktoolslab.com/best-collaboration-tools-for-small-teams": {
                        "status": "done",
                        "note": "Finished",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(wl_mod, "WORKLOG_PATH", path)
    wl = load_worklog()
    entry = wl.entry_for_url(
        "https://worktoolslab.com/best-collaboration-tools-for-small-teams/"
    )
    assert entry is not None
    assert entry.status == "done"


def test_cluster_shows_worklog_status_not_unset(tmp_path, monkeypatch):
    import linkops.worklog as wl_mod

    path = tmp_path / "worklog.json"
    path.write_text(
        json.dumps(
            {
                "pages": {
                    "https://worktoolslab.com/clickup-vs-trello-for-small-teams/": {
                        "status": "monitor_only",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(wl_mod, "WORKLOG_PATH", path)
    worklog = load_worklog()
    report = build_next_actions_report(_gsc_cache(), _catalog(), worklog)
    handled = [
        c
        for c in report.handled_clusters
        if "clickup-vs-trello" in c.target_url
    ]
    assert len(handled) == 1
    assert handled[0].worklog_status == "monitor_only"
    assert handled[0].worklog_status != ""


def test_worklog_loads_when_present(tmp_path, monkeypatch):
    import linkops.worklog as wl_mod

    path = tmp_path / "worklog.json"
    path.write_text(
        json.dumps(
            {
                "pages": {
                    "https://worktoolslab.com/clickup-vs-trello-for-small-teams/": {
                        "status": "monitor_only",
                        "note": "Reviewed",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(wl_mod, "WORKLOG_PATH", path)
    wl = load_worklog()
    assert wl.status_for_url("https://worktoolslab.com/clickup-vs-trello-for-small-teams/") == (
        "monitor_only"
    )
    assert wl.status_for_url("https://worktoolslab.com/clickup-vs-trello-for-small-teams") == (
        "monitor_only"
    )


def test_done_excluded_from_unresolved_with_flag(tmp_path, monkeypatch):
    import linkops.worklog as wl_mod

    path = tmp_path / "worklog.json"
    path.write_text(
        json.dumps(
            {
                "pages": {
                    "https://worktoolslab.com/clickup-vs-trello-for-small-teams/": {
                        "status": "done",
                        "note": "Finished",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(wl_mod, "WORKLOG_PATH", path)
    worklog = load_worklog()
    report = build_next_actions_report(
        _gsc_cache(),
        _catalog(),
        worklog,
        exclude_done=True,
    )
    unresolved_urls = {c.target_url for c in report.unresolved_clusters}
    assert "https://worktoolslab.com/clickup-vs-trello-for-small-teams/" not in unresolved_urls
    handled = [c for c in report.handled_clusters if "clickup-vs-trello" in c.target_url]
    assert len(handled) == 1
    assert handled[0].worklog_status == "done"


def test_monitor_only_in_handled_section_by_default(tmp_path, monkeypatch):
    import linkops.worklog as wl_mod

    path = tmp_path / "worklog.json"
    path.write_text(
        json.dumps(
            {
                "pages": {
                    "https://worktoolslab.com/clickup-vs-trello-for-small-teams/": {
                        "status": "monitor_only",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(wl_mod, "WORKLOG_PATH", path)
    worklog = load_worklog()
    report = build_next_actions_report(_gsc_cache(), _catalog(), worklog)
    unresolved_urls = {c.target_url.rstrip("/") for c in report.unresolved_clusters}
    assert "https://worktoolslab.com/clickup-vs-trello-for-small-teams" not in unresolved_urls
    assert any(
        "clickup-vs-trello" in c.target_url for c in report.handled_clusters
    )


def test_vague_query_needs_manual_review():
    rec, _, _ = classify_no_target_recommendation(
        "small business teams",
        impressions=60,
        position=45.0,
        partial_matches=[],
    )
    assert rec == NO_TARGET_MANUAL


def test_no_target_in_report():
    report = build_next_actions_report(_gsc_cache(), _catalog(), Worklog())
    no_target = [n for n in report.no_target_queries if n.query == "small business teams"]
    assert len(no_target) == 1
    assert no_target[0].recommendation == NO_TARGET_MANUAL


def test_report_writer_sections(tmp_path, monkeypatch):
    import linkops.next_actions_report_writer as writer_mod

    monkeypatch.setattr(writer_mod, "REPORTS_DIR", tmp_path)
    report = build_next_actions_report(_gsc_cache(), _catalog(), Worklog())
    md_path, csv_path = write_next_actions_reports(report, ts="20260522_150000")
    md = md_path.read_text(encoding="utf-8")
    for section in (
        "## Executive Summary",
        "## Top Unresolved Page Clusters",
        "## Already Handled / Monitor-Only Pages",
        "## No-Target Queries",
        "## Suggested Next LinkOps Commands",
        "## Request Indexing",
        "## GSC Data Lag",
    ):
        assert section in md
    header = csv_path.read_text(encoding="utf-8").splitlines()[0]
    for col in (
        "target_url",
        "total_impressions",
        "strongest_query",
        "status",
        "recommendation",
    ):
        assert col in header
