"""Markdown and CSV writers for next-actions decision reports."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from linkops.config import REPORTS_DIR
from linkops.next_actions_model import NextActionsReport, NoTargetQuery, PageCluster


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _cluster_block(cluster: PageCluster, rank: int) -> list[str]:
    lines = [
        f"### {rank}. {cluster.target_title or cluster.target_url}",
        "",
        f"- **Target URL:** {cluster.target_url}",
        f"- **Worklog status:** {cluster.worklog_status or '_(not set)_'}",
        f"- **Total impressions:** {cluster.total_impressions}",
        f"- **Total clicks:** {cluster.total_clicks}",
        f"- **Weighted avg position:** {cluster.weighted_avg_position:.1f}",
        f"- **Queries ({cluster.query_count}):** {', '.join(cluster.queries[:8])}"
        + (" …" if len(cluster.queries) > 8 else ""),
        f"- **Strongest query:** {cluster.strongest_query}",
        f"- **Action types:** {', '.join(cluster.action_types)}",
        f"- **GSC statuses:** {', '.join(cluster.statuses)}",
        f"- **Confidence:** {cluster.confidence}",
        f"- **Recommended next action:** {cluster.recommended_next_action}",
    ]
    if cluster.worklog_note:
        lines.append(f"- **Worklog note:** {cluster.worklog_note}")
    if cluster.next_commands:
        lines.append("- **Next LinkOps commands:**")
        for cmd in cluster.next_commands:
            lines.append(f"  - `{cmd}`")
    if cluster.request_indexing_urls:
        lines.append("- **Request indexing:**")
        for url in cluster.request_indexing_urls:
            lines.append(f"  - {url}")
    lines.append("")
    return lines


def _no_target_block(item: NoTargetQuery, rank: int) -> list[str]:
    lines = [
        f"### {rank}. {item.query}",
        "",
        f"- **Impressions:** {item.impressions}",
        f"- **Clicks:** {item.clicks}",
        f"- **CTR:** {item.ctr:.2f}%",
        f"- **Position:** {item.position:.1f}",
        f"- **Query intent:** {item.query_intent}",
        f"- **Recommendation:** {item.recommendation}",
        f"- **Worth new article:** {'yes' if item.worth_new_article else 'no'}",
        f"- **Rationale:** {item.rationale}",
    ]
    if item.gsc_pages:
        lines.append(f"- **GSC landing pages:** {', '.join(item.gsc_pages[:4])}")
    if item.partial_matches:
        lines.append("- **Partial catalog matches:**")
        for m in item.partial_matches[:4]:
            lines.append(f"  - {m.title} ({m.url}) — {m.reason}")
    lines.append("")
    return lines


def write_next_actions_reports(
    report: NextActionsReport,
    ts: str | None = None,
) -> tuple[Path, Path]:
    """Write Markdown and CSV next-actions reports."""
    ts = ts or _timestamp()
    md_path = REPORTS_DIR / f"next_actions_{ts}.md"
    csv_path = REPORTS_DIR / f"next_actions_{ts}.csv"

    md: list[str] = [
        "# LinkOps Next Actions",
        "",
        f"**Generated:** {report.generated_at}",
        f"**GSC cache imported:** {report.gsc_imported_at or '_(unknown)_'}",
        f"**Worklog:** {report.worklog_path} ({'loaded' if report.worklog_loaded else 'not found — using defaults'})",
        "",
        "> Read-only decision report. LinkOps does not modify WordPress or call external APIs.",
        "",
        "## Executive Summary",
        "",
        report.executive_summary,
        "",
        f"- Page clusters analyzed: {report.total_page_clusters}",
        f"- Queries in report: {report.total_queries_in_report}",
        f"- Filters: min impressions {report.filters.get('min_impressions')}, "
        f"max clicks {report.filters.get('max_clicks')}, "
        f"max position {report.filters.get('max_position')}",
        "",
        "## Top Unresolved Page Clusters",
        "",
    ]
    if report.unresolved_clusters:
        for i, cluster in enumerate(report.unresolved_clusters, start=1):
            md.extend(_cluster_block(cluster, i))
    else:
        md.append("_(No unresolved page clusters for current filters.)_")
        md.append("")

    md.extend(["## Already Handled / Monitor-Only Pages", ""])
    if report.handled_clusters:
        for i, cluster in enumerate(report.handled_clusters, start=1):
            md.extend(_cluster_block(cluster, i))
    else:
        md.append("_(None marked in worklog or matching handled statuses.)_")
        md.append("")

    md.extend(["## No-Target Queries", ""])
    if report.no_target_queries:
        for i, item in enumerate(report.no_target_queries, start=1):
            md.extend(_no_target_block(item, i))
    else:
        md.append("_(No no-target queries in this report.)_")
        md.append("")

    md.extend(["## Suggested Next LinkOps Commands", ""])
    for cmd in report.suggested_commands:
        md.append(f"- `{cmd}`")
    md.append("")

    md.extend(["## Request Indexing", ""])
    if report.request_indexing_urls:
        for url in report.request_indexing_urls:
            md.append(f"- {url}")
    else:
        md.append("_(No indexing URLs from unresolved clusters.)_")
    md.append("")

    md.extend(["## GSC Data Lag", "", report.gsc_lag_note, ""])
    md_path.write_text("\n".join(md), encoding="utf-8")

    rows: list[dict] = []
    for cluster in report.unresolved_clusters + report.handled_clusters:
        rows.append(
            {
                "target_url": cluster.target_url,
                "target_title": cluster.target_title,
                "total_impressions": cluster.total_impressions,
                "total_clicks": cluster.total_clicks,
                "weighted_avg_position": cluster.weighted_avg_position,
                "strongest_query": cluster.strongest_query,
                "query_count": cluster.query_count,
                "queries": " | ".join(cluster.queries),
                "action_types": " | ".join(cluster.action_types),
                "confidence": cluster.confidence,
                "status": cluster.worklog_status or "unresolved",
                "recommendation": cluster.recommended_next_action,
                "section": "handled" if cluster in report.handled_clusters else "unresolved",
            }
        )
    for item in report.no_target_queries:
        rows.append(
            {
                "target_url": "",
                "target_title": "",
                "total_impressions": item.impressions,
                "total_clicks": item.clicks,
                "weighted_avg_position": item.position,
                "strongest_query": item.query,
                "query_count": 1,
                "queries": item.query,
                "action_types": item.recommendation,
                "confidence": item.query_intent,
                "status": "no_target",
                "recommendation": item.rationale,
                "section": "no_target",
            }
        )
    pd.DataFrame(rows).to_csv(csv_path, index=False, encoding="utf-8")
    return md_path, csv_path
