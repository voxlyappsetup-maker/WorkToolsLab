import re
from html import unescape
from pathlib import Path

files = {
    "clickup": Path(r"C:\dev\worktoolslab_linkops\data\_tmp_clickup.html"),
    "notion": Path(r"C:\dev\worktoolslab_linkops\data\_tmp_notion.html"),
}
for label, path in files.items():
    if not path.exists():
        print(label, "MISSING")
        continue
    html = path.read_text(encoding="utf-8", errors="replace")
    print("FILE", label, "len", len(html))
    for pat, name in [
        (r"<title>([^<]+)</title>", "title"),
        (r'name="description"\s+content="([^"]*)"', "meta"),
        (r'property="og:title"\s+content="([^"]*)"', "og_title"),
        (r'property="og:description"\s+content="([^"]*)"', "og_desc"),
        (r'name="twitter:title"\s+content="([^"]*)"', "twitter_title"),
        (r'name="twitter:description"\s+content="([^"]*)"', "twitter_desc"),
    ]:
        m = re.search(pat, html, re.I)
        print(f"{name}:", unescape(m.group(1)) if m else "N/A")
    hm = re.search(r'"headline"\s*:\s*"([^"]+)"', html)
    dm = re.search(r'"description"\s*:\s*"([^"]+)"', html)
    print("jsonld_headline:", hm.group(1) if hm else "N/A")
    print("jsonld_description:", (dm.group(1)[:120] + "...") if dm else "N/A")
    print("---")
