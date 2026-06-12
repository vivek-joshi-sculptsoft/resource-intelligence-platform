# Story Patterns — Breakdown by Module Type

Every story includes a **Context (read before starting)** section as the first part of the description. This tells the developer or AI agent exactly which spec files to read. Derive file references using the context derivation rules in `jira-mcp-guide.md`. The context examples below show typical files per story type — adapt to the actual module structure.

---

## Pattern 1: CRUD Entity Module
*Modules that own entities with create/read/update/delete.*

### Story List

**Story 1: {Entity} database schema**
- Type: Task
- Size: XS-S
- Labels: database, must-have
- Priority: P0
- Context: `modules/{mod}/SCHEMA.md`, `shared/ENTITIES.md`
- AC:
  - [ ] Migration creates {entity} table with all Phase N fields
  - [ ] Indexes on all FK fields and status
  - [ ] Unique constraints applied
  - [ ] Seed data script (if applicable)

**Story 2: {Entity} CRUD API**
- Type: Feature
- Size: M
- Labels: backend, must-have
- Priority: P1
- Depends: Story 1
- Context: `modules/{mod}/API.md`, `modules/{mod}/REQUIREMENTS.md`, `CLAUDE.md` → API conventions
- AC:
  - [ ] GET /api/{entity} — paginated list with filters
  - [ ] GET /api/{entity}/:id — single record
  - [ ] POST /api/{entity} — create with all validations
  - [ ] PUT /api/{entity}/:id — update with all validations
  - [ ] DELETE /api/{entity}/:id — soft delete
  - [ ] All endpoints return consistent response format

**Story 3: {Entity} access control**
- Type: Feature
- Size: S
- Labels: backend, must-have
- Priority: P1
- Depends: Story 2, auth module
- Context: `shared/ACCESS-MATRIX.md`, `modules/{mod}/API.md` → auth rules per endpoint
- AC:
  - [ ] Role-based endpoint access enforced
  - [ ] Scope filtering applied (ALL/OWN_PORTFOLIO/SELF_ONLY)
  - [ ] Restricted fields return null for unauthorized roles
  - [ ] 403 returned for unauthorized access attempts

**Story 4: {Entity} validations**
- Type: Feature
- Size: S
- Labels: backend
- Priority: P1
- Depends: Story 2
- Context: `modules/{mod}/REQUIREMENTS.md` → validation rules, `modules/{mod}/API.md` → error responses
- AC:
  - [ ] All validation rules from spec implemented
  - [ ] Exact error messages match spec
  - [ ] Hard blocks prevent save
  - [ ] Soft warnings allow save with warning response
  - [ ] Validations tested with invalid data

**Story 5: {Entity} audit logging**
- Type: Feature
- Size: XS
- Labels: backend
- Priority: P2
- Depends: Story 2, audit module
- Context: `CLAUDE.md` → Audit Logging section
- AC:
  - [ ] CREATE logged with all field values
  - [ ] UPDATE logged per changed field (old + new value)
  - [ ] DELETE logged
  - [ ] changed_by captured from session

**Story 6: {Entity} list view**
- Type: Feature
- Size: M
- Labels: frontend
- Priority: P1
- Depends: Story 2
- Context: `modules/{mod}/SCREENS.md` → list view spec, `modules/{mod}/REQUIREMENTS.md`
- AC:
  - [ ] Table with all specified columns
  - [ ] Sortable columns
  - [ ] Filter controls (status, search)
  - [ ] Pagination
  - [ ] Empty state with helpful message
  - [ ] Row click navigates to detail

**Story 7: {Entity} detail view**
- Type: Feature
- Size: M
- Labels: frontend
- Priority: P1
- Depends: Story 2
- Context: `modules/{mod}/SCREENS.md` → detail view spec, `modules/{mod}/REQUIREMENTS.md`
- AC:
  - [ ] All data sections from SCREENS.md
  - [ ] Related entity tabs/sections
  - [ ] Edit button (authorized roles)
  - [ ] Deactivate button (authorized roles)

