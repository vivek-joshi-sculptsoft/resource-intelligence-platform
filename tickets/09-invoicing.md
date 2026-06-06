# Module 09: Invoicing -- JIRA Tickets

---

## Story: Create Milestone and Invoice database tables
**Type:** Task
**Phase:** 2
**Module:** 09-invoicing
**Priority:** P0
**Estimate:** S (1-2d)
**Depends On:** 03-project-management
**Labels:** backend, database

### Description
Create database migrations for the Milestone and Invoice tables per SCHEMA.md. Milestone is linked to FIXED_PRICE projects only. Invoice supports multi-currency with manual exchange rate and computed `amount_inr`. Add all required indexes and constraints.

### Acceptance Criteria
- [ ] Milestone table created: id (UUID PK), project_id (FK), name, amount (DECIMAL(15,2)), planned_delivery_date, actual_delivery_date (NULLABLE), status (ENUM: PLANNED/DELIVERED/APPROVED/INVOICED/PAID, default PLANNED), sort_order, created_at
- [ ] Invoice table created: id (UUID PK), project_id (FK), milestone_id (FK NULLABLE), invoice_date, billing_period_start (NULLABLE), billing_period_end (NULLABLE), amount (DECIMAL(15,2)), currency (STRING(3)), exchange_rate (DECIMAL(10,4) default 1.0), amount_inr (DECIMAL(15,2)), status (ENUM: DRAFT/SUBMITTED/APPROVED/PAID, default DRAFT), notes (TEXT NULLABLE), created_at
- [ ] DB indexes on Milestone: project_id, status, planned_delivery_date
- [ ] DB indexes on Invoice: project_id, milestone_id, status, invoice_date
- [ ] Foreign key constraints enforced

---

## Story: Build milestone CRUD API for Fixed Price projects
**Type:** Feature
**Phase:** 2
**Module:** 09-invoicing
**Priority:** P0
**Estimate:** M (3-5d)
**Depends On:** 09-invoicing (DB tables), 03-project-management
**Labels:** backend

### Description
Implement CRUD endpoints for milestones: `GET/POST /api/projects/:projectId/milestones` and `PUT /api/projects/:projectId/milestones/:id`. Milestones can only be created on FIXED_PRICE projects. Fields are editable only while in PLANNED status. Sort order supports reordering. All changes must be audit logged.

### Acceptance Criteria
- [ ] GET returns milestones ordered by sort_order for an FP project
- [ ] POST creates milestone with name (required), amount (required, > 0), planned_delivery_date, sort_order
- [ ] POST rejects creation on non-FIXED_PRICE projects
- [ ] PUT allows editing name, amount, planned_delivery_date, sort_order while in PLANNED status
- [ ] PUT rejects edits when status is not PLANNED
- [ ] PM (own portfolio), DM (own portfolio), CEO, CTO can create/edit
- [ ] All creates and updates are audit logged
- [ ] Unit tests for CRUD operations and FP-only validation

---

## Story: Build milestone status lifecycle transitions
**Type:** Feature
**Phase:** 2
**Module:** 09-invoicing
**Priority:** P0
**Estimate:** M (3-5d)
**Depends On:** 09-invoicing (milestone CRUD)
**Labels:** backend

### Description
Implement `PUT /api/projects/:projectId/milestones/:id/status` for milestone lifecycle transitions per FSD Section 6.2. Forward: PLANNED -> DELIVERED -> APPROVED -> INVOICED -> PAID. Backward: DELIVERED -> PLANNED (rejected), APPROVED -> DELIVERED (withdrawn). INVOICED and PAID are terminal. Set `actual_delivery_date` when transitioning to DELIVERED. Flag delivery delay when actual > planned. All transitions must be audit logged.

### Acceptance Criteria
- [ ] PLANNED -> DELIVERED: sets actual_delivery_date; PM/DM can trigger
- [ ] DELIVERED -> APPROVED: PM/DM can trigger
- [ ] APPROVED -> INVOICED: Finance only; creates linked invoice
- [ ] INVOICED -> PAID: Finance only
- [ ] Backward: DELIVERED -> PLANNED (rejected by PM/DM)
- [ ] Backward: APPROVED -> DELIVERED (withdrawn by PM/DM)
- [ ] INVOICED and PAID have no backward transitions; attempts return 400
- [ ] Delivery delay flagged when actual_delivery_date > planned_delivery_date
- [ ] Invalid transitions return 400 with descriptive error
- [ ] All transitions are audit logged
- [ ] Unit tests for every valid transition and every invalid transition attempt

---

