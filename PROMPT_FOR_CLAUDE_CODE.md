Read CLAUDE.md, prd/PRD.md, and fsd/FSD.md thoroughly. Then populate all shared/ and modules/ folders by extracting and organizing content from these source documents. Do not invent new requirements — only extract, reorganize, and structure what already exists in the PRD and FSD.

## Task 1: Populate shared/ folder

Create these 4 files:

### shared/ENTITIES.md
Extract FSD Section 2 (all 14 entity definitions) as-is. This is the single source of truth for all field types, constraints, and relationships. Include the Entity Relationships table from FSD Section 3. Every module references this file — do not duplicate entity definitions in module SCHEMA.md files, instead reference this file and only list the fields relevant to that module.

### shared/BUSINESS-RULES.md
Extract FSD Section 7 (all calculations). Include every formula: utilization rates (§7.1), project cost (§7.2), projected revenue (§7.3), actual revenue (§7.4), margin (§7.5), bench cost (§7.6), exchange rate conversion (§7.7). Also include the auto-release logic from FSD Section 8 and the designation resolution fallback rule from FSD Section 11.

### shared/ACCESS-MATRIX.md
Extract FSD Section 10 (access control rules). Include: scope rules table, field-level restrictions table, and the full RolePermission seed data (all 7 roles × 15 data types = 105 rows). Generate the complete seed data table — not just examples. Derive the access level and scope for each combination from the PRD Section 6 access matrix.

### shared/GLOSSARY.md
Extract PRD Section 10 (glossary) and FSD Section 1 (notation guide). Combine into one reference.

---

## Task 2: Populate module folders

For each of the 13 modules below, create 4 files: REQUIREMENTS.md, SCHEMA.md, API.md, SCREENS.md.

Follow this structure for every module:

### REQUIREMENTS.md structure:
```markdown
# Module Name

## Overview
One paragraph describing what this module does and who uses it.

## Phase
Which build phase this belongs to (1, 2, or 3).

## Dependencies
Which modules must be built before this one.

## Features
List each feature with acceptance criteria formatted as:

### Feature: [Name]
**Description:** What it does
**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Validations
List all validation rules from FSD §11 that apply to this module.
Reference the exact rule, condition, and error message.

## Business Rules
Reference specific formulas/rules from shared/BUSINESS-RULES.md that this module implements.
```

### SCHEMA.md structure:
```markdown
# Module Name — Schema

## Entities Owned by This Module
List entities this module creates. Include full field table.
Note which fields are Phase 1 vs Phase 2 (if applicable).

## Entities Referenced from Other Modules
List entities this module reads but doesn't own.
Only list the fields this module actually uses.
Reference shared/ENTITIES.md for full definitions.
```

### API.md structure:
```markdown
# Module Name — API Endpoints

## Endpoints

### [METHOD] /api/[resource]
**Description:** What it does
**Auth:** Which roles can access (reference shared/ACCESS-MATRIX.md)
**Scope:** ALL / OWN_PORTFOLIO / SELF_ONLY
**Request Body:** (for POST/PUT)
**Response:** Key fields returned
**Validations:** Which rules apply
**Notes:** Special behavior, side effects
```

### SCREENS.md structure:
```markdown
# Module Name — Screen Specifications

## Screen: [Name]
**Route:** /path/to/screen
**Audience:** Which roles see this screen
**Layout:** Description of the screen layout

### Components
- Component 1: what it shows, what actions are available
- Component 2: ...

### Data Displayed
Table of fields shown, where they come from, any formatting rules.

### Actions
What buttons/links exist, what they do, any confirmation dialogs.

### Empty State
What shows when there's no data.

### Access Restrictions
What's hidden for restricted roles (reference shared/ACCESS-MATRIX.md).
```

---

## Module Specifications

### Module 01: auth-and-roles
- **Source:** FSD §2.1 (Role), §2.2 (RolePermission), §2.3 (User), §10 (Access Control)
- **Entities owned:** Role, RolePermission, User
- **Features:** Login/logout, session management, role assignment, seed data (7 roles + 105 permissions + admin user), access control middleware
- **Screens:** Login page, User management (admin), Role management (admin)
- **API:** CRUD for users, roles; login/logout; current user profile; middleware for access checking
- **Phase:** 1

### Module 02: client-management
- **Source:** PRD §4.1, FSD §2.4 (Client)
- **Entities owned:** Client
- **Features:** Client CRUD, client list with search/filter, client detail view, client dashboard (resource count, project count — financial metrics added in Phase 2), deactivation with active-project check
- **Screens:** Client list, Client detail, Client create/edit form
- **API:** CRUD for clients, client dashboard aggregation endpoint
- **Phase:** 1