**Story 8: {Entity} create/edit form**
- Type: Feature
- Size: M
- Labels: frontend
- Priority: P1
- Depends: Story 2
- Context: `modules/{mod}/SCREENS.md` → form spec, `modules/{mod}/SCHEMA.md` → field definitions
- AC:
  - [ ] All fields from SCHEMA.md
  - [ ] Client-side validations matching server-side
  - [ ] Dropdowns for FK fields (load options from API)
  - [ ] Success/error feedback
  - [ ] Form resets on success

**Story 9: {Entity} deactivation handling**
- Type: Feature
- Size: S
- Labels: backend, frontend
- Priority: P2
- Depends: Story 2
- Context: `modules/{mod}/REQUIREMENTS.md` → deactivation rules, `modules/{mod}/SCHEMA.md` → entity relationships
- AC:
  - [ ] Cascade validation (block if active references exist)
  - [ ] Confirmation dialog in UI
  - [ ] Cascading side effects executed
  - [ ] Audit logged

---

## Pattern 2: Workflow/Lifecycle Module
*Modules with state machines and complex business logic.*

Includes all Pattern 1 stories PLUS:

**Story: {Entity} state transitions**
- Size: M-L
- Labels: backend
- Priority: P1
- Context: `modules/{mod}/REQUIREMENTS.md` → state machine / lifecycle rules, `modules/{mod}/SCHEMA.md` → status field and allowed values
- AC:
  - [ ] All valid transitions implemented
  - [ ] Invalid transitions return 400 with message
  - [ ] Side effects fire on each transition
  - [ ] Backward transitions (if allowed) implemented with guards
  - [ ] Terminal states prevent further transitions

**Story: {Entity} transition UI**
- Size: M
- Labels: frontend
- Priority: P1
- Context: `modules/{mod}/SCREENS.md` → status transition UI, `modules/{mod}/REQUIREMENTS.md` → transition rules
- AC:
  - [ ] Status badge shows current state
  - [ ] Action buttons for valid transitions only
  - [ ] Confirmation dialog for destructive transitions
  - [ ] UI updates immediately after transition

**Story: Scheduled job — {job name}**
- Size: M
- Labels: backend, infrastructure
- Priority: P1
- Context: `modules/{mod}/JOBS.md` (if exists), `modules/{mod}/REQUIREMENTS.md` → job spec, `CLAUDE.md` → job/worker conventions
- AC:
  - [ ] Job runs on configured schedule
  - [ ] Processes correct set of records
  - [ ] Side effects fire (alerts, status changes)
  - [ ] Idempotent (safe to re-run)
  - [ ] Failures logged, don't block other records
  - [ ] Job execution logged for monitoring

---

## Pattern 3: Financial Module
*Modules with money, currencies, calculations.*

**Story: {Calculation} implementation**
- Size: M-L
- Labels: backend
- Priority: P1
- Context: `shared/BUSINESS-RULES.md` → formula definition, `modules/{mod}/REQUIREMENTS.md` → calculation requirements
- AC:
  - [ ] Formula matches BUSINESS-RULES.md exactly
  - [ ] Handles null inputs gracefully
  - [ ] Handles zero denominators
  - [ ] Rounding applied consistently
  - [ ] Result matches test vectors (known input → expected output)

**Story: Multi-currency support for {Entity}**
- Size: M
- Labels: backend, frontend
- Priority: P1
- Context: `modules/{mod}/SCHEMA.md` → currency fields, `modules/{mod}/SCREENS.md` → currency UI, `shared/BUSINESS-RULES.md` → exchange rate rules
- AC:
  - [ ] Currency selector (ISO 4217 codes)
  - [ ] Exchange rate input (manual, 4 decimal places)
  - [ ] Auto-set rate = 1.0 for base currency, field disabled
  - [ ] Equivalent in base currency auto-calculated
  - [ ] UI shows original amount + rate + base currency side by side
  - [ ] Validation: amount > 0, rate > 0

