"""Tests for v1.5.1 paste-ready FAQ answers (no placeholders)."""

import re

import pytest

from linkops.content_model import ContentItem
from linkops.seo_patch_faq import PASTE_READY_FORBIDDEN_SUBSTRINGS, generate_safe_faq_answer
from linkops.seo_patch_generator import generate_seo_patch
from linkops.seo_patch_model import PATCH_FAQ, PATCH_MANUAL, PATCH_MONITOR
from linkops.seo_patch_report_writer import write_seo_patch_reports


def _page(slug: str, title: str, html: str, plain: str, links: list | None = None) -> ContentItem:
    return ContentItem(
        id=abs(hash(slug)) % 100000,
        type="post",
        title=title,
        url=f"https://worktoolslab.com/{slug}/",
        slug=slug,
        content_html=html,
        excerpt_html="",
        modified="2024-01-01",
        existing_internal_links=links or [],
        word_count=len(plain.split()),
        plain_text=plain,
    )


def _linkers(target_slug: str, n: int = 5) -> list[ContentItem]:
    pages = []
    for i in range(n):
        p = _page(f"link-{i}", f"L{i}", "<p>x</p>", "x")
        p.existing_internal_links = [
            {
                "href": f"https://worktoolslab.com/{target_slug}/",
                "anchor_text": "target",
                "normalized_url": f"https://worktoolslab.com/{target_slug}",
            }
        ]
        pages.append(p)
    return pages


def _webex_weak_faq_page() -> ContentItem:
    intro = ("Webex helps small businesses with video meetings and calling. " * 20) + (
        "Webex review for small businesses "
    )
    html = (
        "<h1>Webex Review for Small Businesses</h1>"
        f"<p>{intro}</p>"
        "<h2>Overview</h2><h2>Pros and Cons</h2>"
    )
    return _page(
        "webex-review-for-small-businesses",
        "Webex Review for Small Businesses",
        html,
        intro,
    )


def _clickup_trello_strong_page() -> ContentItem:
    intro = ("ClickUp vs Trello helps small teams compare tools. " * 12) + "clickup vs trello "
    html = (
        "<h1>ClickUp vs Trello for Small Teams</h1>"
        f"<p>{intro}</p>"
        "<h2>ClickUp vs Trello: Quick Verdict</h2>"
        "<h2>FAQ</h2>"
        "<h3>Is ClickUp Better Than Trello?</h3>"
        "<h3>Is Trello Easier to Use Than ClickUp?</h3>"
        "<h3>Which Is Better for Small Teams, ClickUp or Trello?</h3>"
        "<h3>What Is the Main Difference Between ClickUp and Trello?</h3>"
        "<h3>Should a Small Business Use ClickUp or Trello?</h3>"
    )
    return _page("clickup-vs-trello-for-small-teams", "ClickUp vs Trello for Small Teams", html, intro)


def _collaboration_strong_faq_page() -> ContentItem:
    kw = "best collaboration tools for small teams"
    intro = f"{kw} help teams work together. " * 15
    html = (
        f"<h1>Best Collaboration Tools for Small Teams</h1><p>{intro}</p>"
        "<h2>FAQ</h2>"
        "<h3>What are the best collaboration tools for small teams?</h3>"
        "<h3>What should small teams look for in collaboration tools?</h3>"
        "<h3>Do small teams need collaboration tools?</h3>"
        "<h3>What is the easiest collaboration tool for small teams?</h3>"
        "<h3>What is the difference between collaboration tools and communication tools?</h3>"
    )
    return _page(
        "best-collaboration-tools-for-small-teams",
        "Best Collaboration Tools for Small Teams",
        html,
        intro,
    )


def _paste_ready_section(md: str) -> str:
    start = md.find("## Paste-Ready Changes")
    end = md.find("## Manual Review Needed")
    assert start >= 0 and end > start
    return md[start:end]


def test_no_placeholder_in_paste_ready_section(tmp_path, monkeypatch):
    import linkops.seo_patch_report_writer as writer_mod

    monkeypatch.setattr(writer_mod, "REPORTS_DIR", tmp_path)
    patch = generate_seo_patch(
        [_webex_weak_faq_page(), *_linkers("webex-review-for-small-businesses", 5)],
        "https://worktoolslab.com/webex-review-for-small-businesses/",
        "Webex review for small businesses",
    )
    md_path, csv_path = write_seo_patch_reports(patch, slug="webex-test", ts="20260522_130000")
    md = md_path.read_text(encoding="utf-8")
    section = _paste_ready_section(md).lower()
    for banned in PASTE_READY_FORBIDDEN_SUBSTRINGS:
        assert banned not in section
    csv_text = csv_path.read_text(encoding="utf-8").lower()
    for banned in PASTE_READY_FORBIDDEN_SUBSTRINGS:
        assert banned not in csv_text


