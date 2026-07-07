# P0-3 Screenshot Capture Plan — Free PM for Freelancers

**Date:** 2026-07-06  
**Target article:** https://worktoolslab.com/best-free-project-management-tools-for-freelancers/  
**Rule:** Real product UI only. **No** fabricated UI, mock screenshots, AI-generated product UI, login pages, or marketing-site pages as workflow evidence.

---

## Global requirements

Every accepted screenshot record must include:

| Field | Required |
|-------|----------|
| Product | Tool name |
| Filename | Stable name under owner-controlled storage |
| Real product UI confirmation | Owner confirms authenticated app view |
| Account/plan | Exact plan name at capture time |
| Capture month | `YYYY-MM` |
| Workflow shown | Canonical scenario mapping |
| Article section supported | Tool section + optional evidence block |
| Proposed caption | Factual, non-hype |
| Private information check | Redaction completed |
| Evidence status | `planned` / `captured-valid` / `captured-invalid` / `approved-for-article` |

**Storage:** Keep captures outside gitignored secrets. WorkToolsLab repo has **no** screenshot directory today — import only after redaction review.

---

## Prohibited captures

- ClickUp/Trello/Notion/Todoist/Asana **login or signup** pages  
- AI-generated “fake” product UI  
- Stock marketing hero pages without in-app workflow  
- Duplicate files mistaken for different views (see ClickUp finding below)  
- Screenshots with visible passwords, API tokens, or client PII  

---

## ClickUp (updated 2026-07-07)

**Source path (external):** `C:\dev\clickup-screenshots\screenshots\` — not stored in LinkOps repo.

| # | Filename | View | Classification | Proposed caption | Publication |
|---|----------|------|----------------|------------------|-------------|
| 1 | `clickup-board-view.png` | Board/Kanban, grouped by Status | **VALID EVIDENCE** | “ClickUp Board view showing a six-task freelancer workflow grouped into To Do, In Progress, and Complete.” | **After redaction/crop** — identity in sidebar/workspace |
| 2 | `clickup-list-view.png` | List, status groups, due dates | **VALID EVIDENCE** | “ClickUp List view showing tasks grouped by status with due dates visible in the same workspace.” | **After redaction/crop** — identity in sidebar/workspace |
| 3 | `clickup-dashboard.png` | Home / Recents / My Work / Assigned to me | **INTERNAL TESTING EVIDENCE** | N/A — **not Dashboard evidence** | **Do not publish as-is** |
| — | Owner-supplied Plans screen | Free Forever Plan verification | **PLAN VERIFICATION EVIDENCE** | Internal only | **Do not publish** — confirms Free Forever Plan; 0/100 MB shown |
| 4 | `clickup-task-detail.png` | Task detail | **planned** | Optional future capture | Not required for current tested scope |

**Prior invalid captures (2026-07-06):** login-page PNGs — superseded by 2026-07 authenticated captures.

**Redaction:** Required on board + list before WordPress upload.

---

## Trello (updated 2026-07-08)

| File | Status | Caption |
|------|--------|---------|
| Board workflow | **VALID EVIDENCE** | “Trello Board showing six freelancer work items across To Do, In Progress, and Complete with due dates visible.” |
| Card detail | **VALID EVIDENCE** (redact name) | “Trello card detail showing a due date, task description, and a three-step checklist for a client feedback workflow.” |

---

## Todoist (updated 2026-07-08)

| File | Status | Caption |
|------|--------|---------|
| Board workflow | **VALID EVIDENCE** | “Todoist Board view showing six freelancer work items organized across To Do, In Progress, and Complete with due dates visible.” |
| Latest task detail | **VALID EVIDENCE** | Description, due date, three Sub-tasks |
| Earlier task detail | **SUPERSEDED** | Do not use |

---

## Asana (updated 2026-07-08)

| File | Status | Caption |
|------|--------|---------|
| Board workflow | **VALID EVIDENCE** | “Asana Board view showing six freelancer work items organized across To do, In Progress, and Complete with due dates visible.” |
| Task detail | **VALID EVIDENCE** | “Asana task detail showing a client-feedback task with a due date, description, and three subtasks inside the same Board workflow.” |

---

## Notion (updated 2026-07-08)

| File | Status | Caption |
|------|--------|---------|
| Board workflow | **VALID EVIDENCE** | “Notion database Board showing six freelancer work items grouped by status across To Do, In progress, and Complete.” — dates not on card faces in capture |
| Latest item detail | **VALID EVIDENCE** | Status, Date, context, three To-dos — supersedes earlier detail |
| Earlier detail | **SUPERSEDED** | Do not use |

---

## Acceptance checklist (per screenshot)

- [ ] Captured from authenticated **app** URL (not marketing site)  
- [ ] Shows canonical tasks or clearly labeled test data  
- [ ] Caption matches visible UI (no feature shown that is not in frame)  
- [ ] Redaction pass complete  
- [ ] File unique (not duplicate of another view)  
- [ ] Marked `approved-for-article` in owner notes before WordPress upload  

---

## Related docs

- `docs/P0_3_OWNER_TESTING_EXECUTION_QUEUE_2026_07.md`
- `docs/P0_3_FREE_PM_REAL_TESTING_MATRIX_2026_07.md`
- `docs/ARTICLE_EVIDENCE_FRAMEWORK.md`
