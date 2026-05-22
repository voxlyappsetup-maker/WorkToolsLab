"""Group GSC opportunities by target page and produce next-action decision reports."""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timezone

from linkops.content_model import ContentItem
from linkops.gsc_intent import (
    ACTION_CANNIBALIZATION,
    ACTION_CONTENT_OPTIMIZATION,
    ACTION_INTERNAL_LINKS,
    ACTION_MONITOR,
    ACTION_NEW_ARTICLE,
    ACTION_OLD_URL,
    ACTION_TITLE_META_CTR,
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    CONFIDENCE_MEDIUM,
    INTENT_BROAD_BEST,
    INTENT_INFORMATIONAL,
    INTENT_UNKNOWN,
    detect_query_intent,
)
from linkops.gsc_model import (
    GscCache,
    Opportunity,
    STATUS_NO_TARGET,
)
from linkops.next_actions_model import (
    NO_TARGET_IGNORE,
    NO_TARGET_MANUAL,
    NO_TARGET_NEW_ARTICLE,
    NO_TARGET_RETARGET,
    NextActionsReport,
    NoTargetQuery,
    PageCluster,
    PartialPageMatch,
)
from linkops.opportunity_engine import (
    _is_brand_noise_query,
    _score_page_for_query,
    analyze_opportunities,
    build_catalog_index,
)
from linkops.worklog import HANDLED_STATUSES, Worklog, canonical_worklog_url, load_worklog

_ACTION_PRIORITY = {
    ACTION_CANNIBALIZATION: 100,
    ACTION_OLD_URL: 90,
    ACTION_CONTENT_OPTIMIZATION: 80,
    ACTION_INTERNAL_LINKS: 70,
    ACTION_TITLE_META_CTR: 60,
    ACTION_NEW_ARTICLE: 50,
    ACTION_MONITOR: 10,
}

_CONFIDENCE_RANK = {CONFIDENCE_HIGH: 3, CONFIDENCE_MEDIUM: 2, CONFIDENCE_LOW: 1}

_VAGUE_QUERY_RE = re.compile(
    r"^(?:small\s+business(?:es)?|small\s+teams?|business\s+teams?|remote\s+teams?|"
    r"teams?|business(?:es)?|work\s+tools?)$",
    re.IGNORECASE,
)

_CATEGORY_TOKENS = frozenset(
    {
        "management",
        "communication",
        "productivity",
        "workflow",
        "task",
        "project",
        "software",
        "tools",
        "collaboration",
        "remote",
        "freelance",
    }
)


def weighted_average_position(opportunities: list[Opportunity]) -> float:
    """Impression-weighted mean GSC position."""
    total_imp = sum(o.impressions for o in opportunities)
    if total_imp <= 0:
        return 0.0
    return sum(o.position * o.impressions for o in opportunities) / total_imp


def _best_confidence(opportunities: list[Opportunity]) -> str:
    best = CONFIDENCE_LOW
    best_rank = 0
    for o in opportunities:
        rank = _CONFIDENCE_RANK.get(o.confidence, 1)
        if rank > best_rank:
            best_rank = rank
            best = o.confidence
    return best


def _pick_cluster_action(action_types: list[str]) -> str:
    if not action_types:
        return ACTION_MONITOR
    return max(action_types, key=lambda a: _ACTION_PRIORITY.get(a, 0))


def _action_to_recommendation(action_type: str, strongest_query: str, target_url: str) -> str:
    q = strongest_query.replace('"', '\\"')
    url = target_url
    if action_type == ACTION_CONTENT_OPTIMIZATION:
        return f"Run content optimization and patch for '{strongest_query}' on {url}."
    if action_type == ACTION_INTERNAL_LINKS:
        return f"Build internal links to {url}; start with suggest for '{strongest_query}'."
    if action_type == ACTION_TITLE_META_CTR:
        return (
            f"Improve title/meta CTR for {url} (query '{strongest_query}', "
            "position 8-20, zero clicks)."
        )
    if action_type == ACTION_CANNIBALIZATION:
        return (
            f"Review cannibalization across URLs ranking for '{strongest_query}'; "
            "consolidate intent."
        )
    if action_type == ACTION_OLD_URL:
        return f"Verify canonical/redirects for {url}; request indexing for the HTTPS canonical URL."
    if action_type == ACTION_MONITOR:
        return f"Monitor GSC for {url}; no urgent on-page work for '{strongest_query}'."
    return f"Review {url} for '{strongest_query}'."


