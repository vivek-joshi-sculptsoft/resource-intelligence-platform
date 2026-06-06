# Ticket Patterns — Story Breakdown by Module Type

Use these patterns to break each module into JIRA-ready stories. Adapt the pattern based on the module's type and complexity.

---

## Story Format

```markdown
## Story: {Title}
**Type:** Feature / Task / Enhancement
**Phase:** 1 / 2 / 3
**Module:** {module-folder-name}
**Priority:** P0 (Critical) / P1 (High) / P2 (Medium) / P3 (Low)
**Estimate:** S (1-2 days) / M (3-5 days) / L (5-10 days) / XL (10+ days)
**Depends On:** {list of story titles this blocks on}
**Labels:** backend, frontend, database, infrastructure

### Description
{2-3 sentences: what needs to be built and why.}

### Acceptance Criteria
- [ ] {Specific, testable criterion}
- [ ] {Another criterion}

### Technical Notes
{Implementation hints, relevant FSD section references, gotchas.}
```

---

## Pattern: CRUD Entity Module
*For modules that own entities with standard create/read/update/delete operations.*
*Examples: client-management, resource-management, project-management*

| # | Story | Estimate | Labels | Notes |
|---|---|---|---|---|
| 1 | DB schema and migration for {Entity} | S | database | Create table with all Phase N fields, indexes, constraints |
| 2 | {Entity} API — CRUD endpoints | M | backend | GET list (paginated, filtered), GET by id, POST, PUT, DELETE (soft) |
| 3 | {Entity} API — access control | S | backend | Middleware for role checking, scope filtering, field-level nulling |
| 4 | {Entity} list view | M | frontend | Table with sort, filter, pagination, empty state |
| 5 | {Entity} detail view | M | frontend | Full profile/detail page with all data sections |
| 6 | {Entity} create/edit form | M | frontend | Form with all validations matching FSD |
| 7 | {Entity} validations (server-side) | S | backend | All rules from FSD with exact error messages |
| 8 | {Entity} audit logging | S | backend | Log CREATE/UPDATE/DELETE to AuditLog |
| 9 | {Entity} deactivation handling | S | backend | Cascade effects, validation blocks |

---

## Pattern: Workflow/Lifecycle Module
*For modules with state machines and complex business logic.*
*Examples: allocation-tracking, invoicing*

| # | Story | Estimate | Labels | Notes |
|---|---|---|---|---|
| 1 | DB schema for {Entity} | S | database | |
| 2 | {Entity} CRUD API | M | backend | |
| 3 | {Entity} state machine — transitions | M | backend | Implement all allowed transitions with guards |
| 4 | {Entity} state machine — side effects | M | backend | Cascading changes, notifications, related entity updates |
| 5 | {Entity} state machine — backward transitions | S | backend | If allowed, implement with proper guards |
| 6 | Scheduled job: {job name} | M | backend, infrastructure | Daily/weekly job with retry logic |
| 7 | {Entity} management UI | L | frontend | List + detail + status transition buttons |
| 8 | {Entity} validations | S | backend | All FSD rules |
| 9 | {Entity} access control | S | backend | Role-based, scope-based |
| 10 | {Entity} audit logging | S | backend | All state changes logged |

---

## Pattern: Financial Module
*For modules involving money, currencies, and calculations.*
*Examples: financial-engine, non-human-costs, invoicing*

| # | Story | Estimate | Labels | Notes |
|---|---|---|---|---|
| 1 | DB schema additions | S | database | Add cost/rate fields to existing entities or new tables |
| 2 | Calculation engine: {formula name} | M | backend | Implement exact formula from BUSINESS-RULES.md |
| 3 | Multi-currency support | M | backend, frontend | Currency field, exchange rate input, INR conversion, live preview |
| 4 | Financial API endpoints | M | backend | Aggregation queries, margin calculations |
| 5 | Financial dashboard widgets | L | frontend | Revenue, cost, margin charts/numbers |
| 6 | Access control for financial data | S | backend | Field nulling for restricted roles |
| 7 | Financial validations | S | backend | Amount > 0, exchange rate > 0, etc. |

---

## Pattern: Dashboard/Reporting Module
*For modules that read from many entities and display aggregated views.*
*Examples: utilization-dashboards, bench-forecasting*

| # | Story | Estimate | Labels | Notes |
|---|---|---|---|---|
| 1 | Aggregation API: {level} dashboard | M | backend | SQL queries for metrics, role-scoped |
| 2 | Dashboard UI: {level} | L | frontend | Widgets, charts, KPI cards |
| 3 | Filters and drill-down | M | frontend | Time period, project type, DM, client |
| 4 | Dashboard access control | S | backend | Different data per role |
| 5 | Performance optimization | S | backend | Query caching, efficient aggregation |

---

## Pattern: System/Infrastructure Module
*For modules that provide system-wide services.*
*Examples: auth-and-roles, audit-history, alerts*

| # | Story | Estimate | Labels | Notes |
|---|---|---|---|---|
| 1 | DB schema and seed data | M | database | Tables + seed script (roles, permissions, config) |
| 2 | Core service implementation | L | backend | Auth flow, or alert engine, or audit service |
| 3 | Middleware/interceptors | M | backend | Auth middleware, audit interceptor |
| 4 | Admin UI | M | frontend | User management, role config, system settings |
| 5 | Integration testing | M | backend | Test with other modules' endpoints |

---

## Estimation Guidelines

| Size | Days | Criteria |
|---|---|---|
| S | 1-2 | Single entity, <5 API endpoints, simple UI, <3 validations |
| M | 3-5 | Single entity with lifecycle, 5-10 endpoints, moderate UI |
| L | 5-10 | Multiple entities, complex calculations, rich UI with charts |
| XL | 10+ | Cross-cutting feature, many integrations, complex state machines |

---

## Priority Guidelines

| Priority | Criteria |
|---|---|
| P0 - Critical | Blocks other stories. Infrastructure (auth, DB). Core entities. |
| P1 - High | Primary user workflow. CRUD for main entities. Key dashboards. |
| P2 - Medium | Secondary features. Reporting. Configuration UI. |
| P3 - Low | Nice-to-have. Advanced filters. Audit viewer. Historical queries. |

---

## Module-Level Ticket File

Each module's ticket file in `tickets/{module-name}.md` should:
1. List all stories in build order (DB first, then API, then UI)
2. Include a total estimate (sum of individual stories)
3. Note which phase the module belongs to
4. List blockers from other modules
