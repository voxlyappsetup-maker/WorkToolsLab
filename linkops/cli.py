"""Command-line interface for LinkOps."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from linkops.config import CACHE_PATH, DATA_DIR, GSC_CACHE_PATH, REPORTS_DIR, load_settings
from linkops.content_model import ContentItem, from_wp_item
from linkops.link_analyzer import analyze_site
from linkops.gsc_parser import import_gsc_csvs
from linkops.gsc_report_writer import write_gsc_opportunity_reports
from linkops.opportunity_engine import analyze_opportunities
from linkops.content_optimization_report_writer import write_content_optimization_reports
from linkops.content_optimizer import analyze_content_optimization
from linkops.report_writer import write_site_link_map_csv, write_suggestions_reports
from linkops.suggestion_engine import generate_suggestions
from linkops.wordpress_client import WordPressClient

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def _ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def _load_cache() -> list[ContentItem]:
    if not CACHE_PATH.exists():
        print(
            f"Cache not found at {CACHE_PATH}\n"
            "Run: python -m linkops.cli fetch",
            file=sys.stderr,
        )
        sys.exit(1)
    data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return [ContentItem.from_dict(item) for item in data]


def _save_cache(items: list[ContentItem]) -> None:
    _ensure_dirs()
    payload = [item.to_dict() for item in items]
    CACHE_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Saved %d items to %s", len(items), CACHE_PATH)


def cmd_fetch(_args: argparse.Namespace) -> None:
    _ensure_dirs()
    settings = load_settings()
    client = WordPressClient(settings)
    logger.info("Fetching published posts and pages (read-only)...")
    posts = client.fetch_posts()
    pages = client.fetch_pages()
    catalog: list[ContentItem] = []
    for raw in posts:
        catalog.append(from_wp_item(raw, "post"))
    for raw in pages:
        catalog.append(from_wp_item(raw, "page"))
    _save_cache(catalog)
    print(f"Fetched {len(catalog)} published items ({len(posts)} posts, {len(pages)} pages).")


def cmd_analyze(_args: argparse.Namespace) -> None:
    catalog = _load_cache()
    edges, meta = analyze_site(catalog)
    path = write_site_link_map_csv(edges)
    few = meta["pages_with_few_links"]
    print(f"Site internal link map: {path}")
    print(f"Total link edges: {len(edges)}")
    print(f"Pages with few internal links (≤2): {len(few)}")


def _load_gsc_cache():
    from linkops.gsc_model import GscCache

    if not GSC_CACHE_PATH.exists():
        print(
            f"GSC cache not found at {GSC_CACHE_PATH}\n"
            "Run: python -m linkops.cli gsc-import --queries-csv ...",
            file=sys.stderr,
        )
        sys.exit(1)
    data = json.loads(GSC_CACHE_PATH.read_text(encoding="utf-8"))
    return GscCache.from_dict(data)


def cmd_gsc_import(args: argparse.Namespace) -> None:
    _ensure_dirs()
    queries = Path(args.queries_csv) if args.queries_csv else None
    pages = Path(args.pages_csv) if args.pages_csv else None
    query_pages = Path(args.query_pages_csv) if args.query_pages_csv else None
    if not any([queries, pages, query_pages]):
        print("Provide at least one of --queries-csv, --pages-csv, --query-pages-csv", file=sys.stderr)
        sys.exit(1)
    cache, summary = import_gsc_csvs(queries, pages, query_pages)
    GSC_CACHE_PATH.write_text(
        json.dumps(cache.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"GSC cache saved: {GSC_CACHE_PATH}")
    print(f"Queries imported: {summary.queries_imported}")
    print(f"Pages imported: {summary.pages_imported}")
    print(f"Query-page rows imported: {summary.query_pages_imported}")
    print(f"Skipped rows: {summary.skipped_rows}")


def _load_gsc_cache_optional():
    from linkops.gsc_model import GscCache

    if not GSC_CACHE_PATH.exists():
        return None
    data = json.loads(GSC_CACHE_PATH.read_text(encoding="utf-8"))
    return GscCache.from_dict(data)


def cmd_optimize(args: argparse.Namespace) -> None:
    _ensure_dirs()
    catalog = _load_cache()
    gsc_cache = _load_gsc_cache_optional()
    keyword = args.target_keyword
    if not keyword:
        print("--target-keyword is required for optimize.", file=sys.stderr)
        sys.exit(1)
    try:
        report = analyze_content_optimization(
            catalog,
            args.target_url,
            keyword,
            gsc_query=args.query,
            gsc_cache=gsc_cache,
            max_faq_suggestions=args.max_faq_suggestions,
            max_heading_suggestions=args.max_heading_suggestions,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    md_path, csv_path = write_content_optimization_reports(report, slug=report.target_url.split("/")[-2])
    print(f"Markdown report: {md_path}")
    print(f"CSV report: {csv_path}")
    print(f"Overall recommendation: {report.overall_recommendation}")
    print(f"Intent alignment: {report.intent_alignment}")


def cmd_opportunities(args: argparse.Namespace) -> None:
    _ensure_dirs()
    gsc_cache = _load_gsc_cache()
    catalog = _load_cache()
    report = analyze_opportunities(
        gsc_cache,
        catalog,
        min_impressions=args.min_impressions,
        max_clicks=args.max_clicks,
        max_position=args.max_position,
    )
    md_path, csv_path = write_gsc_opportunity_reports(report)
    print(f"Markdown report: {md_path}")
    print(f"CSV report: {csv_path}")
    print(f"Opportunities: {len(report.opportunities)} (from {report.total_queries_analyzed} queries analyzed)")
    if report.top_actions:
        print("Top action:", report.top_actions[0])


def cmd_suggest(args: argparse.Namespace) -> None:
    catalog = _load_cache()
    report = generate_suggestions(
        catalog,
        target_url=args.target_url,
        target_keyword=args.target_keyword,
        max_suggestions=args.max_suggestions,
        include_high_risk=args.include_high_risk,
        include_core_pages=args.include_core_pages,
    )
    md_path, csv_path = write_suggestions_reports(
        report,
        args.target_url,
        args.target_keyword,
    )
    print(f"Markdown report: {md_path}")
    print(f"CSV report: {csv_path}")
    print(
        f"Suggestions: {len(report.suggestions)} "
        f"(strong: {len(report.strong)}, medium: {len(report.medium)}) | "
        f"Already linking: {len(report.already_linking)} "
        f"(related: {len(report.related_already_linking)}) | "
        f"Rejected: {len(report.rejected)}"
    )
    print(f"Primary cluster: {report.target_primary_cluster or 'none'}")
    print(f"Recommendation: {report.final_recommendation}")
    if report.strict_mode:
        print(report.already_linking_quality_note)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="linkops",
        description="WorkToolsLab LinkOps — read-only internal linking assistant (v1.4.2)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_fetch = sub.add_parser("fetch", help="Fetch published posts/pages and save cache")
    p_fetch.set_defaults(func=cmd_fetch)

    p_analyze = sub.add_parser("analyze", help="Generate sitewide internal link map CSV")
    p_analyze.set_defaults(func=cmd_analyze)

    p_suggest = sub.add_parser("suggest", help="Suggest internal links for a target URL")
    p_suggest.add_argument("--target-url", required=True, help="Target article URL on worktoolslab.com")
    p_suggest.add_argument("--target-keyword", default=None, help="Optional focus keyword")
    p_suggest.add_argument("--max-suggestions", type=int, default=8)
    p_suggest.add_argument(
        "--include-high-risk",
        action="store_true",
        help="Include high-risk suggestions (excluded by default in v1.2)",
    )
    p_suggest.add_argument(
        "--include-core-pages",
        action="store_true",
        help="Allow Home/Blog/Contact/About as medium/high review candidates (excluded by default)",
    )
    p_suggest.set_defaults(func=cmd_suggest)

    p_gsc = sub.add_parser("gsc-import", help="Import local GSC CSV exports into cache")
    p_gsc.add_argument("--queries-csv", default=None, help="Path to GSC queries export CSV")
    p_gsc.add_argument("--pages-csv", default=None, help="Path to GSC pages export CSV")
    p_gsc.add_argument(
        "--query-pages-csv",
        default=None,
        help="Path to GSC query+page export CSV (optional)",
    )
    p_gsc.set_defaults(func=cmd_gsc_import)

    p_opp = sub.add_parser("opportunities", help="Analyze GSC cache vs WordPress content")
    p_opp.add_argument("--min-impressions", type=int, default=20)
    p_opp.add_argument("--max-clicks", type=int, default=0)
    p_opp.add_argument("--max-position", type=float, default=90.0)
    p_opp.set_defaults(func=cmd_opportunities)

    p_opt = sub.add_parser("optimize", help="Content optimization report for a target URL")
    p_opt.add_argument("--target-url", required=True, help="Target article URL on worktoolslab.com")
    p_opt.add_argument("--target-keyword", required=True, help="Focus keyword to audit")
    p_opt.add_argument(
        "--query",
        default=None,
        help="Optional GSC query string (defaults to target keyword when GSC cache exists)",
    )
    p_opt.add_argument("--max-faq-suggestions", type=int, default=5)
    p_opt.add_argument("--max-heading-suggestions", type=int, default=5)
    p_opt.set_defaults(func=cmd_optimize)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
