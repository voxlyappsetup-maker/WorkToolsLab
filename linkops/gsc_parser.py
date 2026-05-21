"""Parse Google Search Console CSV exports into normalized cache models."""

from __future__ import annotations

import csv
import re
from datetime import datetime, timezone
from pathlib import Path

from linkops.gsc_model import (
    GscCache,
    GscImportSummary,
    GscPageRow,
    GscQueryPageRow,
    GscQueryRow,
)

QUERY_HEADER_ALIASES = frozenset(
    {"query", "queries", "top queries", "top query", "search query", "search queries"}
)
PAGE_HEADER_ALIASES = frozenset(
    {"page", "pages", "top pages", "top page", "url", "landing page", "landing pages"}
)
CLICKS_ALIASES = frozenset({"clicks", "click"})
IMPRESSIONS_ALIASES = frozenset({"impressions", "impression"})
CTR_ALIASES = frozenset({"ctr", "click-through rate", "click through rate"})
POSITION_ALIASES = frozenset({"position", "avg. position", "average position", "avg position"})


def _normalize_header(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())


def _map_headers(fieldnames: list[str] | None) -> dict[str, str]:
    """Map canonical field names to actual CSV column names."""
    if not fieldnames:
        return {}
    mapping: dict[str, str] = {}
    for raw in fieldnames:
        if raw is None:
            continue
        norm = _normalize_header(raw)
        if norm in QUERY_HEADER_ALIASES and "query" not in mapping:
            mapping["query"] = raw
        elif norm in PAGE_HEADER_ALIASES and "page" not in mapping:
            mapping["page"] = raw
        elif norm in CLICKS_ALIASES and "clicks" not in mapping:
            mapping["clicks"] = raw
        elif norm in IMPRESSIONS_ALIASES and "impressions" not in mapping:
            mapping["impressions"] = raw
        elif norm in CTR_ALIASES and "ctr" not in mapping:
            mapping["ctr"] = raw
        elif norm in POSITION_ALIASES and "position" not in mapping:
            mapping["position"] = raw
    return mapping


def parse_ctr(value: str | None) -> float | None:
    """Parse CTR to float percentage (e.g. 2.5 means 2.5%)."""
    if value is None:
        return None
    text = str(value).strip()
    if not text or text in {"-", "—", "n/a", "na"}:
        return None
    try:
        if text.endswith("%"):
            return float(text[:-1].strip().replace(",", ""))
        num = float(text.replace(",", ""))
        if 0 < num <= 1:
            # Fractional CTR (e.g. 0.002 -> 0.2%) vs literal percent (e.g. 0.2 -> 0.2%)
            if num < 0.05:
                return num * 100.0
            return num
        return num
    except (ValueError, TypeError):
        return None


def parse_int_metric(value: str | None) -> int | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text or text in {"-", "—", "n/a", "na"}:
        return None
    try:
        return int(float(text))
    except (ValueError, TypeError):
        return None


def parse_position(value: str | None) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text or text in {"-", "—", "n/a", "na"}:
        return None
    try:
        return float(text)
    except (ValueError, TypeError):
        return None


def _cell(row: dict[str, str], col: str | None) -> str | None:
    if not col:
        return None
    val = row.get(col)
    if val is None:
        return None
    return str(val).strip() or None


def _parse_query_row(row: dict[str, str], headers: dict[str, str]) -> GscQueryRow | None:
    query = _cell(row, headers.get("query"))
    if not query:
        return None
    impressions = parse_int_metric(_cell(row, headers.get("impressions")))
    if impressions is None:
        return None
    clicks = parse_int_metric(_cell(row, headers.get("clicks"))) or 0
    ctr = parse_ctr(_cell(row, headers.get("ctr")))
    if ctr is None:
        ctr = (clicks / impressions * 100.0) if impressions else 0.0
    position = parse_position(_cell(row, headers.get("position")))
    if position is None:
        return None
    return GscQueryRow(
        query=query,
        clicks=clicks,
        impressions=impressions,
        ctr=round(ctr, 4),
        position=round(position, 2),
    )