### Module 03: project-management
- **Source:** PRD §4.2, FSD §2.6 (Project), §6.4 (Project Status)
- **Entities owned:** Project
- **Features:** Project CRUD with type selection (FP/T&M/Onboarding), billing currency setting, DM/PM assignment, worklog toggle, project status lifecycle (ACTIVE/ON_HOLD/COMPLETED/CANCELLED), cascading effects on completion (auto-release assignments), project list with filters (by client, type, status, DM)
- **Screens:** Project list, Project detail (header + tabs for each sub-section), Project create/edit form
- **API:** CRUD for projects, status transitions, project list with filters
- **Phase:** 1 (base), Phase 2 adds contract_value and milestone/invoice tabs

### Module 04: resource-management
- **Source:** PRD §4.3, FSD §2.5 (Resource), ResourceTag
- **Entities owned:** Resource, ResourceTag
- **Features:** Resource CRUD with designation and expertise, tag management (add/remove flexible tags), resource profile view (assignments, availability, history), deactivation cascading (releases all assignments), resource list with search/filter by designation, expertise, tags, availability
- **Screens:** Resource list, Resource profile/detail, Resource create/edit form, Tag management UI
- **API:** CRUD for resources, tag add/remove, resource search with filters
- **Phase:** 1 (without loaded_cost_monthly), Phase 2 adds cost field

### Module 05: allocation-tracking
- **Source:** PRD §4.4, FSD §2.7 (Assignment), §6.1 (Assignment Lifecycle), §8 (Auto-Release)
- **Entities owned:** Assignment
- **Features:** Create/edit assignment with allocation_pct, billability_pct, shadow flag, project_designation, project_expertise, start_date, end_date. Recurring model (no monthly re-entry). Manual release. Auto-release daily job. Over-allocation warning (soft, not blocking). Designation resolution (project-level fallback to resource-level). All 7 assignment validations from FSD §11. Change logging to AuditLog.
- **Screens:** Assignment list within Project Detail view, Assignment create/edit form (with designation override fields), Resource assignments panel on Resource profile
- **API:** CRUD for assignments, release endpoint, auto-release job trigger
- **Phase:** 1 (without billing_rate), Phase 2 adds billing_rate

### Module 06: non-human-costs
- **Source:** PRD §4.5, FSD §2.10 (NonHumanCost)
- **Entities owned:** NonHumanCost
- **Features:** Add/edit/delete cost entries against a project with description, category, amount, currency, exchange rate, INR conversion. Recurring costs with end date. Category filtering (AI_TOOLS, CLOUD_INFRA, DEVICES, THIRD_PARTY_LICENSE, OTHER). Auto-set exchange rate to 1.0 for INR. All NonHumanCost validations from FSD §11.
- **Screens:** Cost list tab within Project Detail view, Cost create/edit form with currency selector and live INR preview
- **API:** CRUD for non-human costs, project cost summary endpoint
- **Phase:** 2

### Module 07: utilization-dashboards
- **Source:** PRD §4.6, FSD §9 (View Specifications)
- **Entities owned:** None (reads from Assignment, Resource, Project, Invoice, NonHumanCost)
- **Features:** Company-wide dashboard (utilization %, bench count, shadow allocation, revenue summary, active projects, upcoming releases, overdue milestones). DM-level dashboard (portfolio aggregate). Client-level dashboard (resources, billing, margin). Project-level dashboard (resource list, cost vs revenue). Individual resource dashboard (allocation breakdown, history). All calculations from shared/BUSINESS-RULES.md.
- **Screens:** Company dashboard, DM dashboard, Client dashboard (within client detail), Project financials (within project detail), Resource utilization (within resource profile)
- **API:** Dashboard aggregation endpoints per level with role-based data filtering
- **Phase:** 1 (utilization metrics only), Phase 2 adds financial widgets (revenue, cost, margin)

### Module 08: financial-engine
- **Source:** PRD §4.7, FSD §7 (Calculations), §2.5 (loaded_cost_monthly), §2.7 (billing_rate)
- **Entities owned:** None (adds fields to Resource and Assignment)
- **Features:** Resource loaded cost entry (CTC + overhead). Billing rate per assignment. Resource cost calculation per project. Projected revenue calculation. Actual revenue from invoices. Projected and actual margin. Client-level and company-level financial aggregation. Bench cost calculation.
- **Screens:** Financial data shown in existing dashboards (module 07 update). Cost entry in Resource profile (restricted to CEO/CTO/Finance).
- **API:** Financial calculation endpoints, margin summaries
- **Phase:** 2

