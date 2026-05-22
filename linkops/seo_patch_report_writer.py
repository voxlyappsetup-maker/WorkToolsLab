"""Markdown and CSV writers for paste-ready SEO patch reports."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from slugify import slugify

from linkops.config import REPORTS_DIR
from linkops.content_optimizer import READ_ONLY_NOTICE
from linkops.seo_patch_model import SeoPatchReport


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def write_seo_patch_reports(
    report: SeoPatchReport,
    slug: str | None = None,
    ts: str | None = None,
) -> tuple[Path, Path]:
    """Write Markdown and CSV SEO patch reports."""
    ts = ts or _timestamp()
    slug_part = slug or slugify(report.target_keyword) or "page"
    md_path = REPORTS_DIR / f"seo_patch_{slug_part}_{ts}.md"
    csv_path = REPORTS_DIR / f"seo_patch_{slug_part}_{ts}.csv"

    md_lines = [
        "# Paste-Ready SEO Patch",
        "",
        f"**Generated:** {report.generated_at}",
        f"**Target URL:** {report.target_url}",
        f"**Target keyword:** {report.target_keyword}",
        f"**Overall recommendation:** {report.overall_recommendation}",
        f"**Patch type:** {report.patch_type}",
        f"**Query intent:** {report.query_intent}",
        f"**Page type:** {report.page_type}",
        "",
        f"> {READ_ONLY_NOTICE}",
        "",
        "## Editorial Decision",
        "",
        report.editorial_decision,
        "",
        "## Do Not Change",
        "",
    ]
    for item in report.do_not_change:
        md_lines.append(f"- {item}")
    md_lines.append("")

    md_lines.extend(
        [
            "## Paste-Ready Changes",
            "",
            "### SEO Title",
            "",
            report.seo_title,
            "",
            "### Meta Description",
            "",
            report.meta_description,
            "",
            "### Intro Addition",
            "",
            report.intro_addition,
            "",
            "### Heading Addition",
            "",
            report.heading_addition,
            "",
            "### FAQ Patch",
            "",
        ]
    )
    faq_text = report.faq_patch or "No FAQ additions needed."
    if faq_text in ("No FAQ additions needed.", "No paste-ready FAQ additions available."):
        md_lines.append(faq_text)
    else:
        md_lines.append(faq_text)
    md_lines.append("")

    md_lines.extend(
        [
            "### Internal Link Action",
            "",
            report.internal_link_action,
            "",
            "## Manual Review Needed",
            "",
        ]
    )
    if report.manual_review_needed:
        for item in report.manual_review_needed:
            md_lines.append(f"- {item}")
    else:
        md_lines.append("No manual review items.")
    md_lines.append("")

    md_lines.extend(
        [
            "## Request Indexing",
            "",
        ]
    )
    for url in report.request_indexing_urls:
        md_lines.append(f"- {url}")
    md_lines.append("")

    md_lines.extend(["## Next Commands", ""])
    for cmd in report.next_commands:
        md_lines.append(f"- `{cmd}`")
    md_lines.append("")

    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    row = {
        "target_url": report.target_url,
        "target_keyword": report.target_keyword,
        "overall_recommendation": report.overall_recommendation,
        "patch_type": report.patch_type,
        "seo_title": report.seo_title,
        "meta_description": report.meta_description,
        "intro_addition": report.intro_addition,
        "heading_addition": report.heading_addition,
        "faq_questions_count": len(report.faq_questions),
        "manual_review_count": len(report.manual_review_needed),
        "internal_link_action": report.internal_link_action,
        "request_indexing_urls": " | ".join(report.request_indexing_urls),
        "next_commands": " | ".join(report.next_commands),
    }
    pd.DataFrame([row]).to_csv(csv_path, index=False, encoding="utf-8")

    return md_path, csv_path
