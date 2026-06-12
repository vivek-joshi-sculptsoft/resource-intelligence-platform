# Ticket Patterns — Story Breakdown by Module Type

Use these patterns to break each module into JIRA-ready stories. Adapt the pattern based on the module's type and complexity.

Every story includes a **Context (read before starting)** section as the first part of the description. This lists the spec files a developer or AI agent should read before starting the story. Derive file paths from the module structure based on what the story touches.

---

## Story Format

```markdown
## Story: {Title}
**Type:** Feature / Task / Enhancement
**Phase:** 1 / 2 / 3
**Module:** {module-folder-name}
**Priority:** P0 (Critical) / P1 (High) / P2 (Medium) / P3 (Low) / P4 (Trivial)
**Estimate:** XS (1 pt) / S (2 pts) / M (3 pts) / L (5 pts) / XL (8 pts)
**Depends On:** {list of story titles this blocks on}
**Labels:** backend, frontend, database, infrastructure, testing

### Context (read before starting)
- `{path/to/spec-file}` — {what to look for}
- `{path/to/another-file}` — {relevant section}

### Description
{2-3 sentences: what needs to be built and why.}

### Acceptance Criteria
- [ ] {Specific, testable criterion}
- [ ] {Another criterion}

### Out of Scope
- {What this story does NOT cover — prevents scope creep}
```

### Context Derivation Rules

| Story labels / type | Files to reference |
|---|---|
| `database` (schema/migration) | `modules/{mod}/SCHEMA.md`, `shared/ENTITIES.md` |
| `backend` (API/logic) | `modules/{mod}/API.md`, `modules/{mod}/REQUIREMENTS.md` |
| `backend` (business rules) | `shared/BUSINESS-RULES.md` |
| `frontend` (UI) | `modules/{mod}/SCREENS.md`, `modules/{mod}/REQUIREMENTS.md` |
| access control | `shared/ACCESS-MATRIX.md` |
| audit/logging | `CLAUDE.md` → Audit Logging section |
| testing | All relevant module files + `CLAUDE.md` → Testing section |
| scheduled jobs | `modules/{mod}/JOBS.md` (if exists) |
| any story | `CLAUDE.md` → relevant conventions section |

Keep to 2-5 file references per story.

---

## Pattern: CRUD Entity Module
*For modules that own entities with standard create/read/update/delete operations.*

| # | Story | Estimate | Labels | Context files | Notes |
|---|---|---|---|---|---|
| 1 | DB schema and migration for {Entity} | S (2 pts) | database | SCHEMA.md, shared/ENTITIES.md | Create table with all Phase N fields, indexes, constraints |
| 2 | {Entity} API — CRUD endpoints | M (3 pts) | backend | API.md, REQUIREMENTS.md | GET list (paginated, filtered), GET by id, POST, PUT, DELETE (soft) |
| 3 | {Entity} API — access control | S (2 pts) | backend | shared/ACCESS-MATRIX.md, API.md | Middleware for role checking, scope filtering, field-level nulling |
| 4 | {Entity} list view | M (3 pts) | frontend | SCREENS.md, REQUIREMENTS.md | Table with sort, filter, pagination, empty state |
| 5 | {Entity} detail view | M (3 pts) | frontend | SCREENS.md, REQUIREMENTS.md | Full profile/detail page with all data sections |
| 6 | {Entity} create/edit form | M (3 pts) | frontend | SCREENS.md, SCHEMA.md | Form with all validations matching spec |
| 7 | {Entity} validations (server-side) | S (2 pts) | backend | REQUIREMENTS.md, API.md | All rules from spec with exact error messages |
| 8 | {Entity} audit logging | XS (1 pt) | backend | CLAUDE.md → Audit Logging | Log CREATE/UPDATE/DELETE to audit log |
| 9 | {Entity} deactivation handling | S (2 pts) | backend | REQUIREMENTS.md, SCHEMA.md | Cascade effects, validation blocks |

---

## Pattern: Workflow/Lifecycle Module
*For modules with state machines and complex business logic.*

| # | Story | Estimate | Labels | Context files | Notes |
|---|---|---|---|---|---|
| 1 | DB schema for {Entity} | S (2 pts) | database | SCHEMA.md, shared/ENTITIES.md | |
| 2 | {Entity} CRUD API | M (3 pts) | backend | API.md, REQUIREMENTS.md | |
| 3 | {Entity} state machine — transitions | M (3 pts) | backend | REQUIREMENTS.md → lifecycle rules, SCHEMA.md → status values | Implement all allowed transitions with guards |
| 4 | {Entity} state machine — side effects | M (3 pts) | backend | REQUIREMENTS.md, shared/BUSINESS-RULES.md | Cascading changes, notifications, related entity updates |
| 5 | {Entity} state machine — backward transitions | S (2 pts) | backend | REQUIREMENTS.md → transition rules | If allowed, implement with proper guards |
| 6 | Scheduled job: {job name} | M (3 pts) | backend, infrastructure | JOBS.md (if exists), REQUIREMENTS.md | Daily/weekly job with retry logic |
| 7 | {Entity} management UI | L (5 pts) | frontend | SCREENS.md, REQUIREMENTS.md | List + detail + status transition buttons |
| 8 | {Entity} validations | S (2 pts) | backend | REQUIREMENTS.md, API.md | All spec rules |
| 9 | {Entity} access control | S (2 pts) | backend | shared/ACCESS-MATRIX.md, API.md | Role-based, scope-based |
| 10 | {Entity} audit logging | XS (1 pt) | backend | CLAUDE.md → Audit Logging | All state changes logged |

