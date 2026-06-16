# Sprint Plan — All Phases

## Overview

| Metric | Value |
|--------|-------|
| Phases | Phase 1 (Foundation) + Phase 2 (Financial Engine) |
| Modules | 13 total |
| Total Stories | 109 (VRIP-1 to VRIP-109) |
| Sprint Duration | 1 week (5 working days) |
| Team | 1 developer + Claude Code |
| Estimated Sprints | 10 (Sprint 0–9) |
| JIRA Project | VRIP on sspl-organisation.atlassian.net |

### Estimation with AI-Assisted Development

Original estimates assume manual development. With Claude Code handling code generation, the effective velocity multiplier is ~2–3x for backend CRUD, schema, and tests; ~1.5–2x for complex business logic and frontend. Adjusted estimates used below.

| Size | Manual Estimate | AI-Adjusted | Story Points |
|------|----------------|-------------|-------------|
| S | 1–2 days | 0.5–1 day | 1 |
| M | 3–5 days | 1–2 days | 2 |
| L | 5–10 days | 2–4 days | 5 |

---

---

## Phase 1 — Foundation & Visibility ✓ COMPLETE

---

## Sprint 0 — Project Scaffold & Infrastructure Setup ✓ Done
**Goal:** Runnable empty project with CI/CD, Docker, database, and seed data.

| # | Story | Module | Size | SP |
|---|-------|--------|------|---|
| 1 | Set up monorepo with backend (FastAPI) and frontend (React+Vite) scaffolding | — | M | 2 |
| 2 | Docker Compose for local dev (PostgreSQL, Redis, API, Celery) | — | M | 2 |
| 3 | GitHub Actions CI pipeline (lint + test + build) | — | S | 1 |
| 4 | Create Role, RolePermission, User, SystemConfig schema and migrations | 01-auth | M | 2 |
| 5 | Create seed script (7 roles, 105 permissions, 7 config keys, admin user) | 01-auth | M | 2 |
| 6 | Create AuditLog database table | 13-audit | S | 1 |
| 7 | Build audit logging wrapper function | 13-audit | M | 2 |

**Sprint Points:** 12
**Deliverable:** `docker-compose up` boots the full stack with seeded database. CI runs on push.

---

## Sprint 1 — Authentication & Access Control ✓ Done
**Goal:** Login works. RBAC middleware enforced. Users can be managed.

| # | Story | Module | Size | SP |
|---|-------|--------|------|---|
| 1 | Implement login and logout endpoints | 01-auth | M | 2 |
| 2 | Implement GET /api/auth/me | 01-auth | S | 1 |
| 3 | Build access control middleware (RolePermission check + scope filtering) | 01-auth | L | 5 |
| 4 | Implement User CRUD API endpoints | 01-auth | M | 2 |
| 5 | Implement Role and RolePermission read-only API | 01-auth | S | 1 |
| 6 | Integrate audit logging into Module 01 | 13-audit | S | 1 |
| 7 | Build Login screen UI | 01-auth | S | 1 |
| 8 | Build User Management list screen | 01-auth | M | 2 |
| 9 | Build Create/Edit User form | 01-auth | M | 2 |
| 10 | Build Role Management screen (read-only permission matrix) | 01-auth | M | 2 |
| 11 | Write integration tests for auth flow and access control | 01-auth | M | 2 |

**Sprint Points:** 21
**Deliverable:** Login, user management, role viewer, RBAC enforced on every API call. Foundation for all other modules.

---

## Sprint 2 — Resource & Client Management ✓ Done
**Goal:** Resources and clients can be created, listed, filtered, and viewed.

| # | Story | Module | Size | SP |
|---|-------|--------|------|---|
| 1 | Create Resource and ResourceTag tables | 04-resource | S | 1 |
| 2 | Implement Resource CRUD API | 04-resource | M | 2 |
| 3 | Implement access control for Resource endpoints | 04-resource | S | 1 |
| 4 | Implement Tag Management API | 04-resource | S | 1 |
| 5 | Implement audit logging for Resource | 04-resource | S | 1 |
| 6 | Create Client database table | 02-client | S | 1 |
| 7 | Implement Client CRUD API | 02-client | M | 2 |
| 8 | Implement access control and deactivation guard for Client | 02-client | S | 1 |
| 9 | Implement audit logging for Client | 02-client | S | 1 |
| 10 | Build Resource List screen | 04-resource | M | 2 |
| 11 | Build Resource Create/Edit form | 04-resource | S | 1 |
| 12 | Build Client List screen | 02-client | M | 2 |
| 13 | Build Client Create/Edit form | 02-client | S | 1 |
| 14 | Write tests for Resource module | 04-resource | M | 2 |
| 15 | Write tests for Client module | 02-client | S | 1 |

**Sprint Points:** 20
**Deliverable:** Full resource directory with tags/filters. Client list with CRUD. Both with RBAC and audit.

