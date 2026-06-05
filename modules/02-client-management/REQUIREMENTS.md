# Module 02: Client Management

## Overview

Clients are the top-level entity in the system. Every project belongs to a client and every financial metric rolls up to the client level. This module manages client profiles, multi-project visibility, and a consolidated client dashboard. The client dashboard shows resource and project counts in Phase 1; financial metrics (billing, cost, margin) are added in Phase 2.

## Phase

Phase 1 (base). Phase 2 adds financial metrics to the client dashboard.

## Dependencies

- Module 01 (Auth & Roles) — access control middleware required.

---

## Features

### Feature: Client CRUD
**Description:** Create, view, update, and deactivate client profiles.
**Acceptance Criteria:**
- [ ] Create client with name (required), industry, contact name/email/phone, engagement start date, notes
- [ ] Client name must be unique
- [ ] Update any client field
- [ ] Soft-delete client (`is_active = false`) — hard delete blocked
- [ ] Cannot deactivate a client with active projects — must complete or cancel all projects first
- [ ] All changes audit logged

### Feature: Client List with Search and Filter
**Description:** Paginated, searchable list of clients.
**Acceptance Criteria:**
- [ ] List all clients (active by default)
- [ ] Filter by `is_active` (Active / Inactive / All)
- [ ] Search by client name
- [ ] Each row shows: name, industry, engagement_start_date, active project count, is_active
- [ ] Sortable by name, engagement_start_date

### Feature: Client Detail View
**Description:** Full client profile with project list and Phase 1 dashboard metrics.
**Acceptance Criteria:**
- [ ] Show all client fields
- [ ] Show list of all projects for this client (name, type, status, DM)
- [ ] Phase 1 dashboard: active resource count, active project count
- [ ] Phase 2 dashboard (added later): total monthly billing INR, total cost INR, aggregate margin

### Feature: Client Dashboard Aggregation
**Description:** Computed metrics for the client detail page.
**Acceptance Criteria:**
- [ ] Active resource count = count of distinct resources with ACTIVE assignments on client's projects
- [ ] Active project count = count of projects with `status = ACTIVE`

---

## Validations

| Rule | Condition | Error |
|---|---|---|
| Name required | name is blank | "Client name is required" |
| Name unique | Duplicate name | "A client with this name already exists" |
| No deactivation with active projects | `is_active = false` attempted while active projects exist | "Complete or cancel all projects before deactivating this client" |

---

## Business Rules

- Clients use `is_active` soft delete — never hard delete
- Financial aggregations reference `shared/BUSINESS-RULES.md §7.2–§7.5` (Phase 2)
- Access: CEO, CTO have EDIT ALL; DM and PM have VIEW OWN_PORTFOLIO; Finance and HR have VIEW ALL; Engineer has NONE — per `shared/ACCESS-MATRIX.md`
