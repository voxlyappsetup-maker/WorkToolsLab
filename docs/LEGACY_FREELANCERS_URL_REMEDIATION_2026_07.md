# Legacy Freelancers URL Remediation — WorkToolsLab

**Date:** 2026-07-05  
**Phase:** P0-A Authority Implementation Foundation  
**Old URL:** `https://worktoolslab.com/best-project-management-tools-for-freelancers-2/`  
**Audit-assumed canonical:** `https://worktoolslab.com/best-project-management-tools-for-freelancers/`  
**Status:** Partial live verification complete — **owner browser + GSC steps still required**

---

## 1. Repository and cache truth

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

## 2. Live HTTP verification (2026-07-05)

### Automated results

| Probe | Result |
|-------|--------|
| PowerShell `Invoke-WebRequest -Method Head` (prior session) | **403** on `-2` (no Location) — likely bot/WAF |
| `curl.exe -sI` GET/HEAD on `-2` | **301 Moved Permanently** |
| Redirect header | `Location: https://worktoolslab.com/best-free-project-management-tools-for-freelancers/` |
| Redirect agent | `X-Redirect-By: WordPress` |
| Final response (follow redirect) | **200 OK** on **free guide** |

### Important finding

The live **301 target is the FREE guide**, not the paid canonical roundup assumed in the July audit.

| URL | Role |
|-----|------|
| `-2` | Legacy slug |
| **Current 301 target** | `/best-free-project-management-tools-for-freelancers/` |
| **Paid canonical (editorial)** | `/best-project-management-tools-for-freelancers/` |

**Owner decision required:** Is redirect to the free guide intentional (post deep upgrade)? If paid roundup should receive legacy signals, redirect target may need changing.

---

## 3. Sitemap evidence

| Check | Result |
|-------|--------|
| `-2` in WP cache sitemap list | **Not applicable** — not in inventory |
| Automated `sitemap.xml` probe (prior session) | **403** — inconclusive |
| `curl` sitemap | **Not completed this session** |

**Manual:** Search sitemap index for `freelancers-2` after fixing sitemap access.

---

## 4. Canonical tag evidence

Not extracted in this session for `-2` (redirects before body). On final target (free guide), Rank Math emits canonical via WebPage entity:

- `url`: `https://worktoolslab.com/best-free-project-management-tools-for-freelancers/`

**Manual:** View source on final landing page after browser redirect and confirm `<link rel="canonical">`.

---

## 5. Limitations of automated testing

- HEAD requests from some clients returned **403** while `curl` returned **301** — hosting/WAF may treat clients differently.
- Remediation is **not complete** until owner confirms behavior in a normal browser and GSC URL Inspection.

---

## 6. Owner verification checklist

Complete in order. Record results in a comment or worklog note.

### Browser verification

1. [ ] Open `https://worktoolslab.com/best-project-management-tools-for-freelancers-2/` in **incognito** browser.
2. [ ] Record **final browser URL** after redirects.
3. [ ] Confirm which article content is shown (free guide vs paid roundup vs other).
4. [ ] Open DevTools → **Network** tab → reload → note redirect status (**301**, **302**, etc.) and chain.
5. [ ] On final page: **View Source** → find `rel="canonical"` → record href.
6. [ ] Confirm page title and H1 match expected target.

### WordPress admin

7. [ ] **Rank Math → Redirections** (or equivalent) — search `freelancers-2`.
8. [ ] **Posts/Pages** — search slug `freelancers-2` (trash/draft).
9. [ ] If redirect exists, confirm **destination URL** matches editorial intent.

### Sitemap + index

10. [ ] Open live sitemap (`/wp-sitemap.xml` or working sitemap URL) — confirm `-2` is **absent**.
11. [ ] Confirm intended target URL **is** listed.

### Google Search Console

12. [ ] **URL Inspection** on `-2` URL — note coverage, redirect, last crawl.
13. [ ] **URL Inspection** on intended canonical target (free and/or paid — decide which should own legacy intent).
14. [ ] If redirect is correct and permanent: **Validate fix** / request indexing on target as needed.

---

## 7. Decision branches

### If 301/308 to **free guide** (current live behavior)

**If intentional** (legacy URL was replaced by free cornerstone):

- [ ] Keep permanent redirect
- [ ] Ensure paid roundup links clearly to free guide where appropriate
- [ ] Monitor GSC until `-2` impressions fade
- [ ] Request recrawl of free guide if content updated

**If NOT intentional** (paid roundup should own legacy PM-for-freelancers intent):

- [ ] Change WordPress redirect destination to `/best-project-management-tools-for-freelancers/`
- [ ] Use **301** (not 302)
- [ ] Update internal links if any pointed incorrectly
- [ ] GSC URL Inspection on new target
- [ ] Document change date in worklog

### If 302/307 only

- [ ] Change to **301** if move is permanent

### If 200 on `-2` (duplicate content)

- [ ] Remove duplicate; set 301 to chosen canonical
- [ ] Align canonical tag on all variants

### If 404/410

- [ ] Given 3 GSC impressions, consider **301 to chosen canonical** (free or paid — editorial decision)
- [ ] Avoid leaving orphan historical URL without redirect

### If 403 for humans (not just bots)

- [ ] Fix server/WAF rule blocking public access — separate from SEO redirect strategy

---

## 8. Recommended editorial default (repository recommendation)

Given:

- Free guide received June deep upgrade
- Strongest LinkedIn direct-link signal on free guide
- Live redirect already points to free guide

**Provisional recommendation:** **Keep 301 → free guide** unless owner explicitly wants paid roundup to absorb all legacy `-2` signals.

Document the decision in `config/worklog.json` after verification.

---

## 9. Unresolved manual items

- [ ] Incognito browser redirect chain confirmation
- [ ] Canonical tag on final URL
- [ ] Rank Math redirect admin screenshot/note
- [ ] Sitemap presence/absence of `-2`
- [ ] GSC URL Inspection for `-2` and target
- [ ] Owner sign-off: free vs paid as legacy redirect target

**Remediation complete:** Only when checklist is filled and GSC shows expected redirect/coverage.

---

## Related docs

- Audit §9: `docs/SITE_FOCUS_AUTHORITY_AUDIT_2026_07.md`
- WP checklist: `docs/P0_A_WORDPRESS_IMPLEMENTATION_CHECKLIST.md`
- Roadmap P0-4: `docs/SITE_AUTHORITY_UPGRADE_ROADMAP_2026_07.md`
