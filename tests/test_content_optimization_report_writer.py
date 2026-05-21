"""Tests for content optimization Markdown and CSV reports."""

from pathlib import Path

from linkops.content_optimization_model import (
    ALIGNMENT_ALIGNED,
    COVERAGE_EXACT,
    COVERAGE_MISSING,
    CoverageField,
    ContentOptimizationReport,
    FaqAnalysis,
    GscQueryMetrics,
    HeadingAnalysis,
    IntroAnalysis,
    InternalLinkSupport,
    REC_CONTENT,
    TitleMetaSuggestions,
)
from linkops.content_optimization_report_writer import write_content_optimization_reports


def _sample_report() -> ContentOptimizationReport:
    return ContentOptimizationReport(
        generated_at="2026-05-21 12:00 UTC",
        target_url="https://worktoolslab.com/best-project-management-tools-for-small-teams/",
        target_keyword="project management software for small teams",
        gsc_query="project management software for small teams",
        query_intent="broad_best_tools",
        page_type="roundup_best_tools",
        intent_alignment=ALIGNMENT_ALIGNED,
        coverage=[
            CoverageField("title", COVERAGE_EXACT, "exact phrase present"),
            CoverageField("intro", COVERAGE_MISSING, "keyword not detected"),
            CoverageField("headings", COVERAGE_MISSING, "keyword not detected"),
            CoverageField("faq", COVERAGE_MISSING, "keyword not detected"),
        ],
        intro=IntroAnalysis(
            word_count=120,
            exact_keyword_early=False,
            answers_intent=True,
            too_generic=True,
            needs_direct_sentence=True,
            paste_ready_sentence="The best project management software for small teams should help with deadlines.",
            notes=["Exact keyword not in opening 150 words."],
        ),
        headings=HeadingAnalysis(
            h1=["Best PM Tools"],
            h2=["Top Tools"],
            h3=[],
            relevant_headings=["Top Tools"],
            missing_opportunities=["Add an H2 with target keyword."],
            keyword_in_h2_recommended=True,
            suggestions=["Best Project Management Software for Small Teams"],
        ),
        faq=FaqAnalysis(
            existing_faq_items=[],
            suggestions=["What is the best project management software for small teams?"],
        ),
        title_meta=TitleMetaSuggestions(
            seo_title="Best Project Management Software for Small Teams",
            meta_description="Find the best options for small teams with practical recommendations."[:160],
            focus_keyword="project management software for small teams",
            slug_recommendation="best-project-management-tools-for-small-teams",
        ),
        content_gaps=["Improve intro: keyword not detected"],
        internal_links=InternalLinkSupport(
            inbound_count=2,
            support_level="moderate",
            next_suggest_command='python -m linkops.cli suggest --target-url "https://worktoolslab.com/best-project-management-tools-for-small-teams/" --target-keyword "project management software for small teams" --max-suggestions 8',
        ),
        overall_recommendation=REC_CONTENT,
        priority_actions=["Add keyword to intro and FAQ."],
        recommendation_rationale="Keyword gaps remain in intro and FAQ.",
        executive_summary="Target keyword needs content optimization.",
        gsc_metrics=GscQueryMetrics(
            query="project management software for small teams",
            clicks=0,
            impressions=67,
            ctr=0.0,
            position=72.8,
        ),
        next_commands=['python -m linkops.cli suggest --target-url "https://worktoolslab.com/best-project-management-tools-for-small-teams/"'],
        request_indexing_urls=["https://worktoolslab.com/best-project-management-tools-for-small-teams/"],
    )


def test_markdown_includes_required_sections(tmp_path, monkeypatch):
    import linkops.content_optimization_report_writer as writer_mod

    monkeypatch.setattr(writer_mod, "REPORTS_DIR", tmp_path)
    md_path, _ = write_content_optimization_reports(_sample_report(), slug="test-slug", ts="20260101_120000")
    text = md_path.read_text(encoding="utf-8")
    for section in (
        "# Content Optimization Report",
        "## Executive Summary",
        "## Query Coverage Audit",
        "## Intro Analysis",
        "## Heading Analysis",
        "## FAQ Opportunities",
        "## Title and Meta Suggestions",
        "## Content Gap Recommendations",
        "## Internal Link Support",
        "## Suggested Next Commands",
        "## Request Indexing Candidates",
        "Query intent:",
        "Page type:",
        "Intent alignment:",
        "read-only",
    ):
        assert section in text or section.lower() in text.lower()


def test_csv_includes_required_columns(tmp_path, monkeypatch):
    import linkops.content_optimization_report_writer as writer_mod

    monkeypatch.setattr(writer_mod, "REPORTS_DIR", tmp_path)
    _, csv_path = write_content_optimization_reports(_sample_report(), slug="test-slug", ts="20260101_120000")
    header = csv_path.read_text(encoding="utf-8").splitlines()[0]
    required = [
        "target_url",
        "target_keyword",
        "query_intent",
        "page_type",
        "intent_alignment",
        "title_status",
        "slug_status",
        "intro_status",
        "heading_status",
        "faq_status",
        "overall_recommendation",
        "priority_actions",
        "seo_title_suggestion",
        "meta_description_suggestion",
        "focus_keyword",
        "slug_recommendation",
        "next_command",
        "request_indexing_urls",
    ]
    for col in required:
        assert col in header
