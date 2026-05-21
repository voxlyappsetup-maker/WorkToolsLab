"""Tests for URL normalization and internal link extraction."""

from linkops.html_tools import (
    extract_internal_links,
    is_internal_url,
    normalize_internal_url,
)


def test_normalize_strips_fragment_and_query():
    url = "https://worktoolslab.com/foo/?utm=1#section"
    assert normalize_internal_url(url) == "https://worktoolslab.com/foo"


def test_normalize_http_https_equivalent():
    a = normalize_internal_url("http://www.worktoolslab.com/page/")
    b = normalize_internal_url("https://worktoolslab.com/page")
    assert a == b


def test_normalize_trailing_slash():
    a = normalize_internal_url("https://worktoolslab.com/asana-review/")
    b = normalize_internal_url("https://worktoolslab.com/asana-review")
    assert a == b


def test_relative_path_is_internal():
    assert normalize_internal_url("/slack-vs-teams/") == "https://worktoolslab.com/slack-vs-teams"


def test_external_url_returns_none():
    assert normalize_internal_url("https://google.com/search") is None


def test_extract_internal_links():
    html = '''
    <p>Compare <a href="https://worktoolslab.com/zoom-review/">Zoom</a> options.</p>
    <a href="https://example.com/out">External</a>
    '''
    links = extract_internal_links(html, "https://worktoolslab.com/source/")
    assert len(links) == 1
    assert links[0].anchor_text == "Zoom"
    assert links[0].normalized_url == "https://worktoolslab.com/zoom-review"


def test_is_internal_url():
    assert is_internal_url("https://worktoolslab.com/foo")
    assert not is_internal_url("https://notours.com/foo")
