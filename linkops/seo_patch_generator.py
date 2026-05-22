"""Generate paste-ready SEO patches from content optimization analysis."""

from __future__ import annotations

from datetime import datetime, timezone

from linkops.content_model import ContentItem
from linkops.content_optimization_model import (
    ALIGNMENT_MISALIGNED,
    COVERAGE_EXACT,
    COVERAGE_MISSING,
    COVERAGE_PARTIAL,
    COVERAGE_STRONG,
    COVERAGE_WEAK,
    ContentOptimizationReport,
    REC_CONTENT,
    REC_FAQ_OPTIMIZATION,
    REC_INTERNAL_LINKS,
    REC_LIGHT,
    REC_MONITOR,
    REC_NO_CHANGE,
    REC_REVIEW_MANUAL,
    REC_TITLE_META,
)
from linkops.content_optimizer import (
    analyze_content_optimization,
    detect_content_topic,
)
from linkops.seo_patch_faq import (
    generate_safe_faq_answer,
    is_pricing_or_current_data_question,
    manual_review_reason,
)
from linkops.gsc_model import GscCache
from linkops.seo_patch_model import (
    PATCH_COMBINED,
    PATCH_FAQ,
    PATCH_HEADING,
    PATCH_INTERNAL,
    PATCH_INTRO,
    PATCH_MANUAL,
    PATCH_MONITOR,
    PATCH_TITLE_META,
    SeoPatchReport,
)

_INTRO_NO_SENTENCE_OPT = "No intro sentence needed."
_INTRO_NO_ADDITION = "No intro addition needed."
_NO_SEO_TITLE = "No SEO title change needed."
_NO_META = "No meta description change needed."
_NO_INTRO = _INTRO_NO_ADDITION
_NO_HEADING = "No heading addition needed."
_NO_FAQ = "No FAQ additions needed."
_NO_PASTE_FAQ = "No paste-ready FAQ additions available."
_NO_INTERNAL = "No new internal links needed now."


def _coverage_map(report: ContentOptimizationReport) -> dict[str, str]:
    return {c.field_name: c.status for c in report.coverage}


def _faq_needs_patch(report: ContentOptimizationReport) -> bool:
    status = _coverage_map(report).get("faq", COVERAGE_MISSING)
    if status in (COVERAGE_EXACT, COVERAGE_STRONG):
        return False
    if report.overall_recommendation == REC_FAQ_OPTIMIZATION:
        return True
    return status in (COVERAGE_WEAK, COVERAGE_MISSING, COVERAGE_PARTIAL)


def determine_patch_type(report: ContentOptimizationReport) -> str:
    """Map optimize analysis to a single primary patch type (or combined)."""
    if (
        report.intent_alignment == ALIGNMENT_MISALIGNED
        or report.overall_recommendation == REC_REVIEW_MANUAL
    ):
        return PATCH_MANUAL

    if report.overall_recommendation in (REC_NO_CHANGE, REC_MONITOR):
        return PATCH_MONITOR

    components: list[str] = []

    if report.overall_recommendation == REC_TITLE_META:
        components.append(PATCH_TITLE_META)
    if _faq_needs_patch(report) and report.faq.suggestions:
        components.append(PATCH_FAQ)
    if report.intro.needs_direct_sentence:
        components.append(PATCH_INTRO)
    if report.headings.keyword_in_h2_recommended or report.headings.missing_opportunities:
        components.append(PATCH_HEADING)
    if (
        report.overall_recommendation == REC_INTERNAL_LINKS
        or report.internal_links.support_level in ("weak", "unknown")
    ):
        components.append(PATCH_INTERNAL)

    if report.overall_recommendation == REC_CONTENT:
        if _faq_needs_patch(report):
            components.append(PATCH_FAQ)
        if report.intro.needs_direct_sentence:
            components.append(PATCH_INTRO)
        if report.headings.keyword_in_h2_recommended or report.headings.missing_opportunities:
            components.append(PATCH_HEADING)

    if report.overall_recommendation == REC_LIGHT and not components:
        if _faq_needs_patch(report):
            components.append(PATCH_FAQ)

    if not components:
        return PATCH_MONITOR
    if len(components) == 1:
        return components[0]
    return PATCH_COMBINED