### Module 09: invoicing
- **Source:** PRD §4.7 (Invoicing Visibility), FSD §2.8 (Milestone), §2.9 (Invoice), §6.2 (Milestone Lifecycle), §6.3 (Invoice Lifecycle)
- **Entities owned:** Milestone, Invoice
- **Features:** Milestone CRUD for FP projects (name, amount, planned date, status, sort order). Milestone status lifecycle with delivery delay detection and backward transitions. Invoice creation with amount in billing currency, manual exchange rate, auto-computed INR. Invoice status lifecycle. Link invoice to milestone for FP. Billing period for T&M/Onboarding invoices. Outstanding receivables tracking. All invoice validations from FSD §11.
- **Screens:** Milestone tab in FP project detail, Invoice tab in all project types, Invoice create form with exchange rate input and live INR preview
- **API:** CRUD for milestones, milestone status transitions, CRUD for invoices, invoice status transitions
- **Phase:** 2

### Module 10: bench-forecasting
- **Source:** PRD §4.8, FSD §7.6 (Bench Cost)
- **Entities owned:** None (reads from Assignment, Resource)
- **Features:** Current bench list (resources at 0% allocation, days on bench, daily bench cost). Upcoming availability view (30/60/90 day filters based on assignment end_dates). Partial availability (resources under 100%). Early release tracking. Bench cost aggregation. Visible to ALL users including engineers.
- **Screens:** Resource Availability view (standalone page accessible to all), Bench summary widget in Company Dashboard
- **API:** Bench list endpoint, upcoming releases endpoint, partial availability endpoint
- **Phase:** 1 (availability view without cost), Phase 2 adds bench cost calculations

### Module 11: worklog
- **Source:** PRD §4.9, FSD §2.11 (Worklog)
- **Entities owned:** Worklog
- **Features:** Daily per-project hour logging by employees. Project-level toggle (worklog_enabled). Half-hour increments (0.5-24.0). Optional note. Manager+ viewing of team worklogs. All worklog validations from FSD §11. Backfill allowed for past dates when assignment was active. Decoupled from all financial workflows.
- **Screens:** Worklog entry in "My Assignments" engineer view, Worklog history table, Worklog tab in Project Detail view (for PM+ viewing)
- **API:** CRUD for worklogs (employee creates/edits own only), worklog list by project (PM+), worklog list by resource
- **Phase:** 1

### Module 12: alerts
- **Source:** PRD §4.10, FSD §2.13 (Alert), §2.14 (SystemConfig), §12 (Alert Specifications)
- **Entities owned:** Alert, SystemConfig (full)
- **Features:** Scheduled alert jobs (contract expiry at 30d and 7d, bench duration > threshold, milestone overdue, utilization drop weekly). Event-triggered alerts (over-allocation on assignment save, auto-release from daily job). Alert UI (notification panel, mark read, dismiss, deep-link to entity). SystemConfig admin UI for configurable thresholds. One alert row per recipient per event.
- **Screens:** Notification bell/panel (global component), Alert list page with filters, SystemConfig admin page
- **API:** Alert list (filtered by recipient), mark read/dismiss, SystemConfig CRUD (admin only), scheduled job endpoints
- **Phase:** 3

### Module 13: audit-history
- **Source:** FSD §2.12 (AuditLog), §13 (Audit & History)
- **Entities owned:** AuditLog
- **Features:** Append-only audit logging for all write operations across all entities. Log one row per changed field. Track entity_type, entity_id, action, field_name, old_value, new_value, changed_by, changed_at. Historical point-in-time reconstruction (given a date, reconstruct entity state by replaying log backwards). Audit log viewer (browse by entity, user, date range).
- **Screens:** Audit log viewer page (Phase 3), Change history panel within entity detail views (Phase 3)
- **API:** Audit log query endpoint (filtered by entity, user, date range), point-in-time reconstruction endpoint
- **Phase:** 1 (logging infrastructure only, no UI), Phase 3 (viewer UI + historical queries)

---

## Execution Instructions

1. Read prd/PRD.md and fsd/FSD.md completely first
2. Create all 4 shared/ files
3. Create all 13 module folders with their 4 files each (52 files total)
4. For each module, extract only the relevant content from PRD and FSD — do not copy entire sections verbatim, restructure them into the module-specific format described above
5. Cross-reference: every entity field in a module's SCHEMA.md must match shared/ENTITIES.md exactly
6. Cross-reference: every validation in a module's REQUIREMENTS.md must match FSD §11 exactly
7. Cross-reference: every API endpoint must specify access control referencing shared/ACCESS-MATRIX.md
8. After creating all files, do a self-review: check that no entity is defined in two different module SCHEMA.md files (each entity has exactly one owning module)
9. Commit all files with message: "docs: populate shared references and all 13 module specifications"
