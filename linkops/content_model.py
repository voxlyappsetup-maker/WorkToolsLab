"""Content models built from WordPress API responses."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from linkops.html_tools import (
    estimate_word_count,
    extract_internal_links,
    html_to_plain_text,
    normalize_internal_url,
)


@dataclass
class ContentItem:
    id: int
    type: str  # post | page
    title: str
    url: str
    slug: str
    content_html: str
    excerpt_html: str
    modified: str
    existing_internal_links: list[dict[str, str]]
    word_count: int
    plain_text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContentItem:
        return cls(
            id=data["id"],
            type=data["type"],
            title=data["title"],
            url=data["url"],
            slug=data["slug"],
            content_html=data["content_html"],
            excerpt_html=data.get("excerpt_html", ""),
            modified=data["modified"],
            existing_internal_links=list(data.get("existing_internal_links", [])),
            word_count=data["word_count"],
            plain_text=data["plain_text"],
        )

    def normalized_url(self) -> str:
        return normalize_internal_url(self.url) or self.url

    def links_to_target(self, target_normalized: str) -> bool:
        """Whether this page links to target_normalized (both sides normalized)."""
        target_norm = normalize_internal_url(target_normalized) or target_normalized
        for lk in self.existing_internal_links:
            try:
                raw = None
                if isinstance(lk, dict):
                    raw = lk.get("normalized_url") or lk.get("href")
                else:
                    raw = getattr(lk, "normalized_url", None) or getattr(lk, "href", None)
                if not raw:
                    continue
                link_norm = normalize_internal_url(str(raw).strip())
                if link_norm and link_norm == target_norm:
                    return True
            except Exception:
                continue
        return False


def _rendered(field: dict | str | None) -> str:
    if isinstance(field, dict):
        return field.get("rendered", "") or ""
    return field or ""


def from_wp_item(raw: dict[str, Any], item_type: str) -> ContentItem:
    content_html = _rendered(raw.get("content"))
    excerpt_html = _rendered(raw.get("excerpt"))
    url = raw.get("link", "")
    plain = html_to_plain_text(content_html)
    internal = extract_internal_links(content_html, url)
    title = _rendered(raw.get("title")) if isinstance(raw.get("title"), dict) else str(raw.get("title", ""))

    return ContentItem(
        id=int(raw["id"]),
        type=item_type,
        title=title,
        url=url,
        slug=raw.get("slug", ""),
        content_html=content_html,
        excerpt_html=excerpt_html,
        modified=raw.get("modified", raw.get("date", "")),
        existing_internal_links=[
            {
                "href": lk.href,
                "anchor_text": lk.anchor_text,
                "normalized_url": lk.normalized_url,
                "surrounding_text": lk.surrounding_text,
            }
            for lk in internal
        ],
        word_count=estimate_word_count(plain),
        plain_text=plain,
    )


def build_catalog(wp_items: list[tuple[dict[str, Any], str]]) -> list[ContentItem]:
    return [from_wp_item(raw, t) for raw, t in wp_items]