def test_webex_faq_has_real_alternative_answer():
    patch = generate_seo_patch(
        [_webex_weak_faq_page(), *_linkers("webex-review-for-small-businesses", 5)],
        "https://worktoolslab.com/webex-review-for-small-businesses/",
        "Webex review for small businesses",
    )
    if patch.faq_questions:
        assert "best alternative" in patch.faq_patch.lower()
        assert "Zoom" in patch.faq_patch
        assert "Google Meet" in patch.faq_patch
        assert "Add a concise answer" not in patch.faq_patch


def test_webex_pricing_faq_in_manual_review(tmp_path, monkeypatch):
    import linkops.seo_patch_report_writer as writer_mod

    monkeypatch.setattr(writer_mod, "REPORTS_DIR", tmp_path)
    patch = generate_seo_patch(
        [_webex_weak_faq_page(), *_linkers("webex-review-for-small-businesses", 5)],
        "https://worktoolslab.com/webex-review-for-small-businesses/",
        "Webex review for small businesses",
    )
    assert patch.manual_review_needed
    manual_blob = " ".join(patch.manual_review_needed).lower()
    assert "pricing" in manual_blob or "cost" in manual_blob
    for item in patch.manual_review_needed:
        if "cost" in item.lower() or "how much" in item.lower():
            assert "verified before publishing" in item.lower()
    md_path, _ = write_seo_patch_reports(patch, slug="webex", ts="20260522_130002")
    paste = _paste_ready_section(md_path.read_text(encoding="utf-8")).lower()
    assert "how much does webex cost" not in paste


def test_webex_pricing_not_in_paste_ready_faq_block():
    patch = generate_seo_patch(
        [_webex_weak_faq_page(), *_linkers("webex-review-for-small-businesses", 5)],
        "https://worktoolslab.com/webex-review-for-small-businesses/",
        "Webex review for small businesses",
    )
    faq_lower = patch.faq_patch.lower()
    assert "how much does" not in faq_lower or "verified" not in faq_lower
    for item in patch.manual_review_needed:
        if "how much" in item.lower():
            assert "How much does" not in patch.faq_patch


def test_safe_webex_alternative_answer_template():
    from linkops.content_optimizer import analyze_content_optimization

    opt = analyze_content_optimization(
        [_webex_weak_faq_page()],
        "https://worktoolslab.com/webex-review-for-small-businesses/",
        "Webex review for small businesses",
    )
    q = "What is the best alternative to Webex for small businesses?"
    ans = generate_safe_faq_answer(q, opt)
    assert ans
    assert "Zoom" in ans
    assert "Microsoft Teams" in ans
    assert "$" not in ans


def test_all_faq_manual_review_no_paste_faq():
    from linkops.content_optimization_model import (
        ContentOptimizationReport,
        FaqAnalysis,
        HeadingAnalysis,
        IntroAnalysis,
        InternalLinkSupport,
        TitleMetaSuggestions,
    )
    from linkops.seo_patch_generator import _faq_section

    from linkops.content_optimization_model import ALIGNMENT_ALIGNED

    report = ContentOptimizationReport(
        generated_at="x",
        target_url="https://worktoolslab.com/webex/",
        target_keyword="Webex",
        gsc_query="Webex",
        query_intent="specific_review",
        page_type="review",
        intent_alignment=ALIGNMENT_ALIGNED,
        coverage=[],
        title_meta=TitleMetaSuggestions("", "", "", "Keep current slug"),
        intro=IntroAnalysis(100, True, True, False, False, "No intro sentence needed."),
        headings=HeadingAnalysis([], [], [], [], [], False, []),
        faq=FaqAnalysis(
            [],
            [
                "How much does Webex cost for a small team?",
                "What are Webex pricing plans for 2026?",
            ],
        ),
        internal_links=InternalLinkSupport(5, "strong", "cmd"),
        overall_recommendation="faq_optimization",
        priority_actions=[],
        executive_summary="",
        content_gaps=[],
    )
    faq_patch, qs, manual = _faq_section(report, PATCH_FAQ, include_faq=False, topic="communication")  # type: ignore[arg-type]
    assert faq_patch == "No paste-ready FAQ additions available."
    assert qs == []
    assert len(manual) == 2


