# Site Authority Upgrade Roadmap — WorkToolsLab

**Date:** 2026-07-05  
**Precedes:** Implementation phase (P0 work — not started in audit phase)  
**Evidence:** `docs/SITE_FOCUS_AUTHORITY_AUDIT_2026_07.md`

---

## Strategic decisions (audit outcomes)

| Decision | Proceed? | Notes |
|----------|----------|-------|
| **A. Topical focus narrowing** | **Yes — editorial, not deletion** | Stop new communication/video/remote breadth; maintain existing URLs |
| **B. Author profile** | **Yes** | `/about/hayssam-dennaoui/` (or equivalent) |
| **C. Methodology page** | **Yes** | `/how-we-review-tools/` |
| **D. Five priority article evidence upgrades** | **Yes — phased** | A first (LinkedIn + differentiation), then B, C, D, E |
| **E. Homepage architecture** | **Yes** | Audience router |
| **F. Tools page restructuring** | **Yes** | Problem-oriented categories |
| **G. Start Here decision path** | **Yes** | Problem → guide → comparison |
| **H. Article/author/ProfilePage schema** | **Yes** | After profile URL live |
| **I. Title/meta CTR tests** | **Selective yes** | C meta first; defer B title; see audit §8 |
| **J. Technical SEO fixes** | **Yes** | freelancers-2, sitemap, http variants |

---

## P0 — Highest-value authority / search improvements

### P0-1 — Publish author profile + link from bylines

| Field | Detail |
|-------|--------|
| **Problem** | No person-level trust; About is anonymous |
| **Evidence** | Audit §5; bylines exist but archive has no bio |
| **Affected** | All posts; About; theme byline |
| **Expected benefit** | E-E-A-T; clearer creator identity for Google and readers |
| **Risk** | Low — copy must stay grounded |
| **Cursor/repo** | Draft in repo docs only; paste-ready copy can be added to `reports/` |
| **WordPress** | **Required** — create page, update byline template |
| **Validation** | Rich Results Test; live byline link |

### P0-2 — Publish review methodology page + About links

| Field | Detail |
|-------|--------|
| **Problem** | No transparent testing boundaries |
| **Evidence** | Priority pages max LEVEL 2; audit §6 |
| **Affected** | `/how-we-review-tools/`, `/about/` |
| **Expected benefit** | Trust; framework for evidence upgrades |
| **Risk** | Low |
| **Cursor/repo** | `AUTHOR_PROFILE_AND_REVIEW_METHODOLOGY_PLAN.md`, `ARTICLE_EVIDENCE_FRAMEWORK.md` |
| **WordPress** | **Required** |
| **Validation** | Internal links from A + C; manual read |

### P0-3 — Evidence upgrade: Free PM for Freelancers (A → LEVEL 3) — **CLOSED PASS**

| Field | Detail |
|-------|--------|
| **Status** | **PASS / CLOSED** (2026-07-09) — **LEVEL 3 LIVE** |
| **Closeout** | `docs/P0_3_FREE_PM_LEVEL3_LIVE_CLOSEOUT_2026_07.md` |
| **Live URL** | `/best-free-project-management-tools-for-freelancers/` |
| **Evidence** | Five-tool direct testing (defined scope); five Board screenshots live; live metadata/schema validated |
| **Boundaries** | Google recrawl/reindex **not claimed**; GSC impact is future evidence |
| **Separate follow-up** | Publisher Knowledge Graph `#person` entity — site-level; not P0-3 blocker |

**Minimum met:** All five tools evidenced for defined scope; article published and validated live.

### P0-4 — Resolve freelancers-2 URL + GSC cleanup — **CLOSED PASS**

| Field | Detail |
|-------|--------|
| **Status** | **PASS / CLOSED** (2026-07-09) |
| **Closeout** | `docs/P0_4_LEGACY_FREELANCERS_URL_GSC_CLOSEOUT_2026_07.md` |
| **Legacy URL** | `/best-project-management-tools-for-freelancers-2/` |
| **Destination** | `/best-free-project-management-tools-for-freelancers/` (indexed) |
| **Rank Math Redirections** | **0 rules** — redirect not Rank Math-managed |
| **GSC legacy** | Not indexed; Page with redirect; crawl Jul 8 2026 |
| **GSC canonical** | User-declared = Google-selected; no disagreement |
| **Decision** | **Keep current redirect** — no WordPress/GSC mutation |
| **Redirect mechanism** | **Unproven** — `_wp_old_slug` plausible inference only |

### P0-5 — Hub differentiation: Home audience routing (first pass) — **CLOSED PASS**

| Field | Detail |
|-------|--------|
| **Status** | **PASS / CLOSED** (2026-07-09) |
| **Closeout** | `docs/P0_5_HOME_AUDIENCE_ROUTING_LIVE_CLOSEOUT_2026_07.md` |
| **Live URL** | `/` — audience routing first pass live |
| **H1** | Work Management Tools for Freelancers and Small Teams |
| **Focus** | Freelancer + small-team work-management routing; broader comm/video clusters demoted from primary Home architecture |
| **Tools/Blog** | Remain broader browse destinations |
| **Boundaries** | Google recrawl/reindex and performance impact **not claimed** |

