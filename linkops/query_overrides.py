"""Optional local query-to-target URL overrides (read-only, no secrets)."""

from __future__ import annotations

import json
from pathlib import Path

from linkops.config import PROJECT_ROOT
from linkops.html_tools import normalize_internal_url

OVERRIDES_PATH = PROJECT_ROOT / "config" / "query_target_overrides.json"
EXAMPLE_OVERRIDES_PATH = PROJECT_ROOT / "config" / "query_target_overrides.example.json"


def load_query_target_overrides(path: Path | None = None) -> dict[str, str]:
    """Load query -> normalized URL overrides. Returns empty dict if file missing."""
    path = path or OVERRIDES_PATH
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(data, dict):
        return {}
    result: dict[str, str] = {}
    for raw_query, raw_url in data.items():
        try:
            q = str(raw_query).strip().lower()
            url = normalize_internal_url(str(raw_url).strip())
            if q and url:
                result[q] = url
        except Exception:
            continue
    return result
