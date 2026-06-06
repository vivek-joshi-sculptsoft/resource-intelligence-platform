# CLAUDE.md Template

Generate this file customized for the specific project. Replace all `{placeholders}` with project-specific content extracted from the PRD and FSD.

---

```markdown
# CLAUDE.md — Master Instructions for Claude Code

## Project Overview

You are building **{project name}** — {one sentence description from PRD executive summary}. {Second sentence about who uses it and what it replaces.}

**Read these files first before writing any code:**
1. `prd/PRD.md` — What the product does (business perspective)
2. `fsd/FSD.md` — How the system works (technical specifications)
3. `shared/ENTITIES.md` — Master entity definitions (single source of truth)
4. `shared/BUSINESS-RULES.md` — Calculations, formulas, and rules
5. `shared/ACCESS-MATRIX.md` — Role-based access control
6. This file — Build conventions and module structure

---

## Tech Stack

> **Confirm with the team before starting. Update this section once decided.**

| Layer | Choice | Notes |
|---|---|---|
| Frontend | {TBD} | |
| Backend | {TBD} | |
| Database | {TBD} | |
| Auth | {TBD} | |
| Hosting | {TBD} | |

---

## Repo Structure

{Generate the actual tree of all generated folders and files}

---

## Build Phases & Module Order

{For each phase, list modules in build order with dependencies and key entities. Extract from the FSD phase guide.}

### Phase 1 — {Phase Name}
| Order | Module | Depends On | Key Entities |
|---|---|---|---|
{rows}

### Phase 2 — {Phase Name}
{same format}

### Phase 3 — {Phase Name}
{same format}

---

## Coding Conventions

### General
- {Language-agnostic conventions}
- Every function touching business logic must comment the FSD section: `// See FSD §{N}`
- No hardcoded magic numbers — use SystemConfig or env vars
- All monetary calculations use exact formulas from shared/BUSINESS-RULES.md

### Database
- UUID v4 for all primary keys
- All tables have created_at and updated_at timestamps
- Soft delete via is_active BOOLEAN DEFAULT true
- {Audit log table} is append-only — no UPDATE or DELETE
- Use DB-level constraints for ENUMs, FKs, unique constraints
- Index all foreign keys and status fields

### API
- RESTful: GET/POST/PUT/DELETE /api/{entity}
- Every endpoint checks access control via {permission mechanism}
- Sensitive fields return null (not omitted) for unauthorized roles
- Pagination: ?page=1&limit=20
- Consistent error format: { error: true, message: "...", field: "..." }

### Frontend
- Component-per-feature: each module owns its components
- SCREENS.md is the component spec — match it exactly
- All monetary displays in {base currency}
- All percentage inputs as whole numbers
- Form validations match FSD exactly — same conditions, same messages
- Empty states show helpful messages

### Access Control
- Middleware checks {permission table} on every API call
- Scope filtering at DB query level (WHERE clause), not post-fetch
- Field-level: set restricted fields to null in serializer

### Audit Logging
- All CREATE/UPDATE/DELETE wrapped in audit-aware function
- One row per changed field on UPDATE
- Fields: entity_type, entity_id, action, field_name, old_value, new_value, changed_by, changed_at

---

## How to Build a Module

1. Read `modules/{name}/REQUIREMENTS.md` — understand what to build
2. Read `modules/{name}/SCHEMA.md` — know the exact entity fields
3. Read `modules/{name}/API.md` — know the endpoints
4. Read `modules/{name}/SCREENS.md` — know the UI
5. Read `modules/{name}/DEPENDENCIES.md` — verify prerequisites exist
6. Also read shared/ files for cross-cutting concerns

**Build order within a module:**
DB migrations → API endpoints → business logic → UI components → validations → audit logging → tests

---

## Seed Data

{List all seed data requirements: default roles, permissions, config values, admin user}

---

## Scheduled Jobs

| Job | Schedule | Module | Description |
|---|---|---|---|
{rows extracted from FSD}

---

## Testing

- Every API endpoint: happy path + access control test
- Every validation: test that triggers the error
- Every state transition: allowed + disallowed
- Every calculation: known input → expected output
- Scheduled jobs: normal case + failure case + idempotency

---

## When In Doubt

1. Check `fsd/FSD.md` — authoritative technical spec
2. Check module's REQUIREMENTS.md — acceptance criteria
3. Check `shared/BUSINESS-RULES.md` — exact formulas
4. If still unclear, ask — don't assume
```