def _parse_page_row(row: dict[str, str], headers: dict[str, str]) -> GscPageRow | None:
    page = _cell(row, headers.get("page"))
    if not page:
        return None
    impressions = parse_int_metric(_cell(row, headers.get("impressions")))
    if impressions is None:
        return None
    clicks = parse_int_metric(_cell(row, headers.get("clicks"))) or 0
    ctr = parse_ctr(_cell(row, headers.get("ctr")))
    if ctr is None:
        ctr = (clicks / impressions * 100.0) if impressions else 0.0
    position = parse_position(_cell(row, headers.get("position")))
    if position is None:
        return None
    return GscPageRow(
        page=page,
        clicks=clicks,
        impressions=impressions,
        ctr=round(ctr, 4),
        position=round(position, 2),
    )


def _parse_query_page_row(row: dict[str, str], headers: dict[str, str]) -> GscQueryPageRow | None:
    query = _cell(row, headers.get("query"))
    page = _cell(row, headers.get("page"))
    if not query or not page:
        return None
    impressions = parse_int_metric(_cell(row, headers.get("impressions")))
    if impressions is None:
        return None
    clicks = parse_int_metric(_cell(row, headers.get("clicks"))) or 0
    ctr = parse_ctr(_cell(row, headers.get("ctr")))
    if ctr is None:
        ctr = (clicks / impressions * 100.0) if impressions else 0.0
    position = parse_position(_cell(row, headers.get("position")))
    if position is None:
        return None
    return GscQueryPageRow(
        query=query,
        page=page,
        clicks=clicks,
        impressions=impressions,
        ctr=round(ctr, 4),
        position=round(position, 2),
    )


def _read_csv_rows(path: Path) -> tuple[list[dict[str, str]], dict[str, str], int]:
    skipped = 0
    rows: list[dict[str, str]] = []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        headers = _map_headers(reader.fieldnames)
        if "clicks" not in headers or "impressions" not in headers or "position" not in headers:
            return [], headers, 0
        for row in reader:
            try:
                if not any(str(v or "").strip() for v in row.values()):
                    skipped += 1
                    continue
                rows.append(row)
            except Exception:
                skipped += 1
    return rows, headers, skipped


def import_gsc_csvs(
    queries_csv: Path | None = None,
    pages_csv: Path | None = None,
    query_pages_csv: Path | None = None,
) -> tuple[GscCache, GscImportSummary]:
    """Import one or more GSC CSV exports into a normalized cache."""
    summary = GscImportSummary()
    queries: list[GscQueryRow] = []
    pages: list[GscPageRow] = []
    query_pages: list[GscQueryPageRow] = []

    if queries_csv and queries_csv.exists():
        raw_rows, headers, skipped = _read_csv_rows(queries_csv)
        summary.skipped_rows += skipped
        if "query" not in headers:
            raise ValueError(f"Queries CSV missing a query column: {queries_csv}")
        for row in raw_rows:
            try:
                parsed = _parse_query_row(row, headers)
                if parsed:
                    queries.append(parsed)
                else:
                    summary.skipped_rows += 1
            except Exception:
                summary.skipped_rows += 1

    if pages_csv and pages_csv.exists():
        raw_rows, headers, skipped = _read_csv_rows(pages_csv)
        summary.skipped_rows += skipped
        if "page" not in headers:
            raise ValueError(f"Pages CSV missing a page/URL column: {pages_csv}")
        for row in raw_rows:
            try:
                parsed = _parse_page_row(row, headers)
                if parsed:
                    pages.append(parsed)
                else:
                    summary.skipped_rows += 1
            except Exception:
                summary.skipped_rows += 1

    if query_pages_csv and query_pages_csv.exists():
        raw_rows, headers, skipped = _read_csv_rows(query_pages_csv)
        summary.skipped_rows += skipped
        if "query" not in headers or "page" not in headers:
            raise ValueError(f"Query-pages CSV missing query or page column: {query_pages_csv}")
        for row in raw_rows:
            try:
                parsed = _parse_query_page_row(row, headers)
                if parsed:
                    query_pages.append(parsed)
                else:
                    summary.skipped_rows += 1
            except Exception:
                summary.skipped_rows += 1

    if not queries and not pages and not query_pages:
        raise ValueError("At least one valid GSC CSV file is required.")

    summary.queries_imported = len(queries)
    summary.pages_imported = len(pages)
    summary.query_pages_imported = len(query_pages)

    cache = GscCache(
        imported_at=datetime.now(timezone.utc).isoformat(),
        queries=queries,
        pages=pages,
        query_pages=query_pages,
    )
    return cache, summary