def _cluster_commands(action_type: str, target_url: str, strongest_query: str) -> list[str]:
    q = strongest_query.replace('"', '\\"')
    url = target_url
    cmds: list[str] = []
    if action_type in (ACTION_CONTENT_OPTIMIZATION, ACTION_TITLE_META_CTR):
        cmds.append(
            f'python -m linkops.cli optimize --target-url "{url}" --target-keyword "{q}"'
        )
        cmds.append(
            f'python -m linkops.cli patch --target-url "{url}" --target-keyword "{q}"'
        )
    if action_type == ACTION_INTERNAL_LINKS:
        cmds.append(
            f'python -m linkops.cli suggest --target-url "{url}" --target-keyword "{q}" --max-suggestions 8'
        )
    if action_type == ACTION_CANNIBALIZATION:
        cmds.append(f'python -m linkops.cli optimize --target-url "{url}" --target-keyword "{q}"')
    if not cmds and url:
        cmds.append(
            f'python -m linkops.cli suggest --target-url "{url}" --target-keyword "{q}" --max-suggestions 8'
        )
    return cmds


def _cluster_priority_score(opportunities: list[Opportunity]) -> float:
    return sum(o.priority_score for o in opportunities)


def _build_page_cluster(
    target_url: str,
    opps: list[Opportunity],
    worklog: Worklog,
) -> PageCluster:
    opps_sorted = sorted(opps, key=lambda o: (-o.impressions, -o.priority_score))
    strongest = max(opps, key=lambda o: (o.impressions, o.priority_score))
    action_types = list(dict.fromkeys(o.action_type for o in opps))
    statuses = list(dict.fromkeys(o.status for o in opps))
    primary_action = _pick_cluster_action(action_types)
    indexing: list[str] = []
    for o in opps:
        for u in o.request_indexing_urls:
            if u and u not in indexing:
                indexing.append(u)
    entry = worklog.entry_for_url(target_url)
    return PageCluster(
        target_url=target_url,
        target_title=strongest.target_title,
        total_impressions=sum(o.impressions for o in opps),
        total_clicks=sum(o.clicks for o in opps),
        weighted_avg_position=round(weighted_average_position(opps), 2),
        queries=[o.query for o in opps_sorted],
        strongest_query=strongest.query,
        action_types=action_types,
        statuses=statuses,
        confidence=_best_confidence(opps),
        recommended_next_action=_action_to_recommendation(
            primary_action, strongest.query, target_url
        ),
        next_commands=_cluster_commands(primary_action, target_url, strongest.query),
        request_indexing_urls=indexing,
        worklog_status=entry.status if entry else "",
        worklog_note=entry.note if entry else "",
        cluster_priority_score=_cluster_priority_score(opps),
        query_count=len(opps),
    )


def _is_vague_query(query: str) -> bool:
    q = query.strip().lower()
    if _VAGUE_QUERY_RE.match(q):
        return True
    tokens = set(re.findall(r"[a-z0-9]+", q))
    if len(tokens) <= 2 and not (tokens & _CATEGORY_TOKENS):
        return True
    if len(tokens) <= 3 and tokens <= {"small", "business", "teams"} | {"small", "business", "team"}:
        return True
    return False