### P0-6 — CTR: differentiate Best PM for Freelancers (C) meta + intro — **NEXT**

| Field | Detail |
|-------|--------|
| **Problem** | 681 imp, 0 clicks; overlaps free guide |
| **Evidence** | GSC; audit §8 |
| **Affected** | `/best-project-management-tools-for-freelancers/` |
| **Expected benefit** | Improved snippet clarity for paid/broad freelancer intent |
| **Risk** | Low if no false testing claims |
| **Cursor/repo** | `patch` report after fresh GSC (optional) |
| **WordPress** | **Required** — meta + intro lede only |
| **Validation** | GSC CTR after 28+ days post-change |

### P0-7 — Article + Person structured data — **CLOSED PASS**

| Field | Detail |
|-------|--------|
| **Status** | **PASS — LIVE FIX VERIFIED / GOOGLE REPROCESSING PENDING** (2026-07-10) |
| **Closeout** | `docs/P0_7_PUBLISHER_PROFILEPAGE_SCHEMA_LIVE_FIX_2026_07.md` |
| **Scope** | Rank Math site entity Person→Organization; deterministic ProfilePage graph; MU-plugin mirror sync |
| **Live validation** | GSC TEST LIVE URL — **1 valid Profile page item** (Jul 10, 2026, 5:17 PM) |
| **Indexing** | Requested once — do not repeat |
| **Index tab** | May still show old invalid item until Google reprocesses — **not claimed** |
| **Does not reopen** | P0-A, P0-3, P0-4, P0-5 |

---

## P1 — Useful follow-up improvements

### P1-1 — Evidence upgrade: Task vs PM (B) — LEVEL 2 polish + methodology links

Add methodology link, improved decision table, FAQ tightening. **Do not** fake testing.

### P1-2 — Evidence upgrade: Best PM for Freelancers (C) — LEVEL 3 partial

Hands-on sections for 2–3 tools; comparison table with criteria from framework.

### P1-3 — Tools page problem-oriented restructure

Categories: manage client work, track daily tasks, run team projects, standardize workflows, organize knowledge, improve coordination.

### P1-4 — Start Here decision path

Problem → recommended guide → comparison → review (see audit §7).

### P1-5 — Internal link pass: elevate Free PM guide (A)

Many pages link to paid freelancer roundup; shift priority links to A where free intent fits.

### P1-6 — Evidence upgrade: How to Manage Tasks (D) — LEVEL 2

Optional one tool walkthrough at LEVEL 3.

### P1-7 — HTTP → HTTPS canonical cleanup

GSC `http://` variants for asana-review, monday-vs-asana — verify redirects in WP.

### P1-8 — Sitemap repair

Fix 403 on `/sitemap.xml` or standardize on `wp-sitemap.xml` in robots.txt.

### P1-9 — Fresh GSC import + selective CTR tests

After P0 publishes and indexing lag — re-run `next-actions`; test Task vs PM meta only if position improves.

### P1-10 — Evidence upgrade: Monday vs ClickUp (E) — LEVEL 3

If operator tests both in small-team scenario.

---

## P2 — Later / maintenance

| ID | Item |
|----|------|
| P2-1 | Mark communication + video meeting articles maintenance-only in editorial queue |
| P2-2 | Productivity roundup deep upgrade (461 imp, 1 click — careful) |
| P2-3 | Teamwork vs Asana hub links + distribution follow-up |
| P2-4 | Breadcrumb schema |
| P2-5 | Core Web Vitals remediation after PSI baseline |
| P2-6 | Orphan audit via `linkops analyze` after hub changes |
| P2-7 | Image alt text patterns audit |
| P2-8 | Category/archive indexability review |
| P2-9 | Roadmap `create_new` review — freelance teams tool (confirm vs A) |
| P2-10 | Paid traffic tests (deferred per strategy) |

---

## Recommended implementation sequence

```
Week 1: P0-1, P0-2, P0-4 (author, methodology, redirect)
Week 2: P0-3 (Free PM evidence) + P0-7 (schema)
Week 3: P0-5, P0-6 (hubs + C meta)
Week 4: P1-1, P1-3, P1-4, P1-5
Then: Fresh GSC → P1-9 → P1-2, P1-10 as capacity allows
```

---

## Explicit non-goals (this roadmap cycle)

- No deletion of communication/video content
- No new broad roundups outside work-management focus
- No broad optimize/patch on June 5 GSC export
- No paid link building
- No invented testing or credentials

---

## Next implementation phase (recommended)

**Phase name:** **Authority Implementation — P0-6 (CTR differentiation)**

P0-1 through P0-5 and **P0-7** are **closed**. Next editorial priority: **P0-6** — CTR: differentiate Best PM for Freelancers (C) meta + intro.

---

## Related docs

- Audit: `docs/SITE_FOCUS_AUTHORITY_AUDIT_2026_07.md`
- Evidence: `docs/ARTICLE_EVIDENCE_FRAMEWORK.md`
- Author/methodology: `docs/AUTHOR_PROFILE_AND_REVIEW_METHODOLOGY_PLAN.md`
- State: `docs/CONTENT_OPERATIONS_STATE.md`
