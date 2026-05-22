"""Integration tests against config/worklog.json when present."""

import json

import pytest

from linkops.config import CACHE_PATH, GSC_CACHE_PATH, WORKLOG_PATH
from linkops.content_model import ContentItem
from linkops.gsc_model import GscCache
from linkops.next_actions_engine import build_next_actions_report
from linkops.worklog import load_worklog


@pytest.mark.skipif(not WORKLOG_PATH.exists(), reason="config/worklog.json not present")
def test_real_worklog_loads_nine_pages():
    wl = load_worklog(WORKLOG_PATH)
    assert len(wl.pages) >= 9


@pytest.mark.skipif(not WORKLOG_PATH.exists(), reason="config/worklog.json not present")
def test_real_worklog_matches_clickup_with_or_without_slash():
    wl = load_worklog(WORKLOG_PATH)
    for url in (
        "https://worktoolslab.com/clickup-vs-trello-for-small-teams",
        "https://worktoolslab.com/clickup-vs-trello-for-small-teams/",
    ):
        entry = wl.entry_for_url(url)
        assert entry is not None, url
        assert entry.status == "monitor_only"


@pytest.mark.skipif(
    not (WORKLOG_PATH.exists() and CACHE_PATH.exists() and GSC_CACHE_PATH.exists()),
    reason="requires worklog, content cache, and gsc cache",
)
def test_real_next_actions_moves_worklog_pages_to_handled():
    catalog = [ContentItem.from_dict(x) for x in json.loads(CACHE_PATH.read_text(encoding="utf-8"))]
    gsc = GscCache.from_dict(json.loads(GSC_CACHE_PATH.read_text(encoding="utf-8")))
    wl = load_worklog(WORKLOG_PATH)
    report = build_next_actions_report(
        gsc, catalog, wl, min_impressions=20, max_position=90, exclude_done=True
    )
    handled_slugs = {
        c.target_url.rstrip("/").split("/")[-1] for c in report.handled_clusters
    }
    assert "clickup-vs-trello-for-small-teams" in handled_slugs
    assert "best-collaboration-tools-for-small-teams" not in {
        c.target_url.rstrip("/").split("/")[-1] for c in report.unresolved_clusters
    }
    clickup_unresolved = [
        c
        for c in report.unresolved_clusters
        if "clickup-vs-trello-for-small-teams" in c.target_url
    ]
    assert clickup_unresolved == []
