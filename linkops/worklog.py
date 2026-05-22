"""Local worklog for marking GSC opportunity pages as handled (optional JSON file)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from linkops.config import PROJECT_ROOT, WORKLOG_PATH
from linkops.html_tools import normalize_internal_url

WORKLOG_EXAMPLE_PATH = PROJECT_ROOT / "config" / "worklog.example.json"

VALID_STATUSES = frozenset(
    {
        "done",
        "monitor_only",
        "request_indexing_done",
        "skip",
        "needs_review",
    }
)

HANDLED_STATUSES = frozenset(
    {
        "done",
        "monitor_only",
        "request_indexing_done",
        "skip",
    }
)


def canonical_worklog_url(url: str) -> str:
    """Normalize a WorkToolsLab page URL for worklog keys and lookups."""
    raw = url.strip()
    if not raw:
        return ""
    norm = normalize_internal_url(raw)
    if norm:
        return norm
    return raw.rstrip("/") or raw


@dataclass
class WorklogPageEntry:
    status: str
    note: str = ""


@dataclass
class Worklog:
    pages: dict[str, WorklogPageEntry] = field(default_factory=dict)

    def status_for_url(self, url: str) -> str | None:
        entry = self.entry_for_url(url)
        return entry.status if entry else None

    def entry_for_url(self, url: str) -> WorklogPageEntry | None:
        canon = canonical_worklog_url(url)
        if canon:
            entry = self.pages.get(canon)
            if entry:
                return entry
        slug = (canon or url.strip()).rstrip("/").split("/")[-1].lower()
        if not slug:
            return None
        for key, entry in self.pages.items():
            if key.rstrip("/").split("/")[-1].lower() == slug:
                return entry
        return None

    def is_handled(self, url: str) -> bool:
        status = self.status_for_url(url)
        return status in HANDLED_STATUSES if status else False


def load_worklog(path: Path | None = None) -> Worklog:
    """Load worklog from disk; return empty worklog if file is missing or invalid."""
    path = path or WORKLOG_PATH
    if not path.exists():
        return Worklog()
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError):
        return Worklog()
    pages_raw = data.get("pages", {})
    if not isinstance(pages_raw, dict):
        return Worklog()
    pages: dict[str, WorklogPageEntry] = {}
    for url, entry in pages_raw.items():
        if isinstance(entry, str):
            status = entry
            note = ""
        elif isinstance(entry, dict):
            status = str(entry.get("status", "")).strip()
            note = str(entry.get("note", "")).strip()
        else:
            continue
        if status not in VALID_STATUSES:
            continue
        canon = canonical_worklog_url(str(url))
        if not canon:
            continue
        pages[canon] = WorklogPageEntry(status=status, note=note)
    return Worklog(pages=pages)
