# WorkToolsLab — Operations Handoff

**Site:** [worktoolslab.com](https://worktoolslab.com)  
**Local project:** `C:\dev\worktoolslab_linkops` (LinkOps — read-only WordPress + GSC assistant)  
**LinkOps version:** 1.7.6 (see `linkops/__init__.py`)

## What this repo does

LinkOps **does not** publish, update, or delete WordPress content. It:

- Caches published posts/pages (`fetch`)
- Analyzes internal links (`analyze`, `suggest`)
- Imports **local** GSC CSV exports (`gsc-import`)
- Reports opportunities, next actions, article roadmap, optimization audits, SEO patches

Credentials live in `.env` (never commit). Reports go to `reports/` (gitignored).

## Documentation map

| File | Purpose |
|------|---------|
| [MEMORY_OFFLOAD_POLICY.md](MEMORY_OFFLOAD_POLICY.md) | What lives locally vs in chat |
| [CONTENT_OPERATIONS_STATE.md](CONTENT_OPERATIONS_STATE.md) | **Living** snapshot — update each session |
| [ARTICLE_WORKFLOW_RULES.md](ARTICLE_WORKFLOW_RULES.md) | Draft → publish → post-publish |
| [INTERNAL_LINKING_POLICY.md](INTERNAL_LINKING_POLICY.md) | Link quality and exclusions |
| [NEXT_CHAT_PROMPT.md](NEXT_CHAT_PROMPT.md) | Paste into a **new** ChatGPT thread |
| [SITE_FOCUS_AUTHORITY_AUDIT_2026_07.md](SITE_FOCUS_AUTHORITY_AUDIT_2026_07.md) | July 2026 focus/authority audit |
| [SITE_AUTHORITY_UPGRADE_ROADMAP_2026_07.md](SITE_AUTHORITY_UPGRADE_ROADMAP_2026_07.md) | P0/P1/P2 implementation roadmap |
| [ARTICLE_EVIDENCE_FRAMEWORK.md](ARTICLE_EVIDENCE_FRAMEWORK.md) | Evidence levels + testing honesty rules |
| [P0_A_WORDPRESS_IMPLEMENTATION_CHECKLIST.md](P0_A_WORDPRESS_IMPLEMENTATION_CHECKLIST.md) | Owner-executable P0-A publish sequence |
| [AUTHOR_BYLINE_SCHEMA_IMPLEMENTATION_2026_07.md](AUTHOR_BYLINE_SCHEMA_IMPLEMENTATION_2026_07.md) | Byline + Rank Math schema strategy |
| [P0_A_AUTHORITY_LIVE_IMPLEMENTATION_RECORD_2026_07.md](P0_A_AUTHORITY_LIVE_IMPLEMENTATION_RECORD_2026_07.md) | Live P0-A authority rollout record |
| [SEO_METADATA_PREFIX_AUDIT_2026_07.md](SEO_METADATA_PREFIX_AUDIT_2026_07.md) | Rank Math prefix audit — **0 errors remaining** |
| [LEGACY_FREELANCERS_URL_REMEDIATION_2026_07.md](LEGACY_FREELANCERS_URL_REMEDIATION_2026_07.md) | `-2` URL verification + P0-4 closeout |
| [P0_5_HOME_AUDIENCE_ROUTING_LIVE_CLOSEOUT_2026_07.md](P0_5_HOME_AUDIENCE_ROUTING_LIVE_CLOSEOUT_2026_07.md) | **P0-5 PASS** — Home audience routing closeout |
| [P0_4_LEGACY_FREELANCERS_URL_GSC_CLOSEOUT_2026_07.md](P0_4_LEGACY_FREELANCERS_URL_GSC_CLOSEOUT_2026_07.md) | **P0-4 PASS** — redirect/GSC closeout |
| [P0_3_FREE_PM_LEVEL3_LIVE_CLOSEOUT_2026_07.md](P0_3_FREE_PM_LEVEL3_LIVE_CLOSEOUT_2026_07.md) | **P0-3 PASS** — LEVEL 3 live publication closeout |
| [P0_3_CLICKUP_DIRECT_TESTING_EVIDENCE_2026_07.md](P0_3_CLICKUP_DIRECT_TESTING_EVIDENCE_2026_07.md) | ClickUp evidence (2026-07) |
| [P0_3_TRELLO_DIRECT_TESTING_EVIDENCE_2026_07.md](P0_3_TRELLO_DIRECT_TESTING_EVIDENCE_2026_07.md) | Trello evidence |
| [P0_3_OFFICIAL_PLAN_VERIFICATION_2026_07.md](P0_3_OFFICIAL_PLAN_VERIFICATION_2026_07.md) | Official plan/feature verification |
| [../content/drafts/best-free-project-management-tools-for-freelancers-level3-2026-07.md](../content/drafts/best-free-project-management-tools-for-freelancers-level3-2026-07.md) | LEVEL 3 source draft (superseded by live publish) |
| [P0_3_FREE_PM_FREELANCERS_EVIDENCE_AUDIT_2026_07.md](P0_3_FREE_PM_FREELANCERS_EVIDENCE_AUDIT_2026_07.md) | P0-3 claim audit (LEVEL 3 live) |
| [P0_3_OWNER_TESTING_EXECUTION_QUEUE_2026_07.md](P0_3_OWNER_TESTING_EXECUTION_QUEUE_2026_07.md) | Owner testing steps (completed) |
| [P0_3_FREE_PM_LEVEL3_ARTICLE_BLUEPRINT_2026_07.md](P0_3_FREE_PM_LEVEL3_ARTICLE_BLUEPRINT_2026_07.md) | Article structure blueprint (published) |
| [P1_3_TOOLS_PAGE_PROBLEM_ORIENTED_RESTRUCTURE_LIVE_CLOSEOUT_2026_07.md](P1_3_TOOLS_PAGE_PROBLEM_ORIENTED_RESTRUCTURE_LIVE_CLOSEOUT_2026_07.md) | **P1-3 PASS** — Tools page problem-oriented restructure |
| [P1_1_TASK_VS_PROJECT_MANAGEMENT_LEVEL2_POLISH_LIVE_CLOSEOUT_2026_07.md](P1_1_TASK_VS_PROJECT_MANAGEMENT_LEVEL2_POLISH_LIVE_CLOSEOUT_2026_07.md) | **P1-1 PASS** — Task vs PM LEVEL 2 polish |
| [P0_6_BEST_PM_FREELANCERS_CTR_DIFFERENTIATION_LIVE_CLOSEOUT_2026_07.md](P0_6_BEST_PM_FREELANCERS_CTR_DIFFERENTIATION_LIVE_CLOSEOUT_2026_07.md) | **P0-6 PASS** — paid freelancer roundup CTR differentiation |
| [P0_7_PUBLISHER_PROFILEPAGE_SCHEMA_LIVE_FIX_2026_07.md](P0_7_PUBLISHER_PROFILEPAGE_SCHEMA_LIVE_FIX_2026_07.md) | **P0-7 PASS** — publisher/ProfilePage schema fix |
| [WORDPRESS_MU_PLUGIN_DEPLOYMENT_STATE_2026_07.md](WORDPRESS_MU_PLUGIN_DEPLOYMENT_STATE_2026_07.md) | MU plugin mirror + deployment (author-links synced 2026-07-10) |
| [../wordpress/mu-plugins/](../wordpress/mu-plugins/) | Repository mirrors of live MU plugins |
| [TRAFFIC_DIAGNOSIS_2026_06.md](TRAFFIC_DIAGNOSIS_2026_06.md) | June traffic diagnosis (historical) |
| [CONTENT_STRATEGY_RESET_2026_06.md](CONTENT_STRATEGY_RESET_2026_06.md) | June strategy reset + July addendum |
| [DISTRIBUTION_AUTHORITY_PLAN_2026_06.md](DISTRIBUTION_AUTHORITY_PLAN_2026_06.md) | Distribution plan |
| [distribution_log_2026_06.md](distribution_log_2026_06.md) | LinkedIn distribution results |
| [../README.md](../README.md) | LinkOps CLI reference |

## Core site pages

| Page | Typical slug |
|------|----------------|
| Home | `/` |
| Start Here | `/start-here/` |
| Tools | `/tools/` — **P1-3 problem-oriented decision hub LIVE** |
| Blog | `/blog/` |
| About | `/about/` |
| Contact | `/contact/` |

Editorial content is mostly **roundups**, **reviews**, **comparisons**, and **guides** under `/best-*`, `/*-review-*`, `/*-vs-*`, `/how-to-*`.

## Standard command sequence

```powershell
cd C:\dev\worktoolslab_linkops
.\.venv\Scripts\Activate.ps1

# Refresh site + GSC (adjust CSV paths)
python -m linkops.cli fetch
python -m linkops.cli gsc-import --queries-csv "exports\gsc_queries.csv" --pages-csv "exports\gsc_pages.csv"

# Sitewide priorities
python -m linkops.cli next-actions --exclude-done --min-impressions 20 --max-position 90
python -m linkops.cli roadmap --min-impressions 10 --max-position 90 --max-candidates 20
```

Per page:

```powershell
python -m linkops.cli optimize --target-url "https://worktoolslab.com/<slug>/" --target-keyword "<keyword>"
python -m linkops.cli patch --target-url "https://worktoolslab.com/<slug>/" --target-keyword "<keyword>"
python -m linkops.cli suggest --target-url "https://worktoolslab.com/<slug>/" --target-keyword "<keyword>" --max-suggestions 8
```

## Config files

| File | Purpose |
|------|---------|
| `config/worklog.json` | Page status: `done`, `monitor_only`, `request_indexing_done`, `skip`, `needs_review` |
| `config/worklog.example.json` | Template |
| `config/query_target_overrides.json` | Optional manual GSC query → URL map |
| `data/worktoolslab_content_cache.json` | WordPress cache (from `fetch`) |
| `data/gsc_cache.json` | GSC cache (from `gsc-import`) |

**Worklog:** Present locally (~11 pages tracked as of 2026-05-29). Open `config/worklog.json` on your machine for URLs and notes — not duplicated here.

## Report artifacts (latest wins)

Use the **newest timestamp** in `reports/`:

| Pattern | Use |
|---------|-----|
| `next_actions_*.md` | What to work on next (grouped by URL) |
| `new_article_roadmap_*.md` | Create vs update vs manual review |
| `content_optimization_<slug>_*.md` | Coverage / intent audit |
| `seo_patch_<slug>_*.md` | Paste-ready title/meta/intro/FAQ |
| `internal_link_suggestions_<slug>_*.md` | Sentence-level link ideas |
| `gsc_opportunities_*.md` | Raw query-level opportunities |

Example recent runs (replace after your next session):

- `reports/next_actions_20260529_151036.md`
- `reports/new_article_roadmap_20260529_151104.md`

## Git (repo state)

Recent commits include article roadmap and SEO patch guardrails. Uncommitted work may include v1.7.x roadmap changes — run `git status` before committing.

**Do not commit:** `data/`, `reports/`, `exports/`, `config/worklog.json`, `.env`

## Content style (summary)

- Plain text deliverables; SEO block with Meta Description **< 160 chars**
- Natural internal links; avoid Blog/Trello/random reviews as filler sources
- See [ARTICLE_WORKFLOW_RULES.md](ARTICLE_WORKFLOW_RULES.md)

## Handoff checklist (end of session)

1. [ ] Update `config/worklog.json` for completed URLs
2. [ ] Update `docs/CONTENT_OPERATIONS_STATE.md`
3. [ ] Regenerate `reports/` if GSC or site changed
4. [ ] Next chat: paste `docs/NEXT_CHAT_PROMPT.md`
