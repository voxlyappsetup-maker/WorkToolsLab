# Legacy Freelancers URL Remediation — WorkToolsLab

**Date:** 2026-07-05 (foundation) · **P0-4 closeout:** 2026-07-09
**Phase:** P0-A Authority Implementation Foundation → **P0-4 PASS / CLOSED**
**Old URL:** `https://worktoolslab.com/best-project-management-tools-for-freelancers-2/`
**Live redirect destination:** `https://worktoolslab.com/best-free-project-management-tools-for-freelancers/`
**Status:** **PASS / CLOSED** — keep current redirect; no remediation mutation required

---

## P0-4 closeout summary (2026-07-09)

| Item | Result | Classification |
|------|--------|----------------|
| Rank Math Redirections rules | **0** (All / Active / Inactive / Trash) | **VERIFIED** |
| Redirect Rank Math-managed | **NO** | **VERIFIED** |
| Exact redirect mechanism | **Not proven** | **UNPROVEN** |
| Plausible mechanism | WordPress old-slug / `_wp_old_slug` | **INFERRED** — not verified via DB |
| GSC legacy URL | Not indexed; **Page with redirect** | **VERIFIED** |
| GSC legacy last crawl | **Jul 8, 2026, 9:05:51 AM** | **VERIFIED** |
| User-declared canonical (legacy inspection) | Free guide URL | **VERIFIED** |
| Google-selected canonical | **Same as user-declared** | **VERIFIED** |
| GSC destination URL | **Indexed** | **VERIFIED** |
| Remediation decision | **Keep current redirect** | **VERIFIED DECISION** |
| WordPress mutation required | **NO** | **NOT REQUIRED** |
| Rank Math redirect creation | **NO** | **NOT REQUIRED** |
| GSC Removals | **NO** | **NOT REQUIRED** |
| Legacy URL indexing request | **NO** | **NOT REQUIRED** |

**Closeout record:** `docs/P0_4_LEGACY_FREELANCERS_URL_GSC_CLOSEOUT_2026_07.md`

**Do not claim:** Google has fully reprocessed the July 8 LEVEL 3 content update on the destination URL.

---

## 1. Repository and cache truth (historical — 2026-07-05)

| Source | Finding |
|--------|---------|
| **WordPress content cache** | `-2` slug **not present** in `data/worktoolslab_content_cache.json` (38 pages/posts) |
| **Canonical paid roundup** | Present: `/best-project-management-tools-for-freelancers/` (post id 61 in REST hints) |
| **Free freelancer guide** | Present: `/best-free-project-management-tools-for-freelancers/` |
| **Internal links to `-2`** | **None** found in content cache |
| **Internal links to paid canonical** | Multiple articles link to `/best-project-management-tools-for-freelancers/` |
| **GSC cache (2026-06-05)** | `-2` URL: **3 impressions**, 0 clicks, avg position **57.7** |
| **GSC paid canonical** | **681 impressions**, 0 clicks, avg position **52.1** |
| **GSC free guide** | **13 impressions**, 0 clicks, avg position **64.4** |

---

## 2. Live HTTP verification (2026-07-05 — historical)

### Automated results

| Probe | Result |
|-------|--------|
| PowerShell `Invoke-WebRequest -Method Head` (prior session) | **403** on `-2` (no Location) — likely bot/WAF |
| `curl.exe -sI` GET/HEAD on `-2` | **301 Moved Permanently** |
| Redirect header | `Location: https://worktoolslab.com/best-free-project-management-tools-for-freelancers/` |
| Redirect agent | `X-Redirect-By: WordPress` |
| Final response (follow redirect) | **200 OK** on **free guide** |

### Important finding (historical)

The live **301 target is the FREE guide**, not the paid canonical roundup assumed in the July audit.

| URL | Role |
|-----|------|
| `-2` | Legacy slug |
| **Current 301 target** | `/best-free-project-management-tools-for-freelancers/` |
| **Paid canonical (editorial)** | `/best-project-management-tools-for-freelancers/` |

**P0-4 decision (2026-07-09):** **Keep 301 → free guide.** GSC confirms redirect behavior and canonical alignment. No change required.

