# Module 11: Worklog

## Overview

Worklog is a lightweight, optional daily time-logging feature. Employees record how many hours they spent on each assigned project per day. It is deliberately decoupled from billing, allocation, and invoicing — it does not block or feed into any financial workflow. A project-level toggle controls whether worklog is active. Managers can view worklogs for their projects.

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
**Description:** Employees log hours per project per day.
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
**Description:** PMs and above can view worklogs for their projects.
**Acceptance Criteria:**
- [ ] PM can view all worklogs for their projects (filtered by `pm_id = current user`)
- [ ] DM can view worklogs for their portfolio (`dm_id = current user`)
- [ ] CEO, CTO can view all worklogs
- [ ] View shows: date, resource name, hours, note

### Feature: Project-Level Toggle
**Description:** PM or DM enables/disables worklog per project.
**Acceptance Criteria:**
- [ ] `worklog_enabled` toggle on project (Module 03)
- [ ] When disabled, employees cannot see the worklog option for that project
- [ ] Existing worklog entries are preserved when toggled off

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
- Access: employees create/edit own worklogs only (SELF_ONLY); PM/DM view own portfolio; CEO/CTO view all — `shared/ACCESS-MATRIX.md` (`worklogs`)
