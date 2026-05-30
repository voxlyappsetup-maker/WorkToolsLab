# Content Operations State — WorkToolsLab

> **Living document.** Update at the end of each working session.  
> Do not rely on ChatGPT memory for this file — edit locally.

**Last updated:** 2026-05-29 (documentation bootstrap)

## Active focus

| Field | Value |
|-------|--------|
| **Current article / URL** | _Set before each session — e.g. Microsoft Teams review update_ |
| **Focus keyword** | _e.g. microsoft teams for small business_ |
| **Stage** | _idea / draft / SEO / links / pre-publish / published / monitor_ |
| **Next action** | _e.g. apply patch report, request indexing, draft new roundup_ |

## LinkOps snapshot

| Item | Value |
|------|--------|
| LinkOps version | 1.7.6 |
| Content cache | `data/worktoolslab_content_cache.json` — refresh with `fetch` |
| GSC cache imported | 2026-05-29 (see latest report header for exact timestamp) |
| Worklog | `config/worklog.json` loaded (~11 pages tracked) |

### Latest reports (replace filenames after each run)

| Report | File (example) |
|--------|----------------|
| Next actions | `reports/next_actions_20260529_151036.md` |
| Article roadmap | `reports/new_article_roadmap_20260529_151104.md` |
| Last per-page optimize | `reports/content_optimization_microsoft-teams-review-for-small-businesses_20260529_145528.md` |
| Last per-page patch | `reports/seo_patch_microsoft-teams-review-for-small-businesses_20260529_145532.md` |

### Roadmap summary (from last roadmap run — verify in MD file)

- Displayed items: **8** (updates + manual review; **0** create-new high/medium)
- Notable **update_existing_page**: productivity, communication (remote), PM freelancers, task management
- Notable **manual_review**: job management software, other ambiguous queries (see report)
- **Excluded:** 27 queries (already covered, low impressions, etc.)

### Next-actions summary (from last next-actions run)

- **0** unresolved clusters (with `--exclude-done` and filters)
- **8** clusters in worklog as handled/monitor-only
- Filters used: min impressions 20, max clicks 0, max position 90

## Worklog (status only)

Statuses in `config/worklog.json`: `done`, `monitor_only`, `request_indexing_done`, `skip`, `needs_review`.

**Do not paste full worklog here** — open `config/worklog.json` locally for URLs and notes.

After completing work on a URL:

```json
"https://worktoolslab.com/your-page-slug/": {
  "status": "done",
  "note": "YYYY-MM-DD: brief note"
}
```

## Queue (editorial — you maintain)

### High priority updates

- [ ] _Copy from top of latest `new_article_roadmap_*.md` or `next_actions_*.md`_
- [ ] Best Productivity Tools for Small Teams — team productivity tools (if not marked done in worklog)
- [ ] Best Communication Tools for Remote Teams — remote work communication tools

### Manual review decisions needed

- [ ] job management software for small teams (field-service vs PM — decide before drafting)
- [ ] _Other `manual_review` rows from roadmap_

### New articles (when roadmap shows create_new)

- [ ] _None in last roadmap run — recheck after `roadmap` command_

### Recently completed (log briefly)

- _Move items here when worklog status = done; include date_

## GSC / data hygiene

- [ ] Export fresh GSC CSVs to `exports/` when data is stale
- [ ] `gsc-import` after new exports
- [ ] `fetch` after WordPress publishes

## Session log (optional, one line per session)

| Date | What changed |
|------|----------------|
| 2026-05-29 | Memory offload docs created; LinkOps v1.7.6 brand gap-reason fix in working tree |

## Notes

- Affiliate and policy pages: do not strip disclosures when editing.
- Branded queries must target the **same brand** review URL (LinkOps brand guard).
- Productivity updates: do not use Blog or unrelated review pages as “related” sources in reports.
