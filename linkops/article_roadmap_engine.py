"""Build new-article opportunity roadmap from GSC queries and WordPress catalog."""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timezone

from linkops.article_roadmap_model import (
    PRIORITY_HIGH,
    PRIORITY_LOW,
    PRIORITY_MANUAL,
    PRIORITY_MEDIUM,
    ARTICLE_COMPARISON,
    ARTICLE_CONCEPT_COMPARISON,
    ARTICLE_GLOSSARY,
    ARTICLE_GUIDE,
    ARTICLE_REVIEW,
    ARTICLE_ROUNDUP,
    ArticleCandidate,
    ArticleRoadmapReport,
    ExcludedQuery,
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
    INTENT_UNKNOWN,
    KNOWN_BRAND_TERMS,
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
    build_catalog_index,
)
from linkops.patch_relevance_guardrails import (
    is_concept_comparison,
    is_software_comparison,
    is_teamwork_vs_asana_query,
    parse_comparison_parts,
)
from linkops.config import WORKLOG_PATH
from linkops.html_tools import normalize_internal_url
from linkops.worklog import Worklog, load_worklog

def _weighted_avg_position_rows(rows: list[GscQueryRow]) -> float:
    total_imp = sum(r.impressions for r in rows)
    if total_imp <= 0:
        return 0.0
    return sum(r.position * r.impressions for r in rows) / total_imp


_AI_TOPIC_RE = re.compile(r"\b(ai|artificial intelligence|generative)\b", re.IGNORECASE)
_FREELANCER_RE = re.compile(r"\bfreelanc", re.IGNORECASE)
_SLUG_SAFE_RE = re.compile(r"[^a-z0-9]+")


def _slugify(text: str) -> str:
    raw = text.lower().strip()
    raw = raw.replace(".com", "")
    slug = _SLUG_SAFE_RE.sub("-", raw).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug[:80].rstrip("-")


def _normalize_key(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def _detect_roadmap_topic(keyword: str, article_type: str) -> str:
    kw = keyword.lower()
    if _AI_TOPIC_RE.search(kw):
        return "AI/productivity"
    if _FREELANCER_RE.search(kw):
        return "freelancer/client_work"
    if "video meeting" in kw or "video-meeting" in kw:
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


def _catalog_has_roundup_for_query(query: str, catalog: list[ContentItem], *, min_score: float = 40.0) -> bool:
    for item in catalog:
        if detect_gsc_page_type(item) != "roundup_best_tools":
            continue
        if _score_page_for_query(query, item) >= min_score:
            return True
    return False


def _catalog_has_guide_for_query(query: str, catalog: list[ContentItem], *, min_score: float = 35.0) -> bool:
    for item in catalog:
        if detect_gsc_page_type(item) not in ("guide", "roundup_best_tools"):
            continue
        if "how-to" in item.slug or item.title.lower().startswith("how to"):
            if _score_page_for_query(query, item) >= min_score:
                return True
    return False


def _is_already_covered(
    query: str,
    catalog: list[ContentItem],
    opp: Opportunity | None,
) -> tuple[bool, str]:
    intent = detect_query_intent(query)
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
            item = next(
                (i for i in catalog if i.normalized_url() == target_norm),
                None,
            )
            if item and detect_gsc_page_type(item) == "comparison":
                return True, "High-confidence comparison target already in catalog."
    if intent == INTENT_REVIEW:
        brands = set(re.findall(r"[a-z0-9]+", query.lower())) & KNOWN_BRAND_TERMS
        for brand in brands:
            if _catalog_has_brand_review(brand, catalog):
                return True, f"Review page already exists for {capitalize_brand(brand)}."
        if opp and opp.target_url and opp.confidence in (CONFIDENCE_HIGH,):
            return True, "Strong review page match already exists."
    if intent == INTENT_BROAD_BEST and _catalog_has_roundup_for_query(query, catalog):
        return True, "Roundup page already covers this commercial query."
    if intent == INTENT_HOW_TO and _catalog_has_guide_for_query(query, catalog):
        return True, "Guide page already covers this how-to query."
    if opp and opp.target_url and opp.confidence == CONFIDENCE_HIGH:
        item = next(
            (i for i in catalog if i.normalized_url() == opp.target_url.rstrip("/").replace("http://", "https://")),
            None,
        )
        if item:
            alignment = compute_intent_alignment(intent, detect_gsc_page_type(item))
            if alignment != ALIGNMENT_MISALIGNED and _score_page_for_query(query, item) >= 45:
                return True, f"Existing page '{item.title}' strongly covers this query."
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
) -> float:
    if vague:
        return 5.0
    total_imp = sum(r.impressions for r in rows)
    total_clicks = sum(r.clicks for r in rows)
    wpos = _weighted_avg_position_rows(rows)
    score = 0.0
    score += min(total_imp, 500) * 0.12
    score += _commercial_relevance(rows[0].query, query_intent)
    score += gap_severity
    score += min(related_count, 5) * 4.0
    if total_clicks == 0 and total_imp >= 15:
        score += 10.0
    if 20 <= wpos <= 90:
        score += 8.0
    elif wpos < 20:
        score += 4.0
    else:
        score -= 6.0
    if article_type == ARTICLE_COMPARISON:
        score += 12.0
    if article_type == ARTICLE_REVIEW:
        score += 10.0
    if article_type == ARTICLE_ROUNDUP:
        score += 8.0
    if cannibalization_risk == "medium":
        score -= 8.0
    elif cannibalization_risk == "high":
        score -= 18.0
    if total_imp < 10:
        score -= 15.0
    return max(score, 0.0)


