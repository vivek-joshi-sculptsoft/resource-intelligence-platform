# ROADMAP — Resource Intelligence & Project Economics Platform

## Overview

Three-phase build plan progressing from core data infrastructure through financial capabilities to intelligent alerting. Each phase builds on the previous — no forward references.

---

## Phase 1 — Foundation & Visibility

**Goal:** Core entities, CRUD operations, resource tracking, utilization dashboards, and audit infrastructure.

| Order | Module | Estimate | Key Deliverables | Depends On |
|---|---|---|---|---|
| 1 | `01-auth-and-roles` | L (5-10d) | Login, user management, 7 roles, 105 permissions, access middleware | Nothing |
| 2 | `04-resource-management` | M (3-5d) | Resource CRUD, tags, profile view, designation/expertise tracking | 01 |
| 3 | `02-client-management` | M (3-5d) | Client CRUD, search/filter, detail view with project aggregation | 01 |
| 4 | `03-project-management` | L (5-10d) | Project CRUD, 3 types (FP/T&M/Onboarding), status lifecycle, worklog toggle | 01, 02, 04 |
| 5 | `05-allocation-tracking` | XL (10+d) | Assignment CRUD, auto-release job, shadow flagging, 7 validations, designation resolution | 03, 04 |
| 6 | `07-utilization-dashboards` | L (5-10d) | Company/DM/client/project/resource dashboards, availability view (utilization metrics only) | 03, 04, 05 |
| 7 | `11-worklog` | M (3-5d) | Daily hour logging, half-hour increments, project toggle, manager viewing | 03, 05 |
| 8 | `13-audit-history` | M (3-5d) | Audit logging infrastructure, append-only AuditLog, wrapper for all write operations | 01 |

**Phase 1 Total Estimate:** ~45-60 days

**Phase 1 Milestone:** All core entities populated. Resources assigned to projects. Utilization visible. Daily worklogs captured. Every write operation audit-logged.

---

## Phase 2 — Financial Engine

**Goal:** Cost tracking, revenue calculations, margin analysis, invoicing, and bench cost forecasting.

| Order | Module | Estimate | Key Deliverables | Depends On |
|---|---|---|---|---|
| 9 | `08-financial-engine` | L (5-10d) | loaded_cost_monthly on Resource, billing_rate on Assignment, all §7 formulas (cost, revenue, margin, bench cost) | 04, 05 |
| 10 | `06-non-human-costs` | M (3-5d) | Non-human cost CRUD, recurring costs with monthly processing job, multi-currency with INR conversion | 03 |
| 11 | `09-invoicing` | XL (10+d) | Milestone lifecycle (PLANNED→PAID), Invoice lifecycle (DRAFT→PAID), backward transitions, outstanding receivables | 03 |
| 12 | `10-bench-forecasting` | M (3-5d) | Current bench list, 30/60/90 day availability, partial availability, bench cost aggregation | 04, 05, 08 |
| 13 | `07-utilization-dashboards` | M (3-5d) | Add financial widgets: revenue, cost, margin charts to existing dashboards | 06, 08, 09 |

**Phase 2 Total Estimate:** ~25-35 days

**Phase 2 Milestone:** Full financial visibility. Loaded costs and billing rates active. Margins calculated at project, client, and company level. Invoices tracked through lifecycle. Bench costs quantified.

---

## Phase 3 — Intelligence & Alerts

**Goal:** Proactive alerting, system configuration, and historical analysis.

| Order | Module | Estimate | Key Deliverables | Depends On |
|---|---|---|---|---|
| 14 | `12-alerts` | L (5-10d) | 4 scheduled alert jobs (contract expiry, bench duration, milestone overdue, utilization drop), 2 event-triggered alerts, notification panel, SystemConfig admin UI | All Phase 1 & 2 |
| 15 | `13-audit-history` | M (3-5d) | Audit log viewer UI, change history panel in entity details, point-in-time reconstruction | 13 (Phase 1 infra) |
| 16 | Role-based access config UI | S (1-2d) | Optional: UserPermissionOverride for per-user permission tweaks | 01 |

**Phase 3 Total Estimate:** ~10-17 days

**Phase 3 Milestone:** System is self-monitoring. Alerts fire proactively for contract expiry, bench buildup, overdue milestones, and utilization drops. Full audit trail queryable with point-in-time reconstruction.

---

## Total Project Estimate

| Phase | Modules | Estimate Range |
|---|---|---|
| Phase 1 — Foundation | 8 modules | 45-60 days |
| Phase 2 — Financial | 5 modules (incl. dashboard update) | 25-35 days |
| Phase 3 — Intelligence | 3 modules (incl. audit update) | 10-17 days |
| **Total** | **16 build steps** | **80-112 days** |

---

## Module Effort Summary (T-Shirt Sizing)

| Module | Size | Rationale |
|---|---|---|
| 01-auth-and-roles | L | Seed data (112 rows), middleware, session management |
| 02-client-management | M | Standard CRUD, simple entity |
| 03-project-management | L | 3 project types, status lifecycle, cascading release |
| 04-resource-management | M | CRUD + tags, profile view |
| 05-allocation-tracking | XL | State machine, auto-release job, 7 validations, shadow flagging, recurring model |
| 06-non-human-costs | M | CRUD + recurring processing job, multi-currency |
| 07-utilization-dashboards | L + M | Phase 1: 5 dashboards (L). Phase 2: financial widgets (M) |
| 08-financial-engine | L | 6 calculation formulas, field additions to existing entities |
| 09-invoicing | XL | 2 state machines (Milestone + Invoice), backward transitions, multi-currency |
| 10-bench-forecasting | M | Read-only aggregation, 30/60/90 day projections |
| 11-worklog | M | Simple CRUD with time validations |
| 12-alerts | L | 4 scheduled jobs, 2 event triggers, notification UI, SystemConfig |
| 13-audit-history | M + M | Phase 1: logging infra (M). Phase 3: viewer UI + reconstruction (M) |

---

## Key Dependencies Between Phases

```
Phase 1                          Phase 2                     Phase 3
────────                         ────────                    ────────
01-auth ─────────────────────────────────────────────────────────────→ (all)
04-resource ──────────────────→ 08-financial (adds loaded_cost)
05-allocation ────────────────→ 08-financial (adds billing_rate)
03-project ───────────────────→ 06-non-human-costs
03-project ───────────────────→ 09-invoicing
08-financial + 06-nhc + 09-inv → 07-dashboards (update)
04 + 05 + 08 ─────────────────→ 10-bench-forecasting
All Phase 1 + 2 ──────────────────────────────────────────→ 12-alerts
13-audit (infra) ─────────────────────────────────────────→ 13-audit (UI)
```

---

## Risk Factors

| Risk | Impact | Mitigation |
|---|---|---|
| Tech stack not yet decided | Blocks all coding | Decide before Phase 1 starts |
| Allocation validations are complex (7 rules) | Module 05 may take longer | Build validations incrementally, test each |
| Two state machines in invoicing | Module 09 complexity | Implement Milestone lifecycle before Invoice lifecycle |
| Dashboard performance at scale | Slow queries | Index strategy, consider materialized views |
| Multi-currency calculations | Rounding errors | Use exact formulas from BUSINESS-RULES.md, test with known values |

---

## Assumptions

- Single-tenant deployment (one IT company, ~30-40 employees)
- No mobile app in initial scope
- All monetary calculations in INR as base currency
- Working days: 22/month, 8 hours/day (configurable via SystemConfig)
- Tech stack decision is a prerequisite, not part of this roadmap
