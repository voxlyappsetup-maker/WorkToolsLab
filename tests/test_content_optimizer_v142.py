"""Tests for v1.4.2 content optimization quality fixes."""

from dataclasses import asdict

from linkops.content_model import ContentItem
from linkops.content_optimization_model import REC_CONTENT, REC_FAQ_OPTIMIZATION, REC_LIGHT
from linkops.content_optimizer import (
    _extract_faq_items,
    analyze_content_optimization,
    detect_content_topic,
    smart_best_title,
    smart_title_case,
    strip_leading_best,
)
from linkops.gsc_model import GscCache, GscQueryRow


def _page(slug: str, title: str, html: str, plain: str, links: list | None = None) -> ContentItem:
    url = f"https://worktoolslab.com/{slug}/"
    return ContentItem(
        id=abs(hash(slug)) % 100000,
        type="post",
        title=title,
        url=url,
        slug=slug,
        content_html=html,
        excerpt_html="",
        modified="2024-01-01",
        existing_internal_links=links or [],
        word_count=len(plain.split()),
        plain_text=plain,
    )


def _report_text(report) -> str:
    return str(asdict(report)).lower()


def _collaboration_page() -> ContentItem:
    kw = "best collaboration tools for small teams"
    intro = f"{kw} help teams share work and stay aligned. " * 8
    html = (
        f"<h1>Best Collaboration Tools for Small Teams</h1>"
        f"<p>{intro}</p>"
        "<h2>Top Collaboration Tools Compared</h2>"
        "<h2>How to Choose Collaboration Software</h2>"
        "<h2>Monday.com vs Asana: Which One Is Better for Small Teams?</h2>"
        "<h2>FAQ</h2>"
        "<h3>What tools do small teams use?</h3>"
    )
    return _page(
        "best-collaboration-tools-for-small-teams",
        "Best Collaboration Tools for Small Teams",
        html,
        plain=intro + " top collaboration tools compared",
    )


def _strong_core_weak_faq_collaboration() -> ContentItem:
    kw = "best collaboration tools for small teams"
    intro = f"{kw} help teams communicate and share files clearly. " * 10
    html = (
        f"<h1>Best Collaboration Tools for Small Teams</h1>"
        f"<p>{intro}</p>"
        f"<h2>{kw}</h2>"
        "<h2>How to Choose Collaboration Tools</h2>"
    )
    return _page(
        "best-collaboration-tools-for-small-teams",
        "Best Collaboration Tools for Small Teams",
        html,
        plain=intro,
    )


def test_no_best_best_in_report_fields():
    report = analyze_content_optimization(
        [_collaboration_page()],
        "https://worktoolslab.com/best-collaboration-tools-for-small-teams/",
        "best collaboration tools for small teams",
    )
    blob = _report_text(report)
    assert "best best" not in blob


def test_collaboration_faq_not_project_management():
    report = analyze_content_optimization(
        [_collaboration_page()],
        "https://worktoolslab.com/best-collaboration-tools-for-small-teams/",
        "best collaboration tools for small teams",
        max_faq_suggestions=5,
    )
    assert detect_content_topic("best collaboration tools for small teams", _collaboration_page()) == "collaboration"
    for s in report.faq.suggestions:
        low = s.lower()
        assert "project management" not in low
        assert "collaboration" in low or "communication" in low


def test_paste_ready_suppressed_when_intro_strong():
    kw = "best collaboration tools for small teams"
    intro = f"{kw} help teams work together every day. " * 12
    page = _page(
        "best-collaboration-tools-for-small-teams",
        "Best Collaboration Tools for Small Teams",
        f"<h1>Best Collaboration Tools for Small Teams</h1><p>{intro}</p>",
        plain=intro,
    )
    report = analyze_content_optimization(
        [page],
        "https://worktoolslab.com/best-collaboration-tools-for-small-teams/",
        kw,
    )
    assert report.intro.exact_keyword_early
    assert report.intro.needs_direct_sentence is False
    assert report.intro.paste_ready_sentence == "No intro sentence needed."


def test_only_faq_gap_strong_links_faq_optimization():
    linking = []
    for i in range(5):
        p = _page(f"link-{i}", f"L{i}", "<p>x</p>", "x")
        p.existing_internal_links = [
            {
                "href": "https://worktoolslab.com/best-collaboration-tools-for-small-teams/",
                "anchor_text": "collab",
                "normalized_url": "https://worktoolslab.com/best-collaboration-tools-for-small-teams",
            }
        ]
        linking.append(p)
    report = analyze_content_optimization(
        [_strong_core_weak_faq_collaboration(), *linking],
        "https://worktoolslab.com/best-collaboration-tools-for-small-teams/",
        "best collaboration tools for small teams",
    )
    assert report.overall_recommendation in (REC_FAQ_OPTIMIZATION, REC_LIGHT)
    assert report.overall_recommendation != REC_CONTENT
    assert any("FAQ" in g for g in report.content_gaps)


def test_faq_detector_excludes_comparison_fragment():
    html = (
        "<h2>com vs Asana: Which One Is Better for Small Teams?</h2>"
        "<h2>FAQ</h2>"
        "<h3>What are the best collaboration tools for small teams?</h3>"
    )
    items = _extract_faq_items(html, {"h2": [], "h3": []})
    assert not any("com vs" in i for i in items)
    assert any("collaboration" in i.lower() for i in items)


def test_seo_title_natural_no_duplicate_best():
    report = analyze_content_optimization(
        [_collaboration_page()],
        "https://worktoolslab.com/best-collaboration-tools-for-small-teams/",
        "best collaboration tools for small teams",
    )
    title = report.title_meta.seo_title
    assert "Best Best" not in title
    assert title.startswith("Best Collaboration")
    assert len(title) <= 80


def test_smart_title_case_keeps_for_lowercase():
    assert smart_title_case("best collaboration tools for small teams") == (
        "Best Collaboration Tools for Small Teams"
    )


def test_strip_leading_best_and_smart_best_title():
    assert strip_leading_best("best collaboration tools") == "collaboration tools"
    assert smart_best_title("best collaboration tools for small teams") == (
        "Best Collaboration Tools for Small Teams"
    )


def test_meta_description_under_160():
    report = analyze_content_optimization(
        [_collaboration_page()],
        "https://worktoolslab.com/best-collaboration-tools-for-small-teams/",
        "best collaboration tools for small teams",
    )
    assert len(report.title_meta.meta_description) <= 160
    assert report.title_meta.slug_recommendation == "Keep current slug"
