# Module 05: Allocation Tracking

## Overview

This is the operational core of the platform. It captures who is working on what, how much of their time is allocated, and how much is billable. Allocations are set once and carry forward automatically — PMs do not re-enter them monthly. This module manages assignment CRUD, the recurring model, manual release, the daily auto-release job, shadow flagging, project-level designation overrides, and the over-allocation warning system. `billing_rate` is added in Phase 2.

## Phase

Phase 1 (without `billing_rate`). Phase 2 adds `billing_rate`.

## Dependencies

- Module 01 (Auth & Roles)
- Module 03 (Project Management)
- Module 04 (Resource Management)
- Module 13 (Audit History) — all write operations must be audit logged from day 1

---

## Features

### Feature: Create Assignment
**Description:** Assign a resource to a project with allocation %, billability %, shadow flag, date range, and optional designation override.
**Acceptance Criteria:**
- [ ] Create assignment: project (required), resource (required), allocation_pct (required, 1–100), billability_pct (required, 0–100), is_shadow, project_designation, project_expertise, start_date (required), end_date (optional)
- [ ] All 7 FSD §11 assignment validations enforced (see Validations section)
- [ ] Over-allocation soft warning shown if total would exceed 100% (not blocking)
- [ ] All creates audit logged (one row per field)

### Feature: Edit Assignment
**Description:** Update any assignment field mid-period.
**Acceptance Criteria:**
- [ ] Update allocation_pct, billability_pct, is_shadow, project_designation, project_expertise, start_date, end_date
- [ ] `billing_rate` editable in Phase 2
- [ ] All validations re-applied on edit
- [ ] All edits audit logged with old and new values (one row per changed field)

### Feature: Manual Release
**Description:** PM explicitly ends an assignment before its end date.
**Acceptance Criteria:**
- [ ] Release button on active assignment → sets `status = RELEASED`, `released_at = now()`
- [ ] If released before `end_date`, logged as early release in AuditLog
- [ ] Total allocation recalculated after release

### Feature: Auto-Release Daily Job
**Description:** Scheduled job (midnight IST) releases assignments whose end_date ≤ today.
**Acceptance Criteria:**
- [ ] Job processes all assignments with `status = ACTIVE AND end_date IS NOT NULL AND end_date <= today`
- [ ] Sets `status = AUTO_RELEASED`, `released_at = end_date + 23:59:59`
- [ ] Fires alert to PM and DM for each released assignment
- [ ] All releases audit logged
- [ ] Edge case: if PM extended end_date before job runs, job skips that assignment
- [ ] Edge case: PM cannot modify already-released assignment; must create new one

### Feature: Recurring Model
**Description:** Allocations carry forward automatically — no monthly re-entry.
**Acceptance Criteria:**
- [ ] An assignment runs continuously from start_date until end_date (if set) or manual release
- [ ] No monthly rollover or re-entry required
- [ ] ~25% mid-period revisions supported without disruption

### Feature: Shadow Flagging
**Description:** Track resources doing unbilled work.
**Acceptance Criteria:**
- [ ] `is_shadow = true` forces `billability_pct = 0` (validation error otherwise)
- [ ] Shadow assignments contribute to resource cost but NOT to projected revenue
- [ ] Shadow flag visible to CEO, CTO, DM, PM, Finance — hidden from HR and Engineer

### Feature: Designation Resolution
**Description:** Per FSD §11 fallback rule — display project-level designation/expertise if set, else resource-level.
**Acceptance Criteria:**
- [ ] `project_designation` shown if set; otherwise `resource.designation`
- [ ] `project_expertise` shown if set; otherwise `resource.technical_expertise`
- [ ] All views, search, and filters apply this fallback

---

## Validations

All 7 FSD §11 assignment validations:

| Rule | Condition | Error |
|---|---|---|
| Billability ≤ Allocation | billability_pct > allocation_pct | "Billability cannot exceed allocation percentage" |
| Shadow = zero billability | is_shadow = true AND billability_pct > 0 | "Shadow resources cannot have billability" |
| End after start | end_date ≤ start_date | "End date must be after start date" |
| No duplicate active | Same resource+project has ACTIVE assignment | "Resource already has an active assignment on this project" |
| Project must be active | project.status ≠ ACTIVE | "Cannot create assignment on a non-active project" |
| Allocation range | < 1 or > 100 | "Allocation must be between 1% and 100%" |
| Over-allocation | Total > 100% after this assignment | Warning (not blocking): "This will bring total allocation to {X}%" |

---

## Business Rules

- Recurring model: set once, runs until end_date or manual release — see `shared/BUSINESS-RULES.md §8`
- Auto-release logic: `shared/BUSINESS-RULES.md §8` — exact job algorithm
- Designation resolution: `shared/BUSINESS-RULES.md §11` (Designation Resolution section)
- Shadow cost: shadow resources count toward project cost (via `loaded_cost_monthly`) but NOT projected revenue — `shared/BUSINESS-RULES.md §7.2`
- `billing_rate` is null in Phase 1; required for projected revenue calculation in Phase 2 — `shared/BUSINESS-RULES.md §7.3`
