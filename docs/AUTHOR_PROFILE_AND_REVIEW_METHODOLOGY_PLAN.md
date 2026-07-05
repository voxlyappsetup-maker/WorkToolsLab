# Author Profile & Review Methodology Plan — WorkToolsLab

**Date:** 2026-07-05  
**Status:** Design only — **do not publish in this phase**

**Subject:** Hayssam Dennaoui  
**Grounding rule:** Use only information supported by repository docs, live site behavior, and stated project context. No invented credentials.

---

## Part 1 — Author identity audit

| Item | Current state | Gap |
|------|---------------|-----|
| Article byline | “Hayssam Dennaoui” on articles | Good |
| Byline → author archive | “View all posts by Hayssam Dennaoui” → `/author/hayssam-dennaoui/` | Archive is **post list only** |
| Author profile page (About-style) | **Missing** | No bio, photo optional, no builder context |
| About page | Site-level; evaluation factors; affiliate note | **No named author** |
| Methodology link from articles | **Missing** | About partially covers evaluation |
| LinkedIn | Used in distribution (`distribution_log_2026_06.md`) | Not linked from site author surface |
| Structured data | Not verified in repo | Likely missing `author.url` / ProfilePage |

---

## Part 2 — Author page proposal

### Purpose

Explain **who** creates WorkToolsLab content, **what experience** informs the reviews (product building and workflow software — not claimed PM certification), and **how** articles relate to testing vs documentation.

### URL strategy

| Option | URL | Recommendation |
|--------|-----|----------------|
| Primary | `/about/hayssam-dennaoui/` or `/author/hayssam-dennaoui/about/` | Prefer **dedicated profile page** linked from byline |
| Archive | `/author/hayssam-dennaoui/` | Keep as post index; add intro block at top OR redirect intro to profile |

**Recommended:** Create **`/about/hayssam-dennaoui/`** (or `/about-the-author/`) as the canonical person page; link from bylines; keep WordPress author archive for posts.

### Headline (proposed)

**Hayssam Dennaoui — Builder & Editor, WorkToolsLab**

Avoid: SEO Expert, Project Management Expert, Certified Analyst, productivity guru, industry-leading.

### Short bio (proposed — ~50 words)

Hayssam Dennaoui builds and ships digital products and writes WorkToolsLab guides to help freelancers and small teams choose work-management software. He focuses on practical workflow fit—client work, tasks, and team visibility—not feature checklists.

### Long bio outline

1. **What I do today** — Digital product builder working on AI-assisted products and mobile-first apps (LaunchOps AI, Vokami, Possessly, WorkToolsLab — as applicable per public project docs).
2. **Why WorkToolsLab exists** — Reduce confusion when choosing PM/task/workflow tools; emphasis on small teams and freelancers.
3. **What I actually test** — Scope honesty: which tools get hands-on workflow tests vs documentation verification (link to methodology page).
4. **What I don’t claim** — Not a certified PM consultant; recommendations are workflow-fit opinions.
5. **How to connect** — LinkedIn (single prominent link); optional contact via site Contact page.

### Methodology link strategy

- Author page → “How I review tools” → `/how-we-review-tools/` (to be created)
- Article bylines → author profile → methodology
- About page → “Meet the editor” link to author profile

### LinkedIn placement

- One link on author profile (icon + text)
- Optional short line in author profile footer: “I share work-management guides on LinkedIn.”
- Do not auto-embed feeds (maintenance cost)

### Article byline behavior (proposed)

**Current:** Hayssam Dennaoui | View all posts  
**Proposed:** Hayssam Dennaoui | [About the author] | View all posts  

Link “About the author” to profile page.

### Author schema recommendations

Implement in WordPress (Rank Math/Yoast or custom):

```json
{
  "@type": "Person",
  "name": "Hayssam Dennaoui",
  "url": "https://worktoolslab.com/about/hayssam-dennaoui/",
  "sameAs": ["https://www.linkedin.com/in/hayssam-dennaoui/"],
  "jobTitle": "Editor",
  "worksFor": { "@type": "Organization", "name": "WorkToolsLab", "url": "https://worktoolslab.com/" }
}
```