def test_manual_review_section_in_markdown(tmp_path, monkeypatch):
    import linkops.seo_patch_report_writer as writer_mod

    monkeypatch.setattr(writer_mod, "REPORTS_DIR", tmp_path)
    patch = generate_seo_patch(
        [_webex_weak_faq_page(), *_linkers("webex-review-for-small-businesses", 5)],
        "https://worktoolslab.com/webex-review-for-small-businesses/",
        "Webex review for small businesses",
    )
    md_path, _ = write_seo_patch_reports(patch, slug="webex", ts="20260522_130001")
    text = md_path.read_text(encoding="utf-8")
    assert "## Manual Review Needed" in text
    if patch.manual_review_needed:
        assert patch.manual_review_needed[0] in text


def test_monitor_only_unchanged_clickup_and_collaboration():
    for slug, page, kw in (
        (
            "clickup-vs-trello-for-small-teams",
            _clickup_trello_strong_page(),
            "clickup vs trello",
        ),
        (
            "best-collaboration-tools-for-small-teams",
            _collaboration_strong_faq_page(),
            "best collaboration tools for small teams",
        ),
    ):
        patch = generate_seo_patch(
            [page, *_linkers(slug, 5)],
            f"https://worktoolslab.com/{slug}/",
            kw,
        )
        assert patch.patch_type == PATCH_MONITOR
        assert patch.seo_title == "No SEO title change needed."
        assert patch.faq_patch == "No FAQ additions needed."


def test_webex_core_sections_no_change_when_strong():
    patch = generate_seo_patch(
        [_webex_weak_faq_page(), *_linkers("webex-review-for-small-businesses", 5)],
        "https://worktoolslab.com/webex-review-for-small-businesses/",
        "Webex review for small businesses",
    )
    if patch.patch_type == PATCH_FAQ:
        assert patch.seo_title == "No SEO title change needed."
        assert patch.meta_description == "No meta description change needed."
        assert patch.intro_addition == "No intro addition needed."
        assert patch.heading_addition == "No heading addition needed."


def test_all_manual_faq_patch_type_not_faq_only():
    """When every FAQ needs manual review, patch type is not faq_patch."""
    from linkops.content_optimization_model import (
        ALIGNMENT_ALIGNED,
        ContentOptimizationReport,
        FaqAnalysis,
        GscQueryMetrics,
        HeadingAnalysis,
        IntroAnalysis,
        InternalLinkSupport,
        TitleMetaSuggestions,
    )
    from linkops.seo_patch_generator import _faq_section, _finalize_patch_type

    opt = ContentOptimizationReport(
        generated_at="x",
        target_url="https://worktoolslab.com/webex-review-for-small-businesses/",
        target_keyword="Webex review",
        gsc_query="Webex review",
        query_intent="specific_review",
        page_type="review",
        intent_alignment=ALIGNMENT_ALIGNED,
        coverage=[],
        title_meta=TitleMetaSuggestions("", "", "Keep current slug", ""),
        intro=IntroAnalysis(100, True, True, False, False, "No intro sentence needed."),
        headings=HeadingAnalysis([], [], [], [], [], False, []),
        faq=FaqAnalysis([], ["How much does Webex cost for a small team?"]),
        internal_links=InternalLinkSupport(5, "strong", "python -m linkops.cli suggest"),
        overall_recommendation="faq_optimization",
        recommendation_rationale="",
        priority_actions=[],
        executive_summary="",
        content_gaps=[],
        request_indexing_urls=[],
        gsc_metrics=GscQueryMetrics("q", 0, 0, 0.0, 0.0, available=False),
    )
    faq_patch, qs, manual = _faq_section(opt, PATCH_FAQ, include_faq=False, topic="communication")
    assert faq_patch == "No paste-ready FAQ additions available."
    ptype = _finalize_patch_type(PATCH_FAQ, opt, len(qs), len(manual))
    assert ptype in (PATCH_MANUAL, PATCH_MONITOR)
    assert ptype != PATCH_FAQ
