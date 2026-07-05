# P0-3 LEVEL 3 Article Blueprint — Free PM for Freelancers

**Date:** 2026-07-06  
**Target URL:** https://worktoolslab.com/best-free-project-management-tools-for-freelancers/  
**Purpose:** Future upgrade structure — **not** the final article draft  
**Rule:** First-person testing language **only** for tools with owner-confirmed direct testing + valid screenshots.

---

## Upgrade principles

1. Preserve strong LEVEL 2 content: criteria, personas, internal links, FAQ skeleton.  
2. Add concise per-tool evidence blocks — not a lab report.  
3. Insert screenshots where they support decisions (list/board/context), not decoration.  
4. Label every behavioral claim: **Tested directly** | **Verified from official documentation** | **Editorial assessment**.  
5. Do not publish this blueprint verbatim; rewrite in site voice after testing.

---

## Article-level additions (after testing begins)

| Addition | Placement | Blocked on testing? |
|----------|-----------|---------------------|
| Link to `/how-we-review-tools/` | After intro or before tool list | No |
| “How we evaluated these tools” (1 short paragraph) | Before detailed tool sections | Partial — cite dates when available |
| “Last checked” pricing note | Quick comparison + each tool pricing paragraph | Doc verification only |
| Evidence blocks per tool | Inside each numbered tool section | **Yes** — per tool |

---

## Evidence block template (use only when tool passes testing gate)

```text
How I Tested [Tool]

Testing environment: [browser, OS, plan name]
Last checked: YYYY-MM

What I tested: [canonical scenario summary — six tasks, three states]

What I noticed in real use:
- [specific observation tied to screenshot or workflow]

Where it starts to feel limiting:
- [honest limitation from session or free plan]

Best fit: [freelancer scenario]
Poor fit: [freelancer scenario]
```

**Tools not yet tested:** keep current editorial sections; add doc-verified pricing notes only:

```text
Pricing and limits (verified from official documentation, checked YYYY-MM): …
```

---

## Section map — existing → future

| Existing section | Future evidence addition | Screenshot | Claim status | Blocked? |
|------------------|-------------------------|------------|--------------|----------|
| Who This Guide Is For | No change | — | **D** | No |
| What Freelancers Should Look For (5 criteria) | Optional footnote linking methodology | — | **D** | No |
| Quick Comparison table | Add “Last checked” row footnote for pricing | — | **C** + **D** | Doc dates only |
| **§1 Trello** | Add evidence block **if tested**; else doc-verified pricing sub-block | Board + card detail | **B** → A after test | **Yes** for first-person |
| **§2 ClickUp** | Same | List + board (+ task detail) | **B** — blocked on auth screenshots | **Yes** |
| **§3 Notion** | Same | Database + client page | **B** | **Yes** |
| **§4 Todoist** | Same | Project list + Upcoming | **B** | **Yes** |
| **§5 Asana** | Same | Sections + board/detail | **B** | **Yes** |
| Which Tool Fits Your Freelance Workflow? | Tie personas to **tested** tools first; mark others editorial | Optional small icons only — no fake UI | **D** | Soft block if citing “easiest in test” |
| Free vs Paid | Verify numeric limits via docs at stated date | — | **C** | No |
| PM vs Task Management | Keep + internal link | — | **D** | No |
| Client Communication patterns | Keep editorial | — | **D** | No |
| Simple Free Setup This Week | Replace generic steps with **tested** tool example only when available | One screenshot max | **D** / **B** | Partial |
| Common Mistakes | Keep; add test-backed mistake only if observed | — | **D** | No |
| FAQ | Avoid “I tested all five”; answer with editorial + doc refs | — | **C** + **D** | Partial |

---

## Per-tool blueprint detail

### 1. Trello

| Element | Action |
|---------|--------|
| Keep | Example pipeline (Brief → … → Published); who should choose/avoid |
| Add after test | Evidence block; 1–2 screenshots |
| Soften until test | “Productive the same day” → editorial or dated observation |
| Doc verify | Free board limits, Power-Ups, automation |
| Internal link | Keep → Trello Review for Freelancers |

### 2. ClickUp

| Element | Action |
|---------|--------|
| Keep | Space/folder/list mental model; discipline warning |
| Add after test | Evidence block referencing **Marketing Team / Content Calendar** or equivalent |
| Screenshot placement | After “Example client workflow” paragraph |
| Do not claim yet | That seeded workspace was used until UI confirmed |
| Internal link | Keep → ClickUp Review for Growing Teams |

### 3. Notion

| Element | Action |
|---------|--------|
| Keep | Document-heavy freelancer angle; template warning |
| Add after test | Evidence block + database screenshot |
| Doc verify | Guest limits, blocks, AI features on free |
| Internal link | Keep → Notion Review for Small Teams |

### 4. Todoist

| Element | Action |
|---------|--------|
| Keep | Task-first positioning vs full PM |
| Add after test | Evidence block + Upcoming screenshot |
| Doc verify | Reminders/filters/projects on free plan |
| Internal link | Consider future Todoist review if created |

### 5. Asana

| Element | Action |
|---------|--------|
| Keep | Retainer/month structure; formal workflow angle |
| Add after test | Evidence block + sections screenshot |
| Doc verify | Timeline/milestones on free plan |
| Internal link | Keep → Asana Review for Small Teams |

---

## Persona section — post-upgrade wording guardrails

| Persona | Current recommendation | After testing |
|---------|------------------------|---------------|
| Solo Freelancer | Todoist or Trello | Prefer tools with **completed** evidence blocks; note others as editorial |
| Client-Service | Trello or Asana | Same |
| Designer/Marketer | Trello or ClickUp | Same |
| Subcontractors | ClickUp or Asana | Add doc caveat on free collaboration limits |
| Recurring client work | Asana or ClickUp | Tie to tested recurrence/template if verified |

---

## FAQ blueprint (do not invent tests)

| Question | Upgrade approach |
|----------|------------------|
| Best free PM tools for freelancers? | List five; clarify evaluation basis (criteria + tested subset) |
| Are free tools enough? | Editorial + doc limits |
| Easiest tool? | **Editorial only** until comparable setup times recorded |
| When to upgrade? | Doc-verified triggers + editorial |

---

## Publication checklist (future phase — not now)

- [ ] Each tested tool has evidence block + ≥2 valid screenshots  
- [ ] No first-person claims for untested tools  
- [ ] Pricing sentences include “checked YYYY-MM” where specific  
- [ ] Images uploaded to WordPress with alt text from capture plan captions  
- [ ] Rank Math fields pasted **values only** (no label prefixes)  
- [ ] Live view-source check after publish  
- [ ] Self-audit against `ARTICLE_EVIDENCE_FRAMEWORK.md` → target LEVEL 3  

---

## Blueprint status

| Field | Value |
|-------|--------|
| **Article rewrite drafted** | **No** |
| **LEVEL 3 complete** | **No** |
| **Blocked on** | Owner testing queue (`docs/P0_3_OWNER_TESTING_EXECUTION_QUEUE_2026_07.md`) |

---

## Related docs

- `docs/P0_3_FREE_PM_FREELANCERS_EVIDENCE_AUDIT_2026_07.md`
- `docs/P0_3_FREE_PM_SCREENSHOT_CAPTURE_PLAN_2026_07.md`
- `docs/ARTICLE_EVIDENCE_FRAMEWORK.md`
