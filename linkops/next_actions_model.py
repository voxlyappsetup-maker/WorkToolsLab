"""Data models for grouped next-actions decision reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

# No-target deep-dive recommendations
NO_TARGET_NEW_ARTICLE = "new_article_needed"
NO_TARGET_RETARGET = "retarget_existing_page"
NO_TARGET_IGNORE = "ignore_low_intent"
NO_TARGET_MANUAL = "needs_manual_review"


@dataclass
class PartialPageMatch:
    url: str
    title: str
    match_score: float
    reason: str


@dataclass
class NoTargetQuery:
    query: str
    clicks: int
    impressions: int
    ctr: float
    position: float
    query_intent: str
    recommendation: str
    rationale: str
    partial_matches: list[PartialPageMatch] = field(default_factory=list)
    gsc_pages: list[str] = field(default_factory=list)
    worth_new_article: bool = False


@dataclass
class PageCluster:
    target_url: str
    target_title: str
    total_impressions: int
    total_clicks: int
    weighted_avg_position: float
    queries: list[str]
    strongest_query: str
    action_types: list[str]
    statuses: list[str]
    confidence: str
    recommended_next_action: str
    next_commands: list[str]
    request_indexing_urls: list[str]
    worklog_status: str = ""
    worklog_note: str = ""
    cluster_priority_score: float = 0.0
    query_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NextActionsReport:
    generated_at: str
    gsc_imported_at: str
    filters: dict[str, Any]
    executive_summary: str
    unresolved_clusters: list[PageCluster]
    handled_clusters: list[PageCluster]
    no_target_queries: list[NoTargetQuery]
    suggested_commands: list[str]
    request_indexing_urls: list[str]
    gsc_lag_note: str
    worklog_path: str
    worklog_loaded: bool
    total_queries_in_report: int = 0
    total_page_clusters: int = 0
