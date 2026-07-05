# P0-A WordPress Implementation Checklist — WorkToolsLab

**Date:** 2026-07-05  
**Phase:** Authority Implementation — P0-A  
**Prerequisite content:** `content/authority/*.md`  
**Support docs:** `docs/AUTHOR_BYLINE_SCHEMA_IMPLEMENTATION_2026_07.md`, `docs/LEGACY_FREELANCERS_URL_REMEDIATION_2026_07.md`

**Important:** LinkOps does not write to WordPress. Execute these steps manually in wp-admin unless write tooling is added later.

---

## Pre-flight (before editing)

- [ ] Backup site or confirm staging available
- [ ] Log in to WordPress admin
- [ ] Confirm Rank Math and Kadence active
- [ ] Open paste sources side-by-side:
  - `content/authority/hayssam-dennaoui-author-profile.md`
  - `content/authority/how-we-review-tools.md`

---

## Part 1 — Author profile page

### Create page

- [ ] **Pages → Add New**
- [ ] **Title (WordPress):** `Hayssam Dennaoui`
- [ ] **H1 in content:** `Hayssam Dennaoui` (matches source file)
- [ ] **Parent:** About (for URL `/about/hayssam-dennaoui/`)
- [ ] **Slug:** `hayssam-dennaoui`
- [ ] **Visibility:** Public
- [ ] Paste body from `content/authority/hayssam-dennaoui-author-profile.md` section **Publish-ready page body**
- [ ] Format headings (H2 for sections as in source)
- [ ] Add internal links as WordPress links (methodology, about, affiliate disclosure, editorial policy)

### Rank Math fields

- [ ] **SEO Title:** `Hayssam Dennaoui | WorkToolsLab Editor & Product Builder`
- [ ] **Meta Description:** `Hayssam Dennaoui builds digital products and writes WorkToolsLab guides on work-management tools for freelancers and small teams.`
- [ ] **Focus Keyword:** `Hayssam Dennaoui WorkToolsLab`
- [ ] **Robots:** Index, Follow
- [ ] **Schema:** Enable Person / ProfilePage if Rank Math schema module offers it on this page

### Page elements

- [ ] LinkedIn link: `https://www.linkedin.com/in/hayssam-dennaoui/` (verify URL opens correctly)
- [ ] Footer line: `Last updated: July 2026` (adjust month when publishing)
- [ ] Featured image: optional — skip if none available

### Publish

- [ ] Publish page
- [ ] Confirm live URL: `https://worktoolslab.com/about/hayssam-dennaoui/` returns **200**

---

## Part 2 — Methodology page

### Create page

- [ ] **Pages → Add New**
- [ ] **Title:** `How WorkToolsLab Reviews Work-Management Tools`
- [ ] **Slug:** `how-we-review-tools`
- [ ] **Parent:** About (recommended) OR top-level — **use one URL consistently**
- [ ] Target URL: `https://worktoolslab.com/how-we-review-tools/`
- [ ] Paste body from `content/authority/how-we-review-tools.md` section **Publish-ready page body**
- [ ] Add internal links (about, author profile, affiliate disclosure, editorial policy, example guides)

### Rank Math fields

- [ ] **SEO Title:** `How We Review Work-Management Tools | WorkToolsLab`
- [ ] **Meta Description:** `How WorkToolsLab evaluates PM and task tools: setup, workflow fit, evidence types, screenshots, updates, and honest limitations.`
- [ ] **Focus Keyword:** `how WorkToolsLab reviews tools`
- [ ] **Robots:** Index, Follow

### Publish

- [ ] Publish page
- [ ] Confirm live URL returns **200**

---

## Part 3 — Navigation and internal links

### About page

- [ ] Edit `/about/`
- [ ] Add short section: **Meet the editor** → link to `/about/hayssam-dennaoui/`
- [ ] Add link: **How we review tools** → `/how-we-review-tools/`
- [ ] Reduce duplicate evaluation bullets if now covered on methodology page (optional light edit)

### Author profile cross-links

- [ ] Profile links to methodology (in body — should exist from paste)
- [ ] Methodology links back to profile (in body — should exist from paste)

### Articles (light pass — not full sitewide footer spam)

- [ ] Optional: add one contextual link to methodology on **Free PM for Freelancers** footer or author box area
- [ ] Do **not** add methodology link to every post in this pass

---

## Part 4 — Byline and author box

See `docs/AUTHOR_BYLINE_SCHEMA_IMPLEMENTATION_2026_07.md`.

- [ ] **Users → Profile** (Hayssam Dennaoui): set **Website** to `https://worktoolslab.com/about/hayssam-dennaoui/`
- [ ] Update author bio in user profile if theme pulls from user description (optional short version)
- [ ] Kadence Customizer → Single Posts → Author Box: verify enabled
- [ ] Change author box name link target to profile URL if theme option exists
- [ ] Update “View all posts” to remain on `/author/hayssam-dennaoui/`
- [ ] Add “About the author” link to profile if theme/custom HTML allows
- [ ] Spot-check one published post: byline href → profile URL

---

