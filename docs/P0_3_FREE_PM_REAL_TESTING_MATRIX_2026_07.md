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
| Trello | _record at test_ | _record at test_ | _record at test_ | **No** |
| ClickUp | to do | in progress | complete | **Yes** — UI confirmed 2026-07 |
| Notion | _record at test_ | _record at test_ | _record at test_ | **No** |
| Todoist | _record at test_ | _record at test_ | _record at test_ | **No** |
| Asana | _record at test_ | _record at test_ | _record at test_ | **No** |

**ClickUp seed reference (separate project, not confirmed in UI):** Team `90182839060`, List `901819251529`, Space **Marketing Team**, List **Content Calendar**.

---

## Trello

| Field | Requirement |
|-------|-------------|
| **Required account state** | Free account; solo workspace |
| **Plan to record** | Exact Trello/Atlassian plan name at test time |
| **Browser/platform** | Desktop Chrome (Edge acceptable); record version |
| **Structure** | One board (e.g. “Freelance Clients — Test”) with three lists mapped to canonical states **or** one list per client with labels — record choice |
| **Screenshots required** | Board overview; one card detail; optional second board for client separation |
| **Redaction** | Email, workspace name, member avatars, private board titles if not test data |
| **Minimum for “directly tested”** | All six tasks visible; three states demonstrated; dated notes; ≥2 real UI screenshots |
| **Doc verification separate** | Free board limit, Power-Ups, automation, member limits, attachment size |

**Native mapping (typical — verify at test):** Lists = stages; “Complete” may be a **Done** list or archived card.

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

| Field | Requirement |
|-------|-------------|
| **Required account state** | Free Plus / free personal workspace (record exact plan label) |
| **Plan to record** | Notion plan name at test time |
| **Browser/platform** | Desktop browser |
| **Structure** | Client page + deliverables database **or** single database with Status property |
| **Screenshots required** | Database/table view with six items; one client page; optional board/kanban view if enabled |
| **Redaction** | Workspace name, email, connected integrations |
| **Minimum for “directly tested”** | Six items with status + due date properties; dated setup time; ≥2 screenshots |
| **Doc verification separate** | Block limits, guest limits, synced blocks, AI features on free plan |

**Native mapping (typical):** Status select property → map to To Do / In Progress / Complete.

---

## Todoist

| Field | Requirement |
|-------|-------------|
| **Required account state** | Free account |
| **Plan to record** | Todoist Beginner/Pro label at test time |
| **Browser/platform** | Desktop web app |
| **Structure** | Project “Freelance Clients — Test”; six tasks; sections or labels for state if used |
| **Screenshots required** | Project task list; Today/Upcoming if used for weekly review; one task detail |
| **Redaction** | Email, integration names, real client names |
| **Minimum for “directly tested”** | Six tasks with due dates; state representation explained; ≥2 screenshots |
| **Doc verification separate** | Project limits, reminders, filters, labels on free plan |

**Native mapping (typical):** May use sections, labels, or completion checkbox only — record honestly if “In Progress” is label-based.

---

## Asana

| Field | Requirement |
|-------|-------------|
| **Required account state** | Free (Personal) workspace |
| **Plan to record** | Asana plan at test time |
| **Browser/platform** | Desktop browser |
| **Structure** | Project with sections: Planned / In Progress / Client Review / Complete **or** map three canonical states to sections |
| **Screenshots required** | List view with sections; board view if available; timeline only if on plan tested |
| **Redaction** | Workspace name, email, assignee photos |
| **Minimum for “directly tested”** | Six tasks across states; due dates; ≥2 screenshots |
| **Doc verification separate** | Collaborator limit, timeline availability, milestones on free plan |

**Native mapping (typical):** Sections or custom fields; Complete = completed tasks section.

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
