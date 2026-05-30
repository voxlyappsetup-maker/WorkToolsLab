# Memory Offload Policy — WorkToolsLab

## Principle

**ChatGPT (or any chat assistant) is not the system of record** for article state, SEO decisions, internal links, or publishing status.

**Local project files are the source of truth:**

| What | Where |
|------|--------|
| Published page inventory | `data/worktoolslab_content_cache.json` (from `fetch`) |
| GSC performance data | `data/gsc_cache.json` (from `gsc-import`) |
| Handled / monitor pages | `config/worklog.json` |
| Query → URL overrides | `config/query_target_overrides.json` (optional) |
| Latest priorities | `reports/next_actions_*.md` |
| New vs update article plan | `reports/new_article_roadmap_*.md` |
| On-page audit | `reports/content_optimization_*.md` |
| Paste-ready edits | `reports/seo_patch_*.md` |
| Internal link ideas | `reports/internal_link_suggestions_*.md` |
| Operational snapshot | `docs/CONTENT_OPERATIONS_STATE.md` (you update) |
| Rules and handoff | Other files in `docs/` |

## Do not store in chat memory

- Full article drafts or revision history
- Complete lists of every URL on the site
- Application passwords, `.env` contents, or API keys
- Entire GSC CSV row dumps
- Long worklog notes with private editorial commentary (keep those in `worklog.json` only)

## Do store in chat (minimal)

- The **current task** for this session (one URL or one article)
- A pointer: “read `docs/NEXT_CHAT_PROMPT.md` and latest `reports/*`”
- Decisions made **this session** that are not yet written to local files (then write them before ending)

## After each work session

1. Update `config/worklog.json` for pages you finished or set to `monitor_only`.
2. Refresh `docs/CONTENT_OPERATIONS_STATE.md` (date, active article, latest report filenames).
3. Run LinkOps commands so `reports/` reflects current GSC/cache (see `WORKTOOLSLAB_HANDOFF.md`).
4. Start the **next** chat with `docs/NEXT_CHAT_PROMPT.md` — not a recap of old articles.

## Regenerating truth from LinkOps

From `C:\dev\worktoolslab_linkops` (venv active):

```powershell
python -m linkops.cli fetch
python -m linkops.cli gsc-import --queries-csv "exports\gsc_queries.csv" --pages-csv "exports\gsc_pages.csv"
python -m linkops.cli next-actions --exclude-done --min-impressions 20 --max-position 90
python -m linkops.cli roadmap --min-impressions 10 --max-position 90 --max-candidates 20
```

Per-article:

```powershell
python -m linkops.cli optimize --target-url "<url>" --target-keyword "<keyword>"
python -m linkops.cli patch --target-url "<url>" --target-keyword "<keyword>"
python -m linkops.cli suggest --target-url "<url>" --target-keyword "<keyword>" --max-suggestions 8
```

## Git

- Commit code and `docs/` when stable.
- Do **not** commit: `.env`, `data/`, `reports/`, `exports/`, `config/worklog.json` (see `.gitignore`).
- Worklog example: `config/worklog.example.json`.
