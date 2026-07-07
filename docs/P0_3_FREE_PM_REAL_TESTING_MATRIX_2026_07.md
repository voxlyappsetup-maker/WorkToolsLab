# P0-3 Real Testing Matrix — Free PM for Freelancers (Five Tools)

**Date:** 2026-07-06  
**Target article:** https://worktoolslab.com/best-free-project-management-tools-for-freelancers/  
**Framework:** `docs/ARTICLE_EVIDENCE_FRAMEWORK.md`  
**Status:** Planning only — **no tool is marked tested until owner confirms session + screenshots**

---

## Canonical freelancer test scenario

**Narrative:** A freelancer managing multiple client deliverables plus one internal content task.

**Workspace intent:** One client/campaign context (or equivalent) visible alongside tasks in To Do / In Progress / Complete states.

### Canonical work items (exact names)

| # | Task name | Target state |
|---|-----------|--------------|
| 1 | Design homepage mockup | To Do |
| 2 | Update pricing page | To Do |
| 3 | Write Q3 blog post | In Progress |
| 4 | Review client feedback | In Progress |
| 5 | Prepare investor deck | Complete |
| 6 | QA test new feature | Complete |

### Canonical workflow states

| Canonical | Meaning |
|-----------|---------|
| **To Do** | Not started |
| **In Progress** | Active work |
| **Complete** | Done / closed |

Record native terminology per tool at test time. Do not claim configuration until performed.

---

## Core tests (required for each tool)

| # | Test | Evidence minimum |
|---|------|------------------|
| 1 | Create project/workspace/list/board (as applicable) | Name recorded; screenshot of container |
| 2 | Create all six work items with exact names | List or board shows all six |
| 3 | Map To Do / In Progress / Complete | State names recorded in test notes |
| 4 | Assign due dates where supported | At least two future dates visible |
| 5 | Inspect list/task view | Screenshot |
| 6 | Inspect board/Kanban view (if available on plan used) | Screenshot or note “not on free plan / not tested” |
| 7 | Inspect calendar or project overview (if available on plan used) | Screenshot or doc-verified limitation |
| 8 | Check recurring task capability | UI test **or** official-doc verification only |
| 9 | Multi-project/client visibility | Second client project **or** doc note on free-plan limit |
| 10 | Task detail / context (description, checklist, comments field) | Screenshot of one task detail |
| 11 | Setup friction (timed) | Start/stop time; steps count |
| 12 | Weekly review visibility | Can user see due-this-week across projects? note + screenshot if yes |

### Optional (only if actually performed)

- Mobile app  
- Team handoff / assignee other than self  
- Collaboration / guest or client access  
- Automations  
- Dashboards / reporting  
- Time tracking  

**Prohibited without evidence:** claiming any optional test was performed.

---

## Status terminology mapping (to fill at test time)

| Tool | To Do (native) | In Progress (native) | Complete (native) | Configured? |
|------|----------------|----------------------|-------------------|-------------|
| Trello | To Do list | In Progress list | Complete list | **Yes** — 2026-07 |
| ClickUp | to do | in progress | complete | **Yes** — 2026-07 |
| Notion | To Do | In progress | Complete | **Yes** — 2026-07 |
| Todoist | To Do section | In Progress section | Complete section | **Yes** — 2026-07 |
| Asana | To do section | In Progress section | Complete section | **Yes** — 2026-07 |

**ClickUp seed reference:** Team `90182839060`, List `901819251529`, Space **Marketing Team**, List **Content Calendar**.

---

## Trello

| Field | Value |
|-------|--------|
| **Matrix status** | **Tested scope complete** — Premium trial session |
| **Setup time** | **3:23** |
| **Evidence** | `docs/P0_3_TRELLO_DIRECT_TESTING_EVIDENCE_2026_07.md` |

---

## ClickUp

| Field | Value |
|-------|--------|
| **Matrix status** | **Tested scope complete** — not “fully tested” |
| **Plan recorded** | **Free Forever Plan** (owner Plans screen, 2026-07) |
| **Environment** | Web app / desktop browser |
| **Test month** | **2026-07** |
| **Setup time** | **Not measured** (seed/API infrastructure — no setup-friction evidence) |
| **List view** | **Tested** |
| **Board view** | **Tested** |
| **Due dates** | **Observed** |
| **Home / Recents** | **Observed** (internal evidence — not Dashboard) |
| **Dashboard / reporting dashboards** | **Not tested** |
| **Manual setup friction** | **Not tested** |
| **Screenshots (external)** | `C:\dev\clickup-screenshots\screenshots\` — board + list valid after redaction |
| **Evidence record** | `docs/P0_3_CLICKUP_DIRECT_TESTING_EVIDENCE_2026_07.md` |

| Field | Requirement |
|-------|-------------|
| **Required account state** | Free Forever Plan workspace; authenticated browser session |
| **Browser/platform** | Desktop browser (screenshot project uses 1600×1000) |
| **Structure** | Content Calendar list, Marketing Team space (seeded) |
| **Redaction** | Workspace name, user email, sidebar identity before article use |
| **Doc verification separate** | Guest limits, automation, recurring tasks, advanced views on free tier |

---

## Notion

| Field | Value |
|-------|--------|
| **Matrix status** | **Tested scope complete** — Free plan |
| **Setup time** | **5:14** |
| **Evidence** | `docs/P0_3_NOTION_DIRECT_TESTING_EVIDENCE_2026_07.md` |

---

## Todoist

| Field | Value |
|-------|--------|
| **Matrix status** | **Tested scope complete** — Beginner plan |
| **Setup time** | **3:19** |
| **Evidence** | `docs/P0_3_TODOIST_DIRECT_TESTING_EVIDENCE_2026_07.md` |

---

## Asana

| Field | Value |
|-------|--------|
| **Matrix status** | **Tested scope complete** — Advanced trial session |
| **Setup time** | **2:39** |
| **Evidence** | `docs/P0_3_ASANA_DIRECT_TESTING_EVIDENCE_2026_07.md` |

---

## Test session record template (owner — one per tool)

Copy into session notes (not committed if containing account details):

```text
Tool:
Plan (exact name):
Browser / OS:
Test date (YYYY-MM):
Structure chosen:
Native state labels:
Setup start / end (minutes):
Weekly review: yes/no — how:
Recurring tasks: tested UI / docs only / not checked:
Limitations noticed:
Best fit (from this session):
Poor fit (from this session):
Screenshots captured (filenames):
Redaction done: yes/no
```

---

## Matrix completion criteria (article LEVEL 3 gate)

| Gate | Requirement |
|------|-------------|
| Minimum tools tested | Roadmap suggests **≥2** on free tier; this matrix plans **all 5** for full roundup upgrade |
| Screenshot integrity | Real product UI only; no login pages; no AI-generated UI |
| Wording gate | First-person testing blocks only for tools passing minimum above |
| Publication gate | Article rewrite + WordPress publish + live validation — **out of scope for this phase** |

---

## Related docs

- `docs/P0_3_FREE_PM_FREELANCERS_EVIDENCE_AUDIT_2026_07.md`
- `docs/P0_3_FREE_PM_SCREENSHOT_CAPTURE_PLAN_2026_07.md`
- `docs/P0_3_OWNER_TESTING_EXECUTION_QUEUE_2026_07.md`
