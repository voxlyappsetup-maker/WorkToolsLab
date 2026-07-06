# P0-3 Owner Testing Execution Queue — Free PM for Freelancers

**Date:** 2026-07-07 (ClickUp confirmed; Trello next)  
**Environment:** Windows + PowerShell  
**Phase result target:** Complete real testing + valid screenshots before article rewrite  
**Do not** add credentials to the WorkToolsLab repository.

---

## Current status

| Tool | Status |
|------|--------|
| **ClickUp** | **CONFIRMED FOR TESTED SCOPE** — see `docs/P0_3_CLICKUP_DIRECT_TESTING_EVIDENCE_2026_07.md` |
| **Trello** | **NEXT — owner action required** |
| Todoist | Pending |
| Asana | Pending |
| Notion | Pending |

---

## Before you start

1. Read `docs/P0_3_FREE_PM_REAL_TESTING_MATRIX_2026_07.md` (canonical six tasks + three states).  
2. Use the same task names across tools where possible.  
3. After each tool session, save notes using the matrix template (plan, date, setup time, limitations).  
4. Report back: plan name, test date, screenshot filenames, valid/invalid, blockers.

**Estimated effort:** ~45–90 minutes per tool first time; ClickUp may be faster if seed + auth succeed.

---

## Session order (recommended)

| Order | Tool | Status |
|------:|------|--------|
| 1 | **ClickUp** | **Done** — confirmed for tested scope (2026-07) |
| 2 | **Trello** | **NEXT** |
| 3 | **Todoist** | Pending |
| 4 | **Asana** | Pending |
| 5 | **Notion** | Pending |

---

## Tool 1 — ClickUp — CONFIRMED FOR TESTED SCOPE

**Recorded:** `docs/P0_3_CLICKUP_DIRECT_TESTING_EVIDENCE_2026_07.md`  
**Plan:** Free Forever Plan | **Month:** 2026-07 | **Setup time:** Not measured  

**Valid publication candidates (external, after redaction):**

- `C:\dev\clickup-screenshots\screenshots\clickup-board-view.png`
- `C:\dev\clickup-screenshots\screenshots\clickup-list-view.png`

**Internal only:** `clickup-dashboard.png` (Home/Recents — not Dashboard evidence)

No further ClickUp action unless article rewrite requires redacted exports.

---

## Tool 2 — Trello — **NEXT OWNER SESSION**

### Sign-in

1. Open https://trello.com and sign in manually (no repo credentials).  
2. Record **exact plan name** from Trello account/billing UI (do not assume “Free” label).

### Build canonical scenario (one session)

1. Create one board for freelancer/client work (e.g. `Freelance Clients — Test`).  
2. Create three lists mapped to **To Do**, **In Progress**, **Complete** (or native equivalent + record mapping).  
3. Add six cards with **exact** canonical names:
   - Design homepage mockup  
   - Update pricing page  
   - Write Q3 blog post  
   - Review client feedback  
   - Prepare investor deck  
   - QA test new feature  
4. Add due dates to at least two cards.  
5. Open one card — add checklist or labels if useful for card-detail screenshot.

### Inspect (only what you actually open)

| Item | Required? |
|------|-----------|
| Board view (full pipeline) | **Yes** — screenshot |
| One card detail | **Yes** — screenshot |
| Multi-board / workspace overview | **Only if** you use a second board for client separation |
| Calendar view | **Only if** on your plan and you open it |
| Recurring tasks | **Only if** used in UI; else verify via official docs separately |

### Capture (Win+Shift+S or preferred tool)

Save locally with stable names:

- `trello-board-client-pipeline.png` — full board with three lists + six cards  
- `trello-card-detail.png` — one card open (due date, checklist/labels if added)  
- `trello-multi-board.png` — **optional** — only if second board adds evidence value

### Report back (required fields)

```text
Tool: Trello
Plan: [exact from account UI]
Test month: 2026-07
Setup time: [minutes] or Not measured
Screenshot filenames:
Valid/invalid per file:
What felt easy in actual use:
What felt limiting in actual use:
Feature expected but unavailable on actual plan:
Official docs checked (if any):
```

Do **not** store Trello credentials in the repository.

---

## Tool 3 — Todoist (manual browser session)

### Sign-in

1. Open https://todoist.com → log in.  
2. Record plan name (Beginner/Pro/etc.).

### Build canonical scenario

1. Create project `Freelance Clients — Test`.  
2. Add six tasks with canonical names + due dates.  
3. Represent In Progress via label, section, or filter — record method honestly.  
4. Open **Upcoming** or **Today** for weekly-review screenshot.

### Capture

- `todoist-project-task-list.png`  
- `todoist-upcoming-week.png`

### Docs verification

- Todoist pricing page — project limits, reminders, filters on free tier.

### Report back

Same fields as Trello session.

---

## Tool 4 — Asana (manual browser session)

### Sign-in

1. Open https://app.asana.com → log in.  
2. Record free/personal plan label.

### Build canonical scenario

1. Create project `Freelance Clients — Test`.  
2. Add sections (e.g. Planned, In Progress, Complete) or map to article’s retainer structure.  
3. Add six tasks; complete two; set due dates.  
4. Open **Board** view if available on your plan.

### Capture

- `asana-project-sections.png`  
- `asana-board-view.png` (if available)  
- `asana-task-detail.png`

### Docs verification

- Asana free plan — collaborators, timeline, milestones.

### Report back

Same fields as above.

---

## Tool 5 — Notion (manual browser session)

### Sign-in

1. Open https://www.notion.so → log in.  
2. Record plan label.

### Build canonical scenario

1. Create page `Client — Sample Co` (test name).  
2. Create deliverables database with properties: Name, Status, Due date.  
3. Add six rows with canonical task names; set statuses.  
4. Optional: board view grouped by Status.

### Capture

- `notion-deliverables-database.png`  
- `notion-client-page.png`  
- `notion-status-view.png` (filtered In Progress)

### Docs verification

- Notion free plan — guests, blocks, synced databases.

### Report back

Same fields; include setup time (Notion often longest).

---

## After all sessions — owner checklist

- [ ] All screenshots reviewed for redaction  
- [ ] Session notes completed per tool  
- [ ] Invalid ClickUp login PNGs replaced or deleted to avoid confusion  
- [ ] No auth JSON or `.env` copied into WorkToolsLab repo  
- [ ] Notify next agent session: ready for `P0_3_FREE_PM_LEVEL3_ARTICLE_BLUEPRINT` implementation rewrite  

---

## Operational notes

| Topic | Guidance |
|-------|----------|
| `python -m linkops.cli fetch` | **Do not run repeatedly** — SiteGround sgcaptcha blocks REST locally (HTTP 202). Not a testing blocker. |
| WordPress | **No writes** in this phase |
| Minimum for roadmap | At least **2 tools** with valid evidence to begin partial LEVEL 3 rewrite; **5 tools** for full roundup upgrade |

---

## Related docs

- `docs/P0_3_FREE_PM_SCREENSHOT_CAPTURE_PLAN_2026_07.md`
- `docs/P0_3_FREE_PM_LEVEL3_ARTICLE_BLUEPRINT_2026_07.md`
- `docs/P0_3_FREE_PM_FREELANCERS_EVIDENCE_AUDIT_2026_07.md`
