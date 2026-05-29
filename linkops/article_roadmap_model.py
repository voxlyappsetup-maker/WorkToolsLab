"""Data models for new-article opportunity roadmap reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

PRIORITY_HIGH = "high"
PRIORITY_MEDIUM = "medium"
PRIORITY_LOW = "low"
PRIORITY_MANUAL = "manual_review"

ARTICLE_ROUNDUP = "roundup"
ARTICLE_COMPARISON = "comparison"
ARTICLE_CONCEPT_COMPARISON = "concept_comparison"
ARTICLE_REVIEW = "review"
ARTICLE_GUIDE = "guide"
ARTICLE_GLOSSARY = "glossary"
ARTICLE_LANDING = "landing"

ACTION_CREATE_NEW_ARTICLE = "create_new_article"
ACTION_UPDATE_EXISTING_PAGE = "update_existing_page"
ACTION_EXPAND_EXISTING_SECTION = "expand_existing_section"
ACTION_MONITOR_ONLY = "monitor_only"
ACTION_MANUAL_REVIEW = "manual_review"
ACTION_SKIP_ALREADY_COVERED = "skip_already_covered"


@dataclass
class ArticleCandidate:
    suggested_title: str
    suggested_slug: str
    article_type: str
    primary_keyword: str
    secondary_queries: list[str]
    topic: str
    priority: str
    priority_score: float
    total_impressions: int
    total_clicks: int
    weighted_avg_position: float
    related_query_count: int
    target_gap_reason: str
    cannibalization_risk: str
    existing_related_pages: list[str]
    suggested_internal_links_from: list[str]
    suggested_internal_links_to: list[str]
    editorial_notes: list[str]
    recommended_next_step: str
    action_type: str = ACTION_CREATE_NEW_ARTICLE
    recommended_existing_url: str = ""
    recommended_existing_title: str = ""
    update_reason: str = ""
    content_gap_to_add: str = ""
    query_group_label: str = ""
    merged_queries: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "suggested_title": self.suggested_title,
            "suggested_slug": self.suggested_slug,
            "article_type": self.article_type,
            "primary_keyword": self.primary_keyword,
            "secondary_queries": "; ".join(self.secondary_queries),
            "topic": self.topic,
            "priority": self.priority,
            "priority_score": round(self.priority_score, 2),
            "total_impressions": self.total_impressions,
            "total_clicks": self.total_clicks,
            "weighted_avg_position": round(self.weighted_avg_position, 2),
            "related_query_count": self.related_query_count,
            "target_gap_reason": self.target_gap_reason,
            "cannibalization_risk": self.cannibalization_risk,
            "existing_related_pages": "; ".join(self.existing_related_pages),
            "suggested_internal_links_from": "; ".join(self.suggested_internal_links_from),
            "suggested_internal_links_to": "; ".join(self.suggested_internal_links_to),
            "editorial_notes": "; ".join(self.editorial_notes),
            "recommended_next_step": self.recommended_next_step,
            "action_type": self.action_type,
            "recommended_existing_url": self.recommended_existing_url,
            "recommended_existing_title": self.recommended_existing_title,
            "update_reason": self.update_reason,
            "content_gap_to_add": self.content_gap_to_add,
            "query_group_label": self.query_group_label,
            "merged_queries": "; ".join(self.merged_queries),
        }


@dataclass
class ConsolidatedQueryGroup:
    query_group_label: str
    merged_queries: list[str]
    action_type: str
    primary_keyword: str
    suggested_title: str
    recommended_existing_url: str = ""
    total_impressions: int = 0


@dataclass
class ExcludedQuery:
    query: str
    impressions: int
    position: float
    exclusion_reason: str
    category: str  # already_covered | vague | low_impressions | unclear_intent | brand_noise


@dataclass
class ArticleRoadmapReport:
    generated_at: str
    gsc_imported_at: str
    worklog_path: str
    worklog_loaded: bool
    filters: dict[str, Any]
    total_queries_analyzed: int
    executive_summary: str
    displayed_roadmap_counts: dict[str, int] = field(default_factory=dict)
    create_new_high: list[ArticleCandidate] = field(default_factory=list)
    create_new_medium: list[ArticleCandidate] = field(default_factory=list)
    create_new_low: list[ArticleCandidate] = field(default_factory=list)
    update_existing_high: list[ArticleCandidate] = field(default_factory=list)
    update_existing_medium: list[ArticleCandidate] = field(default_factory=list)
    update_existing_low: list[ArticleCandidate] = field(default_factory=list)
    manual_review: list[ArticleCandidate] = field(default_factory=list)
    consolidated_groups: list[ConsolidatedQueryGroup] = field(default_factory=list)
    excluded_queries: list[ExcludedQuery] = field(default_factory=list)
    calendar_week1: list[str] = field(default_factory=list)
    calendar_week2: list[str] = field(default_factory=list)
    calendar_later: list[str] = field(default_factory=list)
    suggested_commands: list[str] = field(default_factory=list)
    # Legacy buckets for tests expecting high_priority / all_candidates
    high_priority: list[ArticleCandidate] = field(default_factory=list)
    medium_priority: list[ArticleCandidate] = field(default_factory=list)
    low_priority: list[ArticleCandidate] = field(default_factory=list)
    top_candidates: list[ArticleCandidate] = field(default_factory=list)

    @property
    def all_candidates(self) -> list[ArticleCandidate]:
        return [
            *self.create_new_high,
            *self.create_new_medium,
            *self.create_new_low,
            *self.update_existing_high,
            *self.update_existing_medium,
            *self.update_existing_low,
            *self.manual_review,
        ]