## Story: Build invoice CRUD API with multi-currency support
**Type:** Feature
**Phase:** 2
**Module:** 09-invoicing
**Priority:** P0
**Estimate:** L (5-10d)
**Depends On:** 09-invoicing (DB tables, milestone lifecycle)
**Labels:** backend

### Description
Implement CRUD endpoints for invoices: `GET/POST /api/projects/:projectId/invoices`, `PUT /api/projects/:projectId/invoices/:id`. Support multi-currency with manual exchange rate. For FP projects, `milestone_id` is required and the linked milestone must be APPROVED. For T&M/Onboarding, `billing_period_start` and `billing_period_end` are used. `amount_inr` is computed server-side as `amount * exchange_rate`. Enforce all 5 FSD Section 11 invoice validations. Edits allowed only in DRAFT status.

### Acceptance Criteria
- [ ] GET returns invoices for a project with all fields
- [ ] POST creates invoice: invoice_date (required), amount (required, > 0), currency (from project), exchange_rate (auto 1.0 for INR), notes
- [ ] For FP: milestone_id required; linked milestone must be APPROVED status
- [ ] For T&M/Onboarding: billing_period_start and billing_period_end accepted
- [ ] amount_inr computed server-side: amount * exchange_rate
- [ ] PUT allows editing only in DRAFT status
- [ ] Validation: "Invoice amount must be positive" when amount <= 0
- [ ] Validation: "Exchange rate must be positive" when exchange_rate <= 0
- [ ] Validation: INR auto-sets exchange_rate = 1.0
- [ ] Validation: "Fixed price invoices must be linked to a milestone" for FP without milestone_id
- [ ] Validation: "Milestone must be approved before invoicing" for unapproved milestone
- [ ] Finance role has EDIT ALL access; CEO/CTO have VIEW ALL
- [ ] All creates/updates are audit logged
- [ ] Unit tests for all 5 validations and each project type

---

## Story: Build invoice status lifecycle transitions
**Type:** Feature
**Phase:** 2
**Module:** 09-invoicing
**Priority:** P1
**Estimate:** S (1-2d)
**Depends On:** 09-invoicing (invoice CRUD)
**Labels:** backend

### Description
Implement `PUT /api/projects/:projectId/invoices/:id/status` for invoice lifecycle transitions per FSD Section 6.3. Forward only: DRAFT -> SUBMITTED -> APPROVED -> PAID. Finance manages all transitions. All transitions must be audit logged.

### Acceptance Criteria
- [ ] DRAFT -> SUBMITTED: Finance can trigger
- [ ] SUBMITTED -> APPROVED: Finance can trigger
- [ ] APPROVED -> PAID: Finance can trigger
- [ ] No backward transitions allowed; attempts return 400
- [ ] Only Finance role can trigger transitions
- [ ] All transitions are audit logged
- [ ] Unit tests for each valid transition and invalid attempts

---

## Story: Build outstanding receivables API
**Type:** Feature
**Phase:** 2
**Module:** 09-invoicing
**Priority:** P1
**Estimate:** S (1-2d)
**Depends On:** 09-invoicing (invoice CRUD)
**Labels:** backend

### Description
Implement `GET /api/invoices/receivables` to show all invoices not yet PAID, grouped by client and project. Shows both original currency amount and amount_inr. Supports filtering by status (SUBMITTED, APPROVED). Accessible to Finance, CEO, CTO only.

### Acceptance Criteria
- [ ] Returns all invoices with status != PAID
- [ ] Grouped by client and project
- [ ] Shows amount in original currency and amount_inr
- [ ] Supports `?status=SUBMITTED,APPROVED` filter
- [ ] Accessible to Finance, CEO, CTO only
- [ ] All other roles get 403
- [ ] Pagination supported
- [ ] Unit tests for grouping logic and access control

---

## Story: Build milestones tab UI for Fixed Price projects
**Type:** Feature
**Phase:** 2
**Module:** 09-invoicing
**Priority:** P1
**Estimate:** L (5-10d)
**Depends On:** 09-invoicing (milestone API, milestone lifecycle API), 03-project-management (project detail page)
**Labels:** frontend

### Description
Add a "Milestones" tab to the project detail view, visible only for FIXED_PRICE projects. Display an ordered table with drag-to-reorder (PM/DM only), status badges, delivery delay indicators, and role-appropriate status transition buttons. Include "Add Milestone" button and inline/modal edit form.

