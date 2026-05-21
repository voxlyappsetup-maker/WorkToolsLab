"""Page and query intent detection for GSC opportunity matching."""

from __future__ import annotations

import re

from linkops.content_model import ContentItem
from linkops.suggestion_engine import (
    CORE_PAGE_SLUGS,
    CORE_PAGE_TITLE_TERMS,
    POLICY_PAGE_SLUG_TERMS,
    POLICY_PAGE_TITLE_TERMS,
    classify_page_type as _legacy_classify_page_type,
)

# Page types for GSC matching
PAGE_ROUNDUP = "roundup_best_tools"
PAGE_REVIEW = "review"
PAGE_COMPARISON = "comparison"
PAGE_GUIDE = "guide"
PAGE_CORE = "core_page"
PAGE_POLICY = "policy_or_legal"
PAGE_UNKNOWN = "unknown"

# Query intents
INTENT_BROAD_BEST = "broad_best_tools"
INTENT_REVIEW = "specific_review"
INTENT_COMPARISON = "comparison"
INTENT_HOW_TO = "how_to"
INTENT_INFORMATIONAL = "informational"
INTENT_UNKNOWN = "unknown"

# Action types
ACTION_INTERNAL_LINKS = "internal_links"
ACTION_CONTENT_OPTIMIZATION = "content_optimization"
ACTION_TITLE_META_CTR = "title_meta_ctr"
ACTION_CANNIBALIZATION = "cannibalization_review"
ACTION_OLD_URL = "old_url_monitor"
ACTION_NEW_ARTICLE = "new_article_needed"
ACTION_MONITOR = "monitor_only"

CONFIDENCE_HIGH = "high"
CONFIDENCE_MEDIUM = "medium"
CONFIDENCE_LOW = "low"

KNOWN_BRAND_TERMS = frozenset(
    {
        "monday",
        "asana",
        "trello",
        "clickup",
        "slack",
        "notion",
        "zoom",
        "webex",
        "teams",
        "todoist",
        "basecamp",
        "smartsheet",
        "airtable",
        "jira",
        "linear",
        "hubspot",
        "salesforce",
    }
)

COMMERCIAL_QUERY_TERMS = frozenset(
    {"best", "tools", "tool", "software", "platforms", "platform", "apps", "app"}
)


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def detect_gsc_page_type(item: ContentItem) -> str:
    """Classify page intent for GSC target matching."""
    slug = item.slug.lower().strip("/")
    title = _normalize_text(item.title)
    slug_text = slug.replace("-", " ")

    for term in POLICY_PAGE_TITLE_TERMS:
        if term in title:
            return PAGE_POLICY
    for term in POLICY_PAGE_SLUG_TERMS:
        if term in slug or term.replace("-", " ") in slug_text:
            return PAGE_POLICY

    if slug in CORE_PAGE_SLUGS or title in CORE_PAGE_TITLE_TERMS:
        return PAGE_CORE
    for term in CORE_PAGE_TITLE_TERMS:
        if term == title or title.startswith(f"{term} "):
            return PAGE_CORE
    if slug in {"tools", "start-here", "start_here"} or title in {"tools", "start here"}:
        return PAGE_CORE

    if "how-to" in slug or slug.startswith("how-to-") or title.startswith("how to"):
        return PAGE_GUIDE

    if " vs " in title or "-vs-" in slug or " versus " in title:
        return PAGE_COMPARISON

    if "review" in title or slug.endswith("-review") or " review" in slug_text:
        return PAGE_REVIEW

    if slug.startswith("best-") or title.startswith("best "):
        if any(t in title or t in slug_text for t in ("tools", "tool", "software", "apps")):
            return PAGE_ROUNDUP

    legacy = _legacy_classify_page_type(item)
    if legacy == "category_guide":
        return PAGE_ROUNDUP
    if legacy == "comparison":
        return PAGE_COMPARISON
    if legacy == "review":
        return PAGE_REVIEW
    if legacy == "core_page":
        return PAGE_CORE
    if legacy == "policy_legal":
        return PAGE_POLICY

    return PAGE_UNKNOWN


def _query_has_comparison_language(query: str) -> bool:
    q = _normalize_text(query)
    return bool(
        re.search(r"\bvs\.?\b|\bversus\b|\balternative\b|\bcompare\b|\bcomparison\b", q)
    )


def _query_has_review_intent(query: str) -> bool:
    q = _normalize_text(query)
    if "review" not in q and "reviews" not in q:
        return False
    tokens = set(re.findall(r"[a-z0-9]+", q))
    return bool(tokens & KNOWN_BRAND_TERMS)


