# SEO Metadata Prefix Audit — WorkToolsLab

**Date:** 2026-07-06  
**Phase:** P0-A closeout — read-only audit  
**Problem:** Literal field labels (`SEO Title:`, `Meta Description:`) pasted into Rank Math SEO fields from LinkOps/article delivery blocks.

**Correction rule:** Remove only the accidental label prefix. Do not run CTR experiments or rewrite copy beyond prefix removal unless an approved repository value exists.

---

## Audit scope and methods

| Source | Role in audit |
|--------|----------------|
| **Live WebFetch (read-only)** | Primary check — first line usually reflects `<title>` / document title |
| **Subagent WebFetch batch** | 18 roundup/review URLs — first 3 lines scanned |
| **WordPress content cache** | `data/worktoolslab_content_cache.json` — **no Rank Math fields stored**; no prefix hits in post body |
| **Local curl / Python urllib** | **403 Forbidden** on bulk HTML fetch — inconclusive for `<meta>` tags |
| **Repository docs/content** | Label lines in checklists only — **not live errors** |
| **LinkOps reports** | `reports/` gitignored — not scanned in repo |
| **GSC exports** | Not modified; not used for mutation |

**Total URLs in scope:** **32** post/article URLs from content cache + **3** authority pages (profile, methodology, about) = **35** audited via WebFetch where accessible.

---

## Summary counts

| Classification | Count |
|----------------|------:|
| **A — Confirmed live metadata error** | **1** |
| **B — Suspected live metadata error** | **1** |
| **D — Fixed** | **1** |
| **C — Repository/documentation only** | Multiple checklist lines (not live) |
| **Clean (no title prefix in live WebFetch title)** | **33** |

---

## Classification key

| Code | Meaning |
|------|---------|
| **A** | Literal prefix confirmed in live document title (WebFetch) and/or owner-visible SERP |
| **B** | Strong suspicion; HTML meta not confirmed due to access limits |
| **D** | Previously affected; live title now clean |
| **C** | Docs/handoff labels only |

---

## Confirmed and suspected pages

### 1. Notion vs Trello vs ClickUp — **A (title)** / **B (meta)**

| Field | Value |
|-------|--------|
| **URL** | https://worktoolslab.com/notion-vs-trello-vs-clickup-which-one-is-best-for-your-workflow/ |
| **Classification** | **A — Confirmed live SEO title error** |
| **Live title evidence (WebFetch)** | `SEO Title: Notion vs Trello vs ClickUp: Best Workflow Tool?` |
| **Offending prefix** | `SEO Title:` |
| **Proposed corrected SEO title** | `Notion vs Trello vs ClickUp: Best Workflow Tool?` |
| **Meta description evidence** | Not readable via WebFetch; **B — suspected** — owner should open Rank Math sidebar |
| **Proposed corrected meta description** | Remove `Meta Description:` prefix only if present; keep existing description body unchanged |
| **Owner action required?** | **Yes** |
| **Rank Math fields** | SEO Title; Meta Description |
| **Validation after change** | View page source `<title>`; Rank Math preview; optional GSC URL Inspection |

**Note:** Public search results reported by owner may still show old prefixed title until recrawl.

---

### 2. ClickUp vs Trello for Small Teams — **D (fixed)**

| Field | Value |
|-------|--------|
| **URL** | https://worktoolslab.com/clickup-vs-trello-for-small-teams/ |
| **Classification** | **D — Fixed** |
| **Live title evidence (WebFetch)** | `ClickUp vs Trello for Small Teams: Which Is Better?` |
| **Owner-reported corrected SEO title** | `ClickUp vs Trello for Small Teams: Which Is Better?` |
| **Owner-reported corrected meta** | `Compare ClickUp vs Trello for small teams and see which tool is better for tasks, projects, workflows, collaboration, and growth.` |
| **Owner action required?** | **No** — verify meta has no prefix in Rank Math if not already checked |
| **Validation** | Re-inspect after Google recrawl if SERP still shows old snippet |

---

## Comparison pages — clean (WebFetch title check)

No `SEO Title:` prefix in live document title:

| URL | Live title (WebFetch first line) |
|-----|----------------------------------|
| `/monday-com-vs-clickup-for-small-teams/` | Monday.com vs ClickUp for Small Teams: Which Is Better? |
| `/monday-com-vs-asana-for-small-teams/` | Monday.com vs Asana for Small Teams \| WorkToolsLab |
| `/asana-vs-clickup-for-small-teams/` | Asana vs ClickUp for Small Teams: Which One Is Better? |
| `/teamwork-vs-asana-for-small-teams/` | Teamwork vs Asana for Small Teams: Which Is Better? |
| `/clickup-vs-trello-for-small-teams/` | ClickUp vs Trello for Small Teams: Which Is Better? **(fixed)** |

---

## June 2026 cleanup pages — title spot-check (clean)

| URL | Live title (WebFetch) |
|-----|------------------------|
| `/best-free-project-management-tools-for-freelancers/` | Best Free Project Management Tools for Freelancers (2026 Guide) |
| `/how-to-manage-tasks-in-a-small-team/` | How to Manage Tasks in a Small Team: Practical Guide |
| `/task-management-vs-project-management/` | Task Management vs Project Management: What Is the Difference? |
| `/trello-review-for-freelancers/` | Trello Review for Freelancers |

**Caveat:** Title clean in WebFetch does **not** guarantee Rank Math meta description fields are prefix-free. Owner spot-check recommended on posts edited from paste-ready SEO blocks.

---

## Roundups and reviews — batch check (clean titles)

Subagent WebFetch of 18 URLs found **no** `SEO Title:` or `Meta Description:` in first three visible lines. Includes all `best-*` roundups, communication/video guides, and product reviews in scope.

---

## Repository / documentation only (C)

These contain `SEO Title:` as **field labels**, not live Rank Math values:

| File | Notes |
|------|--------|
| `docs/P0_A_WORDPRESS_IMPLEMENTATION_CHECKLIST.md` | Rank Math field instructions |
| `content/authority/*.md` | Metadata tables for paste |
| `linkops/content_optimization_report_writer.py` | Report output labels |

---

## Exact owner correction queue

| Priority | URL | Action |
|----------|-----|--------|
| **P0** | `/notion-vs-trello-vs-clickup-which-one-is-best-for-your-workflow/` | Remove `SEO Title:` prefix from Rank Math SEO Title |
| **P0** | Same URL | Open Meta Description field — remove `Meta Description:` prefix if present |
| **P1** | All posts edited from LinkOps `patch` / paste-ready blocks (June cycle) | Rank Math sidebar spot-check for label prefixes |
| **P2** | Sitewide | Search Rank Math posts list is not available in repo — manual WP search not performed |

---

## Prevention (future)

When pasting from LinkOps SEO patch or article delivery blocks:

- Paste **only the value** after `SEO Title:` and `Meta Description:` labels.
- Never paste the label line into Rank Math fields.

Consider a future LinkOps guardrail to strip labels on copy — **out of scope for this closeout**.

---

## Related docs

- `docs/P0_A_AUTHORITY_LIVE_IMPLEMENTATION_RECORD_2026_07.md`
- `docs/P0_A_WORDPRESS_IMPLEMENTATION_CHECKLIST.md`