**Story: Financial dashboard widgets**
- Size: L
- Labels: frontend, backend
- Priority: P2
- Context: `modules/{mod}/SCREENS.md` → dashboard widgets, `shared/BUSINESS-RULES.md` → aggregation formulas, `shared/ACCESS-MATRIX.md` → financial data visibility
- AC:
  - [ ] Revenue widget (projected vs actual)
  - [ ] Cost widget (resource + non-human)
  - [ ] Margin widget (projected vs actual, percentage)
  - [ ] Data restricted per access matrix
  - [ ] Aggregation at correct level (project/client/company)

---

## Pattern 4: Dashboard/Reporting Module
*Read-only modules that aggregate data.*

**Story: {Level} dashboard — data API**
- Size: M
- Labels: backend
- Priority: P2
- Context: `modules/{mod}/REQUIREMENTS.md` → metrics definitions, `modules/{mod}/API.md`, `shared/ACCESS-MATRIX.md` → role scoping
- AC:
  - [ ] Aggregation queries optimized
  - [ ] Role-scoped data (users see only what their role permits)
  - [ ] All metrics from SCREENS.md included
  - [ ] Response time < 2s for typical dataset

**Story: {Level} dashboard — UI**
- Size: L
- Labels: frontend
- Priority: P2
- Context: `modules/{mod}/SCREENS.md` → dashboard layout and widgets, `modules/{mod}/REQUIREMENTS.md`
- AC:
  - [ ] All widgets from SCREENS.md
  - [ ] KPI cards for key numbers
  - [ ] Drill-down links to detail views
  - [ ] Responsive layout
  - [ ] Loading states for each widget

**Story: Dashboard filters**
- Size: S
- Labels: frontend
- Priority: P3
- Context: `modules/{mod}/SCREENS.md` → filter specs
- AC:
  - [ ] Filter by time period
  - [ ] Filter by project type / status
  - [ ] Filters persist in URL params

---

## Pattern 5: System/Infrastructure Module
*Auth, audit, alerts, config.*

**Story: Auth — login flow**
- Size: M
- Labels: backend, frontend, infrastructure
- Priority: P0
- Context: `modules/{mod}/REQUIREMENTS.md` → auth requirements, `modules/{mod}/API.md` → auth endpoints, `CLAUDE.md` → auth conventions
- AC:
  - [ ] Login with email/password
  - [ ] Session/token management
  - [ ] Current user endpoint (role, permissions)
  - [ ] Logout
  - [ ] Protected route middleware

**Story: Auth — access control middleware**
- Size: M
- Labels: backend
- Priority: P0
- Context: `shared/ACCESS-MATRIX.md`, `modules/{mod}/REQUIREMENTS.md` → access control rules
- AC:
  - [ ] Reads role permissions for current user's role
  - [ ] Checks access level per data type
  - [ ] Applies scope filter per role
  - [ ] Nulls restricted fields in response
  - [ ] Returns 403 for unauthorized access

**Story: Seed data script**
- Size: S
- Labels: database, infrastructure
- Priority: P0
- Context: `shared/ACCESS-MATRIX.md` → full role-permission matrix, `modules/{mod}/SCHEMA.md`, `CLAUDE.md` → seed data section
- AC:
  - [ ] Creates all default roles
  - [ ] Creates all role-permission entries (full matrix)
  - [ ] Creates system config defaults
  - [ ] Creates admin user
  - [ ] Idempotent (safe to re-run)

**Story: Alert engine — scheduled jobs**
- Size: L
- Labels: backend, infrastructure
- Priority: P2
- Context: `modules/{mod}/JOBS.md` (if exists), `modules/{mod}/REQUIREMENTS.md` → alert rules and thresholds
- AC:
  - [ ] Each alert type runs on its schedule
  - [ ] Reads thresholds from system config
  - [ ] Creates alert records (one per recipient)
  - [ ] Doesn't duplicate alerts for same event
  - [ ] Job failures don't block other alert types

**Story: Alert UI — notification panel**
- Size: M
- Labels: frontend
- Priority: P2
- Context: `modules/{mod}/SCREENS.md` → notification panel spec
- AC:
  - [ ] Bell icon with unread count
  - [ ] Dropdown panel with recent alerts
  - [ ] Mark as read
  - [ ] Dismiss
  - [ ] Click navigates to related entity
  - [ ] Filter by type