def _editorial_decision(report: ContentOptimizationReport, patch_type: str) -> str:
    rec = report.overall_recommendation.replace("_", " ")
    if patch_type == PATCH_MONITOR:
        return (
            f"The page is in good shape for «{report.target_keyword}». "
            f"Recommendation: {rec}. Monitor GSC performance before making edits."
        )
    if patch_type == PATCH_MANUAL:
        return (
            "Intent alignment or page type may not match the target query. "
            "Review manually before applying any paste-ready changes."
        )
    if patch_type == PATCH_FAQ:
        return (
            "Core page coverage is already strong. Apply a focused FAQ-only patch "
            "using the questions below (do not duplicate existing FAQ content)."
        )
    if patch_type == PATCH_TITLE_META:
        return (
            "On-page coverage is solid but CTR may be low for the current GSC position. "
            "Consider updating the SEO title and meta description only."
        )
    if patch_type == PATCH_INTERNAL:
        return (
            "Content coverage is acceptable. Priority is building inbound internal links "
            "from related articles using the suggest command."
        )
    return (
        f"Apply a light combined patch ({patch_type.replace('_', ' ')}). "
        f"Do not rewrite the full article."
    )


def _do_not_change_checklist(report: ContentOptimizationReport) -> list[str]:
    slug_rec = report.title_meta.slug_recommendation
    items = [
        "Do not change the published URL slug unless manually required.",
        "Do not remove existing internal links.",
        "Do not rewrite the full article unless the page is clearly weak.",
        "Do not add duplicate FAQ questions.",
    ]
    title_status = _coverage_map(report).get("title", "")
    if title_status in (COVERAGE_EXACT, COVERAGE_PARTIAL, COVERAGE_STRONG):
        items.append("Do not change the main title if current coverage is already strong.")
    if "Keep current slug" in slug_rec:
        items.append(f"Slug: {slug_rec}.")
    elif "Review manually" in slug_rec:
        items.append(slug_rec)
    if report.faq.coverage_note:
        items.append("Do not add FAQ questions that repeat existing comparison or topic coverage.")
    return items


def _seo_title_section(
    report: ContentOptimizationReport,
    patch_type: str,
    *,
    include_title_meta: bool,
) -> str:
    if patch_type in (PATCH_MONITOR,) or report.overall_recommendation in (
        REC_NO_CHANGE,
        REC_MONITOR,
    ):
        return _NO_SEO_TITLE
    if patch_type == PATCH_TITLE_META or include_title_meta:
        title = report.title_meta.seo_title
        if "best best" in title.lower():
            return _NO_SEO_TITLE
        return title
    title_status = _coverage_map(report).get("title", "")
    if title_status in (COVERAGE_EXACT, COVERAGE_STRONG) and patch_type != PATCH_TITLE_META:
        return _NO_SEO_TITLE
    return _NO_SEO_TITLE


def _meta_section(
    report: ContentOptimizationReport,
    patch_type: str,
    *,
    include_title_meta: bool,
) -> str:
    if patch_type in (PATCH_MONITOR,) or report.overall_recommendation in (
        REC_NO_CHANGE,
        REC_MONITOR,
    ):
        return _NO_META
    if patch_type == PATCH_TITLE_META or include_title_meta:
        meta = report.title_meta.meta_description
        if len(meta) > 160:
            meta = meta[:157] + "..."
        return meta
    return _NO_META


def _intro_section(
    report: ContentOptimizationReport,
    patch_type: str,
    *,
    include_intro: bool,
) -> str:
    if patch_type == PATCH_MONITOR:
        return _NO_INTRO
    if report.intro.needs_direct_sentence or (
        include_intro and patch_type not in (PATCH_MONITOR,)
    ):
        sentence = report.intro.paste_ready_sentence
        if sentence == _INTRO_NO_SENTENCE_OPT or "No intro" in sentence:
            return _NO_INTRO
        return sentence
    return _NO_INTRO


