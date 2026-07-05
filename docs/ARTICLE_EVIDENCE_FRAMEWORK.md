# Article Evidence Framework — WorkToolsLab

**Purpose:** Reusable, solo-operator-friendly standard for how WorkToolsLab articles document tool evaluation — without inventing experience.

**Scope:** Editorial standard for future upgrades. This document does **not** claim any page currently meets LEVEL 3–4 unless explicitly verified after implementation.

---

## Evidence maturity levels

| Level | Name | What the reader sees |
|------:|------|----------------------|
| **0** | Generic editorial | Feature summaries, marketing language, no clear criteria |
| **1** | Decision guidance | “Choose X if…” without documented evaluation process |
| **2** | Transparent criteria | Stated dimensions, who should choose/avoid, pricing caveats |
| **3** | Visible first-hand testing | Dated testing notes, real screenshots, honest limitations |
| **4** | Repeatable methodology | LEVEL 3 + consistent template, verification dates, workflow captions |

**Rule:** Do not label LEVEL 3–4 without actual testing or verification work performed by the operator.

---

## Required honesty distinctions

Every article that mentions tool behavior must classify claims:

| Label | Meaning | Example phrasing |
|-------|---------|------------------|
| **Tested directly** | Operator used the tool in a real workflow during the review period | “In my test workspace, I…” |
| **Verified from official documentation** | Checked vendor docs/pricing pages at a stated date | “According to [Vendor]’s pricing page (checked YYYY-MM)…” |
| **Editorial inference** | Logical conclusion from public info + workflow fit | “For most freelancers, a Kanban board is usually easier to…” |

**Prohibited:** Presenting editorial inference or documentation checks as hands-on testing.

---

## Optional article components (copy-paste blocks)

Use only sections that apply. Omit rather than fabricate.

### How I Tested This (or How We Tested This)

Use **“How I Tested This”** for solo-operator byline consistency.

```text
How I Tested This

I tested [Tool name] in a [free plan / trial / paid plan — specify which] using a realistic freelance/small-team workflow. This is not a feature-by-feature benchmark. I focused on whether the tool helped with real work management tasks.
```

### Tested for (checklist — pick relevant items)

- [ ] Client project tracking
- [ ] Recurring tasks
- [ ] Deadline visibility
- [ ] Weekly review
- [ ] Multi-project overview
- [ ] Team handoff
- [ ] Documentation workflow

### Environment

Document only what was actually used:

- Web app (browser + version optional)
- Desktop app (if used)
- Mobile app (if used)
- Plan tier: free / trial / paid (exact plan name if paid)

### Last checked

```text
Last checked: YYYY-MM
```

Update when pricing, limits, or UI materially change.

### What I Noticed in Real Use

Bullet observations from direct use. Short, specific, workflow-oriented.

**If not tested:** Do not include this section.

### Where the Tool Starts to Feel Limiting

Honest friction points from use or from documented limits (label source).

### Best Fit / Poor Fit

Keep even at LEVEL 2. At LEVEL 3+, tie bullets to observed behavior.

### Screenshots

**Rules:**

- Real product screenshots only — captured by the operator
- No fabricated UI, no AI-generated product screenshots
- Caption must explain the **workflow** shown (not “ClickUp dashboard”)
- Redact personal/client data
- Respect product branding and fair editorial use

**Caption template:**

```text
Figure: [Tool] — [workflow step shown, e.g. “client board with Waiting on Client column”] (screenshot taken YYYY-MM, [plan tier])
```

### Limitations of this review

```text
Limitations

- I tested [plan/workflow scope], not every feature.
- Pricing and limits can change; verify on the vendor site.
- Your client load and team size may differ from my test setup.
```

---

## Minimum bar by article type

| Article type | Minimum level before promoting as “cornerstone” | Required sections |
|--------------|--------------------------------------------------|-------------------|
| Best-of roundup | LEVEL 2 + link to methodology | Criteria, best/poor fit, pricing caveat |
| Comparison (A vs B) | LEVEL 2; LEVEL 3 for priority comparisons | Comparison dimensions, best/poor fit |
| Concept guide (task vs PM) | LEVEL 1–2 | Decision routing; no fake testing |
| How-to / process | LEVEL 1 | Process steps; tool mentions labeled as editorial unless tested |
| Single-tool review | LEVEL 3 for trust | How I tested, environment, last checked, limitations |

---

## Priority pages — target levels (implementation phase)

| Page | Current (Jul 2026 audit) | Target |
|------|--------------------------|--------|
| Free PM for Freelancers | LEVEL 2 | LEVEL 3 (select tools actually tested on free tier) |
| Task vs PM | LEVEL 1–2 | LEVEL 2 (keep conceptual; add methodology link, not fake tests) |
| Best PM for Freelancers | LEVEL 0–1 | LEVEL 3 on 2–3 tools max |
| How to Manage Tasks | LEVEL 1 | LEVEL 2 (process evidence; optional one tool walkthrough at LEVEL 3) |
| Monday vs ClickUp | LEVEL 1 | LEVEL 3 if both tested in small-team scenario |

---

## Workflow for solo operator

1. **Pick one workflow** (e.g. “two client retainers, weekly review”).
2. **Pick plan tier** you will actually use.
3. **Spend 45–90 minutes** per tool minimum for LEVEL 3 — enough to capture 2–3 screenshots.
4. **Write claims** → tag each as tested / verified / inference.
5. **Set Last checked** month.
6. **Link** to `/how-we-review-tools/` and author profile when published.

---

## Explicit prohibitions

- Do **not** invent usage history, client stories, or test durations
- Do **not** add “tested” or “hands-on” to titles/meta unless LEVEL 3 content exists on page
- Do **not** use stock or generated UI as product evidence
- Do **not** claim certifications, expert titles, or industry authority without evidence
- Do **not** copy competitor review screenshots

---

## Repository integration

- Deep upgrade reports in `reports/deep_upgrade_*.md` should reference target evidence level
- After WordPress publish: `python -m linkops.cli fetch` to refresh cache
- Update `docs/CONTENT_OPERATIONS_STATE.md` with evidence level achieved

---

## Related docs

- Audit: `docs/SITE_FOCUS_AUTHORITY_AUDIT_2026_07.md`
- Author + methodology: `docs/AUTHOR_PROFILE_AND_REVIEW_METHODOLOGY_PLAN.md`
- Roadmap: `docs/SITE_AUTHORITY_UPGRADE_ROADMAP_2026_07.md`
