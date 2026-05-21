"""Sitewide internal link map and statistics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from linkops.content_model import ContentItem
from linkops.html_tools import normalize_internal_url
from linkops.suggestion_engine import item_links_to_target


@dataclass
class LinkEdge:
    source_url: str
    source_title: str
    target_url: str
    anchor_text: str
    target_known: bool


FEW_LINKS_THRESHOLD = 2


def analyze_site(catalog: list[ContentItem]) -> tuple[list[LinkEdge], dict[str, Any]]:
    known_urls = {c.normalized_url() for c in catalog}
    url_to_title = {c.normalized_url(): c.title for c in catalog}
    edges: list[LinkEdge] = []
    links_per_page: dict[str, int] = {}

    for item in catalog:
        src = item.normalized_url()
        count = 0
        for lk in item.existing_internal_links:
            tgt = lk["normalized_url"]
            count += 1
            edges.append(
                LinkEdge(
                    source_url=src,
                    source_title=item.title,
                    target_url=tgt,
                    anchor_text=lk["anchor_text"],
                    target_known=tgt in known_urls,
                )
            )
        links_per_page[src] = count

    few = [
        {"url": c.url, "title": c.title, "internal_link_count": links_per_page.get(c.normalized_url(), 0)}
        for c in catalog
        if links_per_page.get(c.normalized_url(), 0) <= FEW_LINKS_THRESHOLD
    ]
    few.sort(key=lambda x: x["internal_link_count"])

    meta = {
        "known_urls": known_urls,
        "url_to_title": url_to_title,
        "links_per_page": links_per_page,
        "pages_with_few_links": few,
    }
    return edges, meta


def pages_already_linking(catalog: list[ContentItem], target_url: str) -> list[ContentItem]:
    return [c for c in catalog if item_links_to_target(c, target_url)]


def pages_not_linking(catalog: list[ContentItem], target_url: str, exclude_url: str | None = None) -> list[ContentItem]:
    target_norm = normalize_internal_url(target_url)
    if not target_norm:
        return list(catalog)
    exclude_norm = normalize_internal_url(exclude_url) if exclude_url else None
    result = []
    for c in catalog:
        norm = c.normalized_url()
        if norm == target_norm or norm == exclude_norm:
            continue
        if not item_links_to_target(c, target_url):
            result.append(c)
    return result
