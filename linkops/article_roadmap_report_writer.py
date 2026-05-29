"""Markdown and CSV writers for new-article roadmap reports."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from linkops.article_roadmap_model import (
    ACTION_CREATE_NEW_ARTICLE,
    ACTION_UPDATE_EXISTING_PAGE,
    ArticleCandidate,
    ArticleRoadmapReport,
    ConsolidatedQueryGroup,
)
from linkops.config import REPORTS_DIR


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _candidate_block(candidate: ArticleCandidate, rank: int) -> list[str]:
    lines = [
        f"### {rank}. {candidate.suggested_title}",
        "",
        f"- **Action type:** {candidate.action_type}",
        f"- **Suggested slug:** `{candidate.suggested_slug}`",
        f"- **Article type:** {candidate.article_type}",
        f"- **Primary keyword:** {candidate.primary_keyword}",
        f"- **Topic:** {candidate.topic}",
        f"- **Priority:** {candidate.priority} (score {candidate.priority_score:.0f})",
        f"- **Total impressions:** {candidate.total_impressions}",
        f"- **Total clicks:** {candidate.total_clicks}",
        f"- **Weighted avg position:** {candidate.weighted_avg_position:.1f}",
        f"- **Related queries:** {candidate.related_query_count}",
        f"- **Gap reason:** {candidate.target_gap_reason}",
        f"- **Cannibalization risk:** {candidate.cannibalization_risk}",
        f"- **Recommended next step:** {candidate.recommended_next_step}",
    ]
    if candidate.query_group_label:
        lines.append(f"- **Query group:** {candidate.query_group_label}")
    if candidate.merged_queries:
        lines.append(
            f"- **Merged queries:** {', '.join(candidate.merged_queries[:8])}"
            + (" …" if len(candidate.merged_queries) > 8 else "")
        )
    if candidate.recommended_existing_url:
        lines.append(f"- **Update existing URL:** {candidate.recommended_existing_url}")
    if candidate.recommended_existing_title:
        lines.append(f"- **Existing page:** {candidate.recommended_existing_title}")
    if candidate.update_reason:
        lines.append(f"- **Update reason:** {candidate.update_reason}")
    if candidate.content_gap_to_add:
        lines.append(f"- **Content gap to add:** {candidate.content_gap_to_add}")
    if candidate.secondary_queries:
        lines.append(
            f"- **Secondary queries:** {', '.join(candidate.secondary_queries[:6])}"
            + (" …" if len(candidate.secondary_queries) > 6 else "")
        )
    if candidate.existing_related_pages:
        lines.append(f"- **Existing related pages:** {', '.join(candidate.existing_related_pages[:4])}")
    if candidate.suggested_internal_links_from:
        lines.append(
            "- **Link from existing pages:** "
            + ", ".join(candidate.suggested_internal_links_from[:4])
        )
    if candidate.suggested_internal_links_to:
        lines.append(
            "- **Link to from new article:** "
            + ", ".join(candidate.suggested_internal_links_to[:4])
        )
    if candidate.editorial_notes:
        lines.append("- **Editorial notes:**")
        for note in candidate.editorial_notes:
            lines.append(f"  - {note}")
    lines.append("")
    return lines


def _priority_section(title: str, candidates: list[ArticleCandidate], start_rank: int) -> list[str]:
    if not candidates:
        return [f"## {title}", "", "_(none)_", ""]
    lines = [f"## {title}", ""]
    for i, c in enumerate(candidates, start_rank):
        lines.extend(_candidate_block(c, i))
    return lines


def _consolidated_groups_section(groups: list[ConsolidatedQueryGroup]) -> list[str]:
    lines = ["## Consolidated / Merged Query Groups", ""]
    if not groups:
        lines.append("_(none)_")
        lines.append("")
        return lines
    for i, g in enumerate(groups, 1):
        lines.append(f"### {i}. {g.query_group_label}")
        lines.append("")
        lines.append(f"- **Action type:** {g.action_type}")
        lines.append(f"- **Suggested title:** {g.suggested_title}")
        lines.append(f"- **Primary keyword:** {g.primary_keyword}")
        lines.append(f"- **Merged queries:** {', '.join(g.merged_queries)}")
        lines.append(f"- **Total impressions:** {g.total_impressions}")
        if g.recommended_existing_url:
            lines.append(f"- **Existing page:** {g.recommended_existing_url}")
        lines.append("")
    return lines


def write_article_roadmap_reports(
    report: ArticleRoadmapReport,
    ts: str | None = None,
) -> tuple[Path, Path]:
    """Write Markdown and CSV new-article roadmap reports."""
    ts = ts or _timestamp()
    md_path = REPORTS_DIR / f"new_article_roadmap_{ts}.md"
    csv_path = REPORTS_DIR / f"new_article_roadmap_{ts}.csv"

    create_n = (
        len(report.create_new_high)
        + len(report.create_new_medium)
        + len(report.create_new_low)
    )
    update_n = (
        len(report.update_existing_high)
        + len(report.update_existing_medium)
        + len(report.update_existing_low)
    )
    manual_n = len(report.manual_review)

    md: list[str] = [
        "# LinkOps New Article Roadmap",
        "",
        f"**Generated:** {report.generated_at}",
        f"**GSC cache imported:** {report.gsc_imported_at or '_(unknown)_'}",
        f"**Worklog:** {report.worklog_path} ({'loaded' if report.worklog_loaded else 'not used'})",
        "",
        "> Read-only roadmap. LinkOps does not modify WordPress or call external APIs.",
        "",
        "## Executive Summary",
        "",
        report.executive_summary,
        "",
        f"- **Total roadmap items:** {report.displayed_roadmap_counts.get('total', len(report.all_candidates))}",
        f"- **Create new article:** {create_n}",
        f"- **Update existing page:** {update_n}",
        f"- **Manual review:** {manual_n}",
        f"- **Consolidated groups:** {len(report.consolidated_groups)}",
        f"- **Excluded queries:** {len(report.excluded_queries)}",
        "",
        "### Top 5 Candidates",
        "",
    ]
    if report.top_candidates:
        for i, c in enumerate(report.top_candidates, 1):
            md.append(
                f"{i}. **{c.suggested_title}** — {c.action_type}, {c.priority} "
                f"(score {c.priority_score:.0f}, {c.primary_keyword})"
            )
    else:
        md.append("_(none)_")
    md.append("")

    rank = 1
    create_new = report.create_new_high + report.create_new_medium + report.create_new_low
    md.extend(_priority_section("Create New Article Opportunities", create_new, rank))
    rank += len(create_new)

    update_existing = (
        report.update_existing_high + report.update_existing_medium + report.update_existing_low
    )
    md.extend(_priority_section("Existing Page Update Opportunities", update_existing, rank))
    rank += len(update_existing)

    md.extend(_consolidated_groups_section(report.consolidated_groups))
    md.extend(_priority_section("Manual Review Queries", report.manual_review, rank))
    rank += manual_n
    low = report.low_priority
    md.extend(_priority_section("Low-Priority / Monitor", low, rank))

    md.extend(
        [
            "## Suggested Content Calendar",
            "",
            "### Week 1",
            "",
        ]
    )
    if report.calendar_week1:
        md.extend(f"- {t}" for t in report.calendar_week1)
    else:
        md.append("_(none)_")
    md.extend(["", "### Week 2", ""])
    if report.calendar_week2:
        md.extend(f"- {t}" for t in report.calendar_week2)
    else:
        md.append("_(none)_")
    md.extend(["", "### Later", ""])
    if report.calendar_later:
        md.extend(f"- {t}" for t in report.calendar_later)
    else:
        md.append("_(none)_")
    md.append("")

    md.extend(["## Internal Link Plan for New Articles", ""])
    for c in report.create_new_high + report.create_new_medium:
        if c.action_type != ACTION_CREATE_NEW_ARTICLE:
            continue
        md.append(f"### {c.suggested_title}")
        md.append("")
        if c.suggested_internal_links_from:
            md.append("- **Existing pages that should link to this article:**")
            for u in c.suggested_internal_links_from:
                md.append(f"  - {u}")
        if c.suggested_internal_links_to:
            md.append("- **Existing pages to link from the new article:**")
            for u in c.suggested_internal_links_to:
                md.append(f"  - {u}")
        if not c.suggested_internal_links_from and not c.suggested_internal_links_to:
            md.append("- _(No strong related pages in cache)_")
        md.append("")

    for c in report.update_existing_high + report.update_existing_medium:
        md.append(f"### {c.suggested_title}")
        md.append("")
        md.append(f"- **Patch/optimize target:** {c.recommended_existing_url}")
        md.append(f"- **Primary keyword:** {c.primary_keyword}")
        if c.content_gap_to_add:
            md.append(f"- **Gap to add:** {c.content_gap_to_add}")
        md.append("")

    md.extend(["## Excluded / Already Covered Queries", ""])
    if report.excluded_queries:
        by_cat: dict[str, list] = {}
        for ex in report.excluded_queries:
            by_cat.setdefault(ex.category, []).append(ex)
        for cat, items in sorted(by_cat.items()):
            md.append(f"### {cat.replace('_', ' ').title()}")
            md.append("")
            for ex in items[:25]:
                md.append(
                    f"- `{ex.query}` — {ex.exclusion_reason} "
                    f"(impressions {ex.impressions}, position {ex.position:.1f})"
                )
            if len(items) > 25:
                md.append(f"- _… and {len(items) - 25} more_")
            md.append("")
    else:
        md.append("_(none)_")
        md.append("")

    md.extend(["## Suggested LinkOps Commands", ""])
    if report.suggested_commands:
        for cmd in report.suggested_commands:
            md.append(f"- `{cmd}`")
    else:
        md.append("_(none)_")
    md.append("")

    md_path.write_text("\n".join(md), encoding="utf-8")

    rows = [c.to_dict() for c in report.all_candidates]
    if rows:
        df = pd.DataFrame(rows)
    else:
        df = pd.DataFrame(
            columns=[
                "suggested_title",
                "suggested_slug",
                "article_type",
                "primary_keyword",
                "topic",
                "priority",
                "priority_score",
                "action_type",
                "recommended_existing_url",
                "recommended_existing_title",
                "update_reason",
                "content_gap_to_add",
                "query_group_label",
                "merged_queries",
                "total_impressions",
                "total_clicks",
                "weighted_avg_position",
                "related_query_count",
                "target_gap_reason",
                "cannibalization_risk",
                "existing_related_pages",
                "suggested_internal_links_from",
                "suggested_internal_links_to",
                "editorial_notes",
                "recommended_next_step",
            ]
        )
    df.to_csv(csv_path, index=False, encoding="utf-8")

    return md_path, csv_path