def _partial_matches_for_query(
    query: str,
    catalog: list[ContentItem],
    *,
    limit: int = 5,
) -> list[PartialPageMatch]:
    index = build_catalog_index(catalog)
    scored: list[tuple[float, ContentItem, str]] = []
    for item in index.items:
        topical = _score_page_for_query(query, item)
        if topical < 8.0:
            continue
        scored.append((topical, item, f"topical score {topical:.0f}"))
    scored.sort(key=lambda x: -x[0])
    out: list[PartialPageMatch] = []
    for score, item, reason in scored[:limit]:
        out.append(
            PartialPageMatch(
                url=item.url,
                title=item.title,
                match_score=score,
                reason=reason,
            )
        )
    return out


def classify_no_target_recommendation(
    query: str,
    *,
    impressions: int,
    position: float,
    partial_matches: list[PartialPageMatch],
) -> tuple[str, str, bool]:
    """Return recommendation code, rationale, and whether a new article looks worthwhile."""
    if _is_brand_noise_query(query):
        return (
            NO_TARGET_IGNORE,
            "Brand or navigational noise query with little editorial value.",
            False,
        )

    intent = detect_query_intent(query)

    if _is_vague_query(query):
        return (
            NO_TARGET_MANUAL,
            "Broad or vague query (e.g. small business teams) — needs manual editorial review; "
            "do not auto-create a new article.",
            False,
        )

    if partial_matches and partial_matches[0].match_score >= 25.0:
        best = partial_matches[0]
        return (
            NO_TARGET_RETARGET,
            f"Existing page '{best.title}' partially matches (score {best.match_score:.0f}). "
            "Consider retargeting or strengthening that page before creating new content.",
            False,
        )

    if intent == INTENT_INFORMATIONAL and impressions < 30:
        return (
            NO_TARGET_MANUAL,
            "Informational query with limited impressions — review whether a dedicated page is justified.",
            False,
        )

    if intent == INTENT_BROAD_BEST and impressions >= 40 and not partial_matches:
        return (
            NO_TARGET_NEW_ARTICLE,
            "Commercial-style query with meaningful impressions and no strong catalog match — "
            "may warrant a new roundup or guide after editorial review.",
            True,
        )

    if impressions < 15:
        return (
            NO_TARGET_IGNORE,
            "Low impressions — deprioritize unless strategy changes.",
            False,
        )

    if partial_matches:
        return (
            NO_TARGET_MANUAL,
            "Weak partial matches only — manual decision between retargeting and new content.",
            False,
        )

    return (
        NO_TARGET_MANUAL,
        "No strong target page; review GSC landing pages and topical fit before acting.",
        False,
    )


def _build_no_target_query(opp: Opportunity, catalog: list[ContentItem]) -> NoTargetQuery:
    partials = _partial_matches_for_query(opp.query, catalog)
    rec, rationale, worth = classify_no_target_recommendation(
        opp.query,
        impressions=opp.impressions,
        position=opp.position,
        partial_matches=partials,
    )
    return NoTargetQuery(
        query=opp.query,
        clicks=opp.clicks,
        impressions=opp.impressions,
        ctr=opp.ctr,
        position=opp.position,
        query_intent=opp.query_intent,
        recommendation=rec,
        rationale=rationale,
        partial_matches=partials,
        gsc_pages=list(opp.gsc_pages),
        worth_new_article=worth,
    )


def _partition_clusters(
    clusters: list[PageCluster],
    *,
    exclude_done: bool,
    include_monitor_only: bool,
) -> tuple[list[PageCluster], list[PageCluster]]:
    unresolved: list[PageCluster] = []
    handled: list[PageCluster] = []
    for cluster in clusters:
        status = cluster.worklog_status
        if status == "done" and exclude_done:
            handled.append(cluster)
            continue
        if status in HANDLED_STATUSES or status == "done":
            if status == "monitor_only" and include_monitor_only:
                unresolved.append(cluster)
            else:
                handled.append(cluster)
            continue
        if status == "needs_review":
            unresolved.append(cluster)
            continue
        unresolved.append(cluster)
    unresolved.sort(key=lambda c: (-c.cluster_priority_score, -c.total_impressions))
    handled.sort(key=lambda c: (-c.total_impressions,))
    return unresolved, handled


