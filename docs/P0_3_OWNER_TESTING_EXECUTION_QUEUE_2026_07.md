# P0-3 Owner Testing Execution Queue — Free PM for Freelancers

**Date:** 2026-07-06  
**Environment:** Windows + PowerShell  
**Phase result target:** Complete real testing + valid screenshots before article rewrite  
**Do not** add credentials to the WorkToolsLab repository.

---

## Before you start

1. Read `docs/P0_3_FREE_PM_REAL_TESTING_MATRIX_2026_07.md` (canonical six tasks + three states).  
2. Use the same task names across tools where possible.  
3. After each tool session, save notes using the matrix template (plan, date, setup time, limitations).  
4. Report back: plan name, test date, screenshot filenames, valid/invalid, blockers.

**Estimated effort:** ~45–90 minutes per tool first time; ClickUp may be faster if seed + auth succeed.

---

## Session order (recommended)

| Order | Tool | Why |
|------:|------|-----|
| 1 | **ClickUp** | Existing seed + screenshot automation |
| 2 | **Trello** | Fast visual setup; pairs with freelancer angle |
| 3 | **Todoist** | Quick task-first baseline |
| 4 | **Asana** | Structured sections / retainers |
| 5 | **Notion** | Longest setup — do when fresh |

---

## Tool 1 — ClickUp (automated screenshots + manual verification)

### Prerequisites

- Node 18+ installed  
- Project: `C:\dev\clickup-screenshots`  
- `.env` contains `CLICKUP_API_TOKEN` (already configured locally — do not paste into chat/repo)  
- Optional env: `CLICKUP_TEAM_ID=90182839060`, `CLICKUP_LIST_ID=901819251529`

### Step A — Authenticate (required; prior captures failed)

```powershell
cd C:\dev\clickup-screenshots
npm run auth:clickup
```

**Manual in browser:**

1. Log into ClickUp (complete 2FA if prompted).  
2. Navigate until you see the **real workspace** — not the login form.  
3. Confirm List **Content Calendar** under Space **Marketing Team** is visible (or note if missing).  
4. Return to terminal and **press Enter**.

### Step B — Optional re-seed (if tasks missing)

```powershell
cd C:\dev\clickup-screenshots
npm run seed
```

Creates/skips six tasks: Design homepage mockup; Update pricing page; Write Q3 blog post; Review client feedback; Prepare investor deck; QA test new feature.

### Step C — Capture screenshots

```powershell
cd C:\dev\clickup-screenshots
npm run screenshots
```

Expected outputs:

- `screenshots\clickup-list-view.png`  
- `screenshots\clickup-board-view.png`  
- `screenshots\clickup-dashboard.png`

### Step D — Inspect locally (PowerShell)

```powershell
cd C:\dev\clickup-screenshots
Get-ChildItem .\screenshots\*.png | Format-Table Name, Length, LastWriteTime -AutoSize
$files = Get-ChildItem .\screenshots\clickup-*.png
($files | Select-Object -ExpandProperty Length | Sort-Object -Unique).Count
```

**Pass criteria:**

- Three PNGs with **different file sizes** (not all identical).  
- Opening files shows **authenticated ClickUp UI**, not login page.  
- List view shows **six sample tasks** with status columns.

**Manual add:** Capture `clickup-task-detail.png` (open one task → screenshot) for article evidence.

### Step E — Record for handoff

Report:

- ClickUp plan name (Settings)  
- Test date (`YYYY-MM`)  
- Auth success: yes/no  
- Screenshot valid: yes/no  
- Setup time (minutes)  
- Limitations noticed  

**ClickUp direct testing complete:** **NO** until Step D passes.

---

## Tool 2 — Trello (manual browser session)

### Sign-in

1. Open https://trello.com and sign in (manual — no repo credentials).  
2. Confirm you are on **Free** plan (record exact label).

### Build canonical scenario

1. Create board: `Freelance Clients — Test` (or similar).  
2. Create three lists mapped to **To Do**, **In Progress**, **Complete** (or use native Done list).  
3. Add six cards with exact canonical task names.  
4. Add due dates to at least two cards; labels/checklist on one card.

### Capture (manual screenshot tool — Win+Shift+S)

- `trello-board-client-pipeline.png` — full board  
- `trello-card-detail.png` — one card open  
- `trello-multi-board.png` — optional second client board

### Verify free-tier claims (docs)

- Open Trello/Atlassian pricing/help — note board limits, automation, Power-Ups on free plan.  
- Do **not** claim features not verified.

### Report back

Plan, date, setup minutes, screenshot filenames, doc URLs checked, limitations, best/poor fit from session.

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
