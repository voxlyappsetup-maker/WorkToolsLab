"""HTML parsing, URL normalization, and internal link extraction."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse

from bs4 import BeautifulSoup, NavigableString, Tag

SITE_HOST = "worktoolslab.com"


@dataclass
class InternalLink:
    href: str
    anchor_text: str
    normalized_url: str
    surrounding_text: str = ""


def normalize_internal_url(url: str, site_host: str = SITE_HOST) -> str | None:
    """
    Normalize WorkToolsLab internal URLs for matching.
    - http/https equivalent
    - trailing slash removed
    - fragments and query strings stripped
    Returns None if not an internal URL.
    """
    if not url or url.startswith(("#", "mailto:", "tel:", "javascript:")):
        return None
    parsed = urlparse(url.strip())
    host = (parsed.netloc or "").lower().removeprefix("www.")
    if host and host != site_host.lower().removeprefix("www."):
        if not url.startswith("/"):
            return None
        host = site_host.lower()

    path = parsed.path or "/"
    path = path.rstrip("/") or "/"
    scheme = "https"
    return urlunparse((scheme, site_host.lower(), path, "", "", ""))


def is_internal_url(url: str, site_host: str = SITE_HOST) -> bool:
    return normalize_internal_url(url, site_host) is not None


def html_to_plain_text(html: str) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    return re.sub(r"\s+", " ", text).strip()


def estimate_word_count(plain_text: str) -> int:
    if not plain_text:
        return 0
    return len(plain_text.split())


def extract_headings(html: str) -> dict[str, list[str]]:
    """Return H1, H2, and H3 heading text from HTML content."""
    if not html:
        return {"h1": [], "h2": [], "h3": []}
    soup = BeautifulSoup(html, "html.parser")
    return {
        "h1": [tag.get_text(strip=True) for tag in soup.find_all("h1") if tag.get_text(strip=True)],
        "h2": [tag.get_text(strip=True) for tag in soup.find_all("h2") if tag.get_text(strip=True)],
        "h3": [tag.get_text(strip=True) for tag in soup.find_all("h3") if tag.get_text(strip=True)],
    }


def _paragraph_context(link_tag: Tag) -> str:
    parent = link_tag.parent
    while parent and parent.name not in ("p", "li", "h1", "h2", "h3", "h4", "blockquote", "div", "article"):
        parent = parent.parent
    if parent:
        return html_to_plain_text(str(parent))[:500]
    return ""


def extract_internal_links(html: str, page_url: str, site_host: str = SITE_HOST) -> list[InternalLink]:
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    seen: set[str] = set()
    links: list[InternalLink] = []

    for a in soup.find_all("a", href=True):
        href = a.get("href", "").strip()
        normalized = normalize_internal_url(href, site_host)
        if not normalized:
            continue
        anchor = a.get_text(strip=True) or href
        key = f"{normalized}|{anchor}"
        if key in seen:
            continue
        seen.add(key)
        links.append(
            InternalLink(
                href=href,
                anchor_text=anchor,
                normalized_url=normalized,
                surrounding_text=_paragraph_context(a),
            )
        )
    return links
