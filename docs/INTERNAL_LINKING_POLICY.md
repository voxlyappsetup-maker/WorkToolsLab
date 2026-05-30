# Internal Linking Policy — WorkToolsLab

**Site:** [worktoolslab.com](https://worktoolslab.com)  
**Tooling:** LinkOps `suggest` (read-only). See `README.md` for engine rules (v1.2+).

## Goals

- Help readers and crawlers discover **topically related** tools content.
- Avoid spammy or excessive cross-links.
- Never force links from unrelated commercial clusters (e.g. PM roundup → communication target).

## Default exclusions (LinkOps)

Unless you pass `--include-core-pages` or `--include-high-risk`:

| Excluded | Reason |
|----------|--------|
| Home, Blog, About, Contact | Core / utility; weak as contextual sources |
| Privacy, Terms, Editorial Policy, Affiliate Disclosure | Policy / legal |
| Unrelated roundups (PM, task, workflow) | When target is communication/productivity and source lacks heading-level match |
| Product review pages | When target is a broad roundup update (unless query names that brand) |
| High-risk partial matches | Body-only keyword overlap |

## When to link

- **1–3 strong links** per update is usually enough; prefer **1–2** if coverage is already strong.
- Anchor text must read naturally in the sentence (Markdown `[phrase](url)` in LinkOps reports for copy/edit).
- Prefer **same-topic** roundups, guides, or comparisons with clear H2/title alignment.
- For **review** articles: link to relevant roundups or concept guides (e.g. task vs project management), not random tool reviews.

## Cluster discipline (examples)

| Target topic | Good sources | Avoid |
|--------------|--------------|--------|
| Communication / remote / video meeting | Communication roundups, video meeting reviews (Zoom, Teams, Webex), remote work guides | Generic PM or task tool lists |
| Productivity | Productivity roundup, collaboration roundup (if relevant), same-topic guides | Unrelated Trello/Asana reviews |
| Project management | PM roundups, PM comparisons, how-to-choose guides | Communication-only pages |
| Branded review (e.g. Microsoft Teams) | Same-brand or same cluster only | Other brands’ review pages as “related” |

## Core pages (site map)

Use intentionally, not as filler:

- **Start Here** — onboarding / site navigation (sparingly).
- **Tools** — hub (sparingly).
- **Blog** — only when the link is editorially justified; LinkOps excludes Blog from default suggestion sources for roundup updates.

## Workflow

1. Run `fetch` after publish.
2. Run `suggest --target-url ... --target-keyword ...` for the page you are editing.
3. Approve only **low-risk** or clearly labeled medium-risk lines.
4. Paste into WordPress manually; LinkOps does not write to the site.

## Affiliate and editorial

- Preserve existing affiliate disclosures and editorial policy pages; do not strip compliance blocks when adding links.
- Internal links support SEO and UX; they do not replace clear CTAs or disclosure where required.
