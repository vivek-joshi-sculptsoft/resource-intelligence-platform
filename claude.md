# CLAUDE.md — Master Instructions for Claude Code

## Project Overview

You are building a **Resource Intelligence & Project Economics Platform** — an internal tool for an IT services company (~30-40 employees) to track resource allocations, project delivery, client billing, and financial margins. It replaces Google Sheets.

**Read these files first before writing any code:**
1. `prd/PRD.md` — What the product does (business perspective)
2. `fsd/FSD.md` — How the system works (technical specifications)
3. `shared/ENTITIES.md` — Master entity definitions (single source of truth for all field types, constraints, relationships)
4. `shared/BUSINESS-RULES.md` — Canonical calculations, formulas, and rules
5. `shared/ACCESS-MATRIX.md` — Role-based access control rules
6. This file — Build conventions and module structure

---

## Tech Stack

> **Decided 2026-06-09. Full details in `techstack/main.md` and per-layer docs.**

| Layer | Choice | Notes |
|---|---|---|
| Frontend | React 19 + Vite 6 | shadcn/ui + Tailwind CSS, React Router v7, TanStack Query + Zustand |
| Backend | Python 3.12 + FastAPI | Pydantic v2, SQLAlchemy 2.0 + Alembic, uvicorn |
| Database | PostgreSQL 16 (AWS RDS) | db.t4g.micro, UUID PKs, DECIMAL(15,2) for financials |
| Cache / Broker | Redis 7 (Docker on EC2) | Celery broker + API cache |
| Background Jobs | Celery 5.4 + celery-beat | 6 scheduled jobs (auto-release, alerts, recurring costs) |
| Auth | Custom JWT (python-jose + argon2) | httpOnly cookies, 15min access + 7d refresh tokens |
| Hosting | AWS (EC2 t3.small + RDS + S3/CloudFront) | Docker Compose, ap-south-1 (Mumbai), ~$36/mo |
| CI/CD | GitHub Actions | Lint → Test → Build → Deploy |
| Monitoring | Sentry + CloudWatch | Error tracking + infra metrics |

See `techstack/decisions/` for Architecture Decision Records explaining the reasoning behind each choice.

---

## Repo Structure

```
project/
├── prd/PRD.md                        # Product requirements (read-only reference)
├── fsd/FSD.md                        # Functional specs (read-only reference)
├── shared/                           # Cross-cutting references
│   ├── ENTITIES.md                   # Master entity definitions
│   ├── BUSINESS-RULES.md             # Formulas, calculations, constraints
│   ├── ACCESS-MATRIX.md              # Who sees/edits what
│   └── GLOSSARY.md                   # Term definitions
├── modules/                          # Module-wise specifications (13 modules)
│   └── {NN}-{module-name}/
│       ├── REQUIREMENTS.md           # What this module does + acceptance criteria
│       ├── SCHEMA.md                 # Entity fields for this module
│       ├── API.md                    # Endpoints
│       ├── SCREENS.md               # UI views and components
│       ├── DEPENDENCIES.md          # Upstream and downstream module dependencies
│       └── JOBS.md                  # Background jobs (only if module has any)
├── tickets/                          # JIRA-ready story breakdowns per module
│   └── {module-name}.md
├── CLAUDE.md                         # This file
├── ROADMAP.md                        # Phase-wise build plan with estimates
└── README.md                         # Project overview and setup guide
```

---

## Build Phases & Module Order

### Phase 1 — Foundation & Visibility
Build in this exact order (each module depends on the previous):

| Order | Module | Depends On | Key Entities |
|---|---|---|---|
| 1 | `01-auth-and-roles` | Nothing | Role, RolePermission, User |
| 2 | `04-resource-management` | Auth | Resource, ResourceTag |
| 3 | `02-client-management` | Auth | Client |
| 4 | `03-project-management` | Auth, Client, Resource | Project |
| 5 | `05-allocation-tracking` | Project, Resource | Assignment (core — without billing_rate) |
| 6 | `07-utilization-dashboards` | Assignment, Resource, Project | No new entities — reads from existing |
| 7 | `11-worklog` | Assignment, Project | Worklog |
| 8 | `13-audit-history` | All above | AuditLog |