**Article schema:** Set `author.url` to profile page (not bare archive).

**ProfilePage:** Use `ProfilePage` type on author URL with `mainEntity` → Person.

**Do not publish** until copy is approved and LinkedIn URL verified.

---

## Part 3 — Review methodology page design

### Proposed URL

`/how-we-review-tools/`  
Alt: `/editorial-methodology/` — pick one; use consistently in docs and internal links.

### Proposed title / H1

**How WorkToolsLab Reviews Work-Management Tools**

### Purpose

Explain evaluation dimensions, testing boundaries, update policy, screenshots, limitations, affiliate behavior, and that there is no universal “best tool.”

---

### Page sections (outline)

#### 1. What we cover

Work-management software for freelancers and small teams: project management, task management, workflow tools, and related client-work organization.

#### 2. Evaluation dimensions

| Dimension | What we look for |
|-----------|------------------|
| Ease of setup | Time to first useful workflow |
| Learning curve | Can a small team adopt in a week? |
| Task ownership clarity | Single owner, status, due dates |
| Deadline visibility | Weekly view of what is due |
| Client-work fit | Separate clients, waiting states |
| Small-team fit | 2–10 people coordination |
| Workflow flexibility | Boards, lists, docs, automations |
| Reporting visibility | Enough insight without enterprise bloat |
| Free-plan practicality | Meaningful free tier for solo/small team |
| Upgrade pressure | When free becomes unusable |
| Limitations | Where tools break down |
| Long-term complexity | Admin burden over months |

#### 3. What is tested directly

- Operator creates a realistic test workspace (freelance client board or small-team task board)
- Exercises: create project, assign owner, due date, waiting state, weekly review
- **Label:** “Tested directly” in articles

#### 4. What is verified from documentation

- Pricing, seat limits, storage caps, feature gating
- **Label:** “Verified from official documentation (YYYY-MM)”

#### 5. What is editorial inference

- General workflow recommendations not tied to a specific test session
- **Label:** “Editorial recommendation”

#### 6. Update dates

- Articles show **Last updated** when materially changed
- Methodology page explains monthly/quarterly re-check for pricing pages

#### 7. Screenshots

- Real captures only; redacted; captioned with workflow context
- Reference `docs/ARTICLE_EVIDENCE_FRAMEWORK.md` for editors

#### 8. Limitations

- Reviews are workflow-fit guides, not exhaustive benchmarks
- Vendor features change; readers should confirm on official sites

#### 9. No universal “best tool”

Recommendations depend on team size, client load, and workflow style.

#### 10. Affiliate / commercial disclosure

- Some links may be affiliate links; commissions do not determine rankings
- **Do not invent** specific affiliate programs — mirror language from existing Affiliate Disclosure page
- Link to full disclosure page

---

### Relationship to About page

| Page | Role after implementation |
|------|---------------------------|
| **About** | What WorkToolsLab is; who it serves; link to author + methodology |
| **Author profile** | Who Hayssam is; builder context; LinkedIn |
| **Methodology** | How reviews work; testing vs documentation |

Reduce duplicated evaluation bullets on About — replace with links.

---

## Part 4 — Implementation checklist (WordPress — future phase)

- [ ] Draft author profile copy (short + long)
- [ ] Create methodology page from outline
- [ ] Update About with “Meet the editor” + methodology links
- [ ] Configure Article `author.url` in SEO plugin
- [ ] Add ProfilePage schema on author URL
- [ ] Update byline template in theme
- [ ] Verify Rich Results Test
- [ ] Internal link from A, B, C footers to methodology

---

## Related docs

- Audit: `docs/SITE_FOCUS_AUTHORITY_AUDIT_2026_07.md`
- Evidence framework: `docs/ARTICLE_EVIDENCE_FRAMEWORK.md`
- Roadmap: `docs/SITE_AUTHORITY_UPGRADE_ROADMAP_2026_07.md`
