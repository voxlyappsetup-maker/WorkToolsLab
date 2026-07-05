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

## ClickUp (4 captures planned — 3 automated + 1 manual task detail)

| # | Filename | View | Section supported | Proposed caption | Status |
|---|----------|------|-------------------|------------------|--------|
| 1 | `clickup-list-view.png` | List with six canonical tasks | §2 ClickUp — list workflow | ClickUp list view showing freelancer sample tasks in To Do, In Progress, and Complete statuses. | **captured-invalid** — login page |
| 2 | `clickup-board-view.png` | Board/Kanban | §2 ClickUp — visual stages | ClickUp board view of the same sample tasks grouped by status. | **captured-invalid** — login page (identical file size to #1) |
| 3 | `clickup-dashboard.png` | Home / workspace overview | §2 ClickUp — multi-client visibility | ClickUp home view showing active lists and upcoming work. | **captured-invalid** — login page |
| 4 | `clickup-task-detail.png` | Single task drawer/modal | §2 ClickUp — task context | ClickUp task detail with description and due date for a sample client deliverable. | **planned** — manual after auth |

**Inspection (2026-07-06):**

- Path: `C:\dev\clickup-screenshots\screenshots\`  
- All three existing PNGs: **264,507 bytes each**, **byte-identical**, visual content = **ClickUp login page**  
- Auth storage file exists (`auth/clickup.storage.json`, updated 2026-07-05 21:13) but **does not validate** prior captures  
- Captures timestamp **18:10–18:11** precedes auth file update **21:13** — re-capture required after `npm run auth:clickup`

**Redaction:** Workspace name, user email, notifications, sidebar team IDs if sensitive.

---

## Trello (3 captures)

| # | Filename | View | Section supported | Proposed caption | Status |
|---|----------|------|-------------------|------------------|--------|
| 1 | `trello-board-client-pipeline.png` | Board with lists as stages | §1 Trello | Trello board with client pipeline lists and sample deliverable cards. | **planned** |
| 2 | `trello-card-detail.png` | Card modal (checklist, due date, labels) | §1 Trello — revision tracking | Trello card showing due date, checklist, and labels for one deliverable. | **planned** |
| 3 | `trello-multi-board.png` | Workspace/board switcher (two boards) | §1 Trello — client separation | Two client boards visible in Trello for separating freelance work. | **planned** |

**Redaction:** Account email, real client names, private workspace URLs if needed.

---

## Notion (3 captures)

| # | Filename | View | Section supported | Proposed caption | Status |
|---|----------|------|-------------------|------------------|--------|
| 1 | `notion-deliverables-database.png` | Table/board with six items | §3 Notion | Notion database tracking freelance deliverables with status and due dates. | **planned** |
| 2 | `notion-client-page.png` | Client hub page | §3 Notion — context | Notion client page linking brief, notes, and deliverables. | **planned** |
| 3 | `notion-status-view.png` | Filtered “In Progress” view | §3 Notion — weekly review | Notion filtered view of in-progress client work. | **planned** |

**Redaction:** Workspace icon/name, personal email, connected accounts.

---

## Todoist (2 captures)

| # | Filename | View | Section supported | Proposed caption | Status |
|---|----------|------|-------------------|------------------|--------|
| 1 | `todoist-project-task-list.png` | Project with six tasks | §4 Todoist | Todoist project listing freelance tasks with due dates and priorities. | **planned** |
| 2 | `todoist-upcoming-week.png` | Upcoming/Today | §4 Todoist — weekly review | Todoist Upcoming view showing deliverables due this week. | **planned** |

**Redaction:** Email, calendar event titles from integrations.

---

## Asana (3 captures)

| # | Filename | View | Section supported | Proposed caption | Status |
|---|----------|------|-------------------|------------------|--------|
| 1 | `asana-project-sections.png` | List with sections | §5 Asana | Asana project with sections for planned, active, and completed client work. | **planned** |
| 2 | `asana-board-view.png` | Board (if on plan tested) | §5 Asana — client stages | Asana board view of sample client deliverables by stage. | **planned** |
| 3 | `asana-task-detail.png` | Task pane | §5 Asana — deliverable context | Asana task with due date and description for a sample deliverable. | **planned** |

**Redaction:** Workspace name, assignee emails, portfolio names.

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