---

## Sprint 3 — Project Management & Allocations Backend ✓ Done
**Goal:** Projects with status lifecycle. Assignments with all validations. Auto-release job.

| # | Story | Module | Size | SP |
|---|-------|--------|------|---|
| 1 | Create Project database table | 03-project | S | 1 |
| 2 | Implement Project CRUD API | 03-project | M | 2 |
| 3 | Implement access control for Project endpoints | 03-project | S | 1 |
| 4 | Implement project status lifecycle (state machine) | 03-project | M | 2 |
| 5 | Implement worklog toggle for projects | 03-project | S | 1 |
| 6 | Implement audit logging for Project | 03-project | S | 1 |
| 7 | Create Assignment database table | 05-alloc | S | 1 |
| 8 | Implement Assignment CRUD API with all 7 FSD validations | 05-alloc | L | 5 |
| 9 | Implement access control for Assignment endpoints | 05-alloc | S | 1 |
| 10 | Implement manual release of assignments | 05-alloc | S | 1 |
| 11 | Implement auto-release daily scheduled job | 05-alloc | M | 2 |
| 12 | Implement recurring model and shadow flagging | 05-alloc | S | 1 |
| 13 | Implement audit logging for Assignment | 05-alloc | S | 1 |
| 14 | Integrate audit logging into Modules 02–05 | 13-audit | M | 2 |

**Sprint Points:** 22
**Deliverable:** Projects with full lifecycle. Assignments with validation, release, auto-release. All audit logged.

---

## Sprint 4 — Project & Allocation UI + Resource Profile ✓ Done
**Goal:** All CRUD screens for projects and allocations. Resource profile with assignments.

| # | Story | Module | Size | SP |
|---|-------|--------|------|---|
| 1 | Build Project List screen | 03-project | M | 2 |
| 2 | Build Project Create/Edit form with conditional fields | 03-project | M | 2 |
| 3 | Build Project Detail screen with tabs and status buttons | 03-project | L | 5 |
| 4 | Build Assignment List UI within Project Detail (Assignments tab) | 05-alloc | M | 2 |
| 5 | Build Assignment Create/Edit form | 05-alloc | M | 2 |
| 6 | Build Resource Profile screen (assignments, stats, tags) | 04-resource | L | 5 |
| 7 | Build Resource Assignments panel within Resource Profile | 05-alloc | S | 1 |
| 8 | Implement Resource deactivation cascade | 04-resource | S | 1 |
| 9 | Build Client Detail screen with project list | 02-client | M | 2 |

**Sprint Points:** 22
**Deliverable:** Full project detail with assignment management. Resource profiles with live allocation data. Client detail page.

---

## Sprint 5 — Dashboards, Worklog & Polish ✓ Done
**Goal:** Utilization dashboards. Worklog entry. End-to-end testing. Phase 1 complete.

| # | Story | Module | Size | SP |
|---|-------|--------|------|---|
| 1 | Implement Company Dashboard aggregation API | 07-util | L | 5 |
| 2 | Implement DM Dashboard aggregation API | 07-util | M | 2 |
| 3 | Implement Resource Availability API | 07-util | M | 2 |
| 4 | Build Company Dashboard screen with widgets | 07-util | L | 5 |
| 5 | Build Resource Availability screen | 07-util | L | 5 |
| 6 | Build My Assignments screen (Engineer role) | 07-util | S | 1 |
| 7 | Create Worklog database table | 11-worklog | S | 1 |
| 8 | Build worklog CRUD API + validation rules | 11-worklog | M | 2 |
| 9 | Implement worklog access control | 11-worklog | S | 1 |
| 10 | Build worklog entry UI for employees | 11-worklog | L | 5 |
| 11 | Build worklog tab in project detail (manager view) | 11-worklog | M | 2 |
| 12 | Write tests for Assignment module | 05-alloc | L | 5 |
| 13 | Write tests for Project module | 03-project | M | 2 |
| 14 | Write tests for dashboard aggregation | 07-util | M | 2 |

**Sprint Points:** 40
**Note:** This is an overloaded sprint. If velocity doesn't support it, split into Sprint 5 (dashboards + worklog backend) and Sprint 6 (worklog UI + all remaining tests).

---

---

## Phase 2 — Financial Engine

---

## Sprint 6 — Financial Foundation 🔄 In Progress
**Goal:** Activate billing/cost fields. Non-human cost tracking. Recurring cost job.

| # | JIRA | Story | Module | Status |
|---|------|-------|--------|--------|
| 1 | VRIP-87 | Activate loaded_cost_monthly on Resource | 08-financial | ✓ Done |
| 2 | VRIP-88 | Activate billing_rate on Assignment | 08-financial | ✓ Done |
| 3 | VRIP-89 | NonHumanCost database schema | 06-non-human-costs | ✓ Done |
| 4 | VRIP-90 | NonHumanCost CRUD API (multi-currency, access control) | 06-non-human-costs | ✓ Done |
| 5 | VRIP-92 | Recurring cost processing scheduled job | 06-non-human-costs | ✓ Done |
| 6 | VRIP-91 | NonHumanCost list view and form UI | 06-non-human-costs | 🔄 In Progress |