---

## 3. Sitemap evidence (historical)

| Check | Result |
|-------|--------|
| `-2` in WP cache sitemap list | **Not applicable** — not in inventory |
| Automated `sitemap.xml` probe (prior session) | **403** — inconclusive |
| GSC discovery (2026-07-09) | **No referring sitemaps** for legacy URL; referring pages include free guide and `post-sitemap.xml` |

---

## 4. Canonical tag evidence

GSC URL Inspection (2026-07-09) on legacy URL:

- **User-declared canonical:** `https://worktoolslab.com/best-free-project-management-tools-for-freelancers/`
- **Google-selected canonical:** Same as user-declared
- **Canonical disagreement:** None observed

On destination (free guide): **indexed**; HTTPS confirmed.

---

## 5. Limitations of automated testing (historical)

- HEAD requests from some clients returned **403** while `curl` returned **301** — hosting/WAF may treat clients differently.
- P0-4 closeout relied on **owner GSC URL Inspection** and **Rank Math Redirections admin inspection** — not LinkOps `fetch`.

---

## 6. Owner verification checklist — P0-4 completion

### Browser verification (historical / prior sessions)

1. [x] Redirect behavior confirmed via curl (2026-07-05) — **301 → free guide**
2. [x] Editorial decision: **keep redirect to free guide** (P0-4 closeout)

### WordPress admin (2026-07-09)

3. [x] **Rank Math → Redirections** — **0 rules** (All / Active / Inactive / Trash)
4. [x] Redirect is **not** Rank Math-managed

### Google Search Console (2026-07-09)

5. [x] **URL Inspection** on `-2` — not indexed; Page with redirect; crawl Jul 8 2026 9:05:51 AM
6. [x] **URL Inspection** on free guide destination — **indexed**
7. [x] User-declared and Google-selected canonical **agree**
8. [x] **No** indexing request for legacy URL
9. [x] **No** GSC Removals

### Not performed (not required for closeout)

- [ ] WordPress database inspection of `_wp_old_slug` — mechanism remains **inferred**, not proven
- [ ] Rank Math redirect creation — **explicitly not required**

---

## 7. Decision branches (historical reference)

P0-4 closed under **“If 301/308 to free guide (current live behavior) — If intentional”**:

- [x] Keep permanent redirect
- [x] GSC validates redirect + canonical alignment
- [ ] Monitor GSC until `-2` impressions fade (ongoing; fresh GSC export when available)
- [ ] Do **not** request indexing for legacy URL
- [ ] Do **not** claim LEVEL 3 content recrawl complete on destination

Other branches (paid canonical target, 302-only, 200 duplicate, 404, 403) — **not applicable** to current verified state.

---

## 8. Editorial default (repository recommendation — adopted)

Given free guide LEVEL 3 LIVE, strongest LinkedIn signal, live 301 → free guide, and GSC canonical agreement:

**Decision:** **Keep 301 → free guide.** **P0-4 PASS / CLOSED.**

---

## 9. Unresolved items after P0-4 closeout

| Item | Status |
|------|--------|
| Exact WordPress redirect mechanism | **Unproven** — plausible `_wp_old_slug`; not a blocker |
| Fresh GSC CSV import for performance tracking | **Future** — do not patch against 2026-06-05 export |
| LEVEL 3 content recrawl on destination | **Not claimed** |
| Publisher Knowledge Graph entity | **Separate** site-level follow-up |

**Remediation complete:** P0-4 acceptance criteria satisfied. No WordPress or GSC mutation required.

---

## Related docs

- Closeout: `docs/P0_4_LEGACY_FREELANCERS_URL_GSC_CLOSEOUT_2026_07.md`
- Audit §9: `docs/SITE_FOCUS_AUTHORITY_AUDIT_2026_07.md`
- WP checklist: `docs/P0_A_WORDPRESS_IMPLEMENTATION_CHECKLIST.md`
- Roadmap P0-4: `docs/SITE_AUTHORITY_UPGRADE_ROADMAP_2026_07.md`
- P0-3 closeout: `docs/P0_3_FREE_PM_LEVEL3_LIVE_CLOSEOUT_2026_07.md`