### Phase 2 — Financial Engine
| Order | Module | Depends On | Key Entities |
|---|---|---|---|
| 9 | `08-financial-engine` | Resource, Assignment | Add: loaded_cost_monthly, billing_rate |
| 10 | `06-non-human-costs` | Project | NonHumanCost |
| 11 | `09-invoicing` | Project, Milestone | Milestone, Invoice |
| 12 | `10-bench-forecasting` | Resource, Assignment | No new entities — reads + computes |
| 13 | `07-utilization-dashboards` | Update | Add financial widgets to existing dashboards |

### Phase 3 — Intelligence & Alerts
| Order | Module | Depends On | Key Entities |
|---|---|---|---|
| 14 | `12-alerts` | All above | Alert, SystemConfig (full) |
| 15 | `13-audit-history` | Update | Add historical query UI, point-in-time reconstruction |
| 16 | Role-based access config UI | RolePermission | UserPermissionOverride (optional) |

---

## Coding Conventions

### General
- Use TypeScript for both frontend and backend (if JS stack)
- Use Python type hints if Python backend
- Every function that touches business logic must reference the FSD section number in a comment: `// See FSD §7.3 — Projected Revenue`
- No hardcoded magic numbers — use SystemConfig entity or environment variables
- All monetary calculations use the exact formulas from `shared/BUSINESS-RULES.md`

### Database
- Use UUID v4 for all primary keys
- All tables have `created_at TIMESTAMP DEFAULT NOW()` and `updated_at TIMESTAMP`
- Soft delete via `is_active BOOLEAN DEFAULT true` — never hard delete user-facing entities
- AuditLog is append-only — no UPDATE or DELETE on this table ever
- Use database-level constraints for ENUMs, foreign keys, and unique constraints
- Index all foreign keys and status fields

### API
- RESTful endpoints following: `GET /api/{entity}`, `POST /api/{entity}`, `PUT /api/{entity}/:id`, `DELETE /api/{entity}/:id`
- Every endpoint must check access control via RolePermission before returning data
- Sensitive fields (loaded_cost_monthly, billing_rate, margins) must return `null` for unauthorized roles — not omit the field (keeps response shape consistent)
- All list endpoints support pagination: `?page=1&limit=20`
- All list endpoints support filtering by status: `?status=ACTIVE`
- Return consistent error format: `{ error: true, message: "...", field: "..." }`

### Frontend
- Component-per-feature: each module has its own component directory
- Use the SCREENS.md in each module folder as the component spec
- All monetary displays show INR by default with original currency in parentheses where applicable
- All percentage inputs are whole numbers (60, not 0.60)
- All tables support column sorting and at minimum status filtering
- Empty states must show a helpful message, not a blank screen
- Form validations must match FSD §11 exactly — same conditions, same error messages

### Access Control Implementation
- Middleware/decorator checks `RolePermission` table on every API call
- Read the `shared/ACCESS-MATRIX.md` for exact rules
- Scope filtering (ALL, OWN_PORTFOLIO, SELF_ONLY) is applied as a WHERE clause at the database query level, not post-fetch filtering
- Field-level restrictions: set restricted fields to `null` in the API response serializer

### Audit Logging
- Wrap all CREATE/UPDATE/DELETE operations in an audit-aware function
- Capture: entity_type, entity_id, action, field_name, old_value, new_value, changed_by, changed_at
- For UPDATE: log one row per changed field, not one row per save
- old_value and new_value are stored as JSON-serialized strings

---

## How to Build a Module

When I say "build module X" or you're working on a module folder, follow this process:

