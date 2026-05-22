# WorkToolsLab LinkOps

**Read-only internal linking assistant for [WorkToolsLab.com](https://worktoolslab.com).**

LinkOps v1.5.1 fetches published WordPress posts and pages, analyzes existing internal links, generates human-reviewable internal link suggestions, scores **local Google Search Console CSV exports** for SEO opportunities, produces **read-only content optimization reports**, and generates **paste-ready SEO patches** for manual WordPress edits. **It never modifies WordPress content** — no publish, update, delete, or draft operations.

## Safety (v1)

- Read-only WordPress REST API access (`GET` only for content fetch)
- All write/update/delete methods are explicitly blocked in code
- Credentials live in `.env` (never committed)
- Application passwords are never printed or written to reports
- Reports contain only public URLs and editorial suggestions

## Requirements

- Windows 10/11 with PowerShell
- Python 3.10+

## Setup (Windows PowerShell)

```powershell
cd C:\path\to\WorkToolsLab-LinkOps

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt

Copy-Item .env.example .env
# Edit .env with your WordPress username and Application Password
notepad .env
```

### `.env` variables

| Variable | Description |
|----------|-------------|
| `WORKTOOLSLAB_BASE_URL` | Site URL (default `https://worktoolslab.com`) |
| `WORDPRESS_USERNAME` | WordPress user with read access |
| `WORDPRESS_APP_PASSWORD` | [Application Password](https://make.wordpress.org/core/2020/11/05/application-passwords-integration-guide/) (spaces optional) |

Create an Application Password in WordPress: **Users → Profile → Application Passwords**.

## Commands

### 1. Fetch published content

```powershell
python -m linkops.cli fetch
```

Saves normalized cache to `data/worktoolslab_content_cache.json`.

### 2. Analyze sitewide internal links

```powershell
python -m linkops.cli analyze
```

Writes `reports/site_internal_link_map_YYYYMMDD_HHMMSS.csv`.

### 3. Suggest links for a target article

```powershell
python -m linkops.cli suggest --target-url "https://worktoolslab.com/your-new-article/" --target-keyword "video meeting remote" --max-suggestions 8
```

Optional flags:

```powershell
python -m linkops.cli suggest ... --include-high-risk
python -m linkops.cli suggest ... --include-core-pages
```

By default, v1.2 **excludes high-risk suggestions** and **excludes core utility pages** (Home, Blog, Contact, About). Use `--include-high-risk` or `--include-core-pages` only when you want to review borderline candidates manually.

Requires cache from `fetch`. Generates:

- `reports/internal_link_suggestions_<slug>_<timestamp>.md`
- `reports/internal_link_suggestions_<slug>_<timestamp>.csv`

### WorkToolsLab examples

```powershell
python -m linkops.cli fetch

python -m linkops.cli analyze

python -m linkops.cli suggest `
  --target-url "https://worktoolslab.com/best-communication-tools-for-remote-teams/" `
  --target-keyword "remote work communication tools" `
  --max-suggestions 8
```

### 4. Import Google Search Console CSV exports (v1.3)

Export data from [Google Search Console](https://search.google.com/search-console) (Performance → Queries / Pages / Query+Page) and save CSV files locally. LinkOps does **not** connect to Google APIs and does **not** send data externally.

```powershell
python -m linkops.cli gsc-import `
  --queries-csv "exports/gsc_queries.csv" `
  --pages-csv "exports/gsc_pages.csv"
```

Optional query+page dimension:

```powershell
python -m linkops.cli gsc-import `
  --queries-csv "exports/gsc_queries.csv" `
  --pages-csv "exports/gsc_pages.csv" `
  --query-pages-csv "exports/gsc_query_pages.csv"
```

Writes normalized cache to `data/gsc_cache.json` and prints an import summary (counts + skipped rows).

Supported headers include: Query/Top queries, Page/URL, Clicks, Impressions, CTR, Position (variants normalized automatically).

### 5. Generate GSC opportunity reports (v1.3)

Requires `data/gsc_cache.json` from `gsc-import` and `data/worktoolslab_content_cache.json` from `fetch`.

```powershell
python -m linkops.cli opportunities `
  --min-impressions 20 `
  --max-clicks 0 `
  --max-position 90
```

Writes:

- `reports/gsc_opportunities_<timestamp>.md`
- `reports/gsc_opportunities_<timestamp>.csv`

Opportunity statuses include: **Correct page**, **Possible cannibalization**, **Old or redirected URL visible**, **No obvious target**, **Content optimization needed**, and **Internal link support needed**. Reports include recommended actions and suggested `linkops.cli suggest` commands. No passwords or secrets are written to reports.

### v1.3.1 — Smarter GSC target matching

v1.3.1 improves how queries map to WordPress pages:

- **Query intent** (`broad_best_tools`, `specific_review`, `comparison`, `how_to`, …)
- **Page type** (`roundup_best_tools`, `review`, `comparison`, `guide`, …)
- **Intent-aware scoring** — broad commercial queries prefer roundup “best tools” pages over reviews or generic comparison articles
- **Optional overrides** — `config/query_target_overrides.json` (copy from `config/query_target_overrides.example.json`)
- **Action types** — `title_meta_ctr`, `internal_links`, `content_optimization`, `cannibalization_review`, etc.
- **Confidence** — `high` / `medium` / `low` with target selection reasons in Markdown and CSV

Overrides are **local, manual, and read-only**. LinkOps never writes this file for you. If an override URL is missing from the WordPress cache, the report still lists it and notes that fact.

Example workflow:

```powershell
Copy-Item config\query_target_overrides.example.json config\query_target_overrides.json
# Edit overrides as needed (optional)

python -m linkops.cli fetch
python -m linkops.cli gsc-import --queries-csv "exports\gsc_queries.csv" --pages-csv "exports\gsc_pages.csv"
python -m linkops.cli opportunities --min-impressions 20 --max-clicks 0 --max-position 90
```

### 6. Content optimization report (v1.4)

Requires `data/worktoolslab_content_cache.json` from `fetch`. Optionally enriches with `data/gsc_cache.json` when available (no Google API).

```powershell
python -m linkops.cli optimize `
  --target-url "https://worktoolslab.com/best-project-management-tools-for-small-teams/" `
  --target-keyword "project management software for small teams"
```

Optional flags:

```powershell
python -m linkops.cli optimize ... --query "alternate gsc query text"
python -m linkops.cli optimize ... --max-faq-suggestions 5 --max-heading-suggestions 5
```

Writes:

- `reports/content_optimization_<slug>_<timestamp>.md`
- `reports/content_optimization_<slug>_<timestamp>.csv`

The report audits keyword coverage (title, slug, headings, intro, body, FAQ), query/page intent alignment (v1.3.1 logic), intro and heading gaps, FAQ opportunities, deterministic title/meta suggestions, internal link support level, and an overall recommendation (`content_optimization`, `title_meta_ctr`, `internal_links_first`, etc.). **Suggestions only** — apply manually in WordPress.

Example workflow:

```powershell
python -m linkops.cli fetch
python -m linkops.cli gsc-import --queries-csv "exports\gsc_queries.csv" --pages-csv "exports\gsc_pages.csv"
python -m linkops.cli optimize `
  --target-url "https://worktoolslab.com/best-project-management-tools-for-small-teams/" `
  --target-keyword "project management software for small teams"
python -m linkops.cli optimize `
  --target-url "https://worktoolslab.com/webex-review-for-small-businesses/" `
  --target-keyword "Webex review for small businesses"
```

### 7. Paste-ready SEO patch (v1.5)

Requires `data/worktoolslab_content_cache.json` from `fetch`. Reuses the v1.4 optimize engine and outputs copyable WordPress edits (no HTML rewrites, no WordPress writes).

```powershell
python -m linkops.cli patch `
  --target-url "https://worktoolslab.com/clickup-vs-trello-for-small-teams/" `
  --target-keyword "clickup vs trello"
```

Optional flags:

```powershell
python -m linkops.cli patch ... --query "alternate gsc query"
python -m linkops.cli patch ... --max-faq-suggestions 5 --max-heading-suggestions 3
python -m linkops.cli patch ... --include-title-meta --include-intro --include-headings --include-faq
```

Writes:

- `reports/seo_patch_<slug>_<timestamp>.md`
- `reports/seo_patch_<slug>_<timestamp>.csv`

Patch types include `monitor_only`, `faq_patch`, `title_meta_patch`, `intro_patch`, `heading_patch`, `internal_link_patch`, `combined_light_patch`, and `manual_review`. Reports include a **Do Not Change** checklist and **Paste-Ready Changes** (title, meta, intro, headings, FAQ, internal link command).

## Workflow

1. Run `fetch` after publishing new content (or on a schedule).
2. Export GSC CSVs periodically; run `gsc-import` then `opportunities` to prioritize queries.
3. Run `optimize` on high-impression targets to audit on-page coverage before editing.
4. Run `patch` when you want paste-ready title/meta/intro/heading/FAQ snippets for manual WordPress edits.
5. Run `suggest` with the new article URL and optional keyword.
6. Review the Markdown report — suggested sentences use Markdown link syntax for copy/edit.
7. **Manually** add approved links and copy changes in WordPress.
8. Use the report’s “Request Indexing” list in Google Search Console after updates.

**No WordPress update is performed by LinkOps in v1.**

## v1.2 editorial relevance rules

LinkOps v1.2 behaves more like a human SEO editor. It prefers **no suggestions** or **only 1–2 highly relevant suggestions** instead of filling reports with weak links.

### Primary vs secondary target clusters

- **Primary cluster** is determined from the target URL slug, target title, and target keyword only.
- Full target article content is **not** used to assign primary clusters.
- Full content may add weak **secondary** hints (for example, productivity for a communication target).
- Full content will **not** promote a communication target into project management, task management, or workflow management clusters.

Example:

| Input | Result |
|-------|--------|
| Title: Best Communication Tools for Remote Teams | Primary: **communication** |
| Keyword: remote work communication tools | Secondary: productivity (if hinted in content) |
| Slug: best-communication-tools-for-remote-teams | Never: project/task/workflow from body alone |

### Communication cluster rules

For a communication target, accepted source pages usually need title, slug, H1, or H2 signals such as:

- communication, remote, video meeting, meeting, chat, messaging
- Slack, Zoom, Microsoft Teams, Google Meet, Webex, Google Workspace, collaboration

Body-only mentions of generic words like communication, team, remote, tools, or work are **not** enough for low-risk suggestions.

### Core and policy pages

Excluded from suggestions by default:

- Home, Blog, Contact, About
- Privacy Policy, Terms, Editorial Policy, Affiliate Disclosure

Use `--include-core-pages` to allow core pages as medium/high review candidates only (never automatic low-risk). Policy/legal pages are always excluded from suggestions. Core pages may still appear under “already linking to target.”

### Unrelated commercial clusters

For a communication target, project management, task management, and workflow pages are excluded unless their title, slug, or H2 contains a communication-specific term or known communication tool. A sentence in the body is not enough.

Example: **Monday.com vs Asana** is rejected for a communication target unless it has a dedicated communication section in headings.

### Strong suggestions require heading-level relevance

Low-risk / strong suggestions require:

- source title, slug, or H2 matches the target primary cluster, **or**
- source title, slug, or H2 contains a known related entity/tool, **or**
- source is in an allowed supporting cluster with a clear communication section in H2

Body-only keyword overlap is medium at most, and is often rejected.

### Source page type classification

Sources are classified as: article, review, comparison, category guide, core page, or policy/legal page.

Internal linking suggestions:

- Prefer review, comparison, and category guide articles
- Exclude policy/legal pages
- Exclude core pages by default
- Penalize broad generic pages unless explicitly requested

### Quality cap

When **7 or more topically related pages already link** to the target:

- Report warns: “Target already has strong internal support. Additional links may not be necessary.”
- Stricter score thresholds apply
- At most **2** missing sources are returned, and only if they are very strong

Final recommendation examples:

- **No new links needed**
- **No new links are necessary unless you want one optional link from Webex or Google Workspace.**
- **Add only these links**
- **Review manually**

### Report sections (v1.2)

Markdown reports include:

- Primary and secondary target clusters
- Editorial recommendation
- Internal support quality note
- Core pages excluded
- Strong and medium suggestions with page type
- Already linking / related already linking
- Rejected candidates with reasons
- GSC “Request Indexing” list (low/medium only)

## v1.1 scoring notes (still applies)

- **Domain stopwords** — Generic editorial terms are filtered or heavily downweighted.
- **Topic clusters** — Deterministic clusters with compatibility rules.
- **Quality over quantity** — Fewer suggestions when only 1–2 strong matches exist.
- **Risk levels** — `low`, `medium`, `high`; high-risk excluded by default.

## Tests

```powershell
pip install -r requirements.txt
pytest tests/ -v
```

v1.2 tests cover primary cluster assignment, core page exclusion, commercial cluster rejection, strict mode when 7+ related pages link, and final recommendation text.

v1.3 tests cover GSC CSV parsing, opportunity scoring, cannibalization/old-URL detection, and GSC report sections.

v1.3.1 tests cover query/page intent matching, roundup preference for broad queries, query overrides, action types, and extended report columns.

v1.4 tests cover content optimization analysis, coverage audit, FAQ/heading suggestions, title/meta length, intent alignment, and optimization report Markdown/CSV sections.

v1.5 tests cover paste-ready SEO patch generation (`monitor_only`, `faq_patch`, brand capitalization, report sections, CSV columns).

v1.4.1 improves optimize report quality: no contradictory heading gaps when H2/H3 already match, safe slug guidance (`Keep current slug`), natural title case, related GSC query enrichment, and clearer recommendations (`monitor_only`, `Why this recommendation`, `No urgent content gaps detected`).

v1.4.2 improves broad “best tools” queries: no duplicated `best best` phrasing, topic-specific FAQ/intro/SEO templates (collaboration vs project management vs communication), stricter FAQ detection, suppressed intro sentences when coverage is already strong, and `faq_optimization` when only FAQ coverage is weak.

v1.4.3 improves comparison queries (`clickup vs trello`, `monday.com vs asana`): correct brand capitalization (ClickUp, Trello, Monday.com), natural comparison SEO titles without a `Best` prefix, and comparison-specific FAQ/heading suggestions.

v1.4.4 improves comparison FAQ scoring: pages with 3+ strong comparison FAQ questions (both brands, better-than / which-is-better / difference / should-use patterns) are treated as covered — no false `faq_optimization` when comparison FAQs are already strong.

v1.5 adds the `patch` command: paste-ready SEO patches (Markdown + CSV) derived from the optimize engine, with editorial guardrails (Do Not Change checklist, no full rewrites, no slug churn, topic-specific FAQ templates, internal link command only).

v1.5.1 ensures paste-ready reports no longer place placeholder answers inside copyable sections; current-data FAQ candidates (pricing, plans, etc.) are moved to **Manual Review Needed** with deterministic evergreen answers only when safe.

## Project layout

```
linkops/           Core package
  cli.py           fetch | analyze | suggest | gsc-import | opportunities | optimize | patch
  wordpress_client.py   Read-only REST client
  suggestion_engine.py  Deterministic topical scoring
  gsc_parser.py         Local GSC CSV import
  opportunity_engine.py GSC opportunity scoring
  gsc_report_writer.py  GSC Markdown/CSV reports
  content_optimizer.py  Content optimization analysis
  content_optimization_report_writer.py  Optimization Markdown/CSV
  seo_patch_generator.py  Paste-ready SEO patch from optimize
  seo_patch_report_writer.py  Patch Markdown/CSV
exports/           Place GSC CSV exports here (not committed)
config/            Optional query_target_overrides.json (local manual)
data/              Content cache (gitignored)
reports/           Generated reports (gitignored)
tests/             Unit tests
```

## License

Internal tool for WorkToolsLab editorial use.