**Deliverable:** Cost fields live on Resource and Assignment. PM/Finance can track all non-human project costs with multi-currency support. Monthly recurring costs auto-generate.

---

## Sprint 7 — Invoicing
**Goal:** Milestone tracking. Invoice generation and management.

| # | JIRA | Story | Module |
|---|------|-------|--------|
| 1 | VRIP-93 | Milestone schema and CRUD API | 09-invoicing |
| 2 | VRIP-94 | Invoice schema and generation API | 09-invoicing |
| 3 | VRIP-95 | Invoice PDF generation / export | 09-invoicing |
| 4 | VRIP-96 | Milestone list and form UI | 09-invoicing |
| 5 | VRIP-97 | Invoice list and detail UI | 09-invoicing |
| 6 | VRIP-98 | Invoice status workflow UI | 09-invoicing |

**Deliverable:** Projects have milestones. Invoices can be generated, tracked, and marked paid.

---

## Sprint 8 — Calculations & Bench Forecasting
**Goal:** Project cost/revenue/margin calculations. Bench cost API.

| # | JIRA | Story | Module |
|---|------|-------|--------|
| 1 | VRIP-99 | Project financials API — cost, revenue, margin | 08-financial |
| 2 | VRIP-100 | Financial engine tests and validation | 08-financial |
| 3 | VRIP-101 | Resource bench cost API | 08-financial |
| 4 | VRIP-102 | Bench cost and availability API enhancements | 10-bench |
| 5 | VRIP-103 | Bench forecasting UI | 10-bench |

**Deliverable:** Per-project P&L visible. Bench cost calculated from loaded_cost_monthly. Forecasting screen live.

---

## Sprint 9 — Dashboard Financial Updates & Polish
**Goal:** Add financial widgets to existing dashboards. Phase 2 complete.

| # | JIRA | Story | Module |
|---|------|-------|--------|
| 1 | VRIP-104 | Financial summary widget on Company Dashboard | 07-util + 08-financial |
| 2 | VRIP-105 | Project margin widget on Project Detail | 08-financial |
| 3 | VRIP-106 | DM portfolio financial view | 07-util |
| 4 | VRIP-107 | Revenue vs cost trend chart | 07-util |
| 5 | VRIP-108 | Alert system — contract expiry, bench, utilization | 12-alerts |
| 6 | VRIP-109 | Alert management UI | 12-alerts |

**Deliverable:** Dashboards show margin/revenue data. Alert system operational. Phase 2 complete.

---

## Sprint Velocity Tracking

| Sprint | Phase | Planned SP | Actual SP | Status |
|--------|-------|-----------|-----------|--------|
| 0 | 1 | 12 | 12 | ✓ Done |
| 1 | 1 | 21 | 21 | ✓ Done |
| 2 | 1 | 20 | 20 | ✓ Done |
| 3 | 1 | 22 | 22 | ✓ Done |
| 4 | 1 | 22 | 22 | ✓ Done |
| 5 | 1 | 40 | 40 | ✓ Done |
| 6 | 2 | 12 | — | 🔄 In Progress (5/6 done) |
| 7 | 2 | 14 | — | Pending |
| 8 | 2 | 12 | — | Pending |
| 9 | 2 | 14 | — | Pending |

**Total Phase 1:** ~137 story points across 6 sprints (complete)
**Total Phase 2:** ~52 story points across 4 sprints (in progress)

---

## Key Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| RBAC middleware complexity | Blocks all modules | Sprint 1 is entirely focused on auth. No parallel work until middleware is proven. |
| Assignment validation rules (7 FSD rules) | Most complex single story | Allocated as L (5 SP) in Sprint 3 with full sprint focus. |
| Dashboard aggregation queries | Performance at scale | Ship correct first (Sprint 5), optimize after with real data. |
| Sprint 5 overload (40 SP) | May not complete in 1 week | Split into 5a/5b if needed. Dashboards and worklog are independent — can parallelize. |
| Scope creep from Phase 2 dependencies | UI stubs for Phase 2 fields (loaded_cost, billing_rate) | Fields present but disabled/null. No Phase 2 logic in Phase 1 code. |

---

## Definition of Done (per story)

- [ ] Code reviewed (or Claude Code generated + developer verified)
- [ ] API endpoints match module API.md spec
- [ ] Access control tested for at least 2 roles (one allowed, one denied)
- [ ] Audit log entries verified for write operations
- [ ] Frontend matches SCREENS.md layout and states (including empty state)
- [ ] No TypeScript/Python type errors
- [ ] Story-level tests pass
