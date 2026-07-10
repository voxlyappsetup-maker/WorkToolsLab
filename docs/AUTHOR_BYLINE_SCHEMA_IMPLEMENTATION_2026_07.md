# Author, Byline & Schema Implementation — WorkToolsLab

**Date:** 2026-07-05  
**Phase:** P0-A Authority Implementation Foundation  
**Status:** Repository-side plan — **WordPress changes require owner manual action**

---

## 1. Current author implementation audit

Evidence sources: `data/worktoolslab_content_cache.json` (2026-06 fetch), read-only live HTML inspection (2026-07-05), prior audit `docs/SITE_FOCUS_AUTHORITY_AUDIT_2026_07.md`.

### Known from repository + live site

| Item | Current state | Evidence |
|------|---------------|----------|
| **Author archive URL** | `https://worktoolslab.com/author/hayssam-dennaoui/` | Live 200; post excerpts only |
| **Archive unique author content** | **No meaningful bio** — title “Hayssam Dennaoui - WorkToolsLab” + post list | Live fetch |
| **Dedicated author profile** | **`/about/hayssam-dennaoui/` → 404** | Live fetch 2026-07-05 |
| **Methodology page** | **`/how-we-review-tools/` → 404** | Live fetch 2026-07-05 |
| **About page names author** | **No** — site-level evaluation only | Cache + live About |
| **Article byline link** | `By Hayssam Dennaoui` → `/author/hayssam-dennaoui/` | Live HTML on Free PM article |
| **Author box (footer)** | Kadence author box + custom `worktoolslab-author-box` CSS | Live HTML |
| **Author box links** | Name + “View all posts” → archive | Live HTML |
| **SEO plugin** | **Rank Math** — `rank-math-schema` JSON-LD on articles | Live HTML |
| **Theme** | **Kadence** (author-box.min.css) | Live HTML |
| **Article `author` in schema** | `@type Person`, `name`: Hayssam Dennaoui | Rank Math JSON-LD |
| **`author.url` in Article schema** | `https://worktoolslab.com/author/hayssam-dennaoui/` | Rank Math JSON-LD |
| **`sameAs` (author)** | `https://www.linkedin.com/in/hayssam-dennaoui/` | Rank Math JSON-LD |
| **ProfilePage schema** | **Not observed** on author archive | Live HTML inspection |
| **Publisher entity** | WorkToolsLab `@id` `/#person` as Person+Organization hybrid | Rank Math JSON-LD |

### Requires manual WordPress verification (do not infer)

| Item | Why manual check is needed |
|------|----------------------------|
| Rank Math → Titles & Meta → Authors settings | May control author schema URL globally |
| Rank Math → Schema → Person / Article templates | May override per-page JSON-LD |
| Kadence → Theme Customizer → Author Box settings | Controls byline/box link targets |
| Users → Hayssam Dennaoui profile (bio, website, social) | May feed Rank Math author metadata |
| Custom snippet/plugin for `worktoolslab-author-box` | Unknown if PHP filter exists outside repo |
| Whether author archive is noindexed | Rank Math / Kadence setting not visible in repo |

**Repository truth:** LinkOps is read-only; no WordPress write tooling is documented in this repo.

---

## 2. Recommended canonical author architecture

### URLs

| Role | URL | Purpose |
|------|-----|---------|
| **Canonical person profile** | `https://worktoolslab.com/about/hayssam-dennaoui/` | Bio, builder context, methodology link, LinkedIn |
| **WordPress author archive** | `https://worktoolslab.com/author/hayssam-dennaoui/` | Post index — keep for WP author behavior |
| **Methodology** | `https://worktoolslab.com/how-we-review-tools/` | Evaluation standard |

### Byline behavior (target)

```text
By Hayssam Dennaoui → /about/hayssam-dennaoui/
Author box: short bio snippet + About the author + View all posts
```

---

## 3. Author archive handling — option evaluation

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **A. Keep archive indexed; add intro + link to profile** | Preserves WP author UX; no redirect risk; archive can list posts | Two URLs for one person if schema not updated | **Recommended** |
| **B. Noindex archive; profile is canonical identity** | Reduces duplicate person signals | Hides legitimate post index; may confuse “View all posts” value | Not first choice |
| **C. Redirect archive → profile** | Single URL | Breaks WordPress author archive conventions; may break `/author/` feeds and Rank Math author graph | **Do not use** |

### Recommendation: **Option A**

1. Publish dedicated profile at `/about/hayssam-dennaoui/`.
2. Point **bylines**, **author box name**, and **`author.url` in Article schema** to the profile URL.
3. Keep `/author/hayssam-dennaoui/` as post archive.
4. Add a short intro block at top of author archive (optional Phase 1.5):
   - 2–3 sentences + link “Full author profile” → `/about/hayssam-dennaoui/`
5. Do **not** redirect the archive.

---

## 4. Article schema recommendation

Target Rank Math / JSON-LD output for `BlogPosting`:

