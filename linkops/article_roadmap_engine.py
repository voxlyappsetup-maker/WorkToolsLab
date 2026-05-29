"""Build new-article opportunity roadmap from GSC queries and WordPress catalog."""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timezone

from linkops.article_roadmap_model import (
    ACTION_CREATE_NEW_ARTICLE,
    ACTION_MANUAL_REVIEW,
    ACTION_MONITOR_ONLY,
    ACTION_UPDATE_EXISTING_PAGE,
    ARTICLE_COMPARISON,
    ARTICLE_CONCEPT_COMPARISON,
    ARTICLE_GLOSSARY,
    ARTICLE_GUIDE,
    ARTICLE_REVIEW,
    ARTICLE_ROUNDUP,
    ArticleCandidate,
    ArticleRoadmapReport,
    ConsolidatedQueryGroup,
    ExcludedQuery,
    PRIORITY_HIGH,
    PRIORITY_LOW,
    PRIORITY_MANUAL,
    PRIORITY_MEDIUM,
)
from linkops.content_model import ContentItem
from linkops.content_optimizer import (
    ALIGNMENT_MISALIGNED,
    capitalize_brand,
    compute_intent_alignment,
    smart_title_case,
)
from linkops.gsc_intent import (
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    INTENT_BROAD_BEST,
    INTENT_COMPARISON,
    INTENT_HOW_TO,
    INTENT_INFORMATIONAL,
    INTENT_REVIEW,
    KNOWN_BRAND_TERMS,
    PAGE_COMPARISON,
    PAGE_CORE,
    PAGE_GUIDE,
    PAGE_POLICY,
    PAGE_REVIEW,
    PAGE_ROUNDUP,
    detect_gsc_page_type,
    detect_query_intent,
)
from linkops.gsc_model import (
    GscCache,
    GscQueryRow,
    Opportunity,
    STATUS_NO_TARGET,
)
from linkops.next_actions_engine import _is_vague_query, _partial_matches_for_query
from linkops.opportunity_engine import (
    _is_brand_noise_query,
    _score_page_for_query,
    _two_way_vs_tools,
    analyze_opportunities,
)
from linkops.patch_relevance_guardrails import (
    is_concept_comparison,
    is_software_comparison,
    is_teamwork_vs_asana_query,
    parse_comparison_parts,
)
from linkops.config import WORKLOG_PATH
from linkops.html_tools import normalize_internal_url
from linkops.suggestion_engine import CORE_PAGE_SLUGS, CORE_PAGE_TITLE_TERMS, POLICY_PAGE_SLUG_TERMS
from linkops.worklog import Worklog, load_worklog

_UPDATE_MATCH_MIN_SCORE = 28.0
_SAME_INTENT_UPDATE_MIN_SCORE = 22.0
_STRONG_COVERAGE_SCORE = 48.0
_HIGH_CREATE_MAX_WITH_MEDIUM_CANNIBAL = 55.0
_LOW_IMPRESSION_CREATE_CAP = 58.0


def _weighted_avg_position_rows(rows: list[GscQueryRow]) -> float:
    total_imp = sum(r.impressions for r in rows)
    if total_imp <= 0:
        return 0.0
    return sum(r.position * r.impressions for r in rows) / total_imp


_AI_TOPIC_RE = re.compile(r"\b(ai|artificial intelligence|generative)\b", re.IGNORECASE)
_FREELANCER_RE = re.compile(r"\bfreelanc", re.IGNORECASE)
_SLUG_SAFE_RE = re.compile(r"[^a-z0-9]+")
_STRIP_FOR_INTENT_RE = re.compile(
    r"\b(best|top|affordable|for small teams?|for small business(?:es)?|small teams?|small business(?:es)?)\b",
    re.IGNORECASE,
)
_TOOLS_SYNONYM_RE = re.compile(r"\b(tools?|software|apps?|platforms?|suites?)\b", re.IGNORECASE)
_AUDIENCE_VARIANT_RE = re.compile(
    r"\b(for\s+)?(small\s+business(?:es)?|small\s+teams?|teams?|remote\s+teams?)\b",
    re.IGNORECASE,
)
_REMOTE_WORK_TOPIC_RE = re.compile(
    r"\bremote\s+(work|team|communication|collaboration)\b", re.IGNORECASE
)
_JOB_MANAGEMENT_RE = re.compile(r"\bjob\s+management\b", re.IGNORECASE)
_LINK_EXCLUDE_SLUG_TERMS = frozenset(
    {"blog", "contact", "about", "privacy", "terms", "legal", "cookie", "cookies"}
)
_PRODUCTIVITY_LINK_SLUG_HINTS = (
    "best-productivity-tools-for-small-teams",
    "best-collaboration-tools-for-small-teams",
    "best-project-management-tools-for-small-teams",
    "start-here",
    "tools",
)
_REVIEW_SLUG_PREFIX_RE = re.compile(r"^([a-z0-9]+)-review\b", re.IGNORECASE)
_COMPOUND_BRAND_PHRASES = (
    "microsoft teams",
    "google workspace",
    "google meet",
    "microsoft 365",
)
_BRAND_SLUG_NEEDLES: dict[str, tuple[str, ...]] = {
    "microsoft teams": ("microsoft-teams", "microsoft teams"),
    "microsoft 365": ("microsoft-365", "microsoft 365"),
    "google workspace": ("google-workspace", "google workspace"),
    "google meet": ("google-meet", "google meet"),
    "webex": ("webex",),
    "slack": ("slack",),
    "zoom": ("zoom",),
    "trello": ("trello",),
    "clickup": ("clickup",),
    "asana": ("asana",),
    "monday": ("monday",),
    "notion": ("notion",),
}
_ROUNDUP_QUERY_RE = re.compile(
    r"\b(best|top)\b.+\b(tools?|software|apps?|platforms?)\b", re.IGNORECASE
)
_LINK_SOURCE_MIN_SCORE = 32.0
_LINK_SOURCE_COMPARISON_MIN_SCORE = 45.0
_TOPIC_ROUNDUP_SLUG_TERMS: dict[str, tuple[str, ...]] = {
    "productivity": ("productivity",),
    "collaboration": ("collaboration",),
    "video_meeting": ("video-meeting", "meeting"),
    "project_management": ("project-management", "project-management"),
    "task_management": ("task-management", "task-management"),
    "communication": ("communication",),
}


def _slugify(text: str) -> str:
    raw = text.lower().strip().replace(".com", "")
    slug = _SLUG_SAFE_RE.sub("-", raw).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug[:80].rstrip("-")