def _priority_label(score: float, *, force_manual: bool) -> str:
    if force_manual:
        return PRIORITY_MANUAL
    if score >= 70:
        return PRIORITY_HIGH
    if score >= 40:
        return PRIORITY_MEDIUM
    return PRIORITY_LOW


def _cannibalization_risk(query: str, catalog: list[ContentItem], partials: list) -> str:
    if len(partials) >= 3:
        return "medium"
    top = partials[0].match_score if partials else 0
    if top >= 30:
        return "medium"
    if top >= 20:
        return "low"
    return "low"


def _candidate_group_key(article_type: str, primary_keyword: str) -> str:
    return f"{article_type}::{_normalize_key(primary_keyword)}"


def _build_candidate_from_rows(
    rows: list[GscQueryRow],
    *,
    catalog: list[ContentItem],
    gap_reason: str,
    force_manual: bool = False,
    editorial_notes: list[str] | None = None,
) -> ArticleCandidate:
    primary = rows[0].query
    intent = detect_query_intent(primary)
    article_type = _infer_article_type(primary, intent)
    topic = _detect_roadmap_topic(primary, article_type)

    if article_type == ARTICLE_COMPARISON:
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
    related_urls = [p.url for p in partials[:4]]
    links_from = related_urls[:3]
    links_to = related_urls[3:6] if len(related_urls) > 3 else []

    vague = _is_vague_query(primary) or force_manual
    cannibal = _cannibalization_risk(primary, catalog, partials)
    gap_severity = 15.0 if "no strong matching" in gap_reason.lower() else 10.0
    if "mismatch" in gap_reason.lower() or "misroute" in gap_reason.lower():
        gap_severity = 22.0
    if is_teamwork_vs_asana_query(primary):
        gap_severity = 25.0
        force_manual = False
        editorial_notes = editorial_notes or []
        editorial_notes.append(
            "Branded comparison for Teamwork.com vs Asana — not Asana vs ClickUp."
        )

    score = _priority_score(
        rows,
        article_type=article_type,
        query_intent=intent,
        gap_severity=gap_severity,
        related_count=len(rows),
        vague=vague,
        cannibalization_risk=cannibal,
    )
    priority = _priority_label(score, force_manual=vague)

    secondary = [r.query for r in rows[1:]]
    notes = list(editorial_notes or [])
    if vague:
        notes.append("Vague or broad query — confirm search intent before writing.")
    if cannibal == "medium":
        notes.append("Partial overlap with existing pages — differentiate angle to avoid cannibalization.")

    next_step = (
        f"Draft new {article_type.replace('_', ' ')} article: {title}. "
        f"Primary keyword: {primary}."
    )
    if priority == PRIORITY_MANUAL:
        next_step = f"Manual editorial review before drafting: {primary}."

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
        related_query_count=len(rows),
        target_gap_reason=gap_reason,
        cannibalization_risk=cannibal,
        existing_related_pages=related_urls,
        suggested_internal_links_from=links_from,
        suggested_internal_links_to=links_to,
        editorial_notes=notes,
        recommended_next_step=next_step,
    )


def _should_consider_for_roadmap(
    opp: Opportunity,
    *,
    min_impressions: int,
    exclude_existing_covered: bool,
    catalog: list[ContentItem],
) -> tuple[bool, str, str]:
    """Return (include, exclusion_category, exclusion_reason)."""
    if _is_brand_noise_query(opp.query):
        return False, "brand_noise", "Brand or navigational noise query."
    if opp.impressions < min_impressions:
        return False, "low_impressions", f"Below min impressions ({min_impressions})."
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
    if opp.clicks == 0 and opp.impressions >= min_impressions and 20 <= opp.position <= 90:
        if opp.confidence != CONFIDENCE_HIGH:
            return True, "", ""
    intent = opp.query_intent or detect_query_intent(opp.query)
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
        article_type = _infer_article_type(opp.query, opp.query_intent or detect_query_intent(opp.query))
        primary = opp.query
        if article_type == ARTICLE_COMPARISON:
            parts = parse_comparison_parts(opp.query) or _two_way_vs_tools(opp.query)
            if parts:
                primary = f"{parts[0]} vs {parts[1]}"
            if is_teamwork_vs_asana_query(opp.query):
                primary = "teamwork vs asana"
        key = _candidate_group_key(article_type, primary)
        groups[key].append(row)

    return groups, excluded