def _query_brand_tokens(query: str) -> set[str]:
    tokens = set(re.findall(r"[a-z0-9]+", query.lower()))
    return tokens & KNOWN_BRAND_TERMS


def detect_query_intent(query: str) -> str:
    """Lightweight deterministic query intent classifier."""
    q = _normalize_text(query)
    if not q:
        return INTENT_UNKNOWN

    if q.startswith("how to") or " how to " in f" {q} " or q.startswith("how-to"):
        return INTENT_HOW_TO

    if _query_has_comparison_language(q):
        return INTENT_COMPARISON

    if _query_has_review_intent(q):
        return INTENT_REVIEW

    tokens = set(re.findall(r"[a-z0-9]+", q))
    commercial_hits = tokens & COMMERCIAL_QUERY_TERMS
    category_terms = {
        "management",
        "communication",
        "productivity",
        "workflow",
        "task",
        "project",
        "remote",
        "business",
        "freelance",
        "freelancers",
    }
    has_category = bool(tokens & category_terms)
    if not _query_has_review_intent(q):
        if "best" in tokens:
            return INTENT_BROAD_BEST
        if commercial_hits and has_category and not _query_has_comparison_language(q):
            return INTENT_BROAD_BEST
        if len(commercial_hits) >= 2 and not _query_has_comparison_language(q):
            return INTENT_BROAD_BEST

    if len(tokens) >= 3:
        return INTENT_INFORMATIONAL

    return INTENT_UNKNOWN


def _page_mentions_query_brand(query: str, item: ContentItem) -> bool:
    brands = _query_brand_tokens(query)
    if not brands:
        return False
    blob = _normalize_text(f"{item.title} {item.slug.replace('-', ' ')}")
    return any(b in blob for b in brands)


def intent_scoring_adjustment(
    query: str,
    query_intent: str,
    page_type: str,
    item: ContentItem,
) -> tuple[float, str]:
    """Return score adjustment and short reason fragment for target selection."""
    adj = 0.0
    reasons: list[str] = []

    if query_intent == INTENT_BROAD_BEST:
        if page_type == PAGE_ROUNDUP:
            adj += 85.0
            reasons.append("roundup page preferred for broad tools query")
        elif page_type == PAGE_REVIEW:
            if not _page_mentions_query_brand(query, item):
                adj -= 75.0
                reasons.append("review page penalized without brand in query")
        elif page_type == PAGE_COMPARISON:
            if not _query_has_comparison_language(query):
                adj -= 65.0
                reasons.append("comparison page penalized for non-comparison query")
        elif page_type == PAGE_GUIDE:
            if query_intent != INTENT_HOW_TO:
                adj -= 45.0
                reasons.append("guide page penalized for commercial query")
        elif page_type in (PAGE_CORE, PAGE_POLICY):
            adj -= 80.0
            reasons.append("utility/policy page penalized")

    elif query_intent == INTENT_COMPARISON:
        if page_type == PAGE_COMPARISON:
            adj += 70.0
            reasons.append("comparison page preferred")
        elif page_type == PAGE_ROUNDUP:
            adj -= 30.0
        elif page_type == PAGE_REVIEW:
            adj -= 25.0

    elif query_intent == INTENT_REVIEW:
        if page_type == PAGE_REVIEW and _page_mentions_query_brand(query, item):
            adj += 75.0
            reasons.append("brand review page preferred")
        elif page_type == PAGE_ROUNDUP:
            adj -= 35.0
        elif page_type == PAGE_COMPARISON:
            adj -= 20.0

    elif query_intent == INTENT_HOW_TO:
        if page_type == PAGE_GUIDE:
            adj += 70.0
            reasons.append("guide page preferred for how-to query")
        elif page_type == PAGE_ROUNDUP:
            adj -= 25.0

    elif query_intent == INTENT_INFORMATIONAL:
        if page_type == PAGE_ROUNDUP:
            adj += 15.0

    reason = "; ".join(reasons) if reasons else ""
    return adj, reason