def _heading_section(
    report: ContentOptimizationReport,
    patch_type: str,
    *,
    include_headings: bool,
) -> str:
    if patch_type == PATCH_MONITOR:
        return _NO_HEADING
    suggestions = report.headings.suggestions
    if not suggestions and not include_headings:
        return _NO_HEADING
    if not suggestions and include_headings:
        return _NO_HEADING
    if suggestions:
        lines = []
        for h in suggestions[:3]:
            lines.append(f"## {h}")
        return "\n\n".join(lines)
    return _NO_HEADING


def _faq_section(
    report: ContentOptimizationReport,
    patch_type: str,
    *,
    include_faq: bool,
    topic: str,
) -> tuple[str, list[str], list[str]]:
    if report.faq.coverage_note == "strong comparison coverage detected":
        return _NO_FAQ, [], []
    if not _faq_needs_patch(report) and not include_faq:
        return _NO_FAQ, [], []
    if patch_type == PATCH_MONITOR:
        return _NO_FAQ, [], []
    questions = list(report.faq.suggestions)
    if not questions:
        return _NO_FAQ, [], []

    paste_blocks: list[str] = []
    paste_questions: list[str] = []
    manual_items: list[str] = []

    for q in questions:
        answer = generate_safe_faq_answer(q, report, topic=topic)
        if answer is None:
            if is_pricing_or_current_data_question(q):
                manual_items.append(manual_review_reason(q))
            elif "best alternative" in q.lower():
                manual_items.append(manual_review_reason(q))
            else:
                manual_items.append(manual_review_reason(q))
            continue
        paste_questions.append(q)
        paste_blocks.extend([f"### {q}", "", answer, ""])

    if not paste_questions:
        return _NO_PASTE_FAQ, [], manual_items

    lines = ["## FAQ", ""] + paste_blocks
    return "\n".join(lines).strip(), paste_questions, manual_items


def _has_paste_ready_changes(
    seo_title: str,
    meta: str,
    intro: str,
    heading: str,
    faq_patch: str,
) -> bool:
    no_change = {
        _NO_SEO_TITLE,
        _NO_META,
        _NO_INTRO,
        _NO_HEADING,
        _NO_FAQ,
        _NO_PASTE_FAQ,
    }
    return any(
        v.strip() and v not in no_change
        for v in (seo_title, meta, intro, heading, faq_patch)
    )


def _finalize_patch_type(
    patch_type: str,
    report: ContentOptimizationReport,
    paste_faq_count: int,
    manual_faq_count: int,
) -> str:
    """Adjust patch type when FAQ suggestions cannot be pasted safely."""
    if paste_faq_count > 0:
        if patch_type == PATCH_MONITOR and _faq_needs_patch(report):
            return PATCH_FAQ if manual_faq_count == 0 else PATCH_FAQ
        return patch_type

    if patch_type not in (PATCH_FAQ, PATCH_COMBINED):
        return patch_type

    other_components = []
    if report.overall_recommendation == REC_TITLE_META:
        other_components.append(PATCH_TITLE_META)
    if report.intro.needs_direct_sentence:
        other_components.append(PATCH_INTRO)
    if report.headings.keyword_in_h2_recommended or report.headings.missing_opportunities:
        other_components.append(PATCH_HEADING)
    if report.overall_recommendation == REC_INTERNAL_LINKS or report.internal_links.support_level in (
        "weak",
        "unknown",
    ):
        other_components.append(PATCH_INTERNAL)

    if other_components:
        return PATCH_COMBINED if len(other_components) > 1 else other_components[0]

    if report.overall_recommendation in (REC_NO_CHANGE, REC_MONITOR):
        return PATCH_MONITOR
    if manual_faq_count > 0:
        return PATCH_MANUAL
    return PATCH_MONITOR


