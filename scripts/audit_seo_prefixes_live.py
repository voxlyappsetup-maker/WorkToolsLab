#!/usr/bin/env python3
"""Read-only live HTML audit for literal SEO field prefixes."""
from __future__ import annotations

import json
import re
import ssl
import urllib.request
from html import unescape
from pathlib import Path

PREFIX = re.compile(r"^\s*(SEO\s+Title|Meta\s+Description)\s*:\s*", re.I)
UA = "Mozilla/5.0 (compatible; WorkToolsLabLinkOpsAudit/1.0)"
ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "worktoolslab_content_cache.json"
OUT = ROOT / "data" / "seo_prefix_audit_live.json"


def fetch_meta(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=25, context=ssl.create_default_context()) as resp:
            html = resp.read().decode("utf-8", "replace")
    except Exception as exc:  # noqa: BLE001
        return {"url": url, "error": str(exc)}

    def m(pat: str) -> str | None:
        match = re.search(pat, html, re.I | re.S)
        return unescape(match.group(1).strip()) if match else None

    title = m(r"<title>([^<]+)</title>")
    desc = m(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']*)["\']')
    og_title = m(r'<meta\s+property=["\']og:title["\']\s+content=["\']([^"\']*)["\']')
    og_desc = m(
        r'<meta\s+property=["\']og:description["\']\s+content=["\']([^"\']*)["\']'
    )
    tw_title = m(r'<meta\s+name=["\']twitter:title["\']\s+content=["\']([^"\']*)["\']')
    tw_desc = m(
        r'<meta\s+name=["\']twitter:description["\']\s+content=["\']([^"\']*)["\']'
    )

    jsonld_headline = None
    jsonld_description = None
    for block in re.findall(
        r'<script type="application/ld\+json"[^>]*>(.*?)</script>', html, re.I | re.S
    ):
        if "BlogPosting" not in block and "headline" not in block:
            continue
        hm = re.search(r'"headline"\s*:\s*"([^"]+)"', block)
        if hm:
            jsonld_headline = hm.group(1)
        dm = re.search(r'"description"\s*:\s*"([^"]+)"', block)
        if dm:
            jsonld_description = dm.group(1)

    publisher_type = None
    publisher_id = None
    pub_match = re.search(
        r'"@id"\s*:\s*"https://worktoolslab\.com/#person"[^}]*?"@type"\s*:\s*(\[[^\]]+\]|"[^"]+")',
        html,
        re.S,
    )
    if not pub_match:
        pub_match = re.search(
            r'"@type"\s*:\s*(\[[^\]]+\]|"[^"]+")[^}]*?"@id"\s*:\s*"https://worktoolslab\.com/#person"',
            html,
            re.S,
        )
    if pub_match:
        publisher_id = "https://worktoolslab.com/#person"
        publisher_type = pub_match.group(1)

    author_id = None
    am = re.search(
        r'"author"\s*:\s*\{[^}]*?"@id"\s*:\s*"(https://worktoolslab\.com/[^"]+)"',
        html,
        re.S,
    )
    if am:
        author_id = am.group(1)

    fields = {
        "title": title,
        "meta": desc,
        "og_title": og_title,
        "og_desc": og_desc,
        "twitter_title": tw_title,
        "twitter_desc": tw_desc,
        "jsonld_headline": jsonld_headline,
        "jsonld_description": jsonld_description,
    }
    prefix_fields = [name for name, val in fields.items() if val and PREFIX.match(val)]

    return {
        "url": url,
        **fields,
        "prefix_fields": prefix_fields,
        "has_prefix": bool(prefix_fields),
        "publisher_id": publisher_id,
        "publisher_type": publisher_type,
        "author_id": author_id,
    }


def main() -> None:
    pages = json.loads(CACHE.read_text(encoding="utf-8"))
    urls = [
        p["url"]
        for p in pages
        if p.get("type") == "post"
        or any(
            token in p.get("url", "")
            for token in ("best-", "-vs-", "-review-", "how-to", "task-management")
        )
    ]
    urls.extend(
        [
            "https://worktoolslab.com/about/hayssam-dennaoui/",
            "https://worktoolslab.com/how-we-review-tools/",
            "https://worktoolslab.com/about/",
        ]
    )
    urls = sorted(set(urls))
    results = [fetch_meta(u) for u in urls]
    OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"AUDITED {len(results)}")
    print(f"WITH_PREFIX {sum(1 for r in results if r.get('has_prefix'))}")
    print(f"ERRORS {sum(1 for r in results if r.get('error'))}")
    for r in results:
        if r.get("has_prefix") or r.get("error"):
            print("---", r.get("url"))
            if r.get("error"):
                print("ERROR", r["error"])
            for key in ("title", "meta", "og_title", "jsonld_headline"):
                if r.get(key):
                    print(f"{key}: {r[key][:180]}")


if __name__ == "__main__":
    main()
