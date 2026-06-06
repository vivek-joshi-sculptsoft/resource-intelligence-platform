# Module 06: Non-Human Costs — JIRA Tickets

---

## Story: Create NonHumanCost database table and migration
**Type:** Task
**Phase:** 2
**Module:** 06-non-human-costs
**Priority:** P0
**Estimate:** S (1-2d)
**Depends On:** 03-project-management (Project table), 01-auth-and-roles (User table)
**Labels:** backend, database

### Description
Create the NonHumanCost table with id (UUID PK), project_id (FK to Project), description (STRING 500), category (ENUM: AI_TOOLS, CLOUD_INFRA, DEVICES, THIRD_PARTY_LICENSE, OTHER), amount (DECIMAL 15,2), currency (STRING 3 DEFAULT INR), exchange_rate (DECIMAL 10,4 DEFAULT 1.0), amount_inr (DECIMAL 15,2 computed as amount * exchange_rate), cost_date (DATE), is_recurring (BOOLEAN DEFAULT false), recurring_end_date (DATE NULLABLE), created_by (FK to User), and created_at (TIMESTAMP AUTO). Add indexes on project_id, category, is_recurring, and cost_date.

### Acceptance Criteria
- [ ] NonHumanCost table created with all fields per SCHEMA.md
- [ ] ENUM for category: AI_TOOLS, CLOUD_INFRA, DEVICES, THIRD_PARTY_LICENSE, OTHER
- [ ] amount_inr computed/stored as amount * exchange_rate
- [ ] Foreign keys to Project (project_id) and User (created_by)
- [ ] Indexes on project_id, category, is_recurring, cost_date
- [ ] UUID v4 for primary key
- [ ] Migration is reversible

---

## Story: Implement Non-Human Cost CRUD API endpoints
**Type:** Feature
**Phase:** 2
**Module:** 06-non-human-costs
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** NonHumanCost database table, access control middleware
**Labels:** backend

### Description
Build POST /api/projects/:projectId/costs (create), GET /api/projects/:projectId/costs (paginated list with category and recurring filters), GET /api/projects/:projectId/costs/:id (single), PUT /api/projects/:projectId/costs/:id (update), and DELETE /api/projects/:projectId/costs/:id (delete). Create requires description, category, amount (positive), currency, cost_date, and optionally is_recurring with recurring_end_date. Server computes amount_inr = amount * exchange_rate. On update, amount_inr is recomputed. All 5 FSD section 11 NonHumanCost validations are enforced. created_by is set to the authenticated user.

### Acceptance Criteria
- [ ] POST /api/projects/:projectId/costs creates cost entry with all required fields
- [ ] amount_inr computed server-side: amount * exchange_rate
- [ ] GET /api/projects/:projectId/costs returns paginated list with ?category and ?is_recurring filters
- [ ] GET /api/projects/:projectId/costs/:id returns full cost object
- [ ] PUT /api/projects/:projectId/costs/:id updates fields; amount_inr recomputed
- [ ] DELETE /api/projects/:projectId/costs/:id deletes the cost entry
- [ ] Validation: "Cost amount must be positive" when amount <= 0
- [ ] Validation: "Exchange rate must be positive" when exchange_rate <= 0
- [ ] Validation: INR currency auto-sets exchange_rate=1.0
- [ ] Validation: "Recurring costs must have an end date" when is_recurring=true without recurring_end_date
- [ ] Validation: "Recurring end date must be after cost date" when recurring_end_date <= cost_date
- [ ] created_by set to authenticated user ID
- [ ] All changes audit logged

---

## Story: Implement access control for Non-Human Cost endpoints
**Type:** Feature
**Phase:** 2
**Module:** 06-non-human-costs
**Priority:** P1
**Estimate:** S (1-2d)
**Depends On:** Non-Human Cost CRUD API
**Labels:** backend

### Description
Apply role-based access control per shared/ACCESS-MATRIX.md for the non_human_costs data type. CEO/CTO have EDIT ALL. DM has EDIT OWN_PORTFOLIO. PM has EDIT OWN_PORTFOLIO. Finance has EDIT ALL. HR has NONE (403). Engineer has NONE (403). Scope filtering for DM/PM applied as WHERE clause at DB level.

