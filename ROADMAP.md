# ROADMAP — Resource Intelligence & Project Economics Platform

## Overview

Three-phase build plan progressing from core data infrastructure through financial capabilities to intelligent alerting. Each phase builds on the previous — no forward references.

**Tech stack decided 2026-06-09.** Python 3.12 + FastAPI backend, React 19 + Vite 6 frontend, PostgreSQL 16, Redis 7, AWS (EC2 + RDS). See `techstack/main.md`.

**Sprint cadence:** 1-week sprints. 1 developer + Claude Code (agentic). JIRA project: VRIP.

---

## Sprint Progress

| Sprint | Theme | Stories | SP | Status |
|--------|-------|---------|-----|--------|
| Sprint 0 | Bootstrap & DevOps | 8 | 20 | **Done** |
| Sprint 1 | Auth & Roles | 9 | 25 | Planned |
| Sprint 2 | Data Foundation (Resources + Clients) | 15 | 33 | Planned |
| Sprint 3 | Projects & Allocations BE | 11 | 30 | Planned |
| Sprint 4 | Projects & Allocations FE + IaC | 12 | 32 | Planned |
| Sprint 5 | Dashboards & Worklog + Polish | 14 | 35 | Planned |

### Sprint 0 — Completed (2026-06-10)

| Story | Deliverable | JIRA |
|-------|-------------|------|
| S0-01 | FastAPI scaffold, config, health endpoint, error handling | VRIP-11 |
| S0-02 | React + Vite scaffold, routing, auth store, axios client | VRIP-12 |
| S0-03 | Docker Compose (api, celery, redis, postgres) | VRIP-13 |
| S0-04 | GitHub Actions CI (lint, test, build) | VRIP-14 |
| S0-05 | Auth DB schema (roles, permissions, users, system_config) | VRIP-15 |
| S0-06 | Seed script (7 roles, 105 permissions, 7 configs, admin user) | VRIP-16 |
| S0-07 | AuditLog table + audit_log() service (BIGINT PK, append-only) | VRIP-17 |
| S0-08 | Celery + Redis (beat scheduler, ping task, retry policy) | VRIP-18 |

**Test coverage:** 74 backend tests + 7 frontend tests, all passing.

---

## Phase 1 — Foundation & Visibility

**Goal:** Core entities, CRUD operations, resource tracking, utilization dashboards, and audit infrastructure.

| Order | Module | Sprint | Key Deliverables | Depends On |
|---|---|---|---|---|
| 1 | `01-auth-and-roles` | 1 | Login, JWT auth, user management, RBAC middleware, role viewer | Bootstrap (Sprint 0) |
| 2 | `04-resource-management` | 2 | Resource CRUD, tags, profile view, designation/expertise tracking | 01 |
| 3 | `02-client-management` | 2 | Client CRUD, search/filter, detail view with project aggregation | 01 |
| 4 | `03-project-management` | 3–4 | Project CRUD, 3 types (FP/T&M/Onboarding), status lifecycle, worklog toggle | 01, 02, 04 |
| 5 | `05-allocation-tracking` | 3–4 | Assignment CRUD, auto-release job, shadow flagging, 7 validations, designation resolution | 03, 04 |
| 6 | `07-utilization-dashboards` | 5 | Company/DM/client/project/resource dashboards, availability view (utilization metrics only) | 03, 04, 05 |
| 7 | `11-worklog` | 5 | Daily hour logging, half-hour increments, project toggle, manager viewing | 03, 05 |
| 8 | `13-audit-history` | 0 | Audit logging infrastructure, append-only AuditLog, wrapper for all write operations | 01 |
| 9 | Terraform IaC | 4 | AWS provisioning (VPC, EC2, RDS, S3/CloudFront, security groups) | None |

**Phase 1 Milestone:** All core entities populated. Resources assigned to projects. Utilization visible. Daily worklogs captured. Every write operation audit-logged. Production infrastructure provisioned via Terraform.

---

## Phase 2 — Financial Engine

**Goal:** Cost tracking, revenue calculations, margin analysis, invoicing, and bench cost forecasting.

| Order | Module | Estimate | Key Deliverables | Depends On |
|---|---|---|---|---|
| 10 | `08-financial-engine` | L (5-10d) | loaded_cost_monthly on Resource, billing_rate on Assignment, all §7 formulas (cost, revenue, margin, bench cost) | 04, 05 |
| 11 | `06-non-human-costs` | M (3-5d) | Non-human cost CRUD, recurring costs with monthly processing job, multi-currency with INR conversion | 03 |
| 12 | `09-invoicing` | XL (10+d) | Milestone lifecycle (PLANNED→PAID), Invoice lifecycle (DRAFT→PAID), backward transitions, outstanding receivables | 03 |
| 13 | `10-bench-forecasting` | M (3-5d) | Current bench list, 30/60/90 day availability, partial availability, bench cost aggregation | 04, 05, 08 |
| 14 | `07-utilization-dashboards` | M (3-5d) | Add financial widgets: revenue, cost, margin charts to existing dashboards | 06, 08, 09 |

**Phase 2 Milestone:** Full financial visibility. Loaded costs and billing rates active. Margins calculated at project, client, and company level. Invoices tracked through lifecycle. Bench costs quantified.

---

## Phase 3 — Intelligence & Alerts

**Goal:** Proactive alerting, system configuration, and historical analysis.

| Order | Module | Estimate | Key Deliverables | Depends On |
|---|---|---|---|---|
| 15 | `12-alerts` | L (5-10d) | 4 scheduled alert jobs (contract expiry, bench duration, milestone overdue, utilization drop), 2 event-triggered alerts, notification panel, SystemConfig admin UI | All Phase 1 & 2 |
| 16 | `13-audit-history` | M (3-5d) | Audit log viewer UI, change history panel in entity details, point-in-time reconstruction | 13 (Phase 1 infra) |
| 17 | Role-based access config UI | S (1-2d) | Optional: UserPermissionOverride for per-user permission tweaks | 01 |

**Phase 3 Milestone:** System is self-monitoring. Alerts fire proactively for contract expiry, bench buildup, overdue milestones, and utilization drops. Full audit trail queryable with point-in-time reconstruction.

---

## Total Project Estimate

| Phase | Modules | Sprints | Status |
|---|---|---|---|
| Phase 1 — Foundation | 8 modules + IaC | 6 sprints (0–5) | Sprint 0 done, 1–5 planned |
| Phase 2 — Financial | 5 modules (incl. dashboard update) | TBD | Not started |
| Phase 3 — Intelligence | 3 modules (incl. audit update) | TBD | Not started |

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
| ~~Tech stack not yet decided~~ | ~~Blocks all coding~~ | **Resolved 2026-06-09** |
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
- 1-week sprint cadence, 1 developer + Claude Code agentic workflow
- JIRA project VRIP tracks all stories and sprints