### Acceptance Criteria
- [ ] Milestones tab shown only for FIXED_PRICE projects
- [ ] Table displays: sort order (#), Name, Amount (with currency), Planned Date, Actual Date, Status (colored badge), Delay indicator
- [ ] Drag-to-reorder via sort_order (PM/DM only)
- [ ] "Add Milestone" button opens form (PM, DM, CEO, CTO)
- [ ] Click row opens edit form (editable only in PLANNED status)
- [ ] Status buttons per role: "Mark Delivered" (PM/DM), "Approve" (PM/DM), "Invoice" (Finance), "Mark Paid" (Finance)
- [ ] Backward transitions: "Reject" (DELIVERED -> PLANNED), "Withdraw Approval" (APPROVED -> DELIVERED)
- [ ] Delivery delay highlighted when actual > planned with "Delayed X days"
- [ ] Empty state: "No milestones yet. Add milestones to track deliverables."
- [ ] Accessible to CEO, CTO, DM, PM (own portfolio), Finance

---

## Story: Build invoices tab UI
**Type:** Feature
**Phase:** 2
**Module:** 09-invoicing
**Priority:** P1
**Estimate:** L (5-10d)
**Depends On:** 09-invoicing (invoice API, lifecycle API), 03-project-management (project detail page)
**Labels:** frontend

### Description
Add an "Invoices" tab to the project detail view. Display a table of invoices with status filter, "Create Invoice" button (Finance only), and status transition buttons. Include invoice create/edit modal form with live INR preview, milestone dropdown (FP), and billing period fields (T&M/Onboarding). All 5 FSD Section 11 validation messages must be shown client-side.

### Acceptance Criteria
- [ ] Invoices tab displayed in project detail view
- [ ] Table shows: Invoice Date, Milestone (FP) or "--", Billing Period (T&M), Amount + Currency, Exchange Rate, Amount INR, Status (colored badge), Notes (truncated)
- [ ] Status filter dropdown
- [ ] "Create Invoice" button visible to Finance only
- [ ] Click row opens view/edit (Finance only, DRAFT status only for edits)
- [ ] Status transition buttons: Submit, Approve, Mark Paid (Finance only)
- [ ] Accessible to CEO, CTO (view), Finance (view + edit)
- [ ] DM and PM have no access to invoices tab
- [ ] Empty state: "No invoices yet. Create an invoice to begin tracking revenue."

---

## Story: Build invoice create/edit form with validation
**Type:** Feature
**Phase:** 2
**Module:** 09-invoicing
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** 09-invoicing (invoices tab UI)
**Labels:** frontend

### Description
Build the invoice create/edit modal form. Fields: Invoice Date picker, Amount input, Currency (read-only from project), Exchange Rate (disabled for INR, required for others), live INR Preview (amount * exchange_rate, read-only), Milestone dropdown (FP only, shows APPROVED milestones), Billing Period Start/End (T&M/Onboarding), Notes textarea. Client-side validations must match all 5 FSD Section 11 rules.

### Acceptance Criteria
- [ ] Invoice Date picker (required)
- [ ] Amount input (required, positive)
- [ ] Currency field read-only, copied from project
- [ ] Exchange Rate: disabled and auto-set to 1.0 for INR; editable and required for other currencies
- [ ] INR Preview: live-computed amount * exchange_rate (read-only display)
- [ ] Milestone dropdown (required for FP): shows only APPROVED milestones
- [ ] Billing Period Start/End fields shown for T&M/Onboarding projects
- [ ] Validation: "Invoice amount must be positive"
- [ ] Validation: "Exchange rate must be positive"
- [ ] Validation: "Fixed price invoices must be linked to a milestone"
- [ ] Validation: "Milestone must be approved before invoicing"
- [ ] Save triggers POST (create) or PUT (edit); Cancel closes modal
- [ ] Finance role only

---

## Story: Implement invoicing access control
**Type:** Task
**Phase:** 2
**Module:** 09-invoicing
**Priority:** P0
**Estimate:** S (1-2d)
**Depends On:** 01-auth-and-roles, 09-invoicing (all APIs)
**Labels:** backend

### Description
Enforce access control across all invoicing endpoints per ACCESS-MATRIX.md. Finance has EDIT ALL for invoicing. CEO/CTO have VIEW ALL. DM, PM, HR, Engineer have NONE for invoicing data type. Milestone endpoints follow project_details scoping (PM/DM OWN_PORTFOLIO, CEO/CTO ALL). Ensure scope filtering via WHERE clauses at the database level.

### Acceptance Criteria
- [ ] Finance: EDIT ALL on invoice endpoints
- [ ] CEO, CTO: VIEW ALL on invoice endpoints (read-only)
- [ ] DM, PM: NONE for invoicing; milestones follow project_details scope (OWN_PORTFOLIO)
- [ ] HR, Engineer: NONE for invoicing and milestones
- [ ] Scope filtering applied at DB query level
- [ ] Access control tests for all 7 roles on invoice and milestone endpoints