### Acceptance Criteria
- [ ] CEO, CTO: EDIT ALL — full CRUD on all project costs
- [ ] DM: EDIT OWN_PORTFOLIO — CRUD on own project costs (dm_id = self)
- [ ] PM: EDIT OWN_PORTFOLIO — CRUD on own project costs (pm_id = self)
- [ ] Finance: EDIT ALL — full CRUD on all project costs
- [ ] HR: NONE — returns 403
- [ ] Engineer: NONE — returns 403
- [ ] Scope filtering applied as WHERE clause at DB level

---

## Story: Implement cost summary aggregation endpoint
**Type:** Feature
**Phase:** 2
**Module:** 06-non-human-costs
**Priority:** P1
**Estimate:** S (1-2d)
**Depends On:** Non-Human Cost CRUD API
**Labels:** backend

### Description
Build GET /api/projects/:projectId/costs/summary returning aggregated cost metrics for a project: total_inr (sum of all amount_inr), breakdown by category (AI_TOOLS, CLOUD_INFRA, DEVICES, THIRD_PARTY_LICENSE, OTHER), one_time_inr (sum where is_recurring=false), and recurring_monthly_inr (sum of amount_inr for active recurring costs). This data feeds into Module 08 (Financial Engine) margin calculations.

### Acceptance Criteria
- [ ] total_inr = sum of all amount_inr for the project
- [ ] by_category = { AI_TOOLS: decimal, CLOUD_INFRA: decimal, DEVICES: decimal, THIRD_PARTY_LICENSE: decimal, OTHER: decimal }
- [ ] one_time_inr = sum of amount_inr where is_recurring=false
- [ ] recurring_monthly_inr = sum of amount_inr for active recurring costs
- [ ] Same access control as list endpoint
- [ ] Returns zeroes (not null) when no costs exist

---

## Story: Implement recurring cost monthly scheduled job
**Type:** Feature
**Phase:** 2
**Module:** 06-non-human-costs
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** Non-Human Cost CRUD API
**Labels:** backend, infrastructure

### Description
Build the monthly recurring cost processing job (POST /api/jobs/recurring-costs, triggered by scheduler on the 1st of each month). The job finds all NonHumanCost entries where is_recurring=true and cost_date <= today <= recurring_end_date, then creates a new cost entry for each with the same fields and cost_date set to the 1st of the current month. Recurring stops after recurring_end_date. The job returns the count of generated entries.

### Acceptance Criteria
- [ ] Job processes all recurring costs where cost_date <= today <= recurring_end_date
- [ ] Creates new cost entry with same fields: description, category, amount, currency, exchange_rate, project_id
- [ ] New entry has cost_date = 1st of current month
- [ ] New entry has is_recurring=false (it is a generated instance, not the template)
- [ ] Recurring stops after recurring_end_date (no new entries generated)
- [ ] Job is idempotent — does not duplicate entries if run multiple times in same month
- [ ] Returns { generated_count: int }
- [ ] Endpoint secured: internal/admin access only
- [ ] Each generated entry audit logged

---

## Story: Build Non-Human Costs tab UI within Project Detail
**Type:** Feature
**Phase:** 2
**Module:** 06-non-human-costs
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** Non-Human Cost CRUD API, 03-project-management (Project Detail screen)
**Labels:** frontend

### Description
Create the Non-Human Costs tab within /projects/:id showing a table of all cost entries for the project. Columns: date, description, category (pill badge), amount with currency (e.g. "$200 USD"), exchange rate (hidden if INR), amount INR ("Rs.16,700"), recurring status ("Monthly until Dec 2026" or "One-time"), added by. Include "Add Cost" button, category filter dropdown, recurring filter toggle, and a summary row showing total INR, one-time total, recurring monthly total. Click row opens edit form. Delete button with confirmation dialog.

