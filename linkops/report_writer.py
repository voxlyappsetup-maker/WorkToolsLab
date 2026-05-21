"""Write Markdown and CSV reports (no secrets)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from slugify import slugify

from linkops.config import REPORTS_DIR
from linkops.link_analyzer import LinkEdge
from linkops.suggestion_engine import Suggestion, SuggestionReport


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def write_site_link_map_csv(edges: list[LinkEdge], ts: str | None = None) -> Path:
    ts = ts or _timestamp()
    path = REPORTS_DIR / f"site_internal_link_map_{ts}.csv"
    rows = [
        {
            "source_url": e.source_url,
            "source_title": e.source_title,
            "target_url": e.target_url,
            "anchor_text": e.anchor_text,
            "target_known": e.target_known,
        }
        for e in edges
    ]
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8")
    return path


def _format_suggestion_block(s: Suggestion, index: int | None = None) -> list[str]:
    prefix = f"### {index}. {s.source_title}" if index is not None else f"### {s.source_title}"
    return [
        prefix,
        f"- **Source URL:** {s.source_url}",
        f"- **Page type:** {s.page_type.replace('_', ' ')}",
        f"- **Score:** {s.score}",
        f"- **Reason:** {s.reason}",
        f"- **Suggested anchor text:** {s.suggested_anchor_text}",
        f"- **Suggested sentence:** {s.suggested_insertion_sentence}",
        f"- **Location hint:** {s.suggested_location_hint}",
        f"- **Risk level:** {s.risk_level}",
        "",
    ]


def write_suggestions_reports(
    report: SuggestionReport,
    target_url: str,
    target_keyword: str | None,
    ts: str | None = None,
) -> tuple[Path, Path]:
    ts = ts or _timestamp()
    slug = slugify(target_url.rstrip("/").split("/")[-1] or "target", max_length=60)
    md_path = REPORTS_DIR / f"internal_link_suggestions_{slug}_{ts}.md"
    csv_path = REPORTS_DIR / f"internal_link_suggestions_{slug}_{ts}.csv"

    target_item = report.target_item
    target_title = target_item.title if target_item else target_url
    primary_label = (
        report.target_primary_cluster.replace("_", " ")
        if report.target_primary_cluster
        else "_(none detected)_"
    )
    secondary_label = (
        ", ".join(c.replace("_", " ") for c in report.target_secondary_clusters)
        if report.target_secondary_clusters
        else "_(none)_"
    )

    lines = [
        "# Internal Link Suggestions",
        "",
        "## Target article",
        f"- **Title:** {target_title}",
        f"- **URL:** {target_url}",
    ]
    if target_keyword:
        lines.append(f"- **Target keyword:** {target_keyword}")
    lines.extend([
        "",
        "## Target clusters (v1.2)",
        f"- **Primary cluster:** {primary_label}",
        f"- **Secondary clusters:** {secondary_label}",
        "",
        "## Editorial recommendation",
        f"**{report.final_recommendation}**",
        "",
        "## Internal support quality",
        report.already_linking_quality_note,
        "",
        "## Suggestions generated",
        f"- **Total accepted:** {len(report.suggestions)}",
        f"- **Strong:** {len(report.strong)}",
        f"- **Medium:** {len(report.medium)}",
        f"- **Strict mode:** {'yes' if report.strict_mode else 'no'}",
        "",
        "> LinkOps v1.2 is read-only. No WordPress content was modified.",
        "",
    ])

    if report.core_pages_excluded:
        lines.extend(["## Core pages excluded", ""])
        for title in report.core_pages_excluded:
            lines.append(f"- {title}")
        lines.append("")

    lines.extend(["## Strong suggestions", ""])
    if report.strong:
        for i, s in enumerate(report.strong, 1):
            lines.extend(_format_suggestion_block(s, i))
    else:
        lines.append("- _(none)_")
        lines.append("")

    lines.extend(["## Medium suggestions", ""])
    if report.medium:
        for i, s in enumerate(report.medium, 1):
            lines.extend(_format_suggestion_block(s, i))
    else:
        lines.append("- _(none)_")
        lines.append("")

    lines.extend(["## Pages already linking to target", ""])
    if report.already_linking:
        for p in report.already_linking:
            lines.append(f"- [{p.title}]({p.url})")
    else:
        lines.append("- _(none found in cache)_")
    lines.extend(["", "## Related pages already linking to target", ""])
    if report.related_already_linking:
        for p in report.related_already_linking:
            lines.append(f"- [{p.title}]({p.url})")
    else:
        lines.append("- _(none)_")
    lines.extend(["", "## Rejected weak candidates", ""])
    if report.rejected:
        for r in report.rejected[:25]:
            lines.append(
                f"- [{r.source_title}]({r.source_url}) — score {r.score}: {r.reason}"
            )
        if len(report.rejected) > 25:
            lines.append(f"- _…and {len(report.rejected) - 25} more_")
    else:
        lines.append("- _(none)_")
    lines.extend([
        "",
        "## Pages selected for Request Indexing after manual update",
        "",
        "_After you manually add internal links in WordPress, request indexing for these source URLs in Google Search Console (low/medium suggestions only):_",
        "",
    ])
    for s in report.suggestions:
        if s.risk_level in ("low", "medium"):
            lines.append(f"- [{s.source_title}]({s.source_url})")

    md_path.write_text("\n".join(lines), encoding="utf-8")

    csv_rows = [
        {
            "source_title": s.source_title,
            "source_url": s.source_url,
            "target_url": s.target_url,
            "page_type": s.page_type,
            "score": s.score,
            "reason": s.reason,
            "suggested_anchor_text": s.suggested_anchor_text,
            "suggested_sentence": s.suggested_insertion_sentence,
            "location_hint": s.suggested_location_hint,
            "target_already_linked": s.target_already_linked,
            "risk_level": s.risk_level,
            "strength": s.strength,
        }
        for s in report.suggestions
    ]
    pd.DataFrame(csv_rows).to_csv(csv_path, index=False, encoding="utf-8")
    return md_path, csv_path
