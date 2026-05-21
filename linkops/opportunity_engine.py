"""GSC opportunity scoring using WordPress content cache (read-only, local)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from linkops.content_model import ContentItem
from linkops.gsc_model import (
    GscCache,
    GscQueryPageRow,
    GscQueryRow,
    Opportunity,
    OpportunityReport,
    STATUS_CANNIBALIZATION,
    STATUS_CONTENT_OPTIMIZATION,
    STATUS_CORRECT_PAGE,
    STATUS_INTERNAL_LINKS,
    STATUS_NO_TARGET,
    STATUS_OLD_URL,
)
from linkops.gsc_intent import (
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    INTENT_INFORMATIONAL,
    INTENT_UNKNOWN,
    PAGE_UNKNOWN,
    classify_action_type,
    compute_confidence,
    detect_gsc_page_type,
    detect_query_intent,
    intent_scoring_adjustment,
    pool_for_query_intent,
)
from linkops.html_tools import extract_headings, normalize_internal_url
from linkops.query_overrides import load_query_target_overrides
from linkops.suggestion_engine import BASIC_STOP_WORDS, DOMAIN_STOPWORDS

BRAND_NOISE_TERMS = frozenset(
    {"worktoolslab", "worktoolslab.com", "work", "tools", "lab", "www"}
)
LOW_INTERNAL_LINK_THRESHOLD = 2
CANNIBALIZATION_MIN_IMPRESSIONS = 5
MEANINGFUL_IMPRESSIONS_FLOOR = 3


@dataclass
class _PageMatch:
    item: ContentItem | None
    url: str
    title: str
    score: float
    in_catalog: bool
    query_intent: str = INTENT_UNKNOWN
    page_type: str = PAGE_UNKNOWN
    confidence: str = CONFIDENCE_LOW
    target_selection_reason: str = ""
    override_used: bool = False
    intent_reason: str = ""


@dataclass
class _CatalogIndex:
    by_norm_url: dict[str, ContentItem]
    items: list[ContentItem]
    slug_to_url: dict[str, str]


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def _tokenize(text: str, *, exclude_domain: bool = True) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    stop = BASIC_STOP_WORDS | (DOMAIN_STOPWORDS if exclude_domain else frozenset())
    return {w for w in words if len(w) > 2 and w not in stop}


def _meaningful_tokens(text: str) -> set[str]:
    return _tokenize(text, exclude_domain=True)


def _query_phrases(query: str) -> list[str]:
    q = _normalize_text(query)
    phrases = [q] if " " in q else []
    parts = re.split(r"\s+vs\.?\s+|\s+versus\s+", q)
    if len(parts) > 1:
        phrases.append(q)
        for part in parts:
            part = part.strip()
            if part:
                phrases.append(part)
    return phrases


def _is_brand_noise_query(query: str) -> bool:
    tokens = set(re.findall(r"[a-z0-9]+", query.lower()))
    if not tokens:
        return True
    if tokens <= BRAND_NOISE_TERMS:
        return True
    if tokens <= BRAND_NOISE_TERMS | {"site", "login", "official"}:
        return True
    return False


def build_catalog_index(catalog: list[ContentItem]) -> _CatalogIndex:
    by_norm: dict[str, ContentItem] = {}
    slug_map: dict[str, str] = {}
    for item in catalog:
        norm = item.normalized_url()
        by_norm[norm] = item
        slug_map[item.slug.lower().strip("/")] = norm
    return _CatalogIndex(by_norm_url=by_norm, items=catalog, slug_to_url=slug_map)


def _slug_from_url(url: str) -> str:
    norm = normalize_internal_url(url)
    if not norm:
        return ""
    return norm.rstrip("/").split("/")[-1].lower()


def _resolve_gsc_page(url: str, index: _CatalogIndex) -> tuple[ContentItem | None, str, bool]:
    norm = normalize_internal_url(url)
    if norm and norm in index.by_norm_url:
        item = index.by_norm_url[norm]
        return item, item.url, True
    if norm:
        slug = _slug_from_url(norm)
        if slug in index.slug_to_url:
            canon = index.by_norm_url[index.slug_to_url[slug]]
            return canon, canon.url, True
    return None, url, False


def _is_old_or_duplicate_url(url: str, index: _CatalogIndex) -> bool:
    raw = url.strip().lower()
    if raw.startswith("http://"):
        return True
    path = urlparse_path(raw)
    if path.endswith("-2") or path.endswith("-2/") or "/-2/" in path:
        return True
    norm = normalize_internal_url(url)
    if norm and norm not in index.by_norm_url:
        slug = _slug_from_url(norm or url)
        if slug and slug in index.slug_to_url:
            return True
    return False


def urlparse_path(url: str) -> str:
    from urllib.parse import urlparse

    parsed = urlparse(url.strip())
    return (parsed.path or "").rstrip("/")


def _heading_text(item: ContentItem) -> str:
    headings = extract_headings(item.content_html)
    parts = headings.get("h1", []) + headings.get("h2", [])
    return _normalize_text(" ".join(parts))


def _intro_snippet(item: ContentItem, limit: int = 400) -> str:
    return _normalize_text(item.plain_text[:limit])


def _score_page_for_query(query: str, item: ContentItem) -> float:
    if _is_brand_noise_query(query):
        return 0.0
    score = 0.0
    q_norm = _normalize_text(query)
    title_norm = _normalize_text(item.title)
    slug_text = item.slug.replace("-", " ")
    heading = _heading_text(item)
    intro = _intro_snippet(item)

    for phrase in _query_phrases(query):
        if len(phrase) < 4:
            continue
        if phrase in title_norm:
            score += 40.0
        if phrase in slug_text:
            score += 35.0
        if phrase in heading:
            score += 25.0
        if phrase in intro:
            score += 15.0
        if phrase in _normalize_text(item.plain_text[:3000]):
            score += 8.0

    vs_parts = re.split(r"\s+vs\.?\s+|\s+versus\s+", q_norm)
    if len(vs_parts) == 2:
        left, right = vs_parts[0].strip(), vs_parts[1].strip()
        slug_lower = item.slug.lower()
        title_lower = title_norm
        vs_count = slug_lower.count("-vs-")
        if left and right and left in slug_lower and right in slug_lower:
            if vs_count == 1:
                score += 55.0
                if f"{left}-vs-{right}" in slug_lower or f"{right}-vs-{left}" in slug_lower:
                    score += 35.0
            else:
                score += 10.0
        if vs_count >= 2 or title_lower.count(" vs ") >= 2:
            score -= 90.0

    q_tokens = _meaningful_tokens(q_norm)
    if not q_tokens:
        return score
    title_tokens = _meaningful_tokens(f"{item.title} {slug_text}")
    heading_tokens = _meaningful_tokens(heading)
    content_tokens = _meaningful_tokens(item.plain_text[:2500])
    overlap_title = q_tokens & title_tokens
    overlap_heading = q_tokens & heading_tokens
    overlap_content = q_tokens & content_tokens
    if overlap_title:
        score += 12.0 * min(len(overlap_title), 4)
    if overlap_heading:
        score += 8.0 * min(len(overlap_heading), 4)
    if overlap_content:
        score += 3.0 * min(len(overlap_content), 4)
    generic = overlap_content & DOMAIN_STOPWORDS
    if generic and not (overlap_title or overlap_heading):
        score += min(len(generic), 2) * 0.5
    return score


def _two_way_vs_tools(query: str) -> tuple[str, str] | None:
    q_norm = _normalize_text(query)
    parts = re.split(r"\s+vs\.?\s+|\s+versus\s+", q_norm)
    if len(parts) != 2:
        return None
    left, right = parts[0].strip(), parts[1].strip()
    if not left or not right:
        return None
    return left, right


def _match_from_override(
    query: str,
    index: _CatalogIndex,
    overrides: dict[str, str],
    query_intent: str,
) -> _PageMatch | None:
    key = query.strip().lower()
    url = overrides.get(key)
    if not url:
        return None
    item, canon, in_cat = _resolve_gsc_page(url, index)
    page_type = detect_gsc_page_type(item) if item else PAGE_UNKNOWN
    if in_cat and item:
        conf, sel_reason = compute_confidence(
            override_used=True,
            override_in_catalog=True,
            query_intent=query_intent,
            page_type=page_type,
            match_score=100.0,
            topical_reason="",
            intent_reason="",
        )
        return _PageMatch(
            item=item,
            url=canon,
            title=item.title,
            score=100.0,
            in_catalog=True,
            query_intent=query_intent,
            page_type=page_type,
            confidence=conf,
            target_selection_reason=sel_reason,
            override_used=True,
        )
    conf, sel_reason = compute_confidence(
        override_used=True,
        override_in_catalog=False,
        query_intent=query_intent,
        page_type=PAGE_UNKNOWN,
        match_score=0.0,
        topical_reason="",
        intent_reason="",
    )
    return _PageMatch(
        item=None,
        url=url,
        title="",
        score=0.0,
        in_catalog=False,
        query_intent=query_intent,
        page_type=PAGE_UNKNOWN,
        confidence=conf,
        target_selection_reason=sel_reason,
        override_used=True,
    )


def _best_catalog_match(
    query: str,
    index: _CatalogIndex,
    overrides: dict[str, str] | None = None,
) -> _PageMatch:
    overrides = overrides if overrides is not None else load_query_target_overrides()
    query_intent = detect_query_intent(query)

    override_match = _match_from_override(query, index, overrides, query_intent)
    if override_match:
        return override_match

    best: ContentItem | None = None
    best_score = 0.0
    best_page_type = PAGE_UNKNOWN
    best_intent_reason = ""
    pool = pool_for_query_intent(query, query_intent, index.items)

    for item in pool:
        page_type = detect_gsc_page_type(item)
        topical = _score_page_for_query(query, item)
        intent_adj, intent_reason = intent_scoring_adjustment(
            query, query_intent, page_type, item
        )
        sc = topical + intent_adj
        if sc > best_score:
            best_score = sc
            best = item
            best_page_type = page_type
            best_intent_reason = intent_reason

    if best and best_score >= 8.0:
        topical_only = _score_page_for_query(query, best)
        if topical_only < 12.0 and query_intent in (INTENT_INFORMATIONAL, INTENT_UNKNOWN):
            return _PageMatch(
                None,
                "",
                "",
                0.0,
                False,
                query_intent=query_intent,
                confidence=CONFIDENCE_LOW,
                target_selection_reason="topical overlap too weak for informational query",
            )
        conf, sel_reason = compute_confidence(
            override_used=False,
            override_in_catalog=True,
            query_intent=query_intent,
            page_type=best_page_type,
            match_score=best_score,
            topical_reason=f"topical score {topical_only:.0f}",
            intent_reason=best_intent_reason,
        )
        return _PageMatch(
            best,
            best.url,
            best.title,
            best_score,
            True,
            query_intent=query_intent,
            page_type=best_page_type,
            confidence=conf,
            target_selection_reason=sel_reason,
            override_used=False,
            intent_reason=best_intent_reason,
        )
    return _PageMatch(
        None,
        "",
        "",
        0.0,
        False,
        query_intent=query_intent,
        confidence=CONFIDENCE_LOW,
        target_selection_reason="no page met minimum match threshold",
    )


def _gsc_pages_for_query(
    query: str,
    cache: GscCache,
) -> list[GscQueryPageRow]:
    q_lower = query.lower().strip()
    return [qp for qp in cache.query_pages if qp.query.lower().strip() == q_lower]


def _top_gsc_page_for_query(query: str, cache: GscCache) -> str | None:
    rows = _gsc_pages_for_query(query, cache)
    if not rows:
        return None
    rows_sorted = sorted(rows, key=lambda r: (-r.impressions, -r.clicks))
    return rows_sorted[0].page


def _detect_cannibalization(
    query: str,
    cache: GscCache,
    index: _CatalogIndex,
) -> tuple[bool, list[str], str]:
    rows = _gsc_pages_for_query(query, cache)
    if len(rows) < 2:
        return False, [], ""
    significant = []
    for row in rows:
        norm = normalize_internal_url(row.page)
        if row.impressions >= CANNIBALIZATION_MIN_IMPRESSIONS:
            significant.append(row.page)
    if len(significant) < 2:
        return False, [], ""
    catalog_urls: list[str] = []
    for url in significant:
        item, canon, in_cat = _resolve_gsc_page(url, index)
        if in_cat and canon:
            catalog_urls.append(canon)
    unique = list(dict.fromkeys(catalog_urls))
    if len(unique) >= 2:
        reason = (
            f"Query appears on {len(unique)} WorkToolsLab pages with meaningful impressions: "
            + "; ".join(unique[:4])
        )
        return True, unique, reason
    return False, [], ""


def _query_weak_in_content(query: str, item: ContentItem) -> bool:
    q_norm = _normalize_text(query)
    title_blob = _normalize_text(f"{item.title} {item.slug.replace('-', ' ')}")
    heading = _heading_text(item)
    intro = _intro_snippet(item)
    if q_norm in title_blob or q_norm in heading:
        return False
    q_tokens = _meaningful_tokens(q_norm)
    if not q_tokens:
        return True
    title_tokens = _meaningful_tokens(title_blob)
    heading_tokens = _meaningful_tokens(heading)
    intro_tokens = _meaningful_tokens(intro)
    strong_overlap = len(q_tokens & (title_tokens | heading_tokens)) >= max(2, len(q_tokens) // 2)
    if strong_overlap:
        return False
    intro_overlap = q_tokens & intro_tokens
    return len(intro_overlap) < max(1, len(q_tokens) // 3)


def _needs_internal_link_support(item: ContentItem, index: _CatalogIndex) -> bool:
    link_count = len(item.existing_internal_links)
    return link_count <= LOW_INTERNAL_LINK_THRESHOLD


def _priority_score(
    row: GscQueryRow,
    match_score: float,
    status: str,
    *,
    max_position: float,
) -> float:
    score = 0.0
    score += min(row.impressions, 500) * 0.15
    if row.clicks == 0:
        score += 25.0
    elif row.clicks <= 2:
        score += 10.0
    else:
        score -= row.clicks * 2.0
    if 20 <= row.position <= 90:
        score += 20.0
    elif row.position < 20:
        score += 8.0
    elif row.position <= max_position:
        score += 5.0
    else:
        score -= 15.0
    score += min(match_score, 60.0) * 0.5
    if status == STATUS_NO_TARGET:
        score -= 20.0
    elif status == STATUS_OLD_URL:
        score += 5.0
    elif status == STATUS_CANNIBALIZATION:
        score += 12.0
    elif status == STATUS_CONTENT_OPTIMIZATION:
        score += 18.0
    elif status == STATUS_INTERNAL_LINKS:
        score += 14.0
    elif status == STATUS_CORRECT_PAGE:
        score += 10.0
    if row.impressions < 10:
        score -= 8.0
    return score


def _suggest_next_command(target_url: str, query: str) -> str:
    if not target_url:
        return ""
    q = query.replace('"', '\\"')
    return (
        f'python -m linkops.cli suggest --target-url "{target_url}" '
        f'--target-keyword "{q}" --max-suggestions 8'
    )


def _classify_opportunity(
    row: GscQueryRow,
    cache: GscCache,
    index: _CatalogIndex,
    match: _PageMatch,
) -> tuple[str, str, str, list[str]]:
    """Return status, reason, recommended_action, gsc_page_urls."""
    gsc_pages = [qp.page for qp in _gsc_pages_for_query(row.query, cache)]
    top_gsc = _top_gsc_page_for_query(row.query, cache)

    is_cannibal, cannibal_urls, cannibal_reason = _detect_cannibalization(row.query, cache, index)
    if is_cannibal:
        action = (
            "Consolidate search intent on one primary URL; add canonical/internal links; "
            "differentiate secondary pages or noindex weaker duplicates after editorial review."
        )
        return STATUS_CANNIBALIZATION, cannibal_reason, action, gsc_pages or cannibal_urls

    old_urls = [u for u in (gsc_pages or ([top_gsc] if top_gsc else [])) if _is_old_or_duplicate_url(u, index)]
    if old_urls:
        resolved, canon, in_cat = _resolve_gsc_page(old_urls[0], index)
        reason = f"GSC shows URL variant not in cache or duplicate slug: {old_urls[0]}"
        if in_cat and canon:
            reason += f"; canonical match: {canon}"
        action = "Verify redirects/canonical tags; request indexing for the canonical HTTPS URL in GSC."
        return STATUS_OLD_URL, reason, action, old_urls

    if not match.in_catalog or not match.item:
        reason = "No strong matching published page in WordPress cache for this query."
        action = "Create or retarget content; compare top GSC landing pages and align internal linking."
        return STATUS_NO_TARGET, reason, action, gsc_pages

    item = match.item
    gsc_supports = False
    if top_gsc:
        _, canon, in_cat = _resolve_gsc_page(top_gsc, index)
        if in_cat and canon == item.normalized_url():
            gsc_supports = True

    if _query_weak_in_content(row.query, item):
        reason = (
            f"Target page '{item.title}' exists but query phrase/tokens are weak in title, slug, "
            "headings, and intro."
        )
        action = (
            "Strengthen title/H1/intro with the query intent; add FAQ section; refresh meta description."
        )
        return STATUS_CONTENT_OPTIMIZATION, reason, action, gsc_pages

    if _needs_internal_link_support(item, index):
        reason = (
            f"Correct topical page identified ({item.title}) but only "
            f"{len(item.existing_internal_links)} internal links — weak internal support."
        )
        action = "Add contextual internal links from related cluster pages; run LinkOps suggest."
        return STATUS_INTERNAL_LINKS, reason, action, gsc_pages

    if gsc_supports or match.score >= 15.0:
        reason = (
            f"Query aligns with '{item.title}'"
            + (" and GSC shows the same page." if gsc_supports else " (content match).")
        )
        if row.clicks == 0:
            action = "Improve CTR (title/meta), confirm indexing, and monitor position 20-90 stretch."
        else:
            action = "Maintain rankings; optional content refresh if CTR is below expectations."
        return STATUS_CORRECT_PAGE, reason, action, gsc_pages

    reason = f"Possible match to '{item.title}' but GSC landing page differs or match score is moderate."
    action = "Confirm preferred URL in GSC; align on-page SEO and internal links to the target page."
    return STATUS_CORRECT_PAGE, reason, action, gsc_pages


def analyze_opportunities(
    cache: GscCache,
    catalog: list[ContentItem],
    *,
    min_impressions: int = 20,
    max_clicks: int = 0,
    max_position: float = 90.0,
) -> OpportunityReport:
    """Build ranked GSC opportunities from cache + WordPress catalog."""
    from datetime import datetime, timezone

    index = build_catalog_index(catalog)
    overrides = load_query_target_overrides()
    query_rows = list(cache.queries)
    if not query_rows and cache.query_pages:
        seen: set[str] = set()
        for qp in cache.query_pages:
            key = qp.query.lower().strip()
            if key in seen:
                continue
            seen.add(key)
            query_rows.append(
                GscQueryRow(
                    query=qp.query,
                    clicks=qp.clicks,
                    impressions=qp.impressions,
                    ctr=qp.ctr,
                    position=qp.position,
                )
            )

    candidates: list[Opportunity] = []
    for row in query_rows:
        if _is_brand_noise_query(row.query):
            continue
        if row.impressions < min_impressions:
            continue
        if row.clicks > max_clicks:
            continue
        if row.position > max_position:
            continue
        if row.impressions < MEANINGFUL_IMPRESSIONS_FLOOR:
            continue

        match = _best_catalog_match(row.query, index, overrides)
        status, reason, action, gsc_pages = _classify_opportunity(row, cache, index, match)
        target_url = match.url if match.in_catalog or match.override_used else ""
        target_title = match.title if match.in_catalog else ""
        if match.override_used and not match.in_catalog:
            reason = (
                f"{reason} Override target not found in content cache: {match.url}."
                if reason
                else f"Override target not found in content cache: {match.url}."
            )
        if not target_url and gsc_pages:
            item, canon, in_cat = _resolve_gsc_page(gsc_pages[0], index)
            if in_cat:
                target_url = canon
                target_title = item.title if item else ""

        needs_links = bool(
            match.item and _needs_internal_link_support(match.item, index)
        )
        is_cannibal = status == STATUS_CANNIBALIZATION
        is_old = status == STATUS_OLD_URL
        is_content_weak = bool(
            match.item and _query_weak_in_content(row.query, match.item)
        )
        action_type = classify_action_type(
            status=status,
            clicks=row.clicks,
            impressions=row.impressions,
            position=row.position,
            has_target=bool(target_url),
            needs_internal_links=needs_links,
            is_cannibal=is_cannibal,
            is_old_url=is_old,
            is_content_weak=is_content_weak,
        )

        pri_score = _priority_score(row, match.score, status, max_position=max_position)
        if match.confidence == CONFIDENCE_HIGH:
            pri_score += 5.0
        elif match.confidence == CONFIDENCE_LOW:
            pri_score -= 5.0

        indexing = [target_url] if target_url else []
        for u in gsc_pages[:3]:
            item, canon, in_cat = _resolve_gsc_page(u, index)
            if in_cat and canon and canon not in indexing:
                indexing.append(canon)

        candidates.append(
            Opportunity(
                priority_rank=0,
                query=row.query,
                clicks=row.clicks,
                impressions=row.impressions,
                ctr=row.ctr,
                position=row.position,
                target_url=target_url,
                target_title=target_title,
                status=status,
                reason=reason,
                recommended_action=action,
                next_command=_suggest_next_command(target_url, row.query),
                request_indexing_urls=indexing,
                query_intent=match.query_intent,
                page_type=match.page_type,
                confidence=match.confidence,
                action_type=action_type,
                override_used=match.override_used,
                target_selection_reason=match.target_selection_reason,
                priority_score=pri_score,
                gsc_pages=gsc_pages,
            )
        )

    candidates.sort(key=lambda o: (-o.priority_score, -o.impressions, o.position))
    for i, opp in enumerate(candidates, start=1):
        opp.priority_rank = i

    summary = {
        "total_opportunities": len(candidates),
        STATUS_CORRECT_PAGE: sum(1 for o in candidates if o.status == STATUS_CORRECT_PAGE),
        STATUS_CANNIBALIZATION: sum(1 for o in candidates if o.status == STATUS_CANNIBALIZATION),
        STATUS_OLD_URL: sum(1 for o in candidates if o.status == STATUS_OLD_URL),
        STATUS_NO_TARGET: sum(1 for o in candidates if o.status == STATUS_NO_TARGET),
        STATUS_CONTENT_OPTIMIZATION: sum(
            1 for o in candidates if o.status == STATUS_CONTENT_OPTIMIZATION
        ),
        STATUS_INTERNAL_LINKS: sum(1 for o in candidates if o.status == STATUS_INTERNAL_LINKS),
    }
    top_actions = [
        f"{o.query} -> {o.recommended_action[:80]}"
        for o in candidates[:10]
    ]

    return OpportunityReport(
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        opportunities=candidates,
        total_queries_analyzed=len(query_rows),
        filters={
            "min_impressions": min_impressions,
            "max_clicks": max_clicks,
            "max_position": max_position,
        },
        summary=summary,
        top_actions=top_actions,
    )