### Acceptance Criteria
- [ ] Cost table with all specified columns
- [ ] "Add Cost" button opens create form
- [ ] Category filter dropdown: All / AI Tools / Cloud Infra / Devices / License / Other
- [ ] Recurring filter toggle
- [ ] Summary row: total INR, one-time total, recurring monthly total
- [ ] Click row opens edit form
- [ ] Delete button with confirmation dialog
- [ ] Exchange rate column hidden when currency is INR
- [ ] Empty state: "No costs recorded yet. Add your first cost entry."
- [ ] HR and Engineer cannot see this tab

---

## Story: Build Non-Human Cost Create / Edit form with live INR preview
**Type:** Feature
**Phase:** 2
**Module:** 06-non-human-costs
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** Non-Human Costs tab UI
**Labels:** frontend

### Description
Create the cost create/edit form as a modal within the project detail page. Fields: description (required), category dropdown (required), amount input (required, positive), currency dropdown (default INR), exchange rate input (auto-set to 1.0 and disabled when INR, required and positive for non-INR), INR preview field (live-computed amount * exchange_rate, read-only, updates as user types), cost date picker (required), recurring toggle, recurring end date picker (shown and required only when recurring is on). All 5 validation messages displayed inline.

### Acceptance Criteria
- [ ] Description input (required)
- [ ] Category dropdown (required): AI Tools, Cloud Infra, Devices, Third-Party License, Other
- [ ] Amount input (required, positive number)
- [ ] Currency dropdown (default INR)
- [ ] Exchange rate input: auto-set to 1.0 and disabled for INR; required positive for others
- [ ] INR preview updates live as user types amount or exchange rate
- [ ] Cost date picker (required)
- [ ] Recurring toggle; recurring end date picker shown/required when on
- [ ] All 4 validation messages displayed inline
- [ ] Save calls POST or PUT; updates cost list
- [ ] Cancel closes modal

---

## Story: Implement audit logging for all Non-Human Cost write operations
**Type:** Task
**Phase:** 2
**Module:** 06-non-human-costs
**Priority:** P1
**Estimate:** S (1-2d)
**Depends On:** Non-Human Cost CRUD API, recurring cost job
**Labels:** backend

### Description
Wrap all NonHumanCost CREATE, UPDATE, and DELETE operations in audit-aware functions. CREATE: one AuditLog row. UPDATE: one row per changed field. DELETE: one row logging the deletion. Recurring job generated entries are logged as CREATE with changed_by=system. Capture entity_type=NonHumanCost, entity_id, action, field_name, old_value, new_value, changed_by, changed_at.

### Acceptance Criteria
- [ ] CREATE: AuditLog entry with entity_type=NonHumanCost, action=CREATE
- [ ] UPDATE: one AuditLog row per changed field with old_value and new_value
- [ ] DELETE: AuditLog entry with action=DELETE
- [ ] Recurring job entries: AuditLog with action=CREATE, changed_by=system
- [ ] changed_by and changed_at captured for all operations

---

## Story: Write tests for Non-Human Cost validations, recurring job, and access control
**Type:** Task
**Phase:** 2
**Module:** 06-non-human-costs
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** All Non-Human Cost API endpoints, recurring cost job
**Labels:** backend

### Description
Write tests covering: CRUD happy paths, all 5 validation rules (amount positive, exchange_rate positive, INR auto-rate, recurring needs end date, end after start), amount_inr computation (amount * exchange_rate), INR auto-rate enforcement, recurring cost job (generates correct entries, stops after recurring_end_date, idempotent), cost summary aggregation correctness, access control per role (CEO/CTO/DM/PM/Finance EDIT, HR/Engineer 403), and audit log generation.

### Acceptance Criteria
- [ ] CRUD happy paths pass
- [ ] All 5 validation rules tested with expected error messages
- [ ] amount_inr correctly computed as amount * exchange_rate
- [ ] INR currency: exchange_rate auto-set to 1.0
- [ ] Recurring job: generates entries for active recurring costs
- [ ] Recurring job: stops generating after recurring_end_date
- [ ] Recurring job: idempotent within same month
- [ ] Cost summary: total_inr, by_category, one_time_inr, recurring_monthly_inr all correct
- [ ] Access control: CEO/CTO/Finance full CRUD; DM/PM own portfolio CRUD; HR/Engineer 403
- [ ] Audit log entries verified