## Part 5 — Schema (Rank Math)

- [ ] Rank Math → Schema → verify **Article** author references Person
- [ ] Set author URL target to profile page (see implementation doc)
- [ ] View source on published post — confirm JSON-LD:
  - `"author": { "@type": "Person", "name": "Hayssam Dennaoui", "url": "https://worktoolslab.com/about/hayssam-dennaoui/" }`
- [ ] Confirm `sameAs` LinkedIn still present once
- [ ] Profile page: run [Google Rich Results Test](https://search.google.com/test/rich-results) on profile URL
- [ ] Optional: [Schema Markup Validator](https://validator.schema.org/) on profile + sample article

**If Rank Math will not change author.url:** document blocker; consider developer snippet (out of repo scope).

---

## Part 6 — Legacy freelancers-2 URL

Follow `docs/LEGACY_FREELANCERS_URL_REMEDIATION_2026_07.md` checklist in full.

Quick reference — **current live curl finding:**

- `-2` → **301** → `/best-free-project-management-tools-for-freelancers/`

- [ ] Confirm in incognito browser (checklist items 1–6)
- [ ] Decide: keep redirect to **free guide** OR change to **paid canonical**
- [ ] Rank Math Redirections: document rule
- [ ] GSC URL Inspection on `-2` and chosen target
- [ ] Log decision in `config/worklog.json`

---

## Part 7 — Post-publish validation

| Check | Pass? |
|-------|-------|
| Profile URL 200 | [x] |
| Methodology URL 200 | [x] |
| Page title in browser tab (Rank Math) | [x] |
| H1 visible on page | [x] |
| Meta description in view-source or Rank Math front-end | [ ] spot-check |
| Indexable (no accidental noindex) | [ ] GSC optional |
| Byline links to profile | [x] |
| Article JSON-LD author.@id → profile | [x] owner-verified |
| Mobile layout readable | [ ] optional |
| About page links to profile + methodology | [x] |
| Internal links on profile/methodology resolve 200 | [x] |
| Sitemap includes new pages (after cache refresh) | [ ] manual |
| GSC URL Inspection submitted for new pages | [ ] manual |

---

## Part 8 — SEO metadata prefix cleanup

See `docs/SEO_METADATA_PREFIX_AUDIT_2026_07.md`.

- [x] ClickUp vs Trello — prefix removed (owner fixed)
- [x] **Notion vs Trello vs ClickUp** — prefix removed (owner fixed 2026-07-06; View Source verified)
- [ ] Spot-check June-updated posts in Rank Math sidebar (optional P1)

---

## Part 9 — Publisher Knowledge Graph review

See `docs/P0_A_AUTHORITY_LIVE_IMPLEMENTATION_RECORD_2026_07.md` (Publisher section).

- [ ] Rank Math → General Settings → Edit Entity / Knowledge Graph
- [ ] Confirm site entity type (prefer **Organization** for WorkToolsLab brand, not dual Person+Organization unless intentional)
- [ ] Re-check JSON-LD `#person` / publisher node on homepage or sample article
- [ ] Optional: Rich Results Test

**Do not** modify MU plugins for publisher identity in this step unless live file intentionally manages publisher (current mirrors do not).

### After WordPress changes

```powershell
cd C:\dev\worktoolslab_linkops
.\.venv\Scripts\Activate.ps1
python -m linkops.cli fetch
```

**Note (2026-07-06):** Local `fetch` may be blocked by SiteGround `sgcaptcha` (HTTP 202). P0-A closeout does not depend on fetch. Retry when REST access works; do not bypass CAPTCHA.

- [ ] Run `fetch` when REST access works (optional — currently blocked locally)
- [x] Update `docs/CONTENT_OPERATIONS_STATE.md` — P0-A closed; P0-3 planning complete

---

## Part 8 — Explicitly out of scope for P0-A

- [ ] Free PM for Freelancers LEVEL 3 evidence upgrade — **P0-3 in progress (owner testing queue)**
- [ ] Home / Tools / Start Here hub restructure — P0-5 later
- [ ] Paid freelancer roundup meta/intro CTR — P0-6 later
- [ ] Broad title/meta rewrites across site

---

## Recommended next phase after this checklist

1. **P0-A validation complete** — **PASS** (2026-07-06)
2. **P0-3:** Free PM for Freelancers evidence upgrade (LEVEL 3) — **READY FOR OWNER TESTING** — see `docs/P0_3_OWNER_TESTING_EXECUTION_QUEUE_2026_07.md`
3. **P0-6:** Canonical paid freelancer roundup snippet differentiation
4. **Fresh GSC import** after 2–3 weeks

---

## Related files

| File | Purpose |
|------|---------|
| `content/authority/hayssam-dennaoui-author-profile.md` | Author paste source |
| `content/authority/how-we-review-tools.md` | Methodology paste source |
| `docs/AUTHOR_BYLINE_SCHEMA_IMPLEMENTATION_2026_07.md` | Byline + schema strategy |
| `docs/LEGACY_FREELANCERS_URL_REMEDIATION_2026_07.md` | `-2` URL remediation |
