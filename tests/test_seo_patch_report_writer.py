"""Tests for SEO patch Markdown and CSV reports."""

from pathlib import Path

from linkops.seo_patch_model import PATCH_MONITOR, SeoPatchReport
from linkops.seo_patch_report_writer import write_seo_patch_reports


def _sample_patch() -> SeoPatchReport:
    return SeoPatchReport(
        generated_at="2026-05-22 12:00 UTC",
        target_url="https://worktoolslab.com/clickup-vs-trello-for-small-teams/",
        target_keyword="clickup vs trello",
        overall_recommendation="monitor_only",
        patch_type=PATCH_MONITOR,
        editorial_decision="Monitor GSC; page coverage is strong.",
        do_not_change=[
            "Do not change the published URL slug unless manually required.",
            "Do not remove existing internal links.",
        ],
        seo_title="No SEO title change needed.",
        meta_description="No meta description change needed.",
        intro_addition="No intro addition needed.",
        heading_addition="No heading addition needed.",
        faq_patch="No FAQ additions needed.",
        faq_questions=[],
        manual_review_needed=[],
        internal_link_action="No new internal links needed now.",
        request_indexing_urls=["https://worktoolslab.com/clickup-vs-trello-for-small-teams/"],
        next_commands=['python -m linkops.cli optimize --target-url "https://worktoolslab.com/clickup-vs-trello-for-small-teams/" --target-keyword "clickup vs trello"'],
        query_intent="comparison",
        page_type="comparison",
        intent_alignment="aligned",
    )


def test_patch_report_includes_required_sections(tmp_path, monkeypatch):
    import linkops.seo_patch_report_writer as writer_mod

    monkeypatch.setattr(writer_mod, "REPORTS_DIR", tmp_path)
    md_path, _ = write_seo_patch_reports(_sample_patch(), slug="test", ts="20260522_120000")
    text = md_path.read_text(encoding="utf-8")
    for section in (
        "# Paste-Ready SEO Patch",
        "## Editorial Decision",
        "## Do Not Change",
        "## Paste-Ready Changes",
        "### SEO Title",
        "### Meta Description",
        "### Intro Addition",
        "### Heading Addition",
        "### FAQ Patch",
        "### Internal Link Action",
        "## Manual Review Needed",
        "## Request Indexing",
        "## Next Commands",
        "read-only",
    ):
        assert section in text


def test_csv_includes_required_columns(tmp_path, monkeypatch):
    import linkops.seo_patch_report_writer as writer_mod

    monkeypatch.setattr(writer_mod, "REPORTS_DIR", tmp_path)
    _, csv_path = write_seo_patch_reports(_sample_patch(), slug="test", ts="20260522_120000")
    header = csv_path.read_text(encoding="utf-8").splitlines()[0]
    for col in (
        "target_url",
        "target_keyword",
        "overall_recommendation",
        "patch_type",
        "seo_title",
        "meta_description",
        "intro_addition",
        "heading_addition",
        "faq_questions_count",
        "internal_link_action",
        "request_indexing_urls",
        "next_commands",
    ):
        assert col in header
