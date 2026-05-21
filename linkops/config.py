"""Configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"
CACHE_PATH = DATA_DIR / "worktoolslab_content_cache.json"
GSC_CACHE_PATH = DATA_DIR / "gsc_cache.json"

# v1: all WordPress write operations are blocked
WRITE_OPERATIONS_BLOCKED = True


@dataclass(frozen=True)
class Settings:
    base_url: str
    username: str
    app_password: str
    site_host: str = "worktoolslab.com"

    @property
    def api_base(self) -> str:
        return self.base_url.rstrip("/") + "/wp-json/wp/v2"


def load_settings() -> Settings:
    load_dotenv(PROJECT_ROOT / ".env")
    base_url = os.getenv("WORKTOOLSLAB_BASE_URL", "https://worktoolslab.com").rstrip("/")
    username = os.getenv("WORDPRESS_USERNAME", "").strip()
    app_password = os.getenv("WORDPRESS_APP_PASSWORD", "").strip()
    if not username or not app_password:
        raise ValueError(
            "Missing credentials. Copy .env.example to .env and set "
            "WORDPRESS_USERNAME and WORDPRESS_APP_PASSWORD (Application Password)."
        )
    return Settings(base_url=base_url, username=username, app_password=app_password)


def assert_read_only(operation: str) -> None:
    """Raise if any write operation is attempted (v1 safety guard)."""
    if WRITE_OPERATIONS_BLOCKED:
        raise RuntimeError(
            f"Blocked: '{operation}' is not allowed in LinkOps v1 (read-only). "
            "This tool never modifies WordPress content."
        )
