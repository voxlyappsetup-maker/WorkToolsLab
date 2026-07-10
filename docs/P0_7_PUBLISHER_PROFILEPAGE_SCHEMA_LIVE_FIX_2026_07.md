# P0-7 Closeout — Publisher / ProfilePage Structured Data Live Fix

**Date:** 2026-07-10  
**Roadmap identifier:** **P0-7** — Article + Person structured data / publisher Knowledge Graph follow-up  
**Repository checkpoint before closeout:** `f53148d`  
**Result:** **PASS — LIVE FIX VERIFIED / GOOGLE REPROCESSING PENDING**

---

## Live profile URL

https://worktoolslab.com/about/hayssam-dennaoui/

---

## Original structured-data defect

| Item | Classification |
|------|----------------|
| **Previous WorkToolsLab publisher entity** | `@type`: `["Person","Organization"]`; `@id`: `https://worktoolslab.com/#person`; `name`: WorkToolsLab |
| **GSC indexed-state (pre-fix)** | URL on Google, but has issues — Profile page: **1 invalid item detected** |
| **Critical error** | `Invalid object type for field "<parent_node>"` |
| **Root cause (verified)** | Mixed Person+Organization site entity; ProfilePage graph depended on Rank Math entities that were removed |

**Historical note:** Prior repo records treated publisher Knowledge Graph as optional follow-up (P0-7). GSC critical issue promoted it to active investigation.

---

## Rank Math site entity correction (VERIFIED LIVE)

| Field | Before | After |
|-------|--------|-------|
| **Rank Math Local SEO → Person or Company** | Person | **Organization** |
| **Website Name** | WorkToolsLab | WorkToolsLab (unchanged) |
| **Person/Organization Name** | WorkToolsLab | WorkToolsLab (unchanged) |
| **URL** | https://worktoolslab.com | https://worktoolslab.com (unchanged) |

**Live site entity after save:**

| Field | Value |
|-------|--------|
| **@type** | Organization |
| **@id** | https://worktoolslab.com/#organization |
| **name** | WorkToolsLab |
| **WebSite publisher** | https://worktoolslab.com/#organization |

---

## Profile page Rank Math change (VERIFIED LIVE)

Default **Article Schema** removed from dedicated author profile page in Rank Math. After removal, Rank Math no longer emitted the prior page graph; existing MU-plugin logic could only convert an existing WebPage/ProfilePage entity — it did not deterministically create ProfilePage when no suitable page entity existed.

---

## MU-plugin fix (VERIFIED LIVE)

**Live file:** `/wp-content/mu-plugins/worktoolslab-author-links.php`  
**Repository mirror:** `wordpress/mu-plugins/worktoolslab-author-links.php` — synchronized to exact verified live implementation.

**Change:** Deterministic four-entity graph on dedicated Hayssam profile page:

```
Organization → WebSite
ProfilePage → Person (mainEntity)
```

**Non-profile pages:** Normalize Hayssam Person + Article/BlogPosting/NewsArticle author references only; do not rebuild Rank Math graph.

---

## Verified live four-entity graph (View Source — 2026-07-10)

| # | Entity | Key fields |
|---|--------|------------|
| 1 | **Organization** | `@id` https://worktoolslab.com/#organization; `name` WorkToolsLab |
| 2 | **WebSite** | `@id` https://worktoolslab.com/#website; `publisher` → `#organization` |
| 3 | **ProfilePage** | `@id` https://worktoolslab.com/about/hayssam-dennaoui/#webpage; `mainEntity` → Hayssam Person |
| 4 | **Person** | `@id` https://worktoolslab.com/about/hayssam-dennaoui/; `worksFor` → `#organization`; `sameAs` LinkedIn; Gravatar ImageObject |

**Absent on profile page (verified):** Article, BlogPosting, mixed Person+Organization WorkToolsLab `#person` entity.

| Field | Value |
|-------|--------|
| **datePublished** | 2026-07-05T22:21:22+03:00 |
| **dateModified** | 2026-07-10T15:48:57+03:00 |

---

## Google Search Console live-test evidence (VERIFIED LIVE)

| Item | Value |
|------|--------|
| **URL** | https://worktoolslab.com/about/hayssam-dennaoui/ |
| **Test type** | URL Inspection → **TEST LIVE URL** |
| **Tested** | **Jul 10, 2026, 5:17 PM** |
| **Page availability** | Page can be indexed |
| **Profile page** | **1 valid item detected** |
| **Pre-fix live test** | 1 invalid item — `Invalid object type for field "<parent_node>"` |

**Live-test graph (expanded):** ProfilePage → WebSite (`#website`) → Organization publisher (`#organization`) → Person mainEntity with jobTitle, description, worksFor, sameAs, image.

---

## Indexing request (VERIFIED — once only)

| Item | Status |
|------|--------|
| **Indexing requested** | **Yes** — once for profile URL |
| **GSC UI** | Button now shows **REQUEST AGAIN** |
| **Do not request again** | **NOT REQUIRED** |

---

## Google Index tab — OLD INDEXED STATE (not live regression)

| Item | Classification |
|------|----------------|
| **Current Index tab may still show** | URL on Google, but has issues — Profile page: 1 invalid item |
| **Interpretation** | **OLD INDEXED STATE** — crawled before Google reprocesses fixed live page |
| **Google Index reprocessed** | **NOT CLAIMED** |
| **Validate Fix action** | **NOT AVAILABLE** — Enhancements: No enhancements yet |
| **Validate Fix run** | **NOT CLAIMED** — action not available in property UI |

---

## Explicit boundaries (NOT CLAIMED)

| Boundary | Status |
|----------|--------|
| Google Index report updated | **NOT CLAIMED** |
| Indexed Profile page invalid item disappeared | **NOT CLAIMED** |
| Property-level Profile page enhancement report | **Not available** |
| P0-A / P0-3 / P0-4 / P0-5 reopened | **NO** |

---

## Phase closeout

| Gate | Status |
|------|--------|
| **P0-7** | **PASS — LIVE FIX VERIFIED / GOOGLE REPROCESSING PENDING** |

---

## Next editorial priority (unchanged)

**P0-6** — CTR: differentiate Best PM for Freelancers (C) meta + intro

**Recommended next owner action:** Execute P0-6 on `/best-project-management-tools-for-freelancers/`. Monitor GSC Index tab for profile URL reprocessing over coming days; do **not** request indexing again; do **not** claim Index tab cleared until Google reprocesses.

---

## Related docs

- `docs/WORDPRESS_MU_PLUGIN_DEPLOYMENT_STATE_2026_07.md`
- `docs/AUTHOR_BYLINE_SCHEMA_IMPLEMENTATION_2026_07.md`
- `docs/SITE_AUTHORITY_UPGRADE_ROADMAP_2026_07.md`
- `wordpress/mu-plugins/worktoolslab-author-links.php`