def _normalize_key(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def _strip_audience_variants(text: str) -> str:
    """Remove audience phrasing so small business / small teams variants merge."""
    if _REMOTE_WORK_TOPIC_RE.search(text):
        return re.sub(r"\s+", " ", text.lower().strip())
    stripped = _AUDIENCE_VARIANT_RE.sub("", text.lower())
    return re.sub(r"\s+", " ", stripped).strip()


def is_audience_variant_overlap(query_a: str, query_b: str) -> bool:
    """True when two queries differ mainly by audience wording (not remote-work topic)."""
    if _REMOTE_WORK_TOPIC_RE.search(query_a) or _REMOTE_WORK_TOPIC_RE.search(query_b):
        return False
    a = _strip_audience_variants(query_a)
    b = _strip_audience_variants(query_b)
    if not a or not b:
        return False
    return a == b or a in b or b in a


def is_same_intent_roundup_overlap(query: str, item: ContentItem, topic: str) -> bool:
    """True when an existing roundup page matches the query's core intent."""
    slug = item.slug.lower()
    title = item.title.lower()
    q = query.lower()
    core = _strip_audience_variants(_TOOLS_SYNONYM_RE.sub("tools", q))
    if topic in ("video_meeting",) or (
        "meeting" in core and re.search(r"\b(apps?|tools?|software|video)\b", q)
    ):
        return "video-meeting" in slug or "video meeting" in title
    if topic == "collaboration" or "collaboration" in core:
        return "collaboration" in slug and ("best-" in slug or "best " in title)
    if topic == "productivity" or "productivity" in core:
        return "productivity" in slug and ("best-" in slug or "best " in title)
    if topic == "project_management" or "project management" in core:
        return "project-management" in slug or "project management" in title
    return False


def should_convert_create_to_update(
    query: str,
    catalog: list[ContentItem],
    article_type: str,
    *,
    cannibalization_risk: str,
) -> tuple[ContentItem, float, str] | None:
    """Prefer updating an existing roundup when intent overlaps strongly."""
    if is_branded_product_query(query):
        return find_existing_brand_review_page(query, catalog)
    if article_type != ARTICLE_ROUNDUP:
        return None
    topic = _detect_roadmap_topic(query, article_type)
    item, score = _find_best_existing_page_match(query, catalog, article_type)
    if item and is_same_intent_roundup_overlap(query, item, topic):
        if score >= _SAME_INTENT_UPDATE_MIN_SCORE:
            reason = (
                f"Query aligns with existing roundup '{item.title}' "
                f"(same-intent overlap, score {score:.0f}); update instead of creating."
            )
            return item, score, reason
    upd = detect_existing_page_update_opportunity(query, catalog, article_type)
    if upd and cannibalization_risk in ("medium", "high"):
        return upd
    return upd if upd and upd[1] >= _UPDATE_MATCH_MIN_SCORE else None


def should_convert_create_to_manual_review(
    query: str,
    *,
    article_type: str,
    cannibalization_risk: str,
    vague: bool,
    related_count: int,
    total_impressions: int,
) -> tuple[bool, str]:
    """Return (True, note) when a new article would be risky or ambiguous."""
    if vague or _is_vague_query(query):
        return True, "Vague or broad query — confirm search intent before writing."
    if _JOB_MANAGEMENT_RE.search(query):
        return (
            True,
            "Job management may mean field-service/scheduling software, not task or project "
            "management — manual editorial review required.",
        )
    topic = _detect_roadmap_topic(query, article_type)
    if topic == "job_scheduling_ambiguous":
        return True, "Ambiguous job vs task/project management intent."
    if article_type == ARTICLE_ROUNDUP and cannibalization_risk in ("medium", "high"):
        if not is_teamwork_vs_asana_query(query):
            return (
                True,
                "Overlaps existing roundup pages — confirm whether to update or split angle.",
            )
    if (
        article_type == ARTICLE_ROUNDUP
        and related_count <= 1
        and total_impressions < 20
        and detect_query_intent(query) not in (INTENT_COMPARISON, INTENT_REVIEW)
    ):
        if cannibalization_risk != "low":
            return True, "Low volume with page overlap — not a confident new-article priority."
    return False, ""


def _brand_phrase_in_query(query: str) -> str | None:
    """Return the primary branded product phrase in the query, if any."""
    q = query.lower()
    for phrase in sorted(_COMPOUND_BRAND_PHRASES, key=len, reverse=True):
        if phrase in q:
            return phrase
    tokens = [t for t in re.findall(r"[a-z0-9]+", q) if t in KNOWN_BRAND_TERMS]
    if not tokens:
        return None
    if tokens == ["teams"] and "microsoft" not in q:
        return None
    if len(tokens) == 1:
        return tokens[0]
    if "microsoft" in q and "teams" in tokens:
        return "microsoft teams"
    return tokens[0]


def is_branded_product_query(query: str) -> bool:
    """True for single-product/brand queries (not roundups or comparisons)."""
    if is_teamwork_vs_asana_query(query):
        return False
    q = query.lower()
    if re.search(r"\breviews?\b", q):
        return False
    if _query_has_comparison_language(q):
        return False
    if _ROUNDUP_QUERY_RE.search(q):
        return False
    if re.search(r"\b(best|top)\s+(tools|software|apps)\b", q):
        return False
    return _brand_phrase_in_query(query) is not None


def _query_has_comparison_language(query: str) -> bool:
    q = query.lower()
    return bool(
        re.search(r"\bvs\.?\b|\bversus\b|\balternative\b|\bcompare\b|\bcomparison\b", q)
    )


def _brand_slug_needles(phrase: str) -> tuple[str, ...]:
    key = phrase.lower().strip()
    if key in _BRAND_SLUG_NEEDLES:
        return _BRAND_SLUG_NEEDLES[key]
    return (key.replace(" ", "-"), key.replace(".", ""), key)


def page_matches_query_brand(query: str, item: ContentItem) -> bool:
    """True when page slug/title clearly belongs to the query's brand."""
    phrase = _brand_phrase_in_query(query)
    if not phrase:
        return True
    slug = item.slug.lower()
    title = item.title.lower()
    return any(needle in slug or needle in title for needle in _brand_slug_needles(phrase))


def is_brand_mismatch_page(query: str, item: ContentItem) -> bool:
    """True when a branded query would be routed to a different brand's page."""
    if not is_branded_product_query(query):
        return False
    return not page_matches_query_brand(query, item)


def find_existing_brand_review_page(
    query: str,
    catalog: list[ContentItem],
) -> tuple[ContentItem, float, str] | None:
    """Locate the existing review page for the query brand (exact brand match only)."""
    if not is_branded_product_query(query):
        return None
    best_item: ContentItem | None = None
    best_score = 0.0
    for item in catalog:
        slug = item.slug.lower()
        if "review" not in slug or detect_gsc_page_type(item) != PAGE_REVIEW:
            continue
        if not page_matches_query_brand(query, item):
            continue
        score = _score_page_for_query(query, item)
        if score > best_score:
            best_score = score
            best_item = item
    if best_item and best_score >= _SAME_INTENT_UPDATE_MIN_SCORE:
        return (
            best_item,
            best_score,
            f"Existing brand review page '{best_item.title}' matches this query "
            f"(score {best_score:.0f}); update instead of creating a guide or new article.",
        )
    return None


def _gap_reason_for_branded_review_update(item: ContentItem, query: str) -> str:
    """Gap reason aligned with the brand-guard selected review page."""
    phrase = _brand_phrase_in_query(query) or query.strip()
    return (
        f"Branded query for '{phrase}' aligns with existing review page "
        f"'{item.title}'; update this page instead of creating new content."
    )


def _gap_reason_for_branded_manual(query: str) -> str:
    phrase = _brand_phrase_in_query(query) or query.strip()
    return (
        f"No matching brand review page in cache for '{phrase}'; "
        "manual editorial review required."
    )


def _normalize_gap_reason_for_branded_update(
    query: str,
    item: ContentItem,
    gap_reason: str,
) -> str:
    """Replace stale GSC overlap text when brand guard selected a different final page."""
    if not is_branded_product_query(query):
        return gap_reason
    if not page_matches_query_brand(query, item):
        return gap_reason
    phrase = _brand_phrase_in_query(query)
    if phrase:
        other_needles = [
            n
            for key, needles in _BRAND_SLUG_NEEDLES.items()
            if key != phrase
            for n in needles
            if n and len(n) > 3
        ]
        lower_gap = gap_reason.lower()
        for needle in other_needles:
            if needle in lower_gap and needle not in _brand_slug_needles(phrase):
                return _gap_reason_for_branded_review_update(item, query)
    if "content match" in gap_reason.lower() and item.title.lower() not in gap_reason.lower():
        return _gap_reason_for_branded_review_update(item, query)
    return gap_reason


def resolve_branded_query_candidate(
    rows: list[GscQueryRow],
    *,
    catalog: list[ContentItem],
    gap_reason: str,
    query_group_label: str,
    merged_queries: list[str],
) -> ArticleCandidate | None:
    """Build update or manual candidate for a branded product query."""
    primary_row = max(rows, key=lambda r: r.impressions)
    primary = primary_row.query
    if not is_branded_product_query(primary):
        return None
    brand_upd = find_existing_brand_review_page(primary, catalog)
    if brand_upd:
        branded_gap = _gap_reason_for_branded_review_update(brand_upd[0], primary)
        return build_existing_page_update_candidate(
            rows,
            catalog=catalog,
            item=brand_upd[0],
            match_score=brand_upd[1],
            update_reason=brand_upd[2],
            gap_reason=branded_gap,
            query_group_label=query_group_label,
            merged_queries=merged_queries,
        )
    return _build_create_candidate_from_rows(
        rows,
        catalog=catalog,
        gap_reason=_gap_reason_for_branded_manual(primary),
        query_group_label=query_group_label,
        merged_queries=merged_queries,
    )


def collect_displayed_candidates(
    buckets: dict[str, list[ArticleCandidate]],
    *,
    include_low: bool,
    include_manual: bool,
) -> list[ArticleCandidate]:
    """Candidates that appear in visible roadmap report sections."""
    displayed = (
        list(buckets.get("create_high", []))
        + list(buckets.get("create_medium", []))
        + list(buckets.get("update_high", []))
        + list(buckets.get("update_medium", []))
    )
    if include_low:
        displayed += list(buckets.get("create_low", [])) + list(
            buckets.get("update_low", [])
        )
    if include_manual:
        displayed += list(buckets.get("manual", []))
    return displayed


def build_top_summary_lines(
    displayed: list[ArticleCandidate],
    *,
    limit: int = 5,
) -> list[str]:
    """Format executive-summary top items from displayed candidates only."""
    ranked = sorted(
        displayed,
        key=lambda c: (-c.priority_score, -c.total_impressions),
    )[:limit]
    lines: list[str] = []
    for i, c in enumerate(ranked, 1):
        lines.append(
            f"{i}. {c.suggested_title} [{c.action_type}, {c.priority}, "
            f"score {c.priority_score:.0f}]"
        )
    return lines


def filter_existing_related_pages(
    urls: list[str],
    catalog: list[ContentItem],
    *,
    query: str,
    topic: str,
    action_type: str = "",
    target_url: str = "",
    limit: int = 4,
) -> list[str]:
    """Apply the same quality rules as link-from suggestions to related-page lists."""
    return filter_high_quality_link_sources(
        urls,
        catalog,
        query=query,
        topic=topic,
        target_url=target_url,
        action_type=action_type,
        limit=limit,
    )


def safe_manual_review_title(query: str) -> tuple[str, str]:
    """Stable title/slug for manual-review queries (avoids awkward auto titles)."""
    q = query.strip()
    if not q:
        return "Manual Review: (unspecified query)", "manual-review-unspecified"
    return f"Manual Review: {q}", f"manual-review-{_slugify(q)[:60]}"


def _review_slug_brand(slug: str) -> str | None:
    m = _REVIEW_SLUG_PREFIX_RE.match(slug.lower().strip("/"))
    return m.group(1) if m else None


def _query_mentions_page_brand(query: str, item: ContentItem) -> bool:
    """True when the query explicitly names the product reviewed on the page."""
    q = query.lower()
    brand = _review_slug_brand(item.slug)
    if brand and brand in q:
        return True
    slug = item.slug.lower()
    for tok in KNOWN_BRAND_TERMS:
        if tok in slug and tok in q:
            return True
    return False


def _is_product_review_link_source(item: ContentItem, query: str) -> bool:
    if detect_gsc_page_type(item) != PAGE_REVIEW:
        return False
    if "review" not in item.slug.lower() and "review" not in item.title.lower():
        return False
    return not _query_mentions_page_brand(query, item)


def _topic_aligned_roundup_slug(topic: str, slug: str, query: str, item: ContentItem) -> bool:
    hints = _TOPIC_ROUNDUP_SLUG_TERMS.get(topic, ())
    if hints and any(h in slug for h in hints):
        return True
    return is_same_intent_roundup_overlap(query, item, topic)


def _is_weak_link_source(
    item: ContentItem,
    *,
    query: str,
    topic: str,
    action_type: str = "",
    target_slug: str = "",
) -> bool:
    slug = item.slug.lower().strip("/")
    title = item.title.lower()
    page_type = detect_gsc_page_type(item)

    if page_type in (PAGE_CORE, PAGE_POLICY):
        return True
    if slug in CORE_PAGE_SLUGS or title in CORE_PAGE_TITLE_TERMS:
        return True
    if any(term in slug for term in _LINK_EXCLUDE_SLUG_TERMS):
        return True
    if any(term in slug for term in POLICY_PAGE_SLUG_TERMS):
        return True
    if target_slug and slug == target_slug.strip("/"):
        return True
    if _is_product_review_link_source(item, query):
        return True

    if action_type == ACTION_UPDATE_EXISTING_PAGE:
        if page_type == PAGE_REVIEW:
            return True
        if page_type == PAGE_COMPARISON:
            return _score_page_for_query(query, item) < _LINK_SOURCE_COMPARISON_MIN_SCORE
        if page_type == PAGE_ROUNDUP:
            if not _topic_aligned_roundup_slug(topic, slug, query, item):
                return True
        elif page_type == PAGE_GUIDE:
            if _score_page_for_query(query, item) < _LINK_SOURCE_MIN_SCORE:
                return True
        elif page_type not in (PAGE_ROUNDUP, PAGE_GUIDE, PAGE_COMPARISON):
            return True
    return False


def _link_source_score(
    item: ContentItem,
    *,
    query: str,
    topic: str,
) -> float:
    score = _score_page_for_query(query, item)
    slug = item.slug.lower()
    page_type = detect_gsc_page_type(item)
    if page_type == PAGE_ROUNDUP and _topic_aligned_roundup_slug(topic, slug, query, item):
        score += 20.0
    if topic == "productivity" and any(h in slug for h in _PRODUCTIVITY_LINK_SLUG_HINTS):
        score += 15.0
    if is_same_intent_roundup_overlap(query, item, topic):
        score += 20.0
    return score


def filter_high_quality_link_sources(
    urls: list[str],
    catalog: list[ContentItem],
    *,
    query: str,
    topic: str,
    target_url: str = "",
    action_type: str = "",
    limit: int = 3,
) -> list[str]:
    """Prefer topical pages; drop core/policy pages and unrelated product reviews."""
    by_url = {i.url.rstrip("/"): i for i in catalog}
    target_norm = target_url.rstrip("/") if target_url else ""
    target_item = by_url.get(target_norm)
    target_slug = target_item.slug if target_item else ""
    scored: list[tuple[float, str]] = []
    for url in urls:
        norm = url.rstrip("/")
        if norm == target_norm:
            continue
        item = by_url.get(norm)
        if not item:
            continue
        if _is_weak_link_source(
            item,
            query=query,
            topic=topic,
            action_type=action_type,
            target_slug=target_slug,
        ):
            continue
        score = _link_source_score(item, query=query, topic=topic)
        if score < _LINK_SOURCE_MIN_SCORE:
            continue
        scored.append((score, item.url))
    scored.sort(key=lambda x: (-x[0], x[1]))
    out = [u for _, u in scored[:limit]]
    if target_norm:
        out = [u for u in out if u.rstrip("/") != target_norm]
    return out


def calculate_displayed_roadmap_counts(
    buckets: dict[str, list[ArticleCandidate]],
    *,
    include_low: bool,
) -> dict[str, int]:
    """Counts that match what appears in bucketed report sections."""
    create_n = (
        len(buckets["create_high"])
        + len(buckets["create_medium"])
        + len(buckets.get("create_low", []))
    )
    update_n = (
        len(buckets["update_high"])
        + len(buckets["update_medium"])
        + len(buckets.get("update_low", []))
    )
    manual_n = len(buckets.get("manual", []))
    low_n = len(buckets.get("create_low", [])) + len(buckets.get("update_low", []))
    if not include_low:
        low_n = 0
        create_n = len(buckets["create_high"]) + len(buckets["create_medium"])
        update_n = len(buckets["update_high"]) + len(buckets["update_medium"])
    total = create_n + update_n + manual_n
    return {
        "total": total,
        "create": create_n,
        "update": update_n,
        "manual": manual_n,
        "create_high": len(buckets["create_high"]),
        "create_medium": len(buckets["create_medium"]),
        "update_high": len(buckets["update_high"]),
        "update_medium": len(buckets["update_medium"]),
        "low": low_n,
    }


def refine_roadmap_candidate(
    candidate: ArticleCandidate,
    catalog: list[ContentItem],
) -> ArticleCandidate:
    """Apply v1.7.2 cannibalization, manual-review, and link-source rules."""
    query = candidate.primary_keyword
    intent = detect_query_intent(query)
    article_type = _infer_article_type(query, intent)
    topic = _detect_roadmap_topic(query, article_type)
    vague = _is_vague_query(query) or candidate.priority == PRIORITY_MANUAL

    if candidate.action_type == ACTION_UPDATE_EXISTING_PAGE and is_branded_product_query(query):
        item = next(
            (i for i in catalog if i.url.rstrip("/") == candidate.recommended_existing_url.rstrip("/")),
            None,
        )
        if item and is_brand_mismatch_page(query, item):
            rows = [
                GscQueryRow(
                    q,
                    0,
                    max(candidate.total_impressions // max(len(candidate.merged_queries or [query]), 1), 1),
                    0.0,
                    candidate.weighted_avg_position,
                )
                for q in (candidate.merged_queries or [query])
            ]
            fixed = resolve_branded_query_candidate(
                rows,
                catalog=catalog,
                gap_reason=candidate.target_gap_reason,
                query_group_label=candidate.query_group_label,
                merged_queries=candidate.merged_queries or [query],
            )
            if fixed:
                return fixed

    if candidate.action_type == ACTION_MANUAL_REVIEW or vague:
        title, slug = safe_manual_review_title(query)
        candidate.suggested_title = title
        candidate.suggested_slug = slug
        candidate.action_type = ACTION_MANUAL_REVIEW
        candidate.priority = PRIORITY_MANUAL
        candidate.recommended_next_step = "Manual editorial review before drafting."
        if "Manual editorial review" not in " ".join(candidate.editorial_notes):
            candidate.editorial_notes.append(
                "Manual editorial review before drafting."
            )
        return candidate

    if candidate.action_type == ACTION_CREATE_NEW_ARTICLE:
        convert_note = ""
        if is_branded_product_query(query):
            brand_upd = find_existing_brand_review_page(query, catalog)
            if brand_upd:
                rows = [
                    GscQueryRow(
                        q,
                        0,
                        max(
                            candidate.total_impressions
                            // max(len(candidate.merged_queries or [query]), 1),
                            1,
                        ),
                        0.0,
                        candidate.weighted_avg_position,
                    )
                    for q in (candidate.merged_queries or [query])
                ]
                return build_existing_page_update_candidate(
                    rows,
                    catalog=catalog,
                    item=brand_upd[0],
                    match_score=brand_upd[1],
                    update_reason=brand_upd[2],
                    gap_reason=candidate.target_gap_reason,
                    query_group_label=candidate.query_group_label,
                    merged_queries=candidate.merged_queries or [query],
                )
            title, slug = safe_manual_review_title(query)
            candidate.suggested_title = title
            candidate.suggested_slug = slug
            candidate.action_type = ACTION_MANUAL_REVIEW
            candidate.priority = PRIORITY_MANUAL
            candidate.recommended_next_step = "Manual editorial review before drafting."
            candidate.editorial_notes.append(
                "Branded product query — confirm whether to update an existing review page."
            )
            return candidate
        if _JOB_MANAGEMENT_RE.search(query):
            title, slug = safe_manual_review_title(query)
            candidate.suggested_title = title
            candidate.suggested_slug = slug
            candidate.action_type = ACTION_MANUAL_REVIEW
            candidate.priority = PRIORITY_MANUAL
            candidate.priority_score = min(candidate.priority_score, 40.0)
            candidate.recommended_next_step = "Manual editorial review before drafting."
            candidate.editorial_notes.append(
                "Job management may mean field-service/scheduling software, not task or "
                "project management — manual editorial review required."
            )
            return candidate
        manual, convert_note = should_convert_create_to_manual_review(
            query,
            article_type=article_type,
            cannibalization_risk=candidate.cannibalization_risk,
            vague=False,
            related_count=candidate.related_query_count,
            total_impressions=candidate.total_impressions,
        )
        upd = should_convert_create_to_update(
            query,
            catalog,
            article_type,
            cannibalization_risk=candidate.cannibalization_risk,
        )
        if upd and not manual:
            rows = [
                GscQueryRow(
                    q,
                    0,
                    max(candidate.total_impressions // max(len(candidate.merged_queries or [query]), 1), 1),
                    0.0,
                    candidate.weighted_avg_position,
                )
                for q in (candidate.merged_queries or [query])
            ]
            return build_existing_page_update_candidate(
                rows,
                catalog=catalog,
                item=upd[0],
                match_score=upd[1],
                update_reason=upd[2],
                gap_reason=candidate.target_gap_reason,
                query_group_label=candidate.query_group_label,
                merged_queries=candidate.merged_queries or [query],
            )
        if manual:
            title, slug = safe_manual_review_title(query)
            candidate.suggested_title = title
            candidate.suggested_slug = slug
            candidate.action_type = ACTION_MANUAL_REVIEW
            candidate.priority = PRIORITY_MANUAL
            candidate.recommended_next_step = "Manual editorial review before drafting."
            if convert_note and convert_note not in candidate.editorial_notes:
                candidate.editorial_notes.append(convert_note)
            if candidate.cannibalization_risk in ("medium", "high") and candidate.priority_score > 45:
                candidate.priority_score = min(candidate.priority_score, 40.0)
            return candidate
        if (
            candidate.cannibalization_risk in ("medium", "high")
            and candidate.priority == PRIORITY_HIGH
        ):
            candidate.priority = PRIORITY_MEDIUM
            candidate.priority_score = min(
                candidate.priority_score, _HIGH_CREATE_MAX_WITH_MEDIUM_CANNIBAL
            )
            candidate.editorial_notes.append(
                "Cannibalization overlap — deprioritized new-article recommendation."
            )

    candidate.suggested_internal_links_from = filter_high_quality_link_sources(
        candidate.suggested_internal_links_from or candidate.existing_related_pages,
        catalog,
        query=query,
        topic=topic,
        target_url=candidate.recommended_existing_url or "",
        action_type=candidate.action_type,
    )
    candidate.suggested_internal_links_to = filter_high_quality_link_sources(
        candidate.suggested_internal_links_to,
        catalog,
        query=query,
        topic=topic,
        target_url=candidate.recommended_existing_url or "",
        action_type=candidate.action_type,
        limit=3,
    )
    candidate.existing_related_pages = filter_existing_related_pages(
        candidate.existing_related_pages,
        catalog,
        query=query,
        topic=topic,
        action_type=candidate.action_type,
        target_url=candidate.recommended_existing_url or "",
    )
    return candidate


def normalize_candidate_intent_key(query: str, article_type: str, topic: str) -> str:
    """Canonical key for merging near-duplicate roadmap intents."""
    if is_teamwork_vs_asana_query(query):
        return "comparison:teamwork-vs-asana"
    if article_type == ARTICLE_COMPARISON:
        parts = parse_comparison_parts(query) or _two_way_vs_tools(query)
        if parts:
            left = _normalize_key(parts[0]).replace(".com", "")
            right = _normalize_key(parts[1]).replace(".com", "")
            return f"comparison:{left}-vs-{right}"
    if article_type == ARTICLE_REVIEW:
        phrase = _brand_phrase_in_query(query)
        if phrase:
            return f"review:{phrase.replace(' ', '-')}"
        for tok in re.findall(r"[a-z0-9]+", query.lower()):
            if tok in KNOWN_BRAND_TERMS:
                return f"review:{tok}"
        return f"review:{_normalize_key(query)}"
    core = _STRIP_FOR_INTENT_RE.sub("", query.lower())
    core = _TOOLS_SYNONYM_RE.sub("tools", core)
    core = re.sub(r"\bteams\b", "team", core)
    core = re.sub(r"\s+", " ", core).strip()
    if topic == "productivity" or "productivity" in core:
        if article_type in (ARTICLE_ROUNDUP, ARTICLE_GUIDE):
            return "roundup:productivity"
    if "collaboration" in core and article_type == ARTICLE_ROUNDUP:
        return "roundup:collaboration"
    if "communication" in core and article_type == ARTICLE_ROUNDUP:
        if _REMOTE_WORK_TOPIC_RE.search(query):
            return "roundup:remote-communication"
        return "roundup:communication"
    if _JOB_MANAGEMENT_RE.search(core) and article_type == ARTICLE_ROUNDUP:
        return "roundup:job-management-ambiguous"
    if "project management" in core and article_type == ARTICLE_ROUNDUP:
        return "roundup:project-management"
    if "task management" in core and "project" not in core and article_type == ARTICLE_ROUNDUP:
        return "roundup:task-management"
    if ("meeting" in core or "video" in core) and article_type == ARTICLE_ROUNDUP:
        return "roundup:video-meeting"
    return f"{article_type}:{topic}:{core[:50]}"


def _page_type_matches_article(page_type: str, article_type: str) -> bool:
    if article_type == ARTICLE_ROUNDUP:
        return page_type == PAGE_ROUNDUP
    if article_type == ARTICLE_COMPARISON:
        return page_type == PAGE_COMPARISON
    if article_type == ARTICLE_REVIEW:
        return page_type == PAGE_REVIEW
    if article_type == ARTICLE_GUIDE:
        return page_type in (PAGE_GUIDE, PAGE_ROUNDUP)
    return True


def _find_best_existing_page_match(
    query: str,
    catalog: list[ContentItem],
    article_type: str,
) -> tuple[ContentItem | None, float]:
    if is_branded_product_query(query):
        brand = find_existing_brand_review_page(query, catalog)
        if brand:
            return brand[0], brand[1]
        return None, 0.0
    best_item: ContentItem | None = None
    best_score = 0.0
    for item in catalog:
        if is_brand_mismatch_page(query, item):
            continue
        score = _score_page_for_query(query, item)
        page_type = detect_gsc_page_type(item)
        if not _page_type_matches_article(page_type, article_type):
            score *= 0.5
        if score > best_score:
            best_score = score
            best_item = item
    return best_item, best_score


def _best_update_for_queries(
    queries: list[str],
    catalog: list[ContentItem],
    article_type: str,
) -> tuple[ContentItem, float, str] | None:
    """Pick the strongest existing-page update match across a query group."""
    best: tuple[ContentItem, float, str] | None = None
    for q in queries:
        upd = detect_existing_page_update_opportunity(q, catalog, article_type)
        if not upd:
            continue
        if best is None or upd[1] > best[1]:
            best = upd
    return best


def detect_existing_page_update_opportunity(
    query: str,
    catalog: list[ContentItem],
    article_type: str,
) -> tuple[ContentItem, float, str] | None:
    """Return existing page to update when overlap is strong and types align."""
    if is_teamwork_vs_asana_query(query):
        return None
    if is_branded_product_query(query):
        return find_existing_brand_review_page(query, catalog)
    topic = _detect_roadmap_topic(query, article_type)
    item, score = _find_best_existing_page_match(query, catalog, article_type)
    if item and is_same_intent_roundup_overlap(query, item, topic):
        min_score = _SAME_INTENT_UPDATE_MIN_SCORE
        if score >= min_score:
            reason = (
                f"Existing page '{item.title}' matches the same roundup intent "
                f"(score {score:.0f}); update instead of creating a new article."
            )
            return item, score, reason
    if not item or score < _UPDATE_MATCH_MIN_SCORE:
        return None
    if _wrong_branded_comparison_page(query, item):
        return None
    page_type = detect_gsc_page_type(item)
    if not _page_type_matches_article(page_type, article_type):
        return None
    intent = detect_query_intent(query)
    if compute_intent_alignment(intent, page_type) == ALIGNMENT_MISALIGNED:
        return None
    reason = (
        f"Existing page '{item.title}' is a strong topical match (score {score:.0f}) "
        f"for this query; refresh the page instead of creating a new article."
    )
    return item, score, reason


def should_create_new_article(
    *,
    query: str,
    catalog: list[ContentItem],
    article_type: str,
    cannibalization_risk: str,
    force_manual: bool,
) -> bool:
    """True when a new article is appropriate instead of updating an existing page."""
    if force_manual or _is_vague_query(query):
        return False
    if is_teamwork_vs_asana_query(query):
        for item in catalog:
            if "teamwork" in item.slug.lower() and "asana" in item.slug.lower():
                return False
        return True
    update = detect_existing_page_update_opportunity(query, catalog, article_type)
    if update and update[1] >= _UPDATE_MATCH_MIN_SCORE:
        return False
    if cannibalization_risk == "high":
        return False
    if cannibalization_risk == "medium" and update:
        return False
    return True


def calculate_cannibalization_adjusted_priority(
    score: float,
    *,
    action_type: str,
    cannibalization_risk: str,
    has_strong_existing: bool,
) -> float:
    if action_type == ACTION_UPDATE_EXISTING_PAGE:
        return score + 12.0
    if action_type == ACTION_MANUAL_REVIEW:
        return score
    if cannibalization_risk == "high":
        return min(score, 35.0)
    if cannibalization_risk == "medium" and has_strong_existing:
        return min(score, _HIGH_CREATE_MAX_WITH_MEDIUM_CANNIBAL)
    if cannibalization_risk == "medium":
        return min(score, 62.0)
    return score


def _detect_roadmap_topic(keyword: str, article_type: str) -> str:
    kw = keyword.lower()
    if _AI_TOPIC_RE.search(kw):
        return "AI/productivity"
    if _FREELANCER_RE.search(kw):
        return "freelancer/client_work"
    if _JOB_MANAGEMENT_RE.search(kw):
        return "job_scheduling_ambiguous"
    if "video meeting" in kw or "video-meeting" in kw:
        return "video_meeting"
    if re.search(r"\b(meeting|video)\b.*\b(apps?|tools?|software)\b", kw) or re.search(
        r"\b(apps?|tools?)\b.*\bmeeting\b", kw
    ):
        return "video_meeting"
    if "communication" in kw and "collaboration" not in kw:
        return "communication"
    if "collaboration" in kw:
        return "collaboration"
    if "productivity" in kw and "project management" not in kw:
        return "productivity"
    if "workflow" in kw:
        return "workflow_management"
    if "task management" in kw and "project management" not in kw:
        return "task_management"
    if "project management" in kw:
        return "project_management"
    if article_type == ARTICLE_COMPARISON:
        return "software_comparison"
    if article_type == ARTICLE_CONCEPT_COMPARISON:
        return "task_management"
    return "unknown/manual_review"


def _title_for_comparison(query: str) -> tuple[str, str]:
    if is_teamwork_vs_asana_query(query):
        return "Teamwork vs Asana for Small Teams", "teamwork-vs-asana-for-small-teams"
    parts = parse_comparison_parts(query)
    if parts:
        left = capitalize_brand(parts[0].strip())
        right = capitalize_brand(parts[1].strip())
        title = f"{left} vs {right} for Small Teams"
        return title, _slugify(title)
    tools = _two_way_vs_tools(query)
    if tools:
        left = capitalize_brand(tools[0])
        right = capitalize_brand(tools[1])
        title = f"{left} vs {right} for Small Teams"
        return title, _slugify(title)
    phrase = smart_title_case(query)
    return f"{phrase}: Comparison for Small Teams", _slugify(phrase + " comparison small teams")


def _title_for_review(query: str) -> tuple[str, str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9.]*", query)
    brand = ""
    for tok in tokens:
        if tok.lower() in KNOWN_BRAND_TERMS or tok.lower() in {"webex", "clickup", "trello"}:
            brand = capitalize_brand(tok)
            break
    if not brand and tokens:
        brand = capitalize_brand(tokens[0])
    if _FREELANCER_RE.search(query):
        title = f"{brand} Review for Freelancers"
        return title, _slugify(title)
    title = f"{brand} Review for Small Businesses"
    return title, _slugify(title)


def _title_for_roundup(query: str) -> tuple[str, str]:
    q = query.strip()
    lower = q.lower()
    if lower.startswith("best "):
        title = smart_title_case(q)
    else:
        core = re.sub(r"^(best|top)\s+", "", lower, flags=re.IGNORECASE).strip()
        title = smart_title_case(f"Best {core}")
    if not re.search(r"small\s+(teams?|business)", title, re.IGNORECASE):
        title = f"{title} for Small Teams"
    return title, _slugify(title)


def _title_for_guide(query: str) -> tuple[str, str]:
    if is_branded_product_query(query):
        return safe_manual_review_title(query)
    q = query.strip()
    if q.lower().startswith("how to"):
        title = smart_title_case(q)
        if not title.endswith("?"):
            title = f"{title}: A Practical Guide for Small Teams"
    elif "how to choose" in q.lower():
        title = smart_title_case(q)
    else:
        title = smart_title_case(f"How to {q} for Small Teams")
    return title, _slugify(title)


def _title_for_concept(query: str) -> tuple[str, str]:
    parts = parse_comparison_parts(query)
    if parts and "project" in parts[0].lower() and "task" in parts[1].lower():
        return (
            "Project vs Task Management for Small Teams",
            "project-vs-task-management-for-small-teams",
        )
    phrase = smart_title_case(query)
    return f"{phrase} for Small Teams", _slugify(phrase + " small teams")


def _infer_article_type(query: str, query_intent: str) -> str:
    if is_concept_comparison(query):
        return ARTICLE_CONCEPT_COMPARISON
    if is_branded_product_query(query):
        return ARTICLE_REVIEW
    if query_intent == INTENT_COMPARISON or is_software_comparison(query, query_intent):
        return ARTICLE_COMPARISON
    if query_intent == INTENT_REVIEW:
        return ARTICLE_REVIEW
    if query_intent == INTENT_HOW_TO:
        return ARTICLE_GUIDE
    if query_intent == INTENT_BROAD_BEST:
        return ARTICLE_ROUNDUP
    if query_intent == INTENT_INFORMATIONAL:
        if re.search(r"\bwhat is\b|\bdefinition\b|\bmeaning\b", query, re.IGNORECASE):
            return ARTICLE_GLOSSARY
        return ARTICLE_GUIDE
    return ARTICLE_GUIDE


def _catalog_has_comparison_page(left: str, right: str, catalog: list[ContentItem]) -> bool:
    left_s = left.lower().replace(".com", "").strip()
    right_s = right.lower().replace(".com", "").strip()
    for item in catalog:
        slug = item.slug.lower()
        if left_s in slug and right_s in slug and ("-vs-" in slug or "-versus-" in slug):
            return True
    return False


def _catalog_has_brand_review(brand: str, catalog: list[ContentItem]) -> bool:
    b = brand.lower().replace(".com", "")
    for item in catalog:
        slug = item.slug.lower()
        if b in slug and "review" in slug:
            return True
    return False


def _wrong_branded_comparison_page(query: str, item: ContentItem) -> bool:
    """True when an existing comparison page is the wrong brand pairing for the query."""
    if not is_teamwork_vs_asana_query(query):
        return False
    slug = item.slug.lower()
    return "teamwork" not in slug


def _strong_existing_coverage(
    query: str,
    catalog: list[ContentItem],
    article_type: str,
) -> tuple[bool, str, ContentItem | None, float]:
    item, score = _find_best_existing_page_match(query, catalog, article_type)
    if not item or score < _STRONG_COVERAGE_SCORE:
        return False, "", item, score
    if _wrong_branded_comparison_page(query, item):
        return False, "", item, score
    intent = detect_query_intent(query)
    if compute_intent_alignment(intent, detect_gsc_page_type(item)) == ALIGNMENT_MISALIGNED:
        return False, "", item, score
    return (
        True,
        f"Existing page '{item.title}' strongly covers this query (score {score:.0f}).",
        item,
        score,
    )


def _is_already_covered(
    query: str,
    catalog: list[ContentItem],
    opp: Opportunity | None,
) -> tuple[bool, str]:
    intent = detect_query_intent(query)
    article_type = _infer_article_type(query, intent)
    if intent == INTENT_COMPARISON or is_software_comparison(query, intent):
        if is_teamwork_vs_asana_query(query):
            for item in catalog:
                if "teamwork" in item.slug.lower() and "asana" in item.slug.lower():
                    return True, "Teamwork vs Asana comparison page already exists."
            return False, ""
        parts = parse_comparison_parts(query) or _two_way_vs_tools(query)
        if parts:
            left, right = parts[0], parts[1]
            if _catalog_has_comparison_page(left, right, catalog):
                return True, f"Comparison page already covers {left} vs {right}."
        if opp and opp.target_url and opp.confidence == CONFIDENCE_HIGH:
            target_norm = normalize_internal_url(opp.target_url)
            item = next((i for i in catalog if i.normalized_url() == target_norm), None)
            if item and detect_gsc_page_type(item) == PAGE_COMPARISON:
                return True, "High-confidence comparison target already in catalog."
    if intent == INTENT_REVIEW:
        brands = set(re.findall(r"[a-z0-9]+", query.lower())) & KNOWN_BRAND_TERMS
        for brand in brands:
            if _catalog_has_brand_review(brand, catalog):
                return True, f"Review page already exists for {capitalize_brand(brand)}."
    covered, reason, _, _ = _strong_existing_coverage(query, catalog, article_type)
    if covered:
        return True, reason
    return False, ""


def _gap_reason_for_opportunity(opp: Opportunity, catalog: list[ContentItem]) -> str:
    if opp.status == STATUS_NO_TARGET:
        return "No strong matching published page in WordPress cache."
    if opp.confidence == CONFIDENCE_LOW:
        return f"Low-confidence target match ({opp.target_selection_reason or 'weak topical fit'})."
    if opp.target_url:
        item = next((i for i in catalog if i.url.rstrip("/") == opp.target_url.rstrip("/")), None)
        if item:
            alignment = compute_intent_alignment(opp.query_intent, detect_gsc_page_type(item))
            if alignment == ALIGNMENT_MISALIGNED:
                return (
                    f"Query intent ({opp.query_intent}) mismatches page type "
                    f"({detect_gsc_page_type(item)}); do not optimize the wrong page."
                )
    if is_teamwork_vs_asana_query(opp.query):
        return (
            "Branded Teamwork.com vs Asana comparison not covered; "
            "do not route to Asana vs ClickUp or similar."
        )
    return opp.reason or "Editorial gap detected from GSC performance."


def _commercial_relevance(query: str, query_intent: str) -> float:
    boost = 0.0
    if query_intent in (INTENT_COMPARISON, INTENT_REVIEW, INTENT_BROAD_BEST):
        boost += 25.0
    if query_intent == INTENT_HOW_TO:
        boost += 12.0
    if is_teamwork_vs_asana_query(query):
        boost += 20.0
    tokens = set(re.findall(r"[a-z0-9]+", query.lower()))
    if tokens & KNOWN_BRAND_TERMS:
        boost += 10.0
    if "best" in tokens or "review" in tokens or "vs" in query.lower():
        boost += 8.0
    return boost


def _priority_score(
    rows: list[GscQueryRow],
    *,
    article_type: str,
    query_intent: str,
    gap_severity: float,
    related_count: int,
    vague: bool,
    cannibalization_risk: str,
    action_type: str,
) -> float:
    if vague:
        return 5.0
    total_imp = sum(r.impressions for r in rows)
    wpos = _weighted_avg_position_rows(rows)
    score = 0.0
    score += min(total_imp, 500) * 0.12
    score += _commercial_relevance(rows[0].query, query_intent)
    score += gap_severity
    score += min(related_count, 5) * 4.0
    if sum(r.clicks for r in rows) == 0 and total_imp >= 15:
        score += 10.0
    if 20 <= wpos <= 90:
        score += 8.0
    elif wpos < 20:
        score += 4.0
    if (
        action_type == ACTION_CREATE_NEW_ARTICLE
        and related_count <= 1
        and total_imp < 20
        and query_intent not in (INTENT_COMPARISON, INTENT_REVIEW)
        and not (KNOWN_BRAND_TERMS & set(re.findall(r"[a-z0-9]+", rows[0].query.lower())))
    ):
        score = min(score, _LOW_IMPRESSION_CREATE_CAP)
    else:
        score -= 6.0
    if article_type == ARTICLE_COMPARISON:
        score += 12.0
    if article_type == ARTICLE_REVIEW:
        score += 10.0
    if article_type == ARTICLE_ROUNDUP:
        score += 8.0
    if action_type == ACTION_UPDATE_EXISTING_PAGE:
        score += 15.0
    elif cannibalization_risk == "medium":
        score -= 20.0
    elif cannibalization_risk == "high":
        score -= 30.0
    if total_imp < 10:
        score -= 15.0
    return max(score, 0.0)


def _priority_label(score: float, *, force_manual: bool, action_type: str) -> str:
    if force_manual:
        return PRIORITY_MANUAL
    if action_type == ACTION_MANUAL_REVIEW:
        return PRIORITY_MANUAL
    if score >= 70:
        return PRIORITY_HIGH
    if score >= 40:
        return PRIORITY_MEDIUM
    return PRIORITY_LOW


def _cannibalization_risk(
    query: str,
    catalog: list[ContentItem],
    partials: list,
    match_score: float,
) -> str:
    if match_score >= 40:
        return "high"
    if len(partials) >= 3:
        return "medium"
    top = partials[0].match_score if partials else 0
    if top >= 30 or match_score >= 28:
        return "medium"
    if top >= 20:
        return "low"
    return "low"


def build_existing_page_update_candidate(
    rows: list[GscQueryRow],
    *,
    catalog: list[ContentItem],
    item: ContentItem,
    match_score: float,
    update_reason: str,
    gap_reason: str,
    query_group_label: str,
    merged_queries: list[str],
) -> ArticleCandidate:
    primary_row = max(rows, key=lambda r: r.impressions)
    primary = primary_row.query
    intent = detect_query_intent(primary)
    article_type = _infer_article_type(primary, intent)
    topic = _detect_roadmap_topic(primary, article_type)
    all_queries = merged_queries or [r.query for r in rows]
    secondary = [q for q in all_queries if q != primary]

    url = item.url
    partials = _partial_matches_for_query(primary, catalog, limit=6)
    related_urls = [p.url for p in partials[:6]]
    filtered_related = filter_existing_related_pages(
        related_urls,
        catalog,
        query=primary,
        topic=topic,
        action_type=ACTION_UPDATE_EXISTING_PAGE,
        target_url=url,
    )
    vague = _is_vague_query(primary)
    cannibal = _cannibalization_risk(primary, catalog, partials, match_score)

    gap_severity = 12.0
    score = _priority_score(
        rows,
        article_type=article_type,
        query_intent=intent,
        gap_severity=gap_severity,
        related_count=len(all_queries),
        vague=vague,
        cannibalization_risk=cannibal,
        action_type=ACTION_UPDATE_EXISTING_PAGE,
    )
    has_strong = match_score >= _UPDATE_MATCH_MIN_SCORE
    score = calculate_cannibalization_adjusted_priority(
        score,
        action_type=ACTION_UPDATE_EXISTING_PAGE,
        cannibalization_risk=cannibal,
        has_strong_existing=has_strong,
    )
    priority = _priority_label(score, force_manual=vague, action_type=ACTION_UPDATE_EXISTING_PAGE)

    gap_reason = _normalize_gap_reason_for_branded_update(primary, item, gap_reason)

    gap_phrases = ", ".join(all_queries[:6])
    content_gap = f"Add or strengthen wording for: {gap_phrases}"
    notes = [
        "Update existing page — do not create a competing new article.",
        update_reason,
    ]
    q_esc = primary.replace('"', '\\"')
    next_step = (
        f"Update existing page at {url} (run patch/optimize for \"{primary}\"); "
        "do not create a new article."
    )

    return ArticleCandidate(
        suggested_title=f"Update: {item.title}",
        suggested_slug=item.slug,
        article_type=article_type,
        primary_keyword=primary,
        secondary_queries=secondary,
        topic=topic,
        priority=priority,
        priority_score=round(score, 2),
        total_impressions=sum(r.impressions for r in rows),
        total_clicks=sum(r.clicks for r in rows),
        weighted_avg_position=round(_weighted_avg_position_rows(rows), 2),
        related_query_count=len(all_queries),
        target_gap_reason=gap_reason or update_reason,
        cannibalization_risk=cannibal,
        existing_related_pages=filtered_related,
        suggested_internal_links_from=filter_high_quality_link_sources(
            filtered_related,
            catalog,
            query=primary,
            topic=topic,
            target_url=url,
            action_type=ACTION_UPDATE_EXISTING_PAGE,
            limit=3,
        ),
        suggested_internal_links_to=[],
        editorial_notes=notes,
        recommended_next_step=next_step,
        action_type=ACTION_UPDATE_EXISTING_PAGE,
        recommended_existing_url=url,
        recommended_existing_title=item.title,
        update_reason=update_reason,
        content_gap_to_add=content_gap,
        query_group_label=query_group_label,
        merged_queries=all_queries,
    )


def _build_create_candidate_from_rows(
    rows: list[GscQueryRow],
    *,
    catalog: list[ContentItem],
    gap_reason: str,
    query_group_label: str,
    merged_queries: list[str],
    force_manual: bool = False,
    editorial_notes: list[str] | None = None,
) -> ArticleCandidate:
    primary_row = max(rows, key=lambda r: r.impressions)
    primary = primary_row.query
    all_queries = merged_queries or [r.query for r in rows]
    intent = detect_query_intent(primary)
    article_type = _infer_article_type(primary, intent)
    topic = _detect_roadmap_topic(primary, article_type)
    vague = _is_vague_query(primary) or force_manual

    if is_branded_product_query(primary):
        brand_upd = find_existing_brand_review_page(primary, catalog)
        if brand_upd:
            return build_existing_page_update_candidate(
                rows,
                catalog=catalog,
                item=brand_upd[0],
                match_score=brand_upd[1],
                update_reason=brand_upd[2],
                gap_reason=gap_reason,
                query_group_label=query_group_label,
                merged_queries=all_queries,
            )
        vague = True
        title, slug = safe_manual_review_title(primary)
        article_type = ARTICLE_REVIEW
    elif vague:
        title, slug = safe_manual_review_title(primary)
    elif article_type == ARTICLE_COMPARISON:
        title, slug = _title_for_comparison(primary)
    elif article_type == ARTICLE_REVIEW:
        title, slug = _title_for_review(primary)
    elif article_type == ARTICLE_ROUNDUP:
        title, slug = _title_for_roundup(primary)
    elif article_type == ARTICLE_CONCEPT_COMPARISON:
        title, slug = _title_for_concept(primary)
    elif article_type == ARTICLE_GUIDE:
        title, slug = _title_for_guide(primary)
    else:
        title = smart_title_case(primary)
        slug = _slugify(title)

    partials = _partial_matches_for_query(primary, catalog, limit=6)
    match_item, match_score = _find_best_existing_page_match(primary, catalog, article_type)
    if match_item and _wrong_branded_comparison_page(primary, match_item):
        match_score = 0.0
    if match_item and is_same_intent_roundup_overlap(primary, match_item, topic):
        match_score = max(match_score, _SAME_INTENT_UPDATE_MIN_SCORE + 5.0)
    related_urls = [p.url for p in partials[:4]]
    cannibal = _cannibalization_risk(primary, catalog, partials, match_score)

    gap_severity = 15.0 if "no strong matching" in gap_reason.lower() else 10.0
    if "mismatch" in gap_reason.lower():
        gap_severity = 22.0
    notes = list(editorial_notes or [])
    action_type = ACTION_CREATE_NEW_ARTICLE

    if vague:
        action_type = ACTION_MANUAL_REVIEW
    elif is_teamwork_vs_asana_query(primary):
        gap_severity = 30.0
        force_manual = False
        cannibal = "low"
        notes.append("Branded comparison for Teamwork.com vs Asana — not Asana vs ClickUp.")
    elif not should_create_new_article(
        query=primary,
        catalog=catalog,
        article_type=article_type,
        cannibalization_risk=cannibal,
        force_manual=vague,
    ):
        update = should_convert_create_to_update(
            primary, catalog, article_type, cannibalization_risk=cannibal
        ) or detect_existing_page_update_opportunity(primary, catalog, article_type)
        if update:
            return build_existing_page_update_candidate(
                rows,
                catalog=catalog,
                item=update[0],
                match_score=update[1],
                update_reason=update[2],
                gap_reason=gap_reason,
                query_group_label=query_group_label,
                merged_queries=all_queries,
            )

    score = _priority_score(
        rows,
        article_type=article_type,
        query_intent=intent,
        gap_severity=gap_severity,
        related_count=len(all_queries),
        vague=vague,
        cannibalization_risk=cannibal,
        action_type=action_type,
    )
    has_strong = bool(match_item and match_score >= _UPDATE_MATCH_MIN_SCORE)
    score = calculate_cannibalization_adjusted_priority(
        score,
        action_type=action_type,
        cannibalization_risk=cannibal,
        has_strong_existing=has_strong,
    )
    manual_conv, manual_note = should_convert_create_to_manual_review(
        primary,
        article_type=article_type,
        cannibalization_risk=cannibal,
        vague=vague,
        related_count=len(all_queries),
        total_impressions=sum(r.impressions for r in rows),
    )
    if manual_conv and not is_teamwork_vs_asana_query(primary):
        vague = True
        action_type = ACTION_MANUAL_REVIEW
        title, slug = safe_manual_review_title(primary)
        if manual_note:
            notes.append(manual_note)
    elif vague:
        action_type = ACTION_MANUAL_REVIEW
    priority = _priority_label(score, force_manual=vague, action_type=action_type)

    if vague and "Manual editorial review" not in " ".join(notes):
        notes.append("Vague or broad query — confirm search intent before writing.")
    if cannibal == "medium":
        notes.append("Partial overlap with existing pages — prefer updating unless angle is clearly distinct.")
    if cannibal == "high":
        notes.append("High cannibalization risk — avoid a new overlapping article.")

    secondary = [q for q in all_queries if q != primary]
    next_step = (
        f"Draft new {article_type.replace('_', ' ')} article: {title}. "
        f"Primary keyword: {primary}."
    )
    if priority == PRIORITY_MANUAL or action_type == ACTION_MANUAL_REVIEW:
        next_step = "Manual editorial review before drafting."

    link_from = filter_high_quality_link_sources(
        related_urls,
        catalog,
        query=primary,
        topic=topic,
        action_type=action_type,
        limit=3,
    )
    link_to = filter_high_quality_link_sources(
        related_urls[3:6] if len(related_urls) > 3 else [],
        catalog,
        query=primary,
        topic=topic,
        action_type=action_type,
        limit=3,
    )

    return ArticleCandidate(
        suggested_title=title,
        suggested_slug=slug,
        article_type=article_type,
        primary_keyword=primary,
        secondary_queries=secondary,
        topic=topic,
        priority=priority,
        priority_score=round(score, 2),
        total_impressions=sum(r.impressions for r in rows),
        total_clicks=sum(r.clicks for r in rows),
        weighted_avg_position=round(_weighted_avg_position_rows(rows), 2),
        related_query_count=len(all_queries),
        target_gap_reason=gap_reason,
        cannibalization_risk=cannibal,
        existing_related_pages=filter_existing_related_pages(
            related_urls,
            catalog,
            query=primary,
            topic=topic,
            action_type=action_type,
            target_url="",
        ),
        suggested_internal_links_from=link_from,
        suggested_internal_links_to=link_to,
        editorial_notes=notes,
        recommended_next_step=next_step,
        action_type=action_type,
        query_group_label=query_group_label,
        merged_queries=all_queries,
    )


def group_similar_article_candidates(
    candidates: list[ArticleCandidate],
) -> list[ArticleCandidate]:
    """Merge candidates that share the same normalized intent key."""
    buckets: dict[str, list[ArticleCandidate]] = defaultdict(list)
    for c in candidates:
        key = c.query_group_label or normalize_candidate_intent_key(
            c.primary_keyword, c.article_type, c.topic
        )
        buckets[key].append(c)

    merged: list[ArticleCandidate] = []
    for key, group in buckets.items():
        if len(group) == 1:
            c = group[0]
            c.query_group_label = key
            if not c.merged_queries:
                c.merged_queries = [c.primary_keyword, *c.secondary_queries]
            merged.append(c)
            continue

        seen_q: set[str] = set()
        unique_queries: list[str] = []
        for c in group:
            for q in c.merged_queries or [c.primary_keyword, *c.secondary_queries]:
                ql = q.strip().lower()
                if ql and ql not in seen_q:
                    seen_q.add(ql)
                    unique_queries.append(q)

        update_group = [c for c in group if c.action_type == ACTION_UPDATE_EXISTING_PAGE]
        if update_group:
            best = max(update_group, key=lambda c: (c.priority_score, c.total_impressions))
        else:
            best = max(group, key=lambda c: (c.priority_score, c.total_impressions))

        best.query_group_label = key
        best.merged_queries = unique_queries
        best.secondary_queries = [q for q in unique_queries if q != best.primary_keyword]
        best.total_impressions = sum(c.total_impressions for c in group)
        best.total_clicks = sum(c.total_clicks for c in group)
        best.related_query_count = len(unique_queries)
        if update_group:
            best.action_type = ACTION_UPDATE_EXISTING_PAGE
        merged.append(best)
    return merged


def _should_consider_for_roadmap(
    opp: Opportunity,
    *,
    min_impressions: int,
    exclude_existing_covered: bool,
    catalog: list[ContentItem],
) -> tuple[bool, str, str]:
    if _is_brand_noise_query(opp.query):
        return False, "brand_noise", "Brand or navigational noise query."
    if opp.impressions < min_impressions:
        return False, "low_impressions", f"Below min impressions ({min_impressions})."
    intent = opp.query_intent or detect_query_intent(opp.query)
    article_type = _infer_article_type(opp.query, intent)
    if exclude_existing_covered:
        covered, reason = _is_already_covered(opp.query, catalog, opp)
        if covered:
            return False, "already_covered", reason
    if _is_vague_query(opp.query):
        return True, "", ""
    if opp.status == STATUS_NO_TARGET:
        return True, "", ""
    if opp.confidence == CONFIDENCE_LOW and opp.target_url:
        return True, "", ""
    if opp.target_url:
        item = next((i for i in catalog if i.url.rstrip("/") == opp.target_url.rstrip("/")), None)
        if item:
            alignment = compute_intent_alignment(opp.query_intent, detect_gsc_page_type(item))
            if alignment == ALIGNMENT_MISALIGNED:
                return True, "", ""
    if is_teamwork_vs_asana_query(opp.query):
        covered, reason = _is_already_covered(opp.query, catalog, opp)
        if not covered:
            return True, "", ""
        return False, "already_covered", reason
    update = detect_existing_page_update_opportunity(opp.query, catalog, article_type)
    if update:
        return True, "", ""
    if opp.clicks == 0 and opp.impressions >= min_impressions and 20 <= opp.position <= 90:
        if opp.confidence != CONFIDENCE_HIGH:
            return True, "", ""
    if intent in (INTENT_COMPARISON, INTENT_REVIEW, INTENT_BROAD_BEST, INTENT_HOW_TO):
        covered, reason = _is_already_covered(opp.query, catalog, opp)
        if not covered:
            return True, "", ""
    return False, "unclear_intent", "Query already has adequate target coverage."


def _merge_opportunities_into_groups(
    opportunities: list[Opportunity],
    cache: GscCache,
    catalog: list[ContentItem],
    *,
    min_impressions: int,
    exclude_existing_covered: bool,
) -> tuple[dict[str, list[GscQueryRow]], list[ExcludedQuery]]:
    groups: dict[str, list[GscQueryRow]] = defaultdict(list)
    excluded: list[ExcludedQuery] = []
    seen_query: set[str] = set()
    row_by_query = {q.query.strip().lower(): q for q in cache.queries}

    for opp in opportunities:
        qkey = opp.query.strip().lower()
        if qkey in seen_query:
            continue
        seen_query.add(qkey)
        include, category, reason = _should_consider_for_roadmap(
            opp,
            min_impressions=min_impressions,
            exclude_existing_covered=exclude_existing_covered,
            catalog=catalog,
        )
        row = row_by_query.get(qkey) or GscQueryRow(
            query=opp.query,
            clicks=opp.clicks,
            impressions=opp.impressions,
            ctr=opp.ctr,
            position=opp.position,
        )
        if not include:
            excluded.append(
                ExcludedQuery(
                    query=opp.query,
                    impressions=opp.impressions,
                    position=opp.position,
                    exclusion_reason=reason,
                    category=category,
                )
            )
            continue
        intent = opp.query_intent or detect_query_intent(opp.query)
        article_type = _infer_article_type(opp.query, intent)
        topic = _detect_roadmap_topic(opp.query, article_type)
        key = normalize_candidate_intent_key(opp.query, article_type, topic)
        groups[key].append(row)

    return groups, excluded


def _assign_buckets(
    candidates: list[ArticleCandidate],
    *,
    include_low: bool,
    include_manual: bool,
    max_candidates: int,
) -> dict[str, list[ArticleCandidate]]:
    create_high: list[ArticleCandidate] = []
    create_medium: list[ArticleCandidate] = []
    create_low: list[ArticleCandidate] = []
    update_high: list[ArticleCandidate] = []
    update_medium: list[ArticleCandidate] = []
    update_low: list[ArticleCandidate] = []
    manual: list[ArticleCandidate] = []

    for c in sorted(candidates, key=lambda x: (-x.priority_score, -x.total_impressions)):
        if c.priority == PRIORITY_MANUAL or c.action_type == ACTION_MANUAL_REVIEW:
            if include_manual:
                manual.append(c)
            continue
        if c.action_type == ACTION_UPDATE_EXISTING_PAGE:
            if c.priority == PRIORITY_HIGH:
                update_high.append(c)
            elif c.priority == PRIORITY_MEDIUM:
                update_medium.append(c)
            elif include_low:
                update_low.append(c)
        elif c.action_type == ACTION_CREATE_NEW_ARTICLE:
            if c.priority == PRIORITY_HIGH:
                create_high.append(c)
            elif c.priority == PRIORITY_MEDIUM:
                create_medium.append(c)
            elif include_low:
                create_low.append(c)

    all_ranked = (
        create_high
        + create_medium
        + update_high
        + update_medium
        + (create_low if include_low else [])
        + (update_low if include_low else [])
        + (manual if include_manual else [])
    )
    if len(all_ranked) > max_candidates:
        trimmed = all_ranked[:max_candidates]
        create_high = [c for c in trimmed if c in create_high]
        create_medium = [c for c in trimmed if c in create_medium]
        create_low = [c for c in trimmed if c in create_low]
        update_high = [c for c in trimmed if c in update_high]
        update_medium = [c for c in trimmed if c in update_medium]
        update_low = [c for c in trimmed if c in update_low]
        manual = [c for c in trimmed if c in manual]

    return {
        "create_high": create_high,
        "create_medium": create_medium,
        "create_low": create_low,
        "update_high": update_high,
        "update_medium": update_medium,
        "update_low": update_low,
        "manual": manual,
    }


def _build_consolidated_groups(candidates: list[ArticleCandidate]) -> list[ConsolidatedQueryGroup]:
    groups: list[ConsolidatedQueryGroup] = []
    for c in candidates:
        if len(c.merged_queries) < 2 and not c.secondary_queries:
            continue
        queries = c.merged_queries or [c.primary_keyword, *c.secondary_queries]
        groups.append(
            ConsolidatedQueryGroup(
                query_group_label=c.query_group_label or c.primary_keyword,
                merged_queries=queries,
                action_type=c.action_type,
                primary_keyword=c.primary_keyword,
                suggested_title=c.suggested_title,
                recommended_existing_url=c.recommended_existing_url,
                total_impressions=c.total_impressions,
            )
        )
    return groups


def _build_calendar(
    create_high: list[ArticleCandidate],
    update_high: list[ArticleCandidate],
    create_medium: list[ArticleCandidate],
    update_medium: list[ArticleCandidate],
    low: list[ArticleCandidate],
) -> tuple[list[str], list[str], list[str]]:
    week1 = [c.suggested_title for c in (update_high[:2] + create_high[:2])]
    week2 = [c.suggested_title for c in (update_medium[:2] + create_medium[:2] + create_high[2:4])]
    later = [c.suggested_title for c in (create_medium[2:] + update_medium[2:] + low[:5])]
    return week1, week2, later


def _suggested_commands(candidates: list[ArticleCandidate]) -> list[str]:
    cmds: list[str] = []
    for c in candidates[:10]:
        if c.action_type == ACTION_UPDATE_EXISTING_PAGE and c.recommended_existing_url:
            url = c.recommended_existing_url
            q = c.primary_keyword.replace('"', '\\"')
            cmds.append(
                f'python -m linkops.cli patch --target-url "{url}" --target-keyword "{q}"'
            )
            cmds.append(
                f'python -m linkops.cli optimize --target-url "{url}" --target-keyword "{q}"'
            )
        elif c.action_type == ACTION_CREATE_NEW_ARTICLE and c.suggested_slug:
            url = f"https://worktoolslab.com/{c.suggested_slug}/"
            q = c.primary_keyword.replace('"', '\\"')
            cmds.append(
                f'python -m linkops.cli suggest --target-url "{url}" '
                f'--target-keyword "{q}" --max-suggestions 8'
            )
    cmds.append(
        "python -m linkops.cli opportunities --min-impressions 20 --max-clicks 0 --max-position 90"
    )
    return list(dict.fromkeys(cmds))


def build_article_roadmap_report(
    cache: GscCache,
    catalog: list[ContentItem],
    worklog: Worklog | None = None,
    *,
    min_impressions: int = 10,
    max_position: float = 90.0,
    max_candidates: int = 20,
    include_low_priority: bool = False,
    include_manual_review: bool = True,
    exclude_existing_covered: bool = True,
    worklog_aware: bool = True,
) -> ArticleRoadmapReport:
    """Build grouped new-article roadmap from GSC and WordPress cache."""
    wl = worklog
    if worklog_aware and wl is None:
        wl = load_worklog()
    opp_report = analyze_opportunities(
        cache,
        catalog,
        min_impressions=min_impressions,
        max_clicks=10,
        max_position=max_position,
    )
    groups, excluded = _merge_opportunities_into_groups(
        opp_report.opportunities,
        cache,
        catalog,
        min_impressions=min_impressions,
        exclude_existing_covered=exclude_existing_covered,
    )

    raw_candidates: list[ArticleCandidate] = []
    opp_by_query = {o.query.strip().lower(): o for o in opp_report.opportunities}
    for intent_key, rows in groups.items():
        rows.sort(key=lambda r: (-r.impressions, r.position))
        merged_queries = [r.query for r in rows]
        primary_row = max(rows, key=lambda r: r.impressions)
        opp = opp_by_query.get(primary_row.query.strip().lower())
        gap = _gap_reason_for_opportunity(opp, catalog) if opp else "GSC query gap with no strong catalog page."
        intent = detect_query_intent(primary_row.query)
        article_type = _infer_article_type(primary_row.query, intent)
        topic = _detect_roadmap_topic(primary_row.query, article_type)
        merged_queries = [r.query for r in rows]
        branded = resolve_branded_query_candidate(
            rows,
            catalog=catalog,
            gap_reason=gap,
            query_group_label=intent_key,
            merged_queries=merged_queries,
        )
        if branded is not None:
            raw_candidates.append(branded)
            continue

        update = _best_update_for_queries(merged_queries, catalog, article_type)
        if not update and opp and "content match" in (gap or "").lower():
            update = _best_update_for_queries(merged_queries, catalog, article_type)

        if update and not is_teamwork_vs_asana_query(primary_row.query):
            if is_brand_mismatch_page(primary_row.query, update[0]):
                update = None
        if update and not is_teamwork_vs_asana_query(primary_row.query):
            raw_candidates.append(
                build_existing_page_update_candidate(
                    rows,
                    catalog=catalog,
                    item=update[0],
                    match_score=update[1],
                    update_reason=update[2],
                    gap_reason=gap,
                    query_group_label=intent_key,
                    merged_queries=merged_queries,
                )
            )
        else:
            raw_candidates.append(
                _build_create_candidate_from_rows(
                    rows,
                    catalog=catalog,
                    gap_reason=gap,
                    query_group_label=intent_key,
                    merged_queries=merged_queries,
                    force_manual=_is_vague_query(primary_row.query),
                )
            )

    candidates = group_similar_article_candidates(raw_candidates)
    final: list[ArticleCandidate] = []
    for c in candidates:
        if is_branded_product_query(c.primary_keyword):
            branded = resolve_branded_query_candidate(
                [
                    GscQueryRow(
                        q,
                        0,
                        max(c.total_impressions // max(len(c.merged_queries or [c.primary_keyword]), 1), 1),
                        0.0,
                        c.weighted_avg_position,
                    )
                    for q in (c.merged_queries or [c.primary_keyword])
                ],
                catalog=catalog,
                gap_reason=c.target_gap_reason,
                query_group_label=c.query_group_label,
                merged_queries=c.merged_queries or [c.primary_keyword],
            )
            if branded:
                final.append(branded)
            continue
        if c.action_type == ACTION_UPDATE_EXISTING_PAGE and is_branded_product_query(
            c.primary_keyword
        ):
            item = next(
                (i for i in catalog if i.url.rstrip("/") == c.recommended_existing_url.rstrip("/")),
                None,
            )
            if item and is_brand_mismatch_page(c.primary_keyword, item):
                branded = resolve_branded_query_candidate(
                    [
                        GscQueryRow(
                            c.primary_keyword,
                            0,
                            c.total_impressions,
                            0.0,
                            c.weighted_avg_position,
                        )
                    ],
                    catalog=catalog,
                    gap_reason=c.target_gap_reason,
                    query_group_label=c.query_group_label,
                    merged_queries=c.merged_queries or [c.primary_keyword],
                )
                if branded:
                    final.append(branded)
                continue
        if c.action_type == ACTION_CREATE_NEW_ARTICLE:
            intent = detect_query_intent(c.primary_keyword)
            atype = _infer_article_type(c.primary_keyword, intent)
            upd = detect_existing_page_update_opportunity(c.primary_keyword, catalog, atype)
            if upd and should_create_new_article(
                query=c.primary_keyword,
                catalog=catalog,
                article_type=atype,
                cannibalization_risk=c.cannibalization_risk,
                force_manual=False,
            ) is False:
                rows = [GscQueryRow(q, 0, c.total_impressions // max(len(c.merged_queries), 1), 0.0, c.weighted_avg_position) for q in (c.merged_queries or [c.primary_keyword])]
                final.append(
                    build_existing_page_update_candidate(
                        rows,
                        catalog=catalog,
                        item=upd[0],
                        match_score=upd[1],
                        update_reason=upd[2],
                        gap_reason=c.target_gap_reason,
                        query_group_label=c.query_group_label,
                        merged_queries=c.merged_queries or [c.primary_keyword],
                    )
                )
                continue
        final.append(c)
    candidates = [refine_roadmap_candidate(c, catalog) for c in final]

    buckets = _assign_buckets(
        candidates,
        include_low=include_low_priority,
        include_manual=include_manual_review,
        max_candidates=max_candidates,
    )
    consolidated = _build_consolidated_groups(candidates)
    week1, week2, later = _build_calendar(
        buckets["create_high"],
        buckets["update_high"],
        buckets["create_medium"],
        buckets["update_medium"],
        buckets["create_low"] + buckets["update_low"],
    )

    counts = calculate_displayed_roadmap_counts(
        buckets, include_low=include_low_priority
    )
    create_n = counts["create"]
    update_n = counts["update"]
    displayed = collect_displayed_candidates(
        buckets,
        include_low=include_low_priority,
        include_manual=include_manual_review,
    )
    top_lines = build_top_summary_lines(displayed, limit=5)
    top_displayed = sorted(
        displayed,
        key=lambda c: (-c.priority_score, -c.total_impressions),
    )[:5]

    summary = (
        f"Analyzed {opp_report.total_queries_analyzed} GSC queries; "
        f"{counts['total']} roadmap item(s) displayed after consolidation "
        f"({len(candidates)} unique intent(s) before max_candidates trim). "
        f"Create new: {create_n} (high {counts['create_high']}, medium {counts['create_medium']}). "
        f"Update existing: {update_n} (high {counts['update_high']}, medium {counts['update_medium']}). "
        f"Manual review: {counts['manual']}, excluded: {len(excluded)}."
    )

    cmd_sources = (
        buckets["update_high"]
        + buckets["update_medium"]
        + buckets["create_high"]
        + buckets["create_medium"]
    )

    return ArticleRoadmapReport(
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        gsc_imported_at=cache.imported_at,
        worklog_path=str(WORKLOG_PATH),
        worklog_loaded=bool(worklog_aware and wl and wl.pages),
        filters={
            "min_impressions": min_impressions,
            "max_position": max_position,
            "max_candidates": max_candidates,
            "include_low_priority": include_low_priority,
            "include_manual_review": include_manual_review,
            "exclude_existing_covered": exclude_existing_covered,
            "worklog_aware": worklog_aware,
        },
        total_queries_analyzed=opp_report.total_queries_analyzed,
        executive_summary=summary + ("\nTop items:\n" + "\n".join(top_lines) if top_lines else ""),
        displayed_roadmap_counts=counts,
        top_candidates=top_displayed,
        create_new_high=buckets["create_high"],
        create_new_medium=buckets["create_medium"],
        create_new_low=buckets["create_low"],
        update_existing_high=buckets["update_high"],
        update_existing_medium=buckets["update_medium"],
        update_existing_low=buckets["update_low"],
        manual_review=buckets["manual"],
        consolidated_groups=consolidated,
        excluded_queries=excluded,
        calendar_week1=week1,
        calendar_week2=week2,
        calendar_later=later,
        suggested_commands=_suggested_commands(cmd_sources),
        high_priority=buckets["create_high"] + buckets["update_high"],
        medium_priority=buckets["create_medium"] + buckets["update_medium"],
        low_priority=buckets["create_low"] + buckets["update_low"],
    )
