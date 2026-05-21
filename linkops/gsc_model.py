"""Data models for Google Search Console CSV imports and opportunities."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class GscQueryRow:
    query: str
    clicks: int
    impressions: int
    ctr: float  # percentage 0-100
    position: float


@dataclass
class GscPageRow:
    page: str
    clicks: int
    impressions: int
    ctr: float
    position: float


@dataclass
class GscQueryPageRow:
    query: str
    page: str
    clicks: int
    impressions: int
    ctr: float
    position: float


@dataclass
class GscImportSummary:
    queries_imported: int = 0
    pages_imported: int = 0
    query_pages_imported: int = 0
    skipped_rows: int = 0


@dataclass
class GscCache:
    imported_at: str
    queries: list[GscQueryRow] = field(default_factory=list)
    pages: list[GscPageRow] = field(default_factory=list)
    query_pages: list[GscQueryPageRow] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "imported_at": self.imported_at,
            "queries": [asdict(q) for q in self.queries],
            "pages": [asdict(p) for p in self.pages],
            "query_pages": [asdict(qp) for qp in self.query_pages],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GscCache:
        return cls(
            imported_at=data.get("imported_at", ""),
            queries=[GscQueryRow(**q) for q in data.get("queries", [])],
            pages=[GscPageRow(**p) for p in data.get("pages", [])],
            query_pages=[GscQueryPageRow(**qp) for qp in data.get("query_pages", [])],
        )


# Opportunity statuses (display labels match report sections)
STATUS_CORRECT_PAGE = "Correct page"
STATUS_CANNIBALIZATION = "Possible cannibalization"
STATUS_OLD_URL = "Old or redirected URL visible"
STATUS_NO_TARGET = "No obvious target"
STATUS_CONTENT_OPTIMIZATION = "Content optimization needed"
STATUS_INTERNAL_LINKS = "Internal link support needed"


@dataclass
class Opportunity:
    priority_rank: int
    query: str
    clicks: int
    impressions: int
    ctr: float
    position: float
    target_url: str
    target_title: str
    status: str
    reason: str
    recommended_action: str
    next_command: str
    request_indexing_urls: list[str]
    query_intent: str = "unknown"
    page_type: str = "unknown"
    confidence: str = "low"
    action_type: str = "monitor_only"
    override_used: bool = False
    target_selection_reason: str = ""
    priority_score: float = 0.0
    gsc_pages: list[str] = field(default_factory=list)


@dataclass
class OpportunityReport:
    generated_at: str
    opportunities: list[Opportunity]
    total_queries_analyzed: int
    filters: dict[str, Any]
    summary: dict[str, int] = field(default_factory=dict)
    top_actions: list[str] = field(default_factory=list)