def pool_for_query_intent(
    query: str,
    query_intent: str,
    items: list[ContentItem],
) -> list[ContentItem]:
    """Optionally narrow candidate pool before topical scoring."""
    if query_intent == INTENT_BROAD_BEST:
        roundups = [i for i in items if detect_gsc_page_type(i) == PAGE_ROUNDUP]
        if roundups:
            return roundups
    if query_intent == INTENT_COMPARISON:
        q = _normalize_text(query)
        parts = re.split(r"\s+vs\.?\s+|\s+versus\s+", q)
        if len(parts) == 2:
            left, right = parts[0].strip(), parts[1].strip()
            narrowed = [
                i
                for i in items
                if i.slug.lower().count("-vs-") == 1
                and left in i.slug.lower()
                and right in i.slug.lower()
            ]
            if narrowed:
                return narrowed
        comparisons = [i for i in items if detect_gsc_page_type(i) == PAGE_COMPARISON]
        if comparisons:
            return comparisons
    if query_intent == INTENT_REVIEW:
        brands = _query_brand_tokens(query)
        if brands:
            reviews = [
                i
                for i in items
                if detect_gsc_page_type(i) == PAGE_REVIEW and _page_mentions_query_brand(query, i)
            ]
            if reviews:
                return reviews
    if query_intent == INTENT_HOW_TO:
        guides = [i for i in items if detect_gsc_page_type(i) == PAGE_GUIDE]
        if guides:
            return guides
    return items


def compute_confidence(
    *,
    override_used: bool,
    override_in_catalog: bool,
    query_intent: str,
    page_type: str,
    match_score: float,
    topical_reason: str,
    intent_reason: str,
) -> tuple[str, str]:
    """Return confidence level and target selection reason."""
    parts: list[str] = []
    if override_used:
        parts.append("query target override applied")
        if override_in_catalog:
            return CONFIDENCE_HIGH, "; ".join(parts)
        parts.append("override target not found in content cache")
        return CONFIDENCE_MEDIUM, "; ".join(parts)

    if intent_reason:
        parts.append(intent_reason)
    if topical_reason:
        parts.append(topical_reason)

    if query_intent == INTENT_BROAD_BEST and page_type == PAGE_REVIEW:
        return CONFIDENCE_LOW, "; ".join(parts) or "review page for broad commercial query"

    if query_intent == INTENT_BROAD_BEST and page_type == PAGE_ROUNDUP and match_score >= 40:
        return CONFIDENCE_HIGH, "; ".join(parts) or "roundup topical match"

    if query_intent == INTENT_COMPARISON and page_type == PAGE_COMPARISON and match_score >= 35:
        return CONFIDENCE_HIGH, "; ".join(parts) or "comparison page match"

    if match_score >= 50:
        return CONFIDENCE_HIGH, "; ".join(parts) or "strong topical match"

    if match_score >= 20:
        return CONFIDENCE_MEDIUM, "; ".join(parts) or "moderate topical match"

    if match_score >= 8:
        return CONFIDENCE_LOW, "; ".join(parts) or "weak topical match"

    return CONFIDENCE_LOW, "; ".join(parts) or "low match confidence"


def classify_action_type(
    *,
    status: str,
    clicks: int,
    impressions: int,
    position: float,
    has_target: bool,
    needs_internal_links: bool,
    is_cannibal: bool,
    is_old_url: bool,
    is_content_weak: bool,
) -> str:
    """Map opportunity context to action_type."""
    from linkops.gsc_model import (
        STATUS_CANNIBALIZATION,
        STATUS_CONTENT_OPTIMIZATION,
        STATUS_CORRECT_PAGE,
        STATUS_INTERNAL_LINKS,
        STATUS_NO_TARGET,
        STATUS_OLD_URL,
    )

    if is_cannibal or status == STATUS_CANNIBALIZATION:
        return ACTION_CANNIBALIZATION
    if is_old_url or status == STATUS_OLD_URL:
        return ACTION_OLD_URL
    if not has_target or status == STATUS_NO_TARGET:
        return ACTION_NEW_ARTICLE

    if (
        status == STATUS_CORRECT_PAGE
        and clicks == 0
        and impressions >= 20
        and 8 <= position <= 20
    ):
        return ACTION_TITLE_META_CTR

    if status == STATUS_INTERNAL_LINKS or needs_internal_links:
        return ACTION_INTERNAL_LINKS

    if status == STATUS_CONTENT_OPTIMIZATION or is_content_weak:
        return ACTION_CONTENT_OPTIMIZATION

    if status == STATUS_CORRECT_PAGE and clicks > 0 and position < 15:
        return ACTION_MONITOR

    if 20 <= position <= 90 and has_target:
        if needs_internal_links:
            return ACTION_INTERNAL_LINKS
        return ACTION_CONTENT_OPTIMIZATION

    return ACTION_MONITOR
