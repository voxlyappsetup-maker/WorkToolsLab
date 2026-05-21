"""Tests for link analysis and already-linked detection."""

from linkops.content_model import ContentItem
from linkops.link_analyzer import pages_already_linking, pages_not_linking


def _item(item_id: int, url: str, title: str, links: list[dict]) -> ContentItem:
    return ContentItem(
        id=item_id,
        type="post",
        title=title,
        url=url,
        slug=url.rstrip("/").split("/")[-1],
        content_html="",
        excerpt_html="",
        modified="2024-01-01",
        existing_internal_links=links,
        word_count=100,
        plain_text="slack zoom teams communication remote work",
    )


def test_pages_already_linking():
    target = "https://worktoolslab.com/zoom-review/"
    catalog = [
        _item(1, "https://worktoolslab.com/slack-vs-teams/", "Slack vs Teams", [
            {"href": target, "anchor_text": "Zoom", "normalized_url": "https://worktoolslab.com/zoom-review", "surrounding_text": ""},
        ]),
        _item(2, "https://worktoolslab.com/asana-review/", "Asana Review", []),
    ]
    already = pages_already_linking(catalog, target)
    assert len(already) == 1
    assert already[0].title == "Slack vs Teams"


def test_pages_not_linking_excludes_target():
    target = "https://worktoolslab.com/zoom-review/"
    catalog = [
        _item(1, target, "Zoom Review", []),
        _item(2, "https://worktoolslab.com/slack-vs-teams/", "Slack vs Teams", []),
        _item(3, "https://worktoolslab.com/asana-review/", "Asana", []),
    ]
    not_linked = pages_not_linking(catalog, target)
    urls = {c.url for c in not_linked}
    assert target not in urls
    assert "https://worktoolslab.com/slack-vs-teams/" in urls
