"""Data models for paste-ready SEO patch reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

PATCH_MONITOR = "monitor_only"
PATCH_FAQ = "faq_patch"
PATCH_TITLE_META = "title_meta_patch"
PATCH_INTRO = "intro_patch"
PATCH_HEADING = "heading_patch"
PATCH_INTERNAL = "internal_link_patch"
PATCH_COMBINED = "combined_light_patch"
PATCH_MANUAL = "manual_review"


@dataclass
class SeoPatchReport:
    generated_at: str
    target_url: str
    target_keyword: str
    overall_recommendation: str
    patch_type: str
    editorial_decision: str
    do_not_change: list[str]
    seo_title: str
    meta_description: str
    intro_addition: str
    heading_addition: str
    faq_patch: str
    faq_questions: list[str]
    internal_link_action: str
    request_indexing_urls: list[str]
    next_commands: list[str]
    query_intent: str = ""
    page_type: str = ""
    intent_alignment: str = ""
    manual_review_needed: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
