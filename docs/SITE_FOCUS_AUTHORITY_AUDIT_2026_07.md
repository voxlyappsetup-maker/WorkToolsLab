# Site Focus & Authority Audit — WorkToolsLab

**Date:** 2026-07-05  
**Site:** [worktoolslab.com](https://worktoolslab.com)  
**Repository:** `C:\dev\worktoolslab_linkops`  
**Phase:** Audit and planning only — **no WordPress changes in this phase**

**Evidence sources:**

- `data/worktoolslab_content_cache.json` (38 pages/posts, cache from WordPress fetch)
- `data/gsc_cache.json` (imported **2026-06-05T10:03:47Z** — do not re-patch against this export)
- `docs/distribution_log_2026_06.md` (LinkedIn distribution results)
- Live read-only checks (About, author archive, priority URLs, redirect/sitemap probes)
- Prior strategy docs: `TRAFFIC_DIAGNOSIS_2026_06.md`, `CONTENT_STRATEGY_RESET_2026_06.md`, `DISTRIBUTION_AUTHORITY_PLAN_2026_06.md`

---

## 1. Repository preflight

| Check | Result |
|-------|--------|
| Repository path | `C:\dev\worktoolslab_linkops` |
| Active branch | `main` |
| Working tree at audit start | Clean |
| Remote | `origin` → `https://github.com/voxlyappsetup-maker/WorkToolsLab.git` |
| LinkOps version | 1.7.6 |

**Recent commits (context):**

- `a8eacc0` Update LinkedIn distribution review results
- Distribution log entries for Free PM Freelancers, Task vs PM, Teamwork vs Asana, How to Manage Tasks, Notion/Trello/ClickUp, Monday vs ClickUp

**Prior phase status (June 2026):**

- On-page cleanup cycle: **complete** (0 unresolved clusters, 18 handled/monitor-only, 2 no-target queries)
- Distribution experiment: **logged** — direct-link engagement strongest on freelancer pain and task vs project distinction

---

## 2. Strategic hypothesis (to validate, not assume)

**Candidate primary focus:** Work management tools for freelancers and small teams

**Candidate supporting clusters:** project management, task management, workflow management, client work organization, small-team productivity

**Candidate deprioritization for *new* content:** broad video conferencing, generic communication tools, general remote-work tool coverage unrelated to core work-management workflows

**Audit conclusion:** Hypothesis is **supported by evidence** but the **live site and inventory do not yet reflect a narrowed focus**. Existing content remains broad; authority signals align with freelancer + task/project distinction, not with communication or meeting tool breadth.

---

## 3. Content inventory by topical cluster

**Inventory basis:** 38 URLs in `worktoolslab_content_cache.json` (posts + core pages). GSC page metrics from June 5 import.

| Cluster | Pages | GSC impressions (sum) | Representative URLs | LinkedIn signal | Overlap / cannibalization | Relevance to proposed focus |
|---------|------:|----------------------:|---------------------|-----------------|---------------------------|----------------------------|
| **Task management** | 3 | **885** | `/task-management-vs-project-management/` (684), `/best-task-management-tools-for-small-teams/` (139), `/how-to-manage-tasks-in-a-small-team/` (62) | **Strong** — Task vs PM: 2 link engagements @ 7d | Overlaps with PM and workflow guides; task vs PM is the hub concept page | **Core** — supports authority |
| **Freelancer project management** | 3 | **794** | `/best-project-management-tools-for-freelancers/` (681), `/trello-review-for-freelancers/` (100), `/best-free-project-management-tools-for-freelancers/` (13) | **Strongest** — Free PM guide: 3 link engagements @ 30d | **High** — paid roundup vs free guide vs Trello review | **Core** — primary commercial intent |
| **Small-team project management** | 1 | 379 | `/best-project-management-tools-for-small-teams/` | None logged | Overlaps freelancer roundup and task roundup | **Core** |
| **Productivity** | 1 | 461 | `/best-productivity-tools-for-small-teams/` (1 click — only sitewide click in top pages) | None logged | Broad; pulls intent away from work-management | **Supporting** — narrow angles only |
| **Workflow management** | 2 | 324 | `/notion-vs-trello-vs-clickup-which-one-is-best-for-your-workflow/` (281), `/best-workflow-management-tools-for-small-teams/` (43) | Awareness only (Notion/Trello/ClickUp post) | Overlaps PM/task comparisons | **Core** |
| **Comparison (PM/productivity)** | 5 | 417 | `/clickup-vs-trello-for-small-teams/` (171), `/monday-com-vs-clickup-for-small-teams/` (139), `/monday-com-vs-asana-for-small-teams/` (75), `/asana-vs-clickup-for-small-teams/` (32), `/teamwork-vs-asana-for-small-teams/` (0 GSC yet) | Mixed — Teamwork vs Asana awareness only | Multiple branded vs pages | **Supporting** — narrow comparisons OK |
| **Collaboration** | 1 | 128 | `/best-collaboration-tools-for-small-teams/` | None | Adjacent to communication | **Peripheral** |
| **Communication** | 3 | **635** | `/best-communication-tools-for-small-businesses/` (368), `/best-communication-tools-for-remote-teams/` (250), `/slack-review-for-small-teams/` (17) | None | Dilutes site theme | **Dilutes focus** — no new content |
| **Video meetings** | 5 | **617** | `/best-video-meeting-tools-for-small-businesses/` (220), Webex/Teams/Meet/Zoom reviews | None | High impression volume, zero clicks | **Dilutes focus** — maintenance only |
| **Communication/video reviews** | 4 | 267 | ClickUp, Notion, Asana, Monday reviews (PM-adjacent) | None | Support PM roundups | **Supporting** when linked from PM/task hubs |
| **Site hub / policy** | 10 | 69 | `/`, `/start-here/`, `/tools/`, `/about/`, etc. | N/A | **Heavy overlap** between Home, Tools, Start Here | **Needs architecture differentiation** |
| **Remote work** | 0 standalone | — | Remote intent mostly in communication cluster | None | — | **Deprioritize** unless tied to task/PM |

**Note:** GSC totals above cover indexed article URLs with page-level data; hub pages have low impressions.

### Explicit answers

| Question | Answer |
|----------|--------|
| **Does WorkToolsLab have a clear primary topical focus today?** | **No.** Published inventory spans work management, productivity, collaboration, communication, and video meetings with similar depth. Positioning copy says “freelancers and small teams” but category breadth matches a general small-business tools site. |
| **Which clusters support authority-building?** | Freelancer PM (especially free guide + pain-led angle), task management (concept + how-to), workflow management, narrow PM comparisons, small-team PM/task roundups when upgraded with evidence. |
| **Which clusters dilute focus?** | Communication roundups (635 imp, 0 clicks), video meeting roundups + reviews (617 imp, 0 clicks), broad productivity roundup (461 imp, weak position). |
| **Which clusters should receive no new content for now?** | Video meetings, generic communication, remote-work communication unless explicitly tied to client-work or task/PM workflows. |
| **Which existing content should stay published but maintenance-only?** | All communication and video meeting articles; broad collaboration roundup; remote-team communication guide. Update only for factual/pricing corrections or strong internal links to core hubs — not expansion. |

**Deletion:** Not recommended. No cluster is harmful enough to remove; dilution is a **focus and architecture** problem, not a delete-content problem.

---

## 4. Priority-page evidence audit (A–E)

### Summary table

| ID | URL | GSC (Jun 5) | LinkedIn | Evidence level | Notes |
|----|-----|-------------|----------|----------------|-------|
| **A** | `/best-free-project-management-tools-for-freelancers/` | 13 imp, 0 clicks, pos 64.4 | **Best signal** — 3 link engagements @ 30d | **LEVEL 2** | Deep June upgrade: criteria, who choose/avoid, workflows; no screenshots or dated testing block |
| **B** | `/task-management-vs-project-management/` | 684 imp, 0 clicks, pos 81.6 | 2 link engagements @ 7d | **LEVEL 1–2** | Strong conceptual guide; decision routing; no first-hand testing |
| **C** | `/best-project-management-tools-for-freelancers/` | 681 imp, 0 clicks, pos 52.1 | None dedicated | **LEVEL 0–1** | Generic roundup; overlaps A; cannibalization risk with free guide |
| **D** | `/how-to-manage-tasks-in-a-small-team/` | 62 imp, 0 clicks, pos 66.6 | Awareness only @ 7d | **LEVEL 1** | Practical process guide; tool mentions; no testing evidence |
| **E** | `/monday-com-vs-clickup-for-small-teams/` | 139 imp, 0 clicks, pos 79.8 | Awareness only (post logged) | **LEVEL 1** | Comparison structure; no methodology section or screenshots |

**Evidence level key:** 0 = generic editorial; 1 = decision guidance; 2 = transparent criteria; 3 = visible first-hand testing; 4 = repeatable methodology + screenshots + limitations + dated verification.

---

### A. Best Free Project Management Tools for Freelancers

| Field | Finding |
|-------|---------|
| **Title / H1** | Best Free Project Management Tools for Freelancers (2026) |
| **Meta description** | Not in WordPress cache excerpt; live page shows strong intro — verify Yoast/meta in WP before CTR tests |
| **Author** | Hayssam Dennaoui — “View all posts” (author archive) |
| **Dates** | Modified **2026-06-05** (cache) |
| **Structure** | Who for → criteria → quick comparison → per-tool sections → fit matrix → FAQ |
| **Methodology** | Practical lens stated (client work, deadlines, setup, free-tier fit); pricing “verify on vendor site” |
| **First-hand evidence** | **Not visible** — no “How I tested”, no screenshots, no Last checked date |
| **Best fit / poor fit** | **Yes** — per-tool who should choose/avoid |
| **Internal links** | Links to paid freelancer roundup, task vs PM, reviews |
| **CTA** | Implicit — pick tool + weekly review habit |
| **GSC** | Low page impressions (13) — newer/smaller sample vs paid freelancer URL |
| **Distribution** | Strongest LinkedIn direct-link performance in log |

**Classification:** **LEVEL 2** — criteria and fit boundaries are explicit; stops short of verified testing artifacts.

---

### B. Task Management vs Project Management

| Field | Finding |
|-------|---------|
| **Title / H1** | Task Management vs Project Management: What Is the Difference? |
| **Modified** | 2026-05-29 |
| **Structure** | Definitions → examples → when each needed → tool routing → FAQ |
| **Methodology** | Conceptual/educational — not tool testing |
| **First-hand evidence** | None |
| **Best fit / poor fit** | Indirect — “choose task tools if… / PM if…” |
| **Overlap** | Links to task roundup, PM roundups, workflow; competes with task how-to for informational intent |
| **GSC** | **Highest impressions** on site (684), position ~82 — snippet/authority problem |
| **Distribution** | Second-strongest direct-link signal (2 engagements) |

**Classification:** **LEVEL 1–2** — excellent decision framing; no evaluation methodology or testing.

**Historical status (July 2026 audit):** Finding above reflected pre-P1-1 baseline.

#### B — P1-1 live supersession (2026-07-11)

**Closeout:** `docs/P1_1_TASK_VS_PROJECT_MANAGEMENT_LEVEL2_POLISH_LIVE_CLOSEOUT_2026_07.md` — **PASS / CLOSED**

| Audit baseline | Live status after P1-1 |
|----------------|------------------------|
| No methodology link | **Added** — `/how-we-review-tools/` |
| LEVEL 1–2 conceptual only | **LEVEL 2** — decision table, FAQ, workflow scope; **not LEVEL 3** |
| Modified 2026-05-29 | **2026-07-11** revision live |
| GSC indexed | **Currently not indexed** — Jun 21 crawl historical; live test PASS Jul 11; indexing requested once |

**Do not claim** indexed, CTR, or ranking improvement.

---

| Field | Finding |
|-------|---------|
| **Canonical live URL** | **`https://worktoolslab.com/best-project-management-tools-for-freelancers/`** (in cache, live 200, byline present) |
| **Old URL candidate** | `https://worktoolslab.com/best-project-management-tools-for-freelancers-2/` — see Section 9 |
| **Title / H1** | Best Project Management Tools for Freelancers |
| **Modified** | 2026-05-29 |
| **Structure** | Criteria section → tool blurbs → choose guide → final thoughts |
| **Comparison methodology** | Feature/usability framing — no table, no testing block |
| **First-hand evidence** | None |
| **Overlap** | **High** with A (free guide) and Trello review; GSC impressions (681) likely split across freelancer PM intent |
| **GSC** | 681 imp, 0 clicks, pos 52.1 |

**Classification:** **LEVEL 0–1** — readable roundup; weaker than A on differentiation.

**Relationship A ↔ C:** Keep both published. A = free-tier + workflow pain; C = broader paid options. Requires clearer cross-linking and distinct snippets to reduce cannibalization.

---

### D. How to Manage Tasks in a Small Team

| Field | Finding |
|-------|---------|
| **Title / H1** | How to Manage Tasks in a Small Team |
| **Modified** | 2026-06-05 |
| **Structure** | Process guide (ownership, statuses, weekly review) + tool pick sections |
| **First-hand evidence** | None |
| **Screenshots** | None |
| **GSC** | 62 imp, pos 66.6 |
| **Distribution** | Posted LinkedIn — awareness only |

**Classification:** **LEVEL 1** — practical guidance; tool sections are editorial not tested.

---

### E. Monday.com vs ClickUp for Small Teams

| Field | Finding |
|-------|---------|
| **Title / H1** | Monday.com vs ClickUp for Small Teams: Which One Is Better? |
| **Modified** | 2026-06-05 |
| **Structure** | Standard comparison article |
| **Methodology** | Editorial comparison dimensions — no “how we tested” |
| **First-hand evidence** | None |
| **GSC** | 139 imp, pos 79.8 |
| **Distribution** | LinkedIn post logged; results pending / awareness pattern |

**Classification:** **LEVEL 1** — comparison intent clear; evidence thin.

---

## 5. Author identity and trust audit

| Check | Status |
|-------|--------|
| Article bylines | **Yes** — “Hayssam Dennaoui” on priority articles |
| Byline links to author archive | **Yes** — “View all posts by Hayssam Dennaoui” |
| Author archive URL | **`/author/hayssam-dennaoui/`** — exists; **post list only**, no bio or methodology |
| Named creator on About | **No** — About describes site evaluation factors, not who writes |
| Methodology page | **No** dedicated URL — criteria duplicated loosely on About |
| Project/building experience on site | **Not represented** — no builder/product context |
| Author in structured data | **Not verified in repo** — requires live HTML / Rich Results test (manual) |
| ProfilePage opportunity | **High** — would separate person trust from site About |

**Conclusion:** Byline consistency is good; **E-E-A-T gap** is missing person-level bio, methodology link, and honest scope of testing vs documentation.

Detailed proposal: `docs/AUTHOR_PROFILE_AND_REVIEW_METHODOLOGY_PLAN.md`.

---

## 6. Review methodology page audit

| Check | Result |
|-------|--------|
| Dedicated methodology page | **Does not exist** |
| About page evaluation section | Partial overlap — generic factors, no testing boundaries |
| Affiliate disclosure | Mentioned on About; separate disclosure page likely exists (policy cluster) |
| “How we tested” anywhere | **Not on priority pages** |

**Conclusion:** Create a standalone **How We Review Tools** page (design only this phase). Link from About, author profile, and cornerstone articles.

---

## 7. Home / Tools / Start Here architecture audit

| Page | Current role (observed) | Overlap problem | Proposed role |
|------|------------------------|-----------------|---------------|
| **Home** | Broad intro + many category links (PM, task, workflow, collaboration, communication, meetings) | Same link lists as Tools/Start Here | **Audience router:** freelance / small team / fix a workflow |
| **Tools** | Category directory mirroring full site breadth | Duplicates Home and Start Here | **Problem-oriented directory** (client work, daily tasks, team projects, workflows, knowledge, coordination) |
| **Start Here** | Another entry-point list | Third copy of similar recommendations | **Decision path:** problem → guide → comparison → review |

**Recommended H1 directions (future implementation):**

- Home: “Work management tools for freelancers and small teams”
- Tools: “Find the right work tool by problem”
- Start Here: “Start with your work problem”

**Primary CTAs:** Home → choose audience path; Tools → pick problem category; Start Here → first recommended guide for stated problem.

**Internal linking:** Hub pages should **not** list every category equally — weight freelancer PM, task, and workflow paths; demote communication/meetings to footer or “other topics”.

**Historical status (July 2026 audit):** Finding above reflected cache/live observation at audit time.

---

## 7a. P0-5 Home audience routing — live supersession (2026-07-09)

**Closeout:** `docs/P0_5_HOME_AUDIENCE_ROUTING_LIVE_CLOSEOUT_2026_07.md` — **PASS / CLOSED**

| Audit finding (July 2026) | Live status after P0-5 |
|---------------------------|------------------------|
| Home broadly routed across productivity, collaboration, communication, video-meeting clusters | **Superseded** — live Home now audience-routes freelancers and small teams into project/task/workflow content |
| Hub duplication (Home / Tools / Start Here) | **Partially addressed** — Home first pass complete; Tools and Start Here remain future P1 work |
| Recommended H1 “Work management tools for freelancers and small teams” | **Implemented** — live H1 matches intent |

**Do not rewrite §7 table** — it documents the pre-P0-5 baseline. **Do not claim** Google recrawl/reindex or performance impact from homepage change.

---

## 7b. P1-3 Tools page restructure — live supersession (2026-07-14)

**Closeout:** `docs/P1_3_TOOLS_PAGE_PROBLEM_ORIENTED_RESTRUCTURE_LIVE_CLOSEOUT_2026_07.md` — **PASS / CLOSED**

| Audit §7 baseline (July 2026) | Live status after P1-3 |
|------------------------------|------------------------|
| Tools = category directory mirroring full site breadth | **Superseded** — problem-oriented decision hub |
| Duplicates Home and Start Here | **Partially addressed** — Tools restructured; Start Here remains P1-4 |
| Proposed problem-oriented directory | **Implemented** — problem-first routing live |
| Communication/meetings equal weight | **Demoted** — secondary resources section |

**GSC:** Indexed; indexing requested once for July 12 recrawl — reprocessing **pending**. **Do not claim** CTR/ranking improvement.

---

## 8. Search snippet / CTR opportunity audit

**Rules applied:** Meaningful impressions at site scale; zero/weak CTR; clear intent; page already relevant; no clickbait; no false “tested” claims.

GSC query-page dimension was **not** in cache — proposals use page-level data + known query list from `gsc_cache.json` queries table.

| Page | Impressions | Current title (live) | Proposed title | Reason | Proposed meta (draft) | Target intent | Cannibalization | Test now? |
|------|------------:|----------------------|----------------|--------|-------------------------|-----------------|-----------------|-----------|
| `/task-management-vs-project-management/` | 684 | Task Management vs Project Management: What Is the Difference? | **Keep title**; test meta first | Title matches `project vs task` / `task and project management` queries; position ~82 suggests authority not snippet alone | “Task vs project explained for small teams: definitions, examples, and when you need task tools vs full project management.” | Informational task/PM distinction | Low vs task roundup | **Defer title**; test meta when WP access |
| `/best-project-management-tools-for-freelancers/` | 681 | Best Project Management Tools for Freelancers | **Best Project Management Tools for Freelancers (Compared for Client Work)** | Differentiate from generic SERP; no testing claim | “Compare ClickUp, Trello, Asana, Monday.com, Notion, and Todoist for freelance client work, deadlines, and workflow fit.” | `project management tools for freelancers` | **Medium** vs free guide | **Test now** (meta + intro lede) after author/methodology links planned |
| `/best-free-project-management-tools-for-freelancers/` | 13 | … (2026) | **Keep** — too few impressions for snippet science | LinkedIn validates angle; wait for GSC volume | Emphasize “free tier” + “client work” in meta when impressions grow | Free freelance PM | **Medium** vs C | **Defer** until fresh GSC |
| `/best-project-management-tools-for-small-teams/` | 379 | (roundup title) | Defer title change | Pos ~72; needs evidence upgrade before CTR test | — | Small-team PM software | vs freelancer URLs | **Defer** |
| `/best-productivity-tools-for-small-teams/` | 461 | (roundup) | **Reject** broad rewrite now | Only page with 1 click — changing may lose only positive signal | — | Productivity | Broad | **Reject** for now |
| `/how-to-manage-tasks-in-a-small-team/` | 62 | How to Manage Tasks in a Small Team | **How to Manage Tasks in a Small Team (Simple Process)** | Clarify guide vs tool roundup SERP | “A practical task system for small teams: ownership, statuses, weekly review, and when to add software.” | Task process intent | vs task roundup | **Defer** |
| `/monday-com-vs-clickup-for-small-teams/` | 139 | Monday.com vs ClickUp for Small Teams: Which One Is Better? | **Keep title** | Brand query `monday.com vs clickup` — title already aligned | “Structure and dashboards vs flexible all-in-one workspace — compared for small teams.” | Comparison | Low | **Defer** |

**Freelancer-specific priority:** Pages A and C need **differentiated snippets** (free vs paid; client-work angle) before more freelancer articles.

---

## 8a. P0-6 Best PM for Freelancers CTR differentiation — live supersession (2026-07-11)

**Closeout:** `docs/P0_6_BEST_PM_FREELANCERS_CTR_DIFFERENTIATION_LIVE_CLOSEOUT_2026_07.md` — **PASS / CLOSED**

| Audit §8 proposal (July 2026) | Live status after P0-6 |
|------------------------------|------------------------|
| Test meta + intro lede on `/best-project-management-tools-for-freelancers/` | **Implemented** — intro + meta differentiated; SEO title unchanged |
| Proposed title change to “Compared for Client Work” | **Not implemented** — P0-6 bounded to intro + meta only |
| Cannibalization risk vs free guide | **Mitigated in copy** — intro routes free intent to LEVEL 3 free guide |
| CTR/ranking impact | **NOT CLAIMED** — Google reprocessing pending; fresh GSC required |

**Do not rewrite §8 table** — historical June 2026 GSC baseline. **Do not claim** snippet/CTR improvement yet.

---

## 9. Technical SEO audit (repo + read-only live)

| Check | Finding |
|-------|---------|
| **freelancers-2 URL** | `https://worktoolslab.com/best-project-management-tools-for-freelancers-2/` → **HTTP 403** on automated HEAD (no `Location` header observed). **Not** in WordPress content cache. **Still in GSC** (3 imp, pos 57.7). No internal links to `-2` found in cache. |
| **Canonical freelancer URL** | `/best-project-management-tools-for-freelancers/` — live **200**, in cache, widely linked internally |
| **HTTP vs HTTPS in GSC** | `http://` variants for asana-review and monday-vs-asana pages — consolidate/canonical check needed in WP |
| **Sitemap** | `https://worktoolslab.com/sitemap.xml` — **403** on automated probe; `wp-sitemap.xml` probe did not complete in session — **manual verification required** |
| **Duplicate titles** | None in cache |
| **Duplicate H1 patterns** | Many “Best … for Small Teams/Businesses” — pattern repetition, not exact duplicates |
| **Article schema / author URL** | Not in repo — manual Rich Results Test on priority URLs |
| **ProfilePage schema** | Not implemented (opportunity) |
| **Breadcrumbs** | Not verified in repo |
| **Internal link concentration** | Many articles link to freelancer PM roundup; free guide under-linked given LinkedIn performance |
| **Orphan risk** | `/teamwork-vs-asana-for-small-teams/` — 0 GSC impressions in export (new); ensure hub links |
| **Core Web Vitals** | **No data in repository.** Owner must run PageSpeed Insights + Search Console CWV report manually. |

**Recommended manual checks (owner):**

1. GSC → Pages → filter `freelancers-2` → request removal or fix redirect if URL should be dead
2. Browser test `-2` URL (GET, not bot) — confirm 301 target or 410
3. Search Console → Sitemaps — submit `wp-sitemap.xml` if classic sitemap blocked
4. Rich Results Test on A, B, C for Article `author` URL
5. PSI mobile on Home + A + B

---

## 10. Strongest authority gaps (executive)

1. **No first-hand testing artifacts** on any priority page (max LEVEL 2)
2. **No person-level trust surface** (author profile + methodology)
3. **Topical sprawl** — communication + video content competes for crawl/context with core work-management URLs
4. **Zero CTR at scale** — 684 + 681 impressions on B and C with 0 clicks
5. **Hub duplication** — Home, Tools, Start Here send mixed signals
6. **Legacy URL** — freelancers-2 still appears in GSC; redirect/canonical unclear under bot blocking
7. **Cannibalization** — freelancer paid vs free guides need clearer SERP differentiation

---

## 11. Phase result

| Result | **PASS** (audit complete; implementation deferred) |
|--------|-----------------------------------------------------|
| Blockers | Sitemap and `-2` redirect require **manual browser/GSC** confirmation — documented, not blocking doc commit |
| Next phase | Implement P0 items in `docs/SITE_AUTHORITY_UPGRADE_ROADMAP_2026_07.md` |

---

## Related documents

- Roadmap: `docs/SITE_AUTHORITY_UPGRADE_ROADMAP_2026_07.md`
- Evidence framework: `docs/ARTICLE_EVIDENCE_FRAMEWORK.md`
- Author + methodology plan: `docs/AUTHOR_PROFILE_AND_REVIEW_METHODOLOGY_PLAN.md`
- Living state: `docs/CONTENT_OPERATIONS_STATE.md`
