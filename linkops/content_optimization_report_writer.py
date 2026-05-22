"""Markdown and CSV writers for content optimization reports."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from slugify import slugify

from linkops.config import REPORTS_DIR
from linkops.content_optimization_model import ContentOptimizationReport
from linkops.content_optimizer import READ_ONLY_NOTICE


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _status_label(status: str) -> str:
    return status.replace("_", " ")


def write_content_optimization_reports(
    report: ContentOptimizationReport,
    slug: str | None = None,
    ts: str | None = None,
) -> tuple[Path, Path]:
    """Write Markdown and CSV content optimization reports."""
    ts = ts or _timestamp()
    slug_part = slug or slugify(report.target_keyword) or "page"
    md_path = REPORTS_DIR / f"content_optimization_{slug_part}_{ts}.md"
    csv_path = REPORTS_DIR / f"content_optimization_{slug_part}_{ts}.csv"

    coverage_map = {c.field_name: c.status for c in report.coverage}

    md_lines = [
        "# Content Optimization Report",
        "",
        f"**Generated:** {report.generated_at}",
        f"**Target URL:** {report.target_url}",
        f"**Target keyword:** {report.target_keyword}",
        f"**Query intent:** {report.query_intent}",
        f"**Page type:** {report.page_type}",
        f"**Intent alignment:** {report.intent_alignment}",
        "",
        f"> {READ_ONLY_NOTICE}",
        "",
        "## Executive Summary",
        "",
        report.executive_summary,
        "",
        f"**Overall recommendation:** {report.overall_recommendation}",
        "",
    ]
    if report.recommendation_rationale:
        md_lines.append(f"**Why this recommendation:** {report.recommendation_rationale}")
        md_lines.append("")
    if report.priority_actions:
        md_lines.append("**Priority actions:**")
        for action in report.priority_actions:
            md_lines.append(f"- {action}")
        md_lines.append("")

    if report.gsc_metrics and report.gsc_metrics.available:
        g = report.gsc_metrics
        md_lines.extend(
            [
                "### GSC metrics (local cache)",
                "",
                f"- Query: {g.query}",
                f"- Impressions: {g.impressions}",
                f"- Clicks: {g.clicks}",
                f"- CTR: {g.ctr:.2f}%",
                f"- Average position: {g.position:.1f}",
                "",
            ]
        )
        if g.match_note:
            md_lines.append(f"- {g.match_note}")
            md_lines.append("")

    md_lines.extend(["## Query Coverage Audit", ""])
    for field in report.coverage:
        md_lines.append(
            f"- **{field.field_name}:** {_status_label(field.status)} — {field.detail}"
        )
    md_lines.append("")

    md_lines.extend(
        [
            "## Intro Analysis",
            "",
            f"- **Words analyzed (first ~150):** {report.intro.word_count}",
            f"- **Exact keyword early:** {report.intro.exact_keyword_early}",
            f"- **Answers search intent:** {report.intro.answers_intent}",
            f"- **Too generic:** {report.intro.too_generic}",
            f"- **Needs direct sentence:** {report.intro.needs_direct_sentence}",
            "",
        ]
    )
    if report.intro.needs_direct_sentence:
        md_lines.extend(
            [
                "**Paste-ready sentence:**",
                "",
                f"> {report.intro.paste_ready_sentence}",
                "",
            ]
        )
    else:
        md_lines.extend(
            [
                f"- **Intro sentence:** {report.intro.paste_ready_sentence}",
                "",
            ]
        )
    for note in report.intro.notes:
        md_lines.append(f"- {note}")
    md_lines.append("")

    md_lines.extend(["## Heading Analysis", ""])
    if report.headings.h1:
        md_lines.append(f"- **H1:** {' | '.join(report.headings.h1)}")
    if report.headings.relevant_headings:
        md_lines.append("- **Relevant existing headings:**")
        for h in report.headings.relevant_headings[:10]:
            md_lines.append(f"  - {h}")
    if report.headings.missing_opportunities:
        md_lines.append("- **Missing opportunities:**")
        for m in report.headings.missing_opportunities:
            md_lines.append(f"  - {m}")
    md_lines.append(
        f"- **H2 should include keyword:** {report.headings.keyword_in_h2_recommended}"
    )
    if report.headings.suggestions:
        md_lines.append("- **Suggested headings:**")
        for s in report.headings.suggestions:
            md_lines.append(f"  - {s}")
    md_lines.append("")

    md_lines.extend(["## FAQ Opportunities", ""])
    if report.faq.coverage_note:
        md_lines.append(f"- **FAQ coverage:** {report.faq.coverage_note}")
    if report.faq.existing_faq_items:
        md_lines.append("- **Existing FAQ-style content:**")
        for f in report.faq.existing_faq_items[:10]:
            md_lines.append(f"  - {f}")
    else:
        md_lines.append("- _(No FAQ-style headings detected)_")
    if report.faq.suggestions:
        md_lines.append("- **Suggested FAQ questions:**")
        for s in report.faq.suggestions:
            md_lines.append(f"  - {s}")
    else:
        md_lines.append("- **No additional FAQ questions needed.**")
    md_lines.append("")

    tm = report.title_meta
    md_lines.extend(
        [
            "## Title and Meta Suggestions",
            "",
            f"- **SEO Title:** {tm.seo_title}",
            f"- **Meta Description ({len(tm.meta_description)} chars):** {tm.meta_description}",
            f"- **Focus Keyword:** {tm.focus_keyword}",
            f"- **Slug recommendation:** {tm.slug_recommendation}",
            "",
            "## Content Gap Recommendations",
            "",
        ]
    )
    if report.content_gaps:
        for gap in report.content_gaps:
            md_lines.append(f"- {gap}")
    else:
        md_lines.append("- No urgent content gaps detected.")
    md_lines.append("")

    il = report.internal_links
    md_lines.extend(
        [
            "## Internal Link Support",
            "",
            f"- **Inbound internal links (cache):** {il.inbound_count if il.inbound_count is not None else 'unknown'}",
            f"- **Support level:** {il.support_level}",
            f"- **Notes:** {il.notes}",
            f"- **Next suggest command:** `{il.next_suggest_command}`",
            "",
            "## Suggested Next Commands",
            "",
        ]
    )
    for cmd in report.next_commands:
        md_lines.append(f"- `{cmd}`")
    md_lines.append("")

    md_lines.extend(["## Request Indexing Candidates", ""])
    for url in report.request_indexing_urls:
        md_lines.append(f"- {url}")
    md_lines.append("")

    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    row = {
        "target_url": report.target_url,
        "target_keyword": report.target_keyword,
        "query_intent": report.query_intent,
        "page_type": report.page_type,
        "intent_alignment": report.intent_alignment,
        "title_status": coverage_map.get("title", ""),
        "slug_status": coverage_map.get("slug", ""),
        "intro_status": coverage_map.get("first_150_words", ""),
        "heading_status": coverage_map.get("headings", ""),
        "faq_status": coverage_map.get("faq", ""),
        "overall_recommendation": report.overall_recommendation,
        "priority_actions": " | ".join(report.priority_actions),
        "seo_title_suggestion": tm.seo_title,
        "meta_description_suggestion": tm.meta_description,
        "focus_keyword": tm.focus_keyword,
        "slug_recommendation": tm.slug_recommendation,
        "next_command": report.internal_links.next_suggest_command,
        "request_indexing_urls": " | ".join(report.request_indexing_urls),
    }
    pd.DataFrame([row]).to_csv(csv_path, index=False, encoding="utf-8")

    return md_path, csv_path
