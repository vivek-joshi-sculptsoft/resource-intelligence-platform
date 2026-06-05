# Module 03: Project Management

## Overview

Projects are the operational unit of the system. Each project belongs to a client, has a type (Fixed Price, Time & Material, Client Onboarding) that determines its billing model and delivery structure, and goes through a defined lifecycle (Active → Completed/Cancelled/On Hold). This module handles project CRUD, status lifecycle management, cascading effects, and project list/detail views. Phase 1 builds the core; Phase 2 adds contract value and milestone/invoice tabs.

## Phase

Phase 1 (base). Phase 2 adds `contract_value` (for FP), milestone tab, and invoice tab.

## Dependencies

- Module 01 (Auth & Roles)
- Module 02 (Client Management) — projects belong to clients
- Module 04 (Resource Management) — DM and PM are resources

---

## Features

### Feature: Project CRUD with Type Selection
**Description:** Create, view, update, and manage projects with type-specific fields.
**Acceptance Criteria:**
- [ ] Create project: name (required), client (required), type (required: FP / T&M / Onboarding), billing currency (default INR), DM (required), PM (required), start_date, contract_end_date, worklog_enabled toggle, notes
- [ ] `contract_end_date` required for T&M and CLIENT_ONBOARDING types
- [ ] `contract_value` shown/required for FIXED_PRICE (Phase 2 only)
- [ ] Update any project field
- [ ] Soft delete not applicable — use status lifecycle instead
- [ ] All changes audit logged

### Feature: Project Status Lifecycle
**Description:** Projects follow a defined status state machine. See FSD §6.4.
**Acceptance Criteria:**
- [ ] Valid transitions: ACTIVE → COMPLETED, ACTIVE ↔ ON_HOLD, ACTIVE → CANCELLED
- [ ] Block creation of new assignments on COMPLETED or CANCELLED projects
- [ ] When COMPLETED or CANCELLED: all ACTIVE assignments auto-released immediately
- [ ] Status changes audit logged
- [ ] Error on invalid transition: "Invalid status transition"

### Feature: Project List with Filters
**Description:** Paginated, searchable list with multi-attribute filtering.
**Acceptance Criteria:**
- [ ] Filter by: client, type (FP/T&M/Onboarding), status, DM
- [ ] Search by project name
- [ ] Sortable by name, start_date, status
- [ ] DM scope: DM sees only projects where `dm_id = current user`
- [ ] PM scope: PM sees only projects where `pm_id = current user`

### Feature: Project Detail View
**Description:** Full project profile with tabbed sub-sections.
**Acceptance Criteria:**
- [ ] Header: name, client, type, status, billing currency, DM, PM — editable by PM+
- [ ] Assignments tab: resource list with allocation/billability/shadow/dates (Module 05 data)
- [ ] Non-human costs tab (Phase 2, Module 06)
- [ ] Milestones tab (FP only, Phase 2, Module 09)
- [ ] Invoices tab (Phase 2, Module 09)
- [ ] Financials tab (restricted — CEO/CTO/Finance only, Phase 2, Module 08)
- [ ] Worklogs tab (only if `worklog_enabled = true`, Phase 1)

### Feature: Worklog Toggle
**Description:** Enable or disable employee worklog per project.
**Acceptance Criteria:**
- [ ] PM and DM can toggle `worklog_enabled` on any of their projects
- [ ] When disabled, employees cannot see the worklog option for that project

---

## Validations

| Rule | Condition | Error |
|---|---|---|
| Name required | name is blank | "Project name is required" |
| Client required | client_id is null | "Project must belong to a client" |
| Type required | type not set | "Project type is required" |
| DM required | dm_id is null | "A Delivery Manager must be assigned" |
| PM required | pm_id is null | "A Project Manager must be assigned" |
| Contract end date required | T&M or ONBOARDING with no contract_end_date | "Contract end date is required for this project type" |
| Assignment on non-active project | assignment created on COMPLETED/CANCELLED project | "Cannot create assignment on a non-active project" |
| Invalid status transition | transition not in allowed set | "Invalid status transition" |

---

## Business Rules

- Status machine: ACTIVE → COMPLETED, ACTIVE ↔ ON_HOLD, ACTIVE → CANCELLED (FSD §6.4)
- Cascading auto-release: COMPLETED/CANCELLED triggers immediate release of all ACTIVE assignments
- `worklog_enabled` default = false; employee worklog only visible when true
- Access control: DM/PM OWN_PORTFOLIO scope enforced at DB query level per `shared/ACCESS-MATRIX.md`
