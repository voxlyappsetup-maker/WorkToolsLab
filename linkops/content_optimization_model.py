"""Data models for read-only content optimization reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

# Coverage field statuses
COVERAGE_EXACT = "exact_match"
COVERAGE_PARTIAL = "partial_match"
COVERAGE_STRONG = "strong_match"
COVERAGE_WEAK = "weak"
COVERAGE_MISSING = "missing"

# Intent alignment
ALIGNMENT_ALIGNED = "aligned"
ALIGNMENT_PARTIAL = "partially_aligned"
ALIGNMENT_MISALIGNED = "misaligned"

# Overall recommendations
REC_NO_CHANGE = "no_change_needed"
REC_LIGHT = "light_optimization"
REC_CONTENT = "content_optimization"
REC_TITLE_META = "title_meta_ctr"
REC_INTERNAL_LINKS = "internal_links_first"
REC_REVIEW_MANUAL = "review_manually"
REC_MONITOR = "monitor_only"
REC_FAQ_OPTIMIZATION = "faq_optimization"

# Internal link support levels
LINK_SUPPORT_STRONG = "strong"
LINK_SUPPORT_MODERATE = "moderate"
LINK_SUPPORT_WEAK = "weak"
LINK_SUPPORT_UNKNOWN = "unknown"


@dataclass
class CoverageField:
    field_name: str
    status: str
    detail: str = ""


@dataclass
class GscQueryMetrics:
    query: str
    clicks: int
    impressions: int
    ctr: float
    position: float
    available: bool = True
    matched_via: str = "exact"  # exact | related
    match_note: str = ""


@dataclass
class IntroAnalysis:
    word_count: int
    exact_keyword_early: bool
    answers_intent: bool
    too_generic: bool
    needs_direct_sentence: bool
    paste_ready_sentence: str
    notes: list[str] = field(default_factory=list)


@dataclass
class HeadingAnalysis:
    h1: list[str]
    h2: list[str]
    h3: list[str]
    relevant_headings: list[str]
    missing_opportunities: list[str]
    keyword_in_h2_recommended: bool
    suggestions: list[str] = field(default_factory=list)


@dataclass
class FaqAnalysis:
    existing_faq_items: list[str]
    suggestions: list[str] = field(default_factory=list)
    coverage_note: str = ""


@dataclass
class TitleMetaSuggestions:
    seo_title: str
    meta_description: str
    focus_keyword: str
    slug_recommendation: str


@dataclass
class InternalLinkSupport:
    inbound_count: int | None
    support_level: str
    next_suggest_command: str
    notes: str = ""


@dataclass
class ContentOptimizationReport:
    generated_at: str
    target_url: str
    target_keyword: str
    gsc_query: str
    query_intent: str
    page_type: str
    intent_alignment: str
    coverage: list[CoverageField]
    intro: IntroAnalysis
    headings: HeadingAnalysis
    faq: FaqAnalysis
    title_meta: TitleMetaSuggestions
    content_gaps: list[str]
    internal_links: InternalLinkSupport
    overall_recommendation: str
    priority_actions: list[str]
    executive_summary: str
    recommendation_rationale: str = ""
    gsc_metrics: GscQueryMetrics | None = None
    next_commands: list[str] = field(default_factory=list)
    request_indexing_urls: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
