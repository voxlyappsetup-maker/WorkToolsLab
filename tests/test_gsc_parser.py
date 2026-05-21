"""Tests for GSC CSV parsing."""

from pathlib import Path

import pytest

from linkops.gsc_parser import (
    import_gsc_csvs,
    parse_ctr,
    parse_int_metric,
    parse_position,
    _map_headers,
    _normalize_header,
)


def test_normalize_header_aliases():
    assert _normalize_header("Top queries") == "top queries"
    assert _normalize_header("  CTR  ") == "ctr"


def test_map_headers_query_and_page():
    fields = ["Top queries", "Clicks", "Impressions", "CTR", "Position"]
    mapping = _map_headers(fields)
    assert mapping["query"] == "Top queries"
    fields_page = ["Page", "Clicks", "Impressions", "CTR", "Position"]
    mapping_p = _map_headers(fields_page)
    assert mapping_p["page"] == "Page"


def test_parse_ctr_percent_string():
    assert parse_ctr("2.5%") == pytest.approx(2.5)
    assert parse_ctr("0%") == pytest.approx(0.0)


def test_parse_ctr_decimal_fraction():
    assert parse_ctr("0.025") == pytest.approx(2.5)
    assert parse_ctr("0.002") == pytest.approx(0.2)
    assert parse_ctr("0.2") == pytest.approx(0.2)


def test_parse_ctr_plain_number():
    assert parse_ctr("1.5") == pytest.approx(1.5)


def test_parse_position_and_int_metrics():
    assert parse_position("24.3") == pytest.approx(24.3)
    assert parse_int_metric("1,234") == 1234
    assert parse_int_metric("") is None


def test_import_queries_only(tmp_path: Path):
    csv_path = tmp_path / "queries.csv"
    csv_path.write_text(
        "Query,Clicks,Impressions,CTR,Position\n"
        "remote work communication tools,0,120,0%,28.5\n"
        "broken query,0,,0%,5\n"
        "worktoolslab,0,5,0%,12\n",
        encoding="utf-8",
    )
    cache, summary = import_gsc_csvs(queries_csv=csv_path)
    assert summary.queries_imported == 2
    assert summary.skipped_rows >= 1
    assert cache.queries[0].query == "remote work communication tools"
    assert cache.queries[0].clicks == 0
    assert cache.queries[0].impressions == 120


def test_import_pages_csv(tmp_path: Path):
    csv_path = tmp_path / "pages.csv"
    csv_path.write_text(
        "Top pages,Clicks,Impressions,CTR,Position\n"
        "https://worktoolslab.com/best-communication-tools-for-remote-teams/,0,80,0%,30\n",
        encoding="utf-8",
    )
    cache, summary = import_gsc_csvs(pages_csv=csv_path)
    assert summary.pages_imported == 1
    assert "communication" in cache.pages[0].page


def test_import_query_pages_csv(tmp_path: Path):
    csv_path = tmp_path / "qp.csv"
    csv_path.write_text(
        "query,page,clicks,impressions,ctr,position\n"
        "trello vs clickup,https://worktoolslab.com/clickup-vs-trello-for-small-teams/,0,50,0%,35\n"
        "trello vs clickup,https://worktoolslab.com/notion-vs-trello-vs-clickup-which-one-is-best-for-your-workflow/,0,40,0%,42\n",
        encoding="utf-8",
    )
    cache, summary = import_gsc_csvs(query_pages_csv=csv_path)
    assert summary.query_pages_imported == 2
    assert len(cache.query_pages) == 2


def test_malformed_rows_skipped_safely(tmp_path: Path):
    csv_path = tmp_path / "queries.csv"
    csv_path.write_text(
        "Query,Clicks,Impressions,CTR,Position\n"
        ",0,10,0%,5\n"
        "valid query,0,25,0%,22\n",
        encoding="utf-8",
    )
    cache, summary = import_gsc_csvs(queries_csv=csv_path)
    assert summary.queries_imported == 1
    assert summary.skipped_rows >= 1
