# Article Workflow Rules — WorkToolsLab

**Site:** worktoolslab.com  
**Audience:** Small businesses and small teams choosing software tools.

## Content deliverable format (ChatGPT / editor)

Unless the user explicitly asks for HTML:

- **Paste-ready plain text** for WordPress (block editor or classic).
- Preserve **headings** (`##`, `###`) and **lists**.
- Do **not** wrap in HTML unless requested.

### Required SEO block (every article)

Include a clearly labeled block the user can paste into WordPress / SEO plugin:

| Field | Rule |
|-------|------|
| **SEO Title** | Accurate, compelling; match search intent |
| **Meta Description** | **Under 160 characters** (count before delivery) |
| **Focus Keyword** | Primary GSC or editorial target phrase |
| **Slug** | Lowercase, hyphenated; stable after publish |
| **Category** | WordPress category name(s) |
| **Pillar Content** | Yes/No — mark cornerstone roundups/guides |

### Style

- **Precise capitalization** for product names (Microsoft Teams, ClickUp, Webex, etc.).
- Practical, non-hype tone; small-business context.
- Comparison and review articles must match **correct brand pairs** (e.g. Teamwork vs Asana ≠ Asana vs ClickUp).

## Workflow stages

### 1. Idea / priority (before drafting)

- Check `reports/new_article_roadmap_*.md` for `create_new_article` vs `update_existing_page` vs `manual_review`.
- Check `reports/next_actions_*.md` for clustered GSC priorities.
- Confirm worklog: `config/worklog.json` (do not duplicate work marked `done` / `monitor_only`).

### 2. Article draft

- Outline H1 → H2 → H3 aligned to intent (roundup, review, comparison, guide).
- Draft body in plain text; short paragraphs; scannable lists.
- Plan 1–3 internal links (see `INTERNAL_LINKING_POLICY.md`).

### 3. SEO metadata

- Set SEO Title, Meta Description (<160 chars), Focus Keyword, Slug, Category, Pillar flag.
- Align title/H1 with primary query; avoid awkward “How to [Brand] for Small Teams” on branded reviews.

### 4. Internal link suggestions

```powershell
python -m linkops.cli suggest --target-url "https://worktoolslab.com/<slug>/" --target-keyword "<focus keyword>" --max-suggestions 8
```

- Review `reports/internal_link_suggestions_<slug>_*.md`.
- Add only approved sentences in WordPress.

### 5. Pre-publish checklist

- [ ] Focus keyword in title, intro, and at least one H2 where natural
- [ ] Meta description < 160 characters
- [ ] Slug final and matches site convention (`best-...-for-small-teams`, `...-review-for-small-businesses`, etc.)
- [ ] Internal links: natural, not excessive (typically ≤3 new contextual links)
- [ ] Affiliate / disclosure blocks intact
- [ ] No duplicate FAQ questions (if FAQ section exists)
- [ ] Fact-check pricing/features; mark “verify before publish” if uncertain

### 6. Publish (manual in WordPress)

LinkOps **never** publishes. User publishes in WP admin.

### 7. Post-publish

1. `python -m linkops.cli fetch` (refresh cache).
2. Request indexing in Google Search Console for the URL.
3. Update `config/worklog.json` (`done` or `monitor_only` + short note).
4. Update `docs/CONTENT_OPERATIONS_STATE.md`.
5. Optional: `optimize` + `patch` if GSC shows impressions with low clicks.

```powershell
python -m linkops.cli optimize --target-url "<url>" --target-keyword "<keyword>"
python -m linkops.cli patch --target-url "<url>" --target-keyword "<keyword>"
```

### 8. Monitor

- Re-import GSC CSVs periodically; re-run `next-actions` and `roadmap`.
- Pages in `monitor_only` still get GSC checks but are deprioritized in `--exclude-done` views.

## Article types (site patterns)

| Type | Slug pattern (typical) | Intent |
|------|------------------------|--------|
| Roundup | `best-*-tools-for-small-teams` | Commercial “best tools” queries |
| Review | `*-review-for-small-businesses` | Brand + review intent |
| Comparison | `*-vs-*-for-small-teams` | “X vs Y” queries |
| Guide | `how-to-*` | Informational / how-to |

## Roadmap actions (LinkOps v1.7+)

| `action_type` | Meaning |
|---------------|---------|
| `create_new_article` | New URL needed |
| `update_existing_page` | Strengthen existing URL (patch/optimize) |
| `manual_review` | Ambiguous intent — decide before writing |
| Excluded / already covered | Do not create competing page |

Branded queries (e.g. Microsoft Teams) must route to the **matching brand review URL**, not another brand’s review (see LinkOps brand guard in engine).