---

## Pattern: Financial Module
*For modules involving money, currencies, and calculations.*

| # | Story | Estimate | Labels | Context files | Notes |
|---|---|---|---|---|---|
| 1 | DB schema additions | S (2 pts) | database | SCHEMA.md, shared/ENTITIES.md | Add cost/rate fields to existing entities or new tables |
| 2 | Calculation engine: {formula name} | M (3 pts) | backend | shared/BUSINESS-RULES.md, REQUIREMENTS.md | Implement exact formula from BUSINESS-RULES.md |
| 3 | Multi-currency support | M (3 pts) | backend, frontend | SCHEMA.md → currency fields, SCREENS.md → currency UI, shared/BUSINESS-RULES.md | Currency field, exchange rate input, base currency conversion |
| 4 | Financial API endpoints | M (3 pts) | backend | API.md, shared/BUSINESS-RULES.md | Aggregation queries, margin calculations |
| 5 | Financial dashboard widgets | L (5 pts) | frontend | SCREENS.md, shared/BUSINESS-RULES.md, shared/ACCESS-MATRIX.md | Revenue, cost, margin charts/numbers |
| 6 | Access control for financial data | S (2 pts) | backend | shared/ACCESS-MATRIX.md | Field nulling for restricted roles |
| 7 | Financial validations | S (2 pts) | backend | REQUIREMENTS.md, API.md | Amount > 0, exchange rate > 0, etc. |

---

## Pattern: Dashboard/Reporting Module
*For modules that read from many entities and display aggregated views.*

| # | Story | Estimate | Labels | Context files | Notes |
|---|---|---|---|---|---|
| 1 | Aggregation API: {level} dashboard | M (3 pts) | backend | REQUIREMENTS.md, API.md, shared/ACCESS-MATRIX.md | SQL queries for metrics, role-scoped |
| 2 | Dashboard UI: {level} | L (5 pts) | frontend | SCREENS.md, REQUIREMENTS.md | Widgets, charts, KPI cards |
| 3 | Filters and drill-down | M (3 pts) | frontend | SCREENS.md → filter specs | Time period, project type, drill-down |
| 4 | Dashboard access control | S (2 pts) | backend | shared/ACCESS-MATRIX.md | Different data per role |
| 5 | Performance optimization | S (2 pts) | backend | API.md | Query caching, efficient aggregation |

---

## Pattern: System/Infrastructure Module
*For modules that provide system-wide services.*

| # | Story | Estimate | Labels | Context files | Notes |
|---|---|---|---|---|---|
| 1 | DB schema and seed data | M (3 pts) | database | SCHEMA.md, shared/ENTITIES.md, shared/ACCESS-MATRIX.md | Tables + seed script (roles, permissions, config) |
| 2 | Core service implementation | L (5 pts) | backend | REQUIREMENTS.md, API.md, CLAUDE.md → conventions | Auth flow, or alert engine, or audit service |
| 3 | Middleware/interceptors | M (3 pts) | backend | REQUIREMENTS.md, shared/ACCESS-MATRIX.md | Auth middleware, audit interceptor |
| 4 | Admin UI | M (3 pts) | frontend | SCREENS.md, REQUIREMENTS.md | User management, role config, system settings |
| 5 | Integration testing | M (3 pts) | testing | All module files, CLAUDE.md → Testing section | Test with other modules' endpoints |

---

## Estimation Guidelines

| Size | Story Points | Days | Criteria |
|---|---|---|---|
| XS | 1 | < 1 day | Config change, seed data, simple fix |
| S | 2 | 1-2 | Single entity, <5 API endpoints, simple UI, <3 validations |
| M | 3 | 2-3 | Single entity with lifecycle, 5-10 endpoints, moderate UI |
| L | 5 | 3-5 | Multiple entities, complex calculations, rich UI with charts |
| XL | 8 | 5-8 | Cross-cutting feature, many integrations, complex state machines |

Cap at XL. If something is bigger than XL, split it.

---

## Priority Guidelines

| Priority | Criteria |
|---|---|
| P0 - Blocker | Blocks other modules. Infrastructure (auth, DB setup). Must be done first. |
| P1 - Critical | Core entity CRUD that other features depend on. Primary user workflows. |
| P2 - Major | Important features, dashboards, calculations. Ship quality suffers without it. |
| P3 - Minor | Secondary features, admin views, advanced filters. Can ship without. |
| P4 - Trivial | Polish, UX improvements, audit viewer. Nice-to-haves. |

---

## Module-Level Ticket File

Each module's ticket file in `tickets/{module-name}.md` should:
1. List all stories in build order (DB first, then API, then UI)
2. Include a total estimate (sum of individual stories)
3. Note which phase the module belongs to
4. List blockers from other modules
