"""Read-only WordPress REST API client."""

from __future__ import annotations

import logging
from typing import Any

import requests

from linkops.config import Settings, assert_read_only

logger = logging.getLogger(__name__)

POST_FIELDS = (
    "id,type,link,slug,title,content,excerpt,date,modified,status"
)
PAGE_FIELDS = POST_FIELDS
PER_PAGE = 100


class WordPressClient:
    """Fetches published posts and pages only. Never writes to WordPress."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.session = requests.Session()
        self.session.auth = (settings.username, settings.app_password)
        self.session.headers.update({"Accept": "application/json"})

    def _get_paginated(self, endpoint: str, resource_label: str) -> list[dict[str, Any]]:
        url = f"{self.settings.api_base}/{endpoint}"
        page = 1
        all_items: list[dict[str, Any]] = []

        while True:
            params = {
                "status": "publish",
                "per_page": PER_PAGE,
                "page": page,
                "_fields": POST_FIELDS,
            }
            resp = self.session.get(url, params=params, timeout=60)
            if resp.status_code == 401:
                raise PermissionError(
                    "WordPress authentication failed. Check WORDPRESS_USERNAME "
                    "and WORDPRESS_APP_PASSWORD in .env."
                )
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break
            for item in batch:
                if item.get("status") != "publish":
                    continue
                all_items.append(item)
            total_pages = int(resp.headers.get("X-WP-TotalPages", 1))
            logger.info("Fetched %s page %d/%d (%d items)", resource_label, page, total_pages, len(batch))
            if page >= total_pages:
                break
            page += 1

        return all_items

    def fetch_posts(self) -> list[dict[str, Any]]:
        return self._get_paginated("posts", "posts")

    def fetch_pages(self) -> list[dict[str, Any]]:
        return self._get_paginated("pages", "pages")

    def fetch_all_published(self) -> list[dict[str, Any]]:
        """Return combined published posts and pages."""
        posts = self.fetch_posts()
        pages = self.fetch_pages()
        return posts + pages

    # --- Explicitly blocked write methods (v1) ---

    def update_post(self, *_args: Any, **_kwargs: Any) -> None:
        assert_read_only("update_post")

    def update_page(self, *_args: Any, **_kwargs: Any) -> None:
        assert_read_only("update_page")

    def create_post(self, *_args: Any, **_kwargs: Any) -> None:
        assert_read_only("create_post")

    def delete_post(self, *_args: Any, **_kwargs: Any) -> None:
        assert_read_only("delete_post")
