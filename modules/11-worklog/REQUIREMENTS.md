# Module 11: Worklog

## Overview

Worklog is a lightweight, optional daily time-logging feature. Anyone with an ACTIVE assignment — engineers, PMs, DMs, CEO, CTO — can record how many hours they spent on each assigned project per day. Finance and HR do not log hours; they can view worklogs company-wide. It is deliberately decoupled from billing, allocation, and invoicing — it does not block or feed into any financial workflow. A project-level toggle controls whether worklog is active. Managers can view worklogs for their projects.

## Phase

Phase 1.

## Dependencies

- Module 01 (Auth & Roles)
- Module 03 (Project Management) — `worklog_enabled` toggle
- Module 04 (Resource Management) — resource linking
- Module 05 (Allocation Tracking) — must have ACTIVE assignment to log hours

---

## Features

### Feature: Daily Worklog Entry
**Description:** Any role with an ACTIVE assignment (Engineer, PM, DM, CEO, CTO) logs hours per project per day. FINANCE and HR do not log hours (view-only, see Manager Worklog Viewing).
**Acceptance Criteria:**
- [ ] Employee selects a project from their ACTIVE assignments (where `worklog_enabled = true`)
- [ ] Enter hours (0.5–24.0 in half-hour increments)
- [ ] Optional note/description
- [ ] Cannot log hours for future dates
- [ ] Cannot log for same project + date twice (edit existing entry instead)
- [ ] Backfill allowed: can log for past dates if assignment was ACTIVE on that date

### Feature: Worklog Edit
**Description:** Employee can edit their own past entries.
**Acceptance Criteria:**
- [ ] Employee can edit `hours` and `note` on own entries
- [ ] Cannot change `project_id` or `log_date` — must delete and recreate
- [ ] No restriction on how far back employee can edit

### Feature: Manager Worklog Viewing
**Description:** PMs and above, plus FINANCE and HR, can view worklogs.
**Acceptance Criteria:**
- [ ] PM can view all worklogs for their projects (filtered by `pm_id = current user`)
- [ ] DM can view worklogs for their portfolio (`dm_id = current user`)
- [ ] CEO, CTO, FINANCE, HR can view all worklogs company-wide
- [ ] View shows: date, resource name, hours, note

### Feature: Project-Level Toggle
**Description:** PM or DM enables/disables worklog per project.
**Acceptance Criteria:**
- [ ] `worklog_enabled` toggle on project (Module 03)
- [ ] When disabled, employees cannot see the worklog option for that project
- [ ] Existing worklog entries are preserved when toggled off

### Feature: Export Worklogs to Excel
**Description:** Anyone with view access to a worklog list can export the currently filtered entries to an Excel (.xlsx) file. Available on the company-wide Worklogs page, the Worklog Tab (Project Detail), and the Recent Entries table on My Assignments.
**Acceptance Criteria:**
- [ ] "Export" button on the Worklogs page (`/worklogs`), Project Detail → Worklogs tab, and My Assignments (Recent Entries)
- [ ] Export respects all currently applied filters (date range, resource, project)
- [ ] Export includes every matching row, not just the current page
- [ ] Exported columns match the on-screen table for that view (Date, Resource where applicable, Project where applicable, Hours, Note)
- [ ] Access control on export is identical to the underlying list endpoint — export never returns rows the viewer couldn't already see on screen
- [ ] An empty filtered result produces an empty spreadsheet with headers, not an error

---

## Validations

FSD §11 Worklog validations:

| Rule | Condition | Error |
|---|---|---|
| Worklog enabled | project.worklog_enabled = false | "Worklog is not enabled for this project" |
| Active assignment | No ACTIVE assignment for resource on project | "You must have an active assignment to log hours" |
| No future dates | log_date > today | "Cannot log hours for future dates" |
| Hours range | < 0.5 or > 24 | "Hours must be between 0.5 and 24" |
| No duplicate | Same resource + project + log_date exists | "Entry already exists for this date. Edit the existing entry." |

---

## Business Rules

- Worklog is **decoupled by design**: no FK or trigger relationship with Invoice, Assignment billability, or any financial entity
- Backfill rule (FSD §14): allow backfill if resource had ACTIVE assignment on `log_date`; block if no ACTIVE assignment on that date
- Total hours logged across projects on the same day > 24: warning (not blocking) per FSD §14 edge cases
- Access: CEO/CTO create/edit own worklogs + view all (EDIT/ALL); DM/PM create/edit own worklogs + view own portfolio (EDIT/OWN_PORTFOLIO); ENGINEER creates/edits own worklogs only (EDIT/SELF_ONLY); FINANCE/HR view all, cannot log hours (VIEW/ALL) — `shared/ACCESS-MATRIX.md` (`worklogs`)
- Export is a read-only operation layered on top of the existing list endpoints — it applies no new access rule, generates the file on demand, and is not audit-logged (same rationale as worklog reads: informational only, no financial impact)