### Step 1: Read the Module Files
```
modules/{module-name}/
├── REQUIREMENTS.md    → Understand what this module does
├── SCHEMA.md          → Know the exact entity fields
├── API.md             → Know the endpoints to build
├── SCREENS.md         → Know the UI components to build
├── DEPENDENCIES.md    → Verify prerequisites exist
└── JOBS.md            → Background jobs to implement (if present)
```

Also read:
- `shared/ENTITIES.md` for any referenced entities from other modules
- `shared/ACCESS-MATRIX.md` for access control on this module's data
- `shared/BUSINESS-RULES.md` if this module involves calculations

### Step 2: Build Backend
1. Database migration for any new tables/columns in SCHEMA.md
2. Entity/model definitions matching SCHEMA.md exactly
3. API endpoints from API.md with access control middleware
4. Business logic layer for calculations (reference BUSINESS-RULES.md)
5. Validation middleware matching FSD §11 rules
6. Background jobs from JOBS.md (if present) — scheduled and event-triggered
7. Audit logging for all write operations

### Step 3: Build Frontend
1. Components from SCREENS.md
2. API integration layer
3. Form validations (client-side, matching server-side rules)
4. Empty states, loading states, error states
5. Responsive layout

### Step 4: Verify
1. All REQUIREMENTS.md acceptance criteria met
2. All validations from FSD §11 implemented
3. Access control tested for each role
4. Audit log entries generated for all writes

---

## Module Dependencies — What NOT to Do

- Never import from a module that hasn't been built yet in the phase order
- Never create an entity that belongs to another module — reference it via the shared/ definitions
- Never hardcode role names — always query the Role table
- Never skip audit logging — even if it seems minor
- Never calculate margins or revenue differently than `shared/BUSINESS-RULES.md` — even if you think there's a better formula
- Never expose sensitive fields to unauthorized roles — even in development/testing

---

## Seed Data

On first deployment, the system needs:

### Roles (7 default)
CEO, CTO, DM (Delivery Manager), PM (Project Manager), FINANCE, HR, ENGINEER

### RolePermissions (105 rows)
One row per role × data_type combination. See `shared/ACCESS-MATRIX.md` for the full matrix. Seed script must generate all 105 rows.

### SystemConfig (7 default keys)
| Key | Default |
|---|---|
| alert.contract_expiry_days | 30 |
| alert.contract_expiry_urgent_days | 7 |
| alert.bench_threshold_days | 7 |
| alert.utilization_threshold_pct | 70 |
| system.working_days_per_month | 22 |
| system.working_hours_per_day | 8 |
| system.default_currency | INR |

### Admin User
Create one admin user with CEO role for initial access.

---

## Scheduled Jobs

| Job | Schedule | Module | Description |
|---|---|---|---|
| Auto-Release | Daily midnight IST | 05-allocation-tracking | Release assignments where end_date ≤ today. See FSD §8. |
| Contract Expiry Alert | Daily | 12-alerts | Check projects with contract_end_date approaching. |
| Bench Duration Alert | Daily | 12-alerts | Check resources on bench > threshold days. |
| Milestone Overdue Alert | Daily | 12-alerts | Check milestones past planned_delivery_date. |
| Utilization Alert | Weekly (Monday) | 12-alerts | Check company utilization < threshold. |
| Recurring Cost Processing | Monthly (1st) | 06-non-human-costs | Auto-create monthly entries for active recurring costs. |

---

## Testing Expectations

- Every API endpoint has at least one happy-path test and one access-control test
- Every validation rule from FSD §11 has a test that triggers it
- Every state machine transition has a test for allowed and disallowed transitions
- Every calculation from BUSINESS-RULES.md has a test with known input/output values
- The auto-release job has tests for: normal release, extension before release, already released

---

## When In Doubt

1. Check `fsd/FSD.md` — it's the authoritative technical spec
2. Check the module's REQUIREMENTS.md — it has acceptance criteria
3. Check `shared/BUSINESS-RULES.md` — it has exact formulas
4. If still unclear, ask — don't assume