```json
"author": {
  "@type": "Person",
  "name": "Hayssam Dennaoui",
  "url": "https://worktoolslab.com/about/hayssam-dennaoui/",
  "sameAs": ["https://www.linkedin.com/in/hayssam-dennaoui/"]
}
```

**Current (live):** `author.url` → `/author/hayssam-dennaoui/` — **change after profile publish**.

### Rank Math configuration paths (verify in WP admin)

1. **Rank Math → Titles & Meta → Authors** — check if author URL can be overridden
2. **Rank Math → Schema Templates → Person** — set default URL to profile page
3. **Users → Profile → Website** — set to profile URL (may feed schema)
4. **Rank Math → General Settings → Links** — confirm no conflicting author base

If Rank Math cannot set `author.url` to a custom page, options (owner decision):

- Rank Math filter/hook (requires developer — **not in repo**)
- Supplemental JSON-LD via approved snippet plugin
- Manual verification that Kadence/Rank Math update after user website field change

**Do not add unsupported PHP to this repository without theme/plugin proof.**

---

## 5. Person / ProfilePage recommendation

### Person entity (profile page)

```json
{
  "@context": "https://schema.org",
  "@type": "Person",
  "name": "Hayssam Dennaoui",
  "url": "https://worktoolslab.com/about/hayssam-dennaoui/",
  "sameAs": ["https://www.linkedin.com/in/hayssam-dennaoui/"],
  "jobTitle": "Editor",
  "worksFor": {
    "@type": "Organization",
    "name": "WorkToolsLab",
    "url": "https://worktoolslab.com/"
  }
}
```

Use **Editor** or **Founder & Editor** only if the owner confirms that job title is accurate.

### ProfilePage (optional enhancement)

```json
{
  "@context": "https://schema.org",
  "@type": "ProfilePage",
  "mainEntity": {
    "@type": "Person",
    "name": "Hayssam Dennaoui",
    "url": "https://worktoolslab.com/about/hayssam-dennaoui/"
  },
  "url": "https://worktoolslab.com/about/hayssam-dennaoui/"
}
```

Rank Math may auto-generate WebPage schema on the profile — enable Person/ProfilePage in Rank Math schema module if available.

### Author archive Person node

Keep or update the existing Person `@id` `/author/hayssam-dennaoui/` in graph **only if** Rank Math requires it for archive pages. Primary **`author.url` on articles** should still point to `/about/hayssam-dennaoui/`.

---

## 6. Kadence theme + author box notes

Observed on live site:

- `kadence-author-box` stylesheet loaded
- Custom inline CSS: `worktoolslab-author-box` (likely child theme or customizer)
- Author box links name to archive today

**Owner actions:**

1. Kadence Customizer → Single Posts → Author Box → enable if disabled
2. Update author box “Author link” behavior if theme option exists
3. If no theme option: edit child theme author box template **only after backup** — not documented in repo

---

## 7. Validation after implementation

| Check | Tool / method |
|-------|----------------|
| Byline href | View source on any post |
| Author box links | Visual + HTML inspect |
| Article JSON-LD `author.url` | View source or Rich Results Test |
| Profile page JSON-LD | Schema Markup Validator |
| LinkedIn `sameAs` | Present once — avoid duplicates |
| Mobile layout | Browser devtools |

---

## 8. Content source files

| Page | Repository paste source |
|------|-------------------------|
| Author profile | `content/authority/hayssam-dennaoui-author-profile.md` |
| Methodology | `content/authority/how-we-review-tools.md` |
| Implementation sequence | `docs/P0_A_WORDPRESS_IMPLEMENTATION_CHECKLIST.md` |

---

## Related docs

- Audit: `docs/SITE_FOCUS_AUTHORITY_AUDIT_2026_07.md`
- Roadmap: `docs/SITE_AUTHORITY_UPGRADE_ROADMAP_2026_07.md`
- Legacy URL: `docs/LEGACY_FREELANCERS_URL_REMEDIATION_2026_07.md`
- P0-7 live fix: `docs/P0_7_PUBLISHER_PROFILEPAGE_SCHEMA_LIVE_FIX_2026_07.md`
- MU plugin state: `docs/WORDPRESS_MU_PLUGIN_DEPLOYMENT_STATE_2026_07.md`

---

## 9. P0-7 live schema fix supersession (2026-07-10)

**Historical §1 publisher row** documented `@id` `/#person` as Person+Organization hybrid — **superseded live**.

| Item | Live status after P0-7 |
|------|------------------------|
| WorkToolsLab site entity | **Organization** — `@id` `https://worktoolslab.com/#organization` |
| WebSite publisher | References `#organization` |
| Hayssam identity | **Person** — canonical profile URL unchanged |
| Dedicated profile page | **ProfilePage** with `mainEntity` → Person |
| GSC TEST LIVE URL | **1 valid Profile page item** (Jul 10, 2026, 5:17 PM) |
| Google Index tab | May still show old invalid item — **reprocessing pending** |

**Closeout:** `docs/P0_7_PUBLISHER_PROFILEPAGE_SCHEMA_LIVE_FIX_2026_07.md`