def build_next_actions_report(
    cache: GscCache,
    catalog: list[ContentItem],
    worklog: Worklog | None = None,
    *,
    min_impressions: int = 20,
    max_clicks: int = 0,
    max_position: float = 90.0,
    exclude_done: bool = False,
    include_monitor_only: bool = False,
) -> NextActionsReport:
    """Build grouped next-actions report from GSC cache and WordPress catalog."""
    worklog = worklog or load_worklog()
    opp_report = analyze_opportunities(
        cache,
        catalog,
        min_impressions=min_impressions,
        max_clicks=max_clicks,
        max_position=max_position,
    )

    by_url: dict[str, list[Opportunity]] = defaultdict(list)
    no_target_opps: list[Opportunity] = []

    for opp in opp_report.opportunities:
        if opp.status == STATUS_NO_TARGET or not opp.target_url:
            no_target_opps.append(opp)
            continue
        canon = canonical_worklog_url(opp.target_url)
        if not canon:
            continue
        by_url[canon].append(opp)

    clusters = [
        _build_page_cluster(url, opps, worklog)
        for url, opps in by_url.items()
    ]
    unresolved, handled = _partition_clusters(
        clusters,
        exclude_done=exclude_done,
        include_monitor_only=include_monitor_only,
    )

    no_target_queries = [_build_no_target_query(o, catalog) for o in no_target_opps]
    no_target_queries.sort(key=lambda n: (-n.impressions, n.position))

    indexing: list[str] = []
    for c in unresolved:
        for u in c.request_indexing_urls:
            if u not in indexing:
                indexing.append(u)

    suggested: list[str] = [
        "python -m linkops.cli fetch",
        "python -m linkops.cli gsc-import --queries-csv exports/gsc_queries.csv --pages-csv exports/gsc_pages.csv",
        f"python -m linkops.cli next-actions --min-impressions {min_impressions} --max-position {max_position}",
    ]
    if unresolved:
        top = unresolved[0]
        for cmd in top.next_commands[:2]:
            if cmd not in suggested:
                suggested.append(cmd)

    from linkops.config import WORKLOG_PATH

    worklog_matched = sum(
        1
        for c in clusters
        if c.worklog_status
    )
    summary_parts = [
        f"{len(unresolved)} unresolved page cluster(s) to work on next.",
        f"{len(handled)} page cluster(s) already marked handled or monitor-only in worklog "
        f"({worklog_matched} cluster(s) matched worklog entries).",
        f"{len(no_target_queries)} no-target query(ies) need editorial decisions.",
    ]
    if unresolved:
        top = unresolved[0]
        summary_parts.append(
            f"Top priority: {top.target_url} ({top.total_impressions} impressions, "
            f"strongest query '{top.strongest_query}')."
        )

    return NextActionsReport(
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        gsc_imported_at=cache.imported_at,
        filters={
            "min_impressions": min_impressions,
            "max_clicks": max_clicks,
            "max_position": max_position,
            "exclude_done": exclude_done,
            "include_monitor_only": include_monitor_only,
        },
        executive_summary=" ".join(summary_parts),
        unresolved_clusters=unresolved,
        handled_clusters=handled,
        no_target_queries=no_target_queries,
        suggested_commands=suggested,
        request_indexing_urls=indexing,
        gsc_lag_note=(
            "GSC CSV exports typically lag 2–3 days behind live Search Console. "
            "Re-import after meaningful on-page changes, then request indexing for updated URLs."
        ),
        worklog_path=str(WORKLOG_PATH),
        worklog_loaded=WORKLOG_PATH.exists(),
        total_queries_in_report=sum(c.query_count for c in clusters) + len(no_target_queries),
        total_page_clusters=len(clusters),
    )
