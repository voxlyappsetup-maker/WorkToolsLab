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
        }


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
    high_priority: list[ArticleCandidate] = field(default_factory=list)
    medium_priority: list[ArticleCandidate] = field(default_factory=list)
    low_priority: list[ArticleCandidate] = field(default_factory=list)
    manual_review: list[ArticleCandidate] = field(default_factory=list)
    excluded_queries: list[ExcludedQuery] = field(default_factory=list)
    calendar_week1: list[str] = field(default_factory=list)
    calendar_week2: list[str] = field(default_factory=list)
    calendar_later: list[str] = field(default_factory=list)
    suggested_commands: list[str] = field(default_factory=list)

    @property
    def all_candidates(self) -> list[ArticleCandidate]:
        return [
            *self.high_priority,
            *self.medium_priority,
            *self.low_priority,
            *self.manual_review,
        ]

    @property
    def top_candidates(self) -> list[ArticleCandidate]:
        ranked = sorted(
            [c for c in self.all_candidates if c.priority != PRIORITY_MANUAL],
            key=lambda c: (-c.priority_score, -c.total_impressions),
        )
        manual = sorted(self.manual_review, key=lambda c: -c.total_impressions)
        return (ranked + manual)[:5]