def _internal_link_section(report: ContentOptimizationReport, patch_type: str) -> str:
    if report.internal_links.support_level == "strong" and patch_type not in (
        PATCH_INTERNAL,
        PATCH_COMBINED,
    ):
        return _NO_INTERNAL
    if report.overall_recommendation == REC_INTERNAL_LINKS or patch_type == PATCH_INTERNAL:
        return report.internal_links.next_suggest_command
    if report.internal_links.support_level in ("weak", "unknown"):
        return report.internal_links.next_suggest_command
    return _NO_INTERNAL


def _next_commands(
    report: ContentOptimizationReport,
    target_url: str,
    keyword: str,
) -> list[str]:
    cmds = [
        f'python -m linkops.cli optimize --target-url "{target_url}" --target-keyword "{keyword}"',
        report.internal_links.next_suggest_command,
        "python -m linkops.cli opportunities --min-impressions 20 --max-clicks 0 --max-position 90",
    ]
    seen: list[str] = []
    for c in cmds:
        if c not in seen:
            seen.append(c)
    return seen


def generate_seo_patch(
    catalog: list[ContentItem],
    target_url: str,
    target_keyword: str,
    *,
    gsc_query: str | None = None,
    gsc_cache: GscCache | None = None,
    max_faq_suggestions: int = 5,
    max_heading_suggestions: int = 3,
    include_title_meta: bool = False,
    include_intro: bool = False,
    include_headings: bool = False,
    include_faq: bool = False,
) -> SeoPatchReport:
    """Build paste-ready SEO patch from optimize analysis."""
    opt = analyze_content_optimization(
        catalog,
        target_url,
        target_keyword,
        gsc_query=gsc_query,
        gsc_cache=gsc_cache,
        max_faq_suggestions=max_faq_suggestions,
        max_heading_suggestions=max_heading_suggestions,
    )

    patch_type = determine_patch_type(opt)
    topic = ""
    for item in catalog:
        if item.url.rstrip("/") == target_url.rstrip("/"):
            topic = detect_content_topic(target_keyword, item)
            break

    seo_title = _seo_title_section(opt, patch_type, include_title_meta=include_title_meta)
    meta = _meta_section(opt, patch_type, include_title_meta=include_title_meta)
    intro = _intro_section(opt, patch_type, include_intro=include_intro)
    heading = _heading_section(opt, patch_type, include_headings=include_headings)
    faq_patch, faq_questions, manual_review = _faq_section(
        opt, patch_type, include_faq=include_faq, topic=topic
    )
    patch_type = _finalize_patch_type(
        patch_type, opt, len(faq_questions), len(manual_review)
    )
    if patch_type == PATCH_MONITOR:
        if faq_patch == _NO_PASTE_FAQ or not faq_questions:
            faq_patch = _NO_FAQ
            faq_questions = []
    elif patch_type == PATCH_MANUAL and not faq_questions:
        faq_patch = _NO_PASTE_FAQ
    internal = _internal_link_section(opt, patch_type)

    has_paste = _has_paste_ready_changes(seo_title, meta, intro, heading, faq_patch)
    indexing_urls = (
        [opt.target_url]
        if has_paste
        else [opt.target_url]
    )

    return SeoPatchReport(
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        target_url=opt.target_url,
        target_keyword=opt.target_keyword,
        overall_recommendation=opt.overall_recommendation,
        patch_type=patch_type,
        editorial_decision=_editorial_decision(opt, patch_type),
        do_not_change=_do_not_change_checklist(opt),
        seo_title=seo_title,
        meta_description=meta,
        intro_addition=intro,
        heading_addition=heading,
        faq_patch=faq_patch,
        faq_questions=faq_questions,
        manual_review_needed=manual_review,
        internal_link_action=internal,
        request_indexing_urls=indexing_urls,
        next_commands=_next_commands(opt, opt.target_url, opt.target_keyword),
        query_intent=opt.query_intent,
        page_type=opt.page_type,
        intent_alignment=opt.intent_alignment,
    )
