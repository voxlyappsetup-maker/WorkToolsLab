"""Markdown and CSV reports for GSC opportunities (no secrets)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from linkops.config import REPORTS_DIR
from linkops.gsc_model import (
    STATUS_CANNIBALIZATION,
    STATUS_CONTENT_OPTIMIZATION,
    STATUS_CORRECT_PAGE,
    STATUS_INTERNAL_LINKS,
    STATUS_NO_TARGET,
    STATUS_OLD_URL,
    Opportunity,
    OpportunityReport,
)


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _opp_block(opp: Opportunity) -> list[str]:
    lines = [
        f"### {opp.priority_rank}. {opp.query}",
        "",
        f"- **Clicks:** {opp.clicks}",
        f"- **Impressions:** {opp.impressions}",
        f"- **CTR:** {opp.ctr:.2f}%",
        f"- **Average position:** {opp.position:.1f}",
        f"- **Query intent:** {opp.query_intent}",
        f"- **Target page:** {opp.target_url or '_(none)_'}",
        f"- **Target page type:** {opp.page_type}",
        f"- **Status:** {opp.status}",
        f"- **Confidence:** {opp.confidence}",
        f"- **Action type:** {opp.action_type}",
        f"- **Override used:** {opp.override_used}",
        f"- **Target selection reason:** {opp.target_selection_reason or '_(none)_'}",
        f"- **Why it matters:** {opp.reason}",
        f"- **Recommended action:** {opp.recommended_action}",
    ]
    if opp.next_command:
        lines.append(f"- **Next LinkOps command:** `{opp.next_command}`")
    if opp.request_indexing_urls:
        lines.append("- **Request indexing candidates:**")
        for url in opp.request_indexing_urls:
            lines.append(f"  - {url}")
    lines.append("")
    return lines


def _section_opportunities(opps: list[Opportunity], heading: str) -> list[str]:
    if not opps:
        return [f"## {heading}", "", "_(none)_", ""]
    lines = [f"## {heading}", ""]
    for opp in opps:
        lines.extend(_opp_block(opp))
    return lines


def write_gsc_opportunity_reports(
    report: OpportunityReport,
    ts: str | None = None,
) -> tuple[Path, Path]:
    ts = ts or _timestamp()
    md_path = REPORTS_DIR / f"gsc_opportunities_{ts}.md"
    csv_path = REPORTS_DIR / f"gsc_opportunities_{ts}.csv"

    summary = report.summary
    top_opps = [o for o in report.opportunities if o.priority_rank <= 15]
    cannibal = [o for o in report.opportunities if o.status == STATUS_CANNIBALIZATION]
    old_url = [o for o in report.opportunities if o.status == STATUS_OLD_URL]
    no_target = [o for o in report.opportunities if o.status == STATUS_NO_TARGET]
    low_ctr = [
        o
        for o in report.opportunities
        if o.clicks <= report.filters.get("max_clicks", 0)
        and o.status not in (STATUS_CANNIBALIZATION, STATUS_OLD_URL)
    ]

    lines = [
        "# WorkToolsLab GSC Opportunities",
        "",
        f"**Generated:** {report.generated_at}",
        "",
        "**Source:** local GSC CSV exports",
        "",
        "> **Read-only notice:** LinkOps analyzed local Search Console exports and cached "
        "WordPress content only. No data was sent externally. No WordPress content was modified.",
        "",
        "## Executive Summary",
        "",
        f"- **Total queries analyzed:** {report.total_queries_analyzed}",
        f"- **Total opportunities:** {summary.get('total_opportunities', 0)}",
        f"- **Correct-page opportunities:** {summary.get(STATUS_CORRECT_PAGE, 0)}",
        f"- **Cannibalization warnings:** {summary.get(STATUS_CANNIBALIZATION, 0)}",
        f"- **Old URL warnings:** {summary.get(STATUS_OLD_URL, 0)}",
        f"- **No-target queries:** {summary.get(STATUS_NO_TARGET, 0)}",
        f"- **Content optimization:** {summary.get(STATUS_CONTENT_OPTIMIZATION, 0)}",
        f"- **Internal link support:** {summary.get(STATUS_INTERNAL_LINKS, 0)}",
        "",
        "### Filters applied",
        "",
        f"- Min impressions: {report.filters.get('min_impressions')}",
        f"- Max clicks: {report.filters.get('max_clicks')}",
        f"- Max position: {report.filters.get('max_position')}",
        "",
        "### Top 10 actions",
        "",
    ]
    if report.top_actions:
        for i, action in enumerate(report.top_actions[:10], 1):
            lines.append(f"{i}. {action}")
    else:
        lines.append("_(none)_")
    lines.append("")

    lines.extend(_section_opportunities(top_opps, "Top Opportunities"))
    lines.extend(_section_opportunities(cannibal, "Cannibalization Warnings"))
    lines.extend(_section_opportunities(old_url, "Old or Redirected URL Warnings"))
    lines.extend(_section_opportunities(no_target, "No Obvious Target Queries"))
    lines.extend(_section_opportunities(low_ctr[:20], "Low-CTR / Zero-Click Opportunities"))

    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text("\n".join(lines), encoding="utf-8")

    rows = [
        {
            "priority_rank": o.priority_rank,
            "query": o.query,
            "clicks": o.clicks,
            "impressions": o.impressions,
            "ctr": o.ctr,
            "position": o.position,
            "target_url": o.target_url,
            "query_intent": o.query_intent,
            "page_type": o.page_type,
            "confidence": o.confidence,
            "action_type": o.action_type,
            "override_used": o.override_used,
            "target_selection_reason": o.target_selection_reason,
            "status": o.status,
            "reason": o.reason,
            "recommended_action": o.recommended_action,
            "next_command": o.next_command,
            "request_indexing_urls": "; ".join(o.request_indexing_urls),
        }
        for o in report.opportunities
    ]
    pd.DataFrame(rows).to_csv(csv_path, index=False, encoding="utf-8")
    return md_path, csv_path