def _partition_candidates(
    candidates: list[ArticleCandidate],
    *,
    include_low: bool,
    include_manual: bool,
    max_candidates: int,
) -> tuple[list[ArticleCandidate], list[ArticleCandidate], list[ArticleCandidate], list[ArticleCandidate]]:
    high: list[ArticleCandidate] = []
    medium: list[ArticleCandidate] = []
    low: list[ArticleCandidate] = []
    manual: list[ArticleCandidate] = []
    for c in sorted(candidates, key=lambda x: (-x.priority_score, -x.total_impressions)):
        if c.priority == PRIORITY_MANUAL:
            if include_manual:
                manual.append(c)
            continue
        if c.priority == PRIORITY_HIGH:
            high.append(c)
        elif c.priority == PRIORITY_MEDIUM:
            medium.append(c)
        elif include_low:
            low.append(c)
    combined = high + medium + (low if include_low else []) + (manual if include_manual else [])
    if len(combined) > max_candidates:
        keep = set()
        trimmed: list[ArticleCandidate] = []
        for bucket in (high, medium, low, manual):
            for c in bucket:
                if len(trimmed) >= max_candidates:
                    break
                if id(c) not in keep:
                    trimmed.append(c)
                    keep.add(id(c))
        high = [c for c in trimmed if c.priority == PRIORITY_HIGH]
        medium = [c for c in trimmed if c.priority == PRIORITY_MEDIUM]
        low = [c for c in trimmed if c.priority == PRIORITY_LOW]
        manual = [c for c in trimmed if c.priority == PRIORITY_MANUAL]
    return high, medium, low, manual


def _build_calendar(
    high: list[ArticleCandidate],
    medium: list[ArticleCandidate],
    low: list[ArticleCandidate],
) -> tuple[list[str], list[str], list[str]]:
    week1 = [c.suggested_title for c in high[:3]]
    week2 = [c.suggested_title for c in high[3:5] + medium[:2]]
    later = [c.suggested_title for c in medium[2:] + low[:5]]
    return week1, week2, later


def _suggested_commands(candidates: list[ArticleCandidate]) -> list[str]:
    cmds: list[str] = []
    for c in candidates[:8]:
        if not c.suggested_slug:
            continue
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

    candidates: list[ArticleCandidate] = []
    opp_by_query = {o.query.strip().lower(): o for o in opp_report.opportunities}
    for _key, rows in groups.items():
        rows.sort(key=lambda r: (-r.impressions, r.position))
        primary = rows[0].query
        opp = opp_by_query.get(primary.strip().lower())
        gap = _gap_reason_for_opportunity(opp, catalog) if opp else "GSC query gap with no strong catalog page."
        force_manual = _is_vague_query(primary)
        candidates.append(
            _build_candidate_from_rows(
                rows,
                catalog=catalog,
                gap_reason=gap,
                force_manual=force_manual,
            )
        )

    high, medium, low, manual = _partition_candidates(
        candidates,
        include_low=include_low_priority,
        include_manual=include_manual_review,
        max_candidates=max_candidates,
    )
    week1, week2, later = _build_calendar(high, medium, low)
    all_ranked = sorted(
        [c for c in candidates if c.priority != PRIORITY_MANUAL],
        key=lambda c: (-c.priority_score, -c.total_impressions),
    )
    top5 = (all_ranked + sorted(manual, key=lambda c: -c.total_impressions))[:5]
    top_lines = [f"{i}. {c.suggested_title} ({c.priority}, score {c.priority_score:.0f})" for i, c in enumerate(top5, 1)]

    summary = (
        f"Analyzed {opp_report.total_queries_analyzed} GSC queries; "
        f"{len(candidates)} new-article candidate(s) identified. "
        f"High: {len(high)}, medium: {len(medium)}, low: {len(low)}, "
        f"manual review: {len(manual)}, excluded: {len(excluded)}."
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
        executive_summary=summary + ("\nTop candidates:\n" + "\n".join(top_lines) if top_lines else ""),
        high_priority=high,
        medium_priority=medium,
        low_priority=low,
        manual_review=manual,
        excluded_queries=excluded,
        calendar_week1=week1,
        calendar_week2=week2,
        calendar_later=later,
        suggested_commands=_suggested_commands(high + medium),
    )
