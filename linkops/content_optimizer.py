"""Read-only content optimization analysis from WordPress and GSC caches."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from linkops.content_model import ContentItem
from linkops.content_optimization_model import (
    ALIGNMENT_ALIGNED,
    ALIGNMENT_MISALIGNED,
    ALIGNMENT_PARTIAL,
    COVERAGE_EXACT,
    COVERAGE_MISSING,
    COVERAGE_PARTIAL,
    COVERAGE_WEAK,
    CoverageField,
    ContentOptimizationReport,
    FaqAnalysis,
    GscQueryMetrics,
    HeadingAnalysis,
    IntroAnalysis,
    InternalLinkSupport,
    LINK_SUPPORT_MODERATE,
    LINK_SUPPORT_STRONG,
    LINK_SUPPORT_UNKNOWN,
    LINK_SUPPORT_WEAK,
    REC_CONTENT,
    REC_INTERNAL_LINKS,
    REC_LIGHT,
    REC_MONITOR,
    REC_NO_CHANGE,
    REC_REVIEW_MANUAL,
    REC_TITLE_META,
    TitleMetaSuggestions,
)
from linkops.gsc_intent import (
    INTENT_BROAD_BEST,
    INTENT_COMPARISON,
    INTENT_HOW_TO,
    INTENT_INFORMATIONAL,
    INTENT_REVIEW,
    INTENT_UNKNOWN,
    PAGE_COMPARISON,
    PAGE_GUIDE,
    PAGE_REVIEW,
    PAGE_ROUNDUP,
    PAGE_UNKNOWN,
    detect_gsc_page_type,
    detect_query_intent,
)
from linkops.gsc_model import GscCache
from linkops.html_tools import extract_headings, html_to_plain_text, normalize_internal_url
from linkops.link_analyzer import pages_already_linking

READ_ONLY_NOTICE = (
    "This report is read-only. LinkOps does not modify WordPress, publish content, "
    "or call external APIs. Apply suggestions manually after editorial review."
)

_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "for",
        "to",
        "of",
        "in",
        "on",
        "and",
        "or",
        "is",
        "are",
        "with",
        "your",
        "my",
        "our",
    }
)

_FAQ_HEADING_MARKERS = (
    "faq",
    "frequently asked",
    "questions and answers",
    "common questions",
)

_TITLE_CASE_SMALL_WORDS = frozenset(
    {"a", "an", "the", "and", "or", "but", "for", "nor", "on", "at", "to", "by", "in", "of", "with", "vs"}
)

_STRONG_COVERAGE = frozenset({COVERAGE_EXACT, COVERAGE_PARTIAL})

_GSC_RELATED_MIN_OVERLAP = 0.45


def _normalize_phrase(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def _keyword_tokens(keyword: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", keyword.lower()) if t not in _STOPWORDS and len(t) > 1]


def _phrase_in_text(phrase: str, text: str) -> bool:
    if not phrase or not text:
        return False
    return _normalize_phrase(phrase) in _normalize_phrase(text)


def _token_overlap_ratio(keyword: str, text: str) -> float:
    tokens = _keyword_tokens(keyword)
    if not tokens:
        return 0.0
    blob = _normalize_phrase(text)
    hits = sum(1 for t in tokens if t in blob)
    return hits / len(tokens)


def smart_title_case(text: str) -> str:
    """Natural English title case; keep short prepositions/articles lowercase."""
    if not text.strip():
        return text

    def _case_segment(segment: str) -> str:
        words = segment.split()
        if not words:
            return segment
        out: list[str] = []
        for i, word in enumerate(words):
            core = re.sub(r"[^a-zA-Z0-9]+", "", word)
            lower = core.lower()
            if not core:
                out.append(word)
                continue
            if i == 0 or i == len(words) - 1 or lower not in _TITLE_CASE_SMALL_WORDS:
                repl = core[0].upper() + core[1:].lower() if len(core) > 1 else core.upper()
                out.append(word.replace(core, repl, 1))
            else:
                out.append(word.replace(core, lower, 1))
        return " ".join(out)

    if ":" in text:
        parts = text.split(":", 1)
        return f"{_case_segment(parts[0].strip())}: {_case_segment(parts[1].strip())}"
    return _case_segment(text)


def classify_coverage(keyword: str, text: str) -> tuple[str, str]:
    """Return coverage status and short detail for a text field."""
    if not text or not text.strip():
        return COVERAGE_MISSING, "field empty"
    if _phrase_in_text(keyword, text):
        return COVERAGE_EXACT, "exact phrase present"
    ratio = _token_overlap_ratio(keyword, text)
    if ratio >= 0.75:
        return COVERAGE_PARTIAL, f"strong token overlap ({ratio:.0%})"
    if ratio >= 0.45:
        return COVERAGE_WEAK, f"partial token overlap ({ratio:.0%})"
    return COVERAGE_MISSING, "keyword not detected"


def classify_heading_coverage(
    keyword: str,
    h2_list: list[str],
    h3_list: list[str],
) -> tuple[str, str, bool]:
    """Return status, detail, and whether exact phrase appears in H2/H3."""
    combined = h2_list + h3_list
    if not combined:
        return COVERAGE_MISSING, "no H2/H3 headings found", False
    if any(_phrase_in_text(keyword, h) for h in combined):
        return COVERAGE_EXACT, "exact phrase present in H2/H3", True
    text = " ".join(combined)
    status, detail = classify_coverage(keyword, text)
    return status, detail, False


def compute_intent_alignment(query_intent: str, page_type: str) -> str:
    """Map query intent and page type to alignment label."""
    aligned = {
        (INTENT_BROAD_BEST, PAGE_ROUNDUP),
        (INTENT_COMPARISON, PAGE_COMPARISON),
        (INTENT_REVIEW, PAGE_REVIEW),
        (INTENT_HOW_TO, PAGE_GUIDE),
    }
    partial = {
        (INTENT_INFORMATIONAL, PAGE_ROUNDUP),
        (INTENT_INFORMATIONAL, PAGE_GUIDE),
        (INTENT_BROAD_BEST, PAGE_GUIDE),
        (INTENT_UNKNOWN, PAGE_ROUNDUP),
        (INTENT_UNKNOWN, PAGE_UNKNOWN),
    }
    pair = (query_intent, page_type)
    if pair in aligned:
        return ALIGNMENT_ALIGNED
    if pair in partial:
        return ALIGNMENT_PARTIAL
    misaligned_pairs = {
        (INTENT_BROAD_BEST, PAGE_REVIEW),
        (INTENT_BROAD_BEST, PAGE_COMPARISON),
        (INTENT_REVIEW, PAGE_ROUNDUP),
        (INTENT_COMPARISON, PAGE_ROUNDUP),
        (INTENT_HOW_TO, PAGE_ROUNDUP),
        (INTENT_HOW_TO, PAGE_REVIEW),
    }
    if pair in misaligned_pairs:
        return ALIGNMENT_MISALIGNED
    if query_intent == INTENT_BROAD_BEST and page_type in (PAGE_REVIEW, PAGE_COMPARISON, PAGE_GUIDE):
        return ALIGNMENT_MISALIGNED
    if query_intent == INTENT_REVIEW and page_type != PAGE_REVIEW:
        return ALIGNMENT_MISALIGNED
    if query_intent == INTENT_COMPARISON and page_type != PAGE_COMPARISON:
        return ALIGNMENT_MISALIGNED
    if query_intent == INTENT_HOW_TO and page_type != PAGE_GUIDE:
        return ALIGNMENT_MISALIGNED
    return ALIGNMENT_PARTIAL


def find_item_by_url(catalog: list[ContentItem], target_url: str) -> ContentItem | None:
    target_norm = normalize_internal_url(target_url)
    if not target_norm:
        return None
    for item in catalog:
        if item.normalized_url() == target_norm:
            return item
    return None


def _first_n_words(text: str, n: int) -> str:
    words = text.split()
    return " ".join(words[:n]) if words else ""


def _extract_faq_items(headings: dict[str, list[str]], plain_text: str) -> list[str]:
    items: list[str] = []
    for level in ("h2", "h3"):
        for h in headings.get(level, []):
            hl = h.lower()
            if "?" in h or any(m in hl for m in _FAQ_HEADING_MARKERS):
                items.append(h)
    for line in plain_text.split("."):
        line = line.strip()
        if line.endswith("?") and len(line) > 15:
            items.append(line[:200])
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique[:20]


def _heading_relevant(keyword: str, heading: str) -> bool:
    return _token_overlap_ratio(keyword, heading) >= 0.4 or _phrase_in_text(keyword, heading)


def _title_case_keyword(keyword: str) -> str:
    return smart_title_case(keyword.strip())


def _generate_intro_sentence(keyword: str, query_intent: str, page_type: str) -> str:
    kw = keyword.strip().rstrip(".")
    if query_intent == INTENT_REVIEW or page_type == PAGE_REVIEW:
        brand = _keyword_tokens(kw)
        product = brand[0].title() if brand else "this tool"
        return (
            f"This {product} review for small businesses covers pricing, meeting quality, "
            f"ease of use, and whether it is worth it for day-to-day team communication."
        )
    if query_intent == INTENT_COMPARISON or page_type == PAGE_COMPARISON:
        return (
            f"Choosing between these tools for a small team comes down to workflow complexity, "
            f"pricing, and how clearly each platform handles tasks, deadlines, and collaboration."
        )
    if query_intent == INTENT_HOW_TO:
        return (
            f"To {kw}, start with a simple workflow your team can follow every week: "
            f"clear ownership, visible deadlines, and one shared place for updates."
        )
    return (
        f"The best {kw} should help with task ownership, deadlines, collaboration, "
        f"and project visibility without adding unnecessary complexity."
    )


def _generate_heading_suggestions(
    keyword: str,
    query_intent: str,
    existing: list[str],
    max_suggestions: int,
) -> list[str]:
    title_kw = _title_case_keyword(keyword)
    candidates: list[str] = []
    if query_intent == INTENT_BROAD_BEST:
        candidates = [
            smart_title_case(f"Best {title_kw}"),
            smart_title_case("Project Management Tools vs Project Management Software for Small Teams"),
            smart_title_case(f"How to Choose Project Management Software for a Small Team"),
            smart_title_case(f"What Small Teams Should Look for in {title_kw}"),
            smart_title_case(f"Top Features to Compare in {title_kw}"),
        ]
    elif query_intent == INTENT_REVIEW:
        brand = _keyword_tokens(keyword)
        product = brand[0].title() if brand else title_kw.split()[0]
        candidates = [
            smart_title_case(f"Is {product} Good for Small Businesses?"),
            smart_title_case(f"{product} Pricing and Plans for Small Teams"),
            smart_title_case(f"Pros and Cons of {product} for Small Business Use"),
            smart_title_case(f"Who Should Use {product}?"),
        ]
    elif query_intent == INTENT_COMPARISON:
        candidates = [
            f"{title_kw}: Quick Comparison",
            f"Which Tool Is Better for Small Teams?",
            f"Key Differences at a Glance",
            f"Pricing and Ease of Use Comparison",
        ]
    elif query_intent == INTENT_HOW_TO:
        candidates = [
            f"How to {title_kw}",
            f"Step-by-Step Setup for Small Teams",
            f"Common Mistakes to Avoid",
        ]
    else:
        candidates = [
            f"{title_kw}: Overview",
            f"What You Need to Know",
            f"Practical Recommendations",
        ]

    existing_lower = {h.lower() for h in existing}
    out: list[str] = []
    for c in candidates:
        if c.lower() not in existing_lower:
            out.append(c)
        if len(out) >= max_suggestions:
            break
    return out


def _generate_faq_suggestions(
    keyword: str,
    query_intent: str,
    existing: list[str],
    max_suggestions: int,
) -> list[str]:
    kw = keyword.strip().rstrip("?")
    title_kw = _title_case_keyword(kw)
    if query_intent == INTENT_REVIEW:
        brand = _keyword_tokens(kw)
        product = brand[0].title() if brand else "this tool"
        candidates = [
            f"Is {product} good for small businesses?",
            f"Is {product} good for small business video meetings and calling?",
            f"Is {product} worth it for a small business?",
            f"What is the best alternative to {product} for small businesses?",
            f"How much does {product} cost for a small team?",
        ]
    elif query_intent == INTENT_COMPARISON:
        candidates = [
            f"Which is better for small teams in this comparison?",
            f"What is the main difference between these tools?",
            f"Which option is easier for a small team to adopt?",
            f"Which tool has better pricing for small businesses?",
        ]
    elif query_intent == INTENT_BROAD_BEST:
        candidates = [
            f"What is the best {kw}?",
            f"What should small teams look for in {kw}?",
            f"Do small teams need project management software?",
            f"What is the easiest {kw}?",
            f"What is the difference between project management tools and project management software?",
        ]
    else:
        candidates = [
            f"What is {title_kw}?",
            f"Who is {title_kw} best for?",
            f"What should I consider before choosing?",
        ]

    existing_blob = " ".join(existing).lower()
    out: list[str] = []
    for c in candidates:
        if c.lower() not in existing_blob:
            out.append(c)
        if len(out) >= max_suggestions:
            break
    return out


def _slug_recommendation(item: ContentItem, keyword: str) -> str:
    """Safe slug guidance for published URLs — never casually suggest replacing indexed slugs."""
    slug_status, _ = classify_coverage(keyword, item.slug.replace("-", " "))
    if slug_status in (COVERAGE_EXACT, COVERAGE_PARTIAL):
        return "Keep current slug"
    return "Review manually; changing published slugs can affect SEO and redirects"


def _build_title_meta(keyword: str, item: ContentItem, query_intent: str) -> TitleMetaSuggestions:
    title_kw = _title_case_keyword(keyword)
    if query_intent == INTENT_REVIEW:
        brand = _keyword_tokens(keyword)
        product = brand[0].title() if brand else title_kw
        seo_title = smart_title_case(f"{product} Review for Small Businesses: Is It Worth It?")
        meta = (
            f"Read our {product} review for small businesses: pricing, pros and cons, "
            f"and whether it fits your team's meetings and communication needs."
        )[:158]
        focus = f"{product.lower()} review small business"
    elif query_intent == INTENT_COMPARISON:
        seo_title = smart_title_case(f"{title_kw} for Small Teams (Compared)")
        meta = (
            f"Compare features, pricing, and fit for small teams. "
            f"See which option is easier to adopt and better for day-to-day work."
        )[:158]
        focus = keyword.lower()
    else:
        seo_title = smart_title_case(f"Best {title_kw} (Practical Guide for Small Teams)")
        meta = (
            f"Find the best options for small teams: features, pricing, and practical "
            f"recommendations to improve visibility and reduce workflow friction."
        )[:158]
        focus = keyword.lower()

    if len(meta) > 160:
        meta = meta[:157] + "..."
    return TitleMetaSuggestions(
        seo_title=seo_title,
        meta_description=meta,
        focus_keyword=focus,
        slug_recommendation=_slug_recommendation(item, keyword),
    )


def _gsc_row_to_metrics(row, *, matched_via: str, match_note: str) -> GscQueryMetrics:
    return GscQueryMetrics(
        query=row.query,
        clicks=row.clicks,
        impressions=row.impressions,
        ctr=row.ctr,
        position=row.position,
        available=True,
        matched_via=matched_via,
        match_note=match_note,
    )


def _queries_for_target_page(
    gsc_cache: GscCache,
    target_norm: str,
) -> list[str]:
    """Distinct queries in GSC cache associated with the target page URL."""
    found: list[str] = []
    seen: set[str] = set()
    for qp in gsc_cache.query_pages:
        page_norm = normalize_internal_url(qp.page)
        if page_norm == target_norm and qp.query.lower().strip() not in seen:
            seen.add(qp.query.lower().strip())
            found.append(qp.query)
    return found


def _lookup_gsc_metrics(
    gsc_cache: GscCache | None,
    lookup_query: str,
    target_url: str,
) -> GscQueryMetrics | None:
    if not gsc_cache:
        return None
    q_norm = _normalize_phrase(lookup_query)
    target_norm = normalize_internal_url(target_url)

    for row in gsc_cache.queries:
        if _normalize_phrase(row.query) == q_norm:
            return _gsc_row_to_metrics(row, matched_via="exact", match_note="")

    page_queries = _queries_for_target_page(gsc_cache, target_norm) if target_norm else []
    candidates: list[tuple[float, object, bool]] = []

    for row in gsc_cache.queries:
        overlap = _token_overlap_ratio(lookup_query, row.query)
        on_page = row.query in page_queries or any(
            _normalize_phrase(row.query) == _normalize_phrase(pq) for pq in page_queries
        )
        if on_page:
            overlap = max(overlap, _GSC_RELATED_MIN_OVERLAP)
        if overlap >= _GSC_RELATED_MIN_OVERLAP:
            score = overlap + (0.25 if on_page else 0.0) + (row.impressions / 10000.0)
            candidates.append((score, row, on_page))

    if not candidates and page_queries:
        for pq in page_queries:
            for row in gsc_cache.queries:
                if _normalize_phrase(row.query) == _normalize_phrase(pq):
                    return _gsc_row_to_metrics(
                        row,
                        matched_via="related",
                        match_note=f"GSC metrics matched from related query: {row.query}",
                    )

    if candidates:
        candidates.sort(key=lambda x: -x[0])
        best_row = candidates[0][1]
        note = ""
        if _normalize_phrase(best_row.query) != q_norm:
            note = f"GSC metrics matched from related query: {best_row.query}"
        return _gsc_row_to_metrics(
            best_row,
            matched_via="related" if note else "exact",
            match_note=note,
        )
    return None


def _inbound_link_support(catalog: list[ContentItem], target_url: str, keyword: str) -> InternalLinkSupport:
    linking = pages_already_linking(catalog, target_url)
    count = len(linking)
    if count >= 5:
        level = LINK_SUPPORT_STRONG
    elif count >= 2:
        level = LINK_SUPPORT_MODERATE
    elif count >= 1:
        level = LINK_SUPPORT_WEAK
    else:
        level = LINK_SUPPORT_WEAK
    cmd = (
        f'python -m linkops.cli suggest --target-url "{target_url}" '
        f'--target-keyword "{keyword}" --max-suggestions 8'
    )
    notes = f"{count} catalog page(s) already link to this target."
    if count == 0:
        notes = "No inbound internal links detected in WordPress cache."
    return InternalLinkSupport(
        inbound_count=count,
        support_level=level,
        next_suggest_command=cmd,
        notes=notes,
    )


def _aggregate_coverage_status(fields: list[CoverageField]) -> dict[str, str]:
    return {f.field_name: f.status for f in fields}


def _coverage_is_strong(coverage_map: dict[str, str]) -> bool:
    """True when title/slug/intro/body/headings/FAQ are in good shape."""
    return (
        coverage_map.get("title") in _STRONG_COVERAGE
        and coverage_map.get("slug") in _STRONG_COVERAGE
        and coverage_map.get("first_150_words") == COVERAGE_EXACT
        and coverage_map.get("body") in _STRONG_COVERAGE
        and coverage_map.get("headings") in _STRONG_COVERAGE
        and coverage_map.get("faq") in _STRONG_COVERAGE
    )


def _has_material_content_gaps(coverage_map: dict[str, str]) -> bool:
    check_fields = ("title", "slug", "first_150_words", "headings", "faq", "body")
    return any(coverage_map.get(f) in (COVERAGE_MISSING, COVERAGE_WEAK) for f in check_fields)


def _compute_overall_recommendation(
    *,
    coverage_map: dict[str, str],
    intent_alignment: str,
    gsc: GscQueryMetrics | None,
    link_support: str,
) -> tuple[str, list[str], str]:
    priority: list[str] = []
    strong = _coverage_is_strong(coverage_map)
    material_gaps = _has_material_content_gaps(coverage_map)

    if intent_alignment == ALIGNMENT_MISALIGNED:
        priority.append("Review page type vs query intent before heavy optimization.")
        rationale = "Query intent and page type do not align; manual editorial review is safer than bulk edits."
        return REC_REVIEW_MANUAL, priority, rationale

    if (
        gsc
        and gsc.available
        and gsc.clicks == 0
        and gsc.impressions >= 20
        and 8 <= gsc.position <= 20
        and not material_gaps
    ):
        priority.append("On-page coverage is solid; prioritize title/meta CTR and indexing.")
        rationale = (
            f"GSC shows position {gsc.position:.1f} with zero clicks — title/meta and SERP presentation "
            "are the main levers, not major content rewrites."
        )
        return REC_TITLE_META, priority, rationale

    if strong and link_support == LINK_SUPPORT_STRONG:
        if gsc and gsc.available and 20 < gsc.position <= 90:
            priority.append("Strong coverage and internal links; monitor position movement.")
            rationale = (
                f"Content and internal links are already strong; GSC position {gsc.position:.1f} "
                "suggests monitoring rather than heavy optimization."
            )
            return REC_MONITOR, priority, rationale
        priority.append("No urgent on-page or internal-link changes detected.")
        rationale = "Title, slug, intro, body, headings, FAQ, and internal links are already in good shape."
        return REC_NO_CHANGE, priority, rationale

    if material_gaps:
        priority.append("Add or strengthen target keyword in title, intro, headings, and FAQ.")
        rationale = "One or more important coverage areas are weak or missing the target keyword."
        return REC_CONTENT, priority, rationale

    if link_support in (LINK_SUPPORT_WEAK, LINK_SUPPORT_UNKNOWN):
        priority.append("Build internal link support from related articles.")
        rationale = "Content coverage is acceptable, but inbound internal links are limited."
        return REC_INTERNAL_LINKS, priority, rationale

    if strong and gsc and gsc.available and 20 < gsc.position <= 90:
        priority.append("Coverage is strong; monitor GSC position and CTR.")
        rationale = (
            f"On-page coverage is already strong for position {gsc.position:.1f}; "
            "prefer monitoring or light tweaks over a full content rewrite."
        )
        return REC_MONITOR, priority, rationale

    weak_any = any(coverage_map.get(f) == COVERAGE_WEAK for f in coverage_map)
    if weak_any:
        priority.append("Light copy tweaks may improve topical clarity.")
        rationale = "Some fields show only partial keyword overlap; light edits may help."
        return REC_LIGHT, priority, rationale

    priority.append("Monitor GSC position and CTR; no urgent on-page changes detected.")
    rationale = "No material content gaps detected; continue monitoring performance."
    return REC_NO_CHANGE, priority, rationale


def _build_content_gaps(
    coverage: list[CoverageField],
    headings: HeadingAnalysis,
    faq: FaqAnalysis,
) -> list[str]:
    gaps: list[str] = []
    skip_heading_gap = not headings.keyword_in_h2_recommended and not headings.missing_opportunities
    for field in coverage:
        if field.field_name == "headings" and skip_heading_gap:
            continue
        if field.status in (COVERAGE_MISSING, COVERAGE_WEAK):
            gaps.append(f"Improve {field.field_name}: {field.detail}")
    for h in headings.missing_opportunities[:1]:
        gaps.append(h)
    if not faq.existing_faq_items and faq.suggestions:
        gaps.append("Add an FAQ section with question-style H2/H3 headings.")
    return gaps


def _executive_summary(
    keyword: str,
    overall: str,
    intent_alignment: str,
    gsc: GscQueryMetrics | None,
    rationale: str,
) -> str:
    parts = [f"Target keyword «{keyword}» — overall recommendation: {overall}."]
    parts.append(f"Intent alignment: {intent_alignment}.")
    if gsc and gsc.available:
        gsc_line = (
            f"GSC: {gsc.impressions} impressions, {gsc.clicks} clicks, avg position {gsc.position:.1f}."
        )
        if gsc.match_note:
            gsc_line += f" {gsc.match_note}"
        parts.append(gsc_line)
    else:
        parts.append("GSC metrics not available for this query (import gsc-import to enrich).")
    parts.append(f"Why this recommendation: {rationale}")
    return " ".join(parts)


def analyze_content_optimization(
    catalog: list[ContentItem],
    target_url: str,
    target_keyword: str,
    *,
    gsc_query: str | None = None,
    gsc_cache: GscCache | None = None,
    max_faq_suggestions: int = 5,
    max_heading_suggestions: int = 5,
) -> ContentOptimizationReport:
    """Build a full content optimization report for one target page."""
    item = find_item_by_url(catalog, target_url)
    if item is None:
        raise ValueError(
            f"Target URL not found in WordPress content cache: {target_url}\n"
            "Run: python -m linkops.cli fetch"
        )

    keyword = target_keyword.strip()
    gsc_lookup = (gsc_query or keyword).strip()
    query_intent = detect_query_intent(keyword)
    page_type = detect_gsc_page_type(item)
    intent_alignment = compute_intent_alignment(query_intent, page_type)

    plain = item.plain_text or html_to_plain_text(item.content_html)
    headings_raw = extract_headings(item.content_html)
    all_headings = headings_raw["h1"] + headings_raw["h2"] + headings_raw["h3"]
    intro_100 = _first_n_words(plain, 100)
    intro_150 = _first_n_words(plain, 150)
    slug_text = item.slug.replace("-", " ")

    heading_status, heading_detail, exact_in_headings = classify_heading_coverage(
        keyword, headings_raw["h2"], headings_raw["h3"]
    )

    coverage = [
        CoverageField("title", *classify_coverage(keyword, item.title)),
        CoverageField("slug", *classify_coverage(keyword, slug_text)),
        CoverageField(
            "h1",
            *classify_coverage(keyword, " ".join(headings_raw["h1"]) or item.title),
        ),
        CoverageField("headings", heading_status, heading_detail),
        CoverageField("first_100_words", *classify_coverage(keyword, intro_100)),
        CoverageField("first_150_words", *classify_coverage(keyword, intro_150)),
        CoverageField("body", *classify_coverage(keyword, plain)),
        CoverageField(
            "faq",
            *classify_coverage(keyword, " ".join(_extract_faq_items(headings_raw, plain))),
        ),
    ]

    exact_early = _phrase_in_text(keyword, intro_150[: max(len(intro_150) // 2, 80)])
    answers_intent = intent_alignment == ALIGNMENT_ALIGNED or _token_overlap_ratio(keyword, intro_150) >= 0.5
    too_generic = _token_overlap_ratio(keyword, intro_150) < 0.35 and not exact_early
    needs_direct = not exact_early or too_generic

    intro = IntroAnalysis(
        word_count=len(intro_150.split()),
        exact_keyword_early=exact_early,
        answers_intent=answers_intent,
        too_generic=too_generic,
        needs_direct_sentence=needs_direct,
        paste_ready_sentence=_generate_intro_sentence(keyword, query_intent, page_type),
        notes=[
            "Exact keyword in first 150 words." if exact_early else "Exact keyword not in opening 150 words.",
            "Intro aligns with detected query intent." if answers_intent else "Intro may not directly answer search intent.",
        ],
    )

    relevant = [h for h in all_headings if _heading_relevant(keyword, h)]
    missing_ops: list[str] = []
    heading_suggestions: list[str] = []
    keyword_h2_rec = False

    if exact_in_headings:
        keyword_h2_rec = False
    elif heading_status == COVERAGE_PARTIAL:
        missing_ops.append(
            "Consider one H2 with a close variant of the target keyword (exact phrase not yet in H2/H3)."
        )
        heading_suggestions = _generate_heading_suggestions(
            keyword, query_intent, all_headings, 1
        )[:1]
        keyword_h2_rec = False
    elif heading_status in (COVERAGE_MISSING, COVERAGE_WEAK):
        missing_ops.append("Add one H2 that includes the target keyword or a close variant.")
        heading_suggestions = _generate_heading_suggestions(
            keyword, query_intent, all_headings, 1
        )[:1]
        keyword_h2_rec = True
    else:
        keyword_h2_rec = False

    headings = HeadingAnalysis(
        h1=headings_raw["h1"],
        h2=headings_raw["h2"],
        h3=headings_raw["h3"],
        relevant_headings=relevant,
        missing_opportunities=missing_ops,
        keyword_in_h2_recommended=keyword_h2_rec,
        suggestions=heading_suggestions,
    )

    faq_existing = _extract_faq_items(headings_raw, plain)
    faq = FaqAnalysis(
        existing_faq_items=faq_existing,
        suggestions=_generate_faq_suggestions(keyword, query_intent, faq_existing, max_faq_suggestions),
    )

    title_meta = _build_title_meta(keyword, item, query_intent)
    gsc_metrics = _lookup_gsc_metrics(gsc_cache, gsc_lookup, target_url)
    internal = _inbound_link_support(catalog, target_url, keyword)
    coverage_map = _aggregate_coverage_status(coverage)
    overall, priority, rationale = _compute_overall_recommendation(
        coverage_map=coverage_map,
        intent_alignment=intent_alignment,
        gsc=gsc_metrics,
        link_support=internal.support_level,
    )

    content_gaps = _build_content_gaps(coverage, headings, faq)
    target_norm = normalize_internal_url(target_url) or target_url
    next_commands = [
        internal.next_suggest_command,
        f'python -m linkops.cli optimize --target-url "{target_norm}/" --target-keyword "{keyword}"',
    ]
    if gsc_cache is None:
        next_commands.append("python -m linkops.cli gsc-import --queries-csv .\\exports\\gsc_queries.csv")

    return ContentOptimizationReport(
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        target_url=target_norm + "/" if not target_url.endswith("/") else target_url,
        target_keyword=keyword,
        gsc_query=gsc_lookup,
        query_intent=query_intent,
        page_type=page_type,
        intent_alignment=intent_alignment,
        coverage=coverage,
        intro=intro,
        headings=headings,
        faq=faq,
        title_meta=title_meta,
        content_gaps=content_gaps,
        internal_links=internal,
        overall_recommendation=overall,
        priority_actions=priority,
        recommendation_rationale=rationale,
        executive_summary=_executive_summary(
            keyword, overall, intent_alignment, gsc_metrics, rationale
        ),
        gsc_metrics=gsc_metrics,
        next_commands=next_commands,
        request_indexing_urls=[target_norm + "/"],
    )
