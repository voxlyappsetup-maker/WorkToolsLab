"""Tests for GSC opportunity report output."""

from pathlib import Path

from linkops.gsc_model import (
    Opportunity,
    OpportunityReport,
    STATUS_CANNIBALIZATION,
    STATUS_CORRECT_PAGE,
    STATUS_NO_TARGET,
)
from linkops.gsc_report_writer import write_gsc_opportunity_reports


def test_report_includes_required_sections(tmp_path, monkeypatch):
    import linkops.gsc_report_writer as writer_mod

    monkeypatch.setattr(writer_mod, "REPORTS_DIR", tmp_path)

    report = OpportunityReport(
        generated_at="2026-05-21 12:00 UTC",
        total_queries_analyzed=5,
        filters={"min_impressions": 20, "max_clicks": 0, "max_position": 90},
        summary={
            "total_opportunities": 3,
            STATUS_CORRECT_PAGE: 1,
            STATUS_CANNIBALIZATION: 1,
            STATUS_NO_TARGET: 1,
        },
        top_actions=["Fix cannibalization on trello vs clickup"],
        opportunities=[
            Opportunity(
                priority_rank=1,
                query="remote work communication tools",
                clicks=0,
                impressions=100,
                ctr=0.0,
                position=28.0,
                target_url="https://worktoolslab.com/best-communication-tools-for-remote-teams/",
                target_title="Best Communication Tools for Remote Teams",
                status=STATUS_CORRECT_PAGE,
                reason="Query aligns with target page.",
                recommended_action="Improve CTR and monitor position.",
                next_command='python -m linkops.cli suggest --target-url "https://worktoolslab.com/best-communication-tools-for-remote-teams/" --target-keyword "remote work communication tools" --max-suggestions 8',
                request_indexing_urls=[
                    "https://worktoolslab.com/best-communication-tools-for-remote-teams/"
                ],
                query_intent="broad_best_tools",
                page_type="roundup_best_tools",
                confidence="high",
                action_type="content_optimization",
                override_used=False,
                target_selection_reason="roundup topical match",
            ),
            Opportunity(
                priority_rank=2,
                query="trello vs clickup",
                clicks=0,
                impressions=90,
                ctr=0.0,
                position=35.0,
                target_url="https://worktoolslab.com/clickup-vs-trello-for-small-teams/",
                target_title="ClickUp vs Trello",
                status=STATUS_CANNIBALIZATION,
                reason="Multiple pages rank.",
                recommended_action="Consolidate intent.",
                next_command="",
                request_indexing_urls=[],
            ),
            Opportunity(
                priority_rank=3,
                query="obscure topic",
                clicks=0,
                impressions=50,
                ctr=0.0,
                position=40.0,
                target_url="",
                target_title="",
                status=STATUS_NO_TARGET,
                reason="No match.",
                recommended_action="Create content.",
                next_command="",
                request_indexing_urls=[],
            ),
        ],
    )

    md_path, csv_path = write_gsc_opportunity_reports(report, ts="test123")
    assert md_path.exists()
    assert csv_path.exists()
    text = md_path.read_text(encoding="utf-8")
    for section in (
        "# WorkToolsLab GSC Opportunities",
        "## Executive Summary",
        "## Top Opportunities",
        "## Cannibalization Warnings",
        "## Old or Redirected URL Warnings",
        "## No Obvious Target Queries",
        "## Low-CTR / Zero-Click Opportunities",
        "Read-only notice",
        "Next LinkOps command",
        "Request indexing candidates",
        "Query intent",
        "Target page type",
        "Confidence",
        "Action type",
        "Override used",
        "Target selection reason",
    ):
        assert section in text

    import pandas as pd

    df = pd.read_csv(csv_path)
    for col in (
        "priority_rank",
        "query",
        "query_intent",
        "page_type",
        "confidence",
        "action_type",
        "override_used",
        "target_selection_reason",
        "next_command",
    ):
        assert col in df.columns
    assert len(df) == 3
