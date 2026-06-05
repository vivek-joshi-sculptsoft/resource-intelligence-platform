# Module 09: Invoicing

## Overview

This module manages the revenue recognition lifecycle. For Fixed Price projects it handles milestones — each with its own amount, planned delivery date, and status lifecycle. For all project types it manages invoices with multi-currency support and a manual exchange rate for INR conversion. Outstanding receivables are tracked. Milestones and invoices are Phase 2 features.

## Phase

Phase 2.

## Dependencies

- Module 01 (Auth & Roles)
- Module 03 (Project Management)
- Module 08 (Financial Engine) — actual revenue feeds from invoice amounts

---

## Features

### Feature: Milestone CRUD (Fixed Price Only)
**Description:** Create and manage milestones for FP projects.
**Acceptance Criteria:**
- [ ] Create milestone: name (required), amount (required, in project billing_currency), planned_delivery_date, sort_order
- [ ] Milestones linked only to FIXED_PRICE projects
- [ ] Reorder milestones via sort_order
- [ ] Edit any milestone field while in PLANNED status
- [ ] All changes audit logged

### Feature: Milestone Status Lifecycle
**Description:** Milestones follow the lifecycle: PLANNED → DELIVERED → APPROVED → INVOICED → PAID.
**Acceptance Criteria:**
- [ ] Valid transitions: PLANNED → DELIVERED (PM), DELIVERED → APPROVED (PM/DM), APPROVED → INVOICED (Finance), INVOICED → PAID (Finance)
- [ ] Backward transitions: DELIVERED → PLANNED (rejected), APPROVED → DELIVERED (withdrawn)
- [ ] INVOICED and PAID are terminal — no backward transitions
- [ ] Delivery delay: flagged when `actual_delivery_date > planned_delivery_date`
- [ ] `actual_delivery_date` set when status → DELIVERED
- [ ] All transitions audit logged

### Feature: Invoice CRUD (All Project Types)
**Description:** Create and manage invoices with currency and exchange rate.
**Acceptance Criteria:**
- [ ] Create invoice: invoice_date (required), amount (required, positive), currency (required, copied from project), exchange_rate (auto-1.0 for INR), optional notes
- [ ] For FP: `milestone_id` required; linked milestone must be APPROVED
- [ ] For T&M/Onboarding: `billing_period_start` and `billing_period_end` fields
- [ ] `amount_inr = amount × exchange_rate` auto-computed
- [ ] All creates/updates audit logged
- [ ] All 5 FSD §11 invoice validations enforced

### Feature: Invoice Status Lifecycle
**Description:** Invoices follow: DRAFT → SUBMITTED → APPROVED → PAID.
**Acceptance Criteria:**
- [ ] Valid transitions: DRAFT → SUBMITTED, SUBMITTED → APPROVED, APPROVED → PAID
- [ ] Finance manages invoice status transitions
- [ ] All transitions audit logged

### Feature: Outstanding Receivables Tracking
**Description:** Show invoices not yet paid.
**Acceptance Criteria:**
- [ ] List all invoices with status ≠ PAID grouped by project/client
- [ ] Show amount (original currency) and amount_inr
- [ ] Accessible to Finance, CEO, CTO

---

## Validations

FSD §11 Invoice validations:

| Rule | Condition | Error |
|---|---|---|
| Amount positive | amount ≤ 0 | "Invoice amount must be positive" |
| Exchange rate positive | exchange_rate ≤ 0 | "Exchange rate must be positive" |
| INR auto-rate | currency = 'INR' | Auto-set exchange_rate = 1.0, disable field |
| FP milestone required | FIXED_PRICE project and no milestone_id | "Fixed price invoices must be linked to a milestone" |
| Milestone approved | Linked milestone status ≠ APPROVED | "Milestone must be approved before invoicing" |

---

## Business Rules

- `amount_inr = amount × exchange_rate` per `shared/BUSINESS-RULES.md §7.7`
- Actual Revenue = `SUM(invoice.amount_inr)` where status ∈ {APPROVED, PAID} per `shared/BUSINESS-RULES.md §7.4`
- Milestone lifecycle and backward transitions: FSD §6.2
- Invoice lifecycle: FSD §6.3
- Access: Finance has EDIT ALL for invoicing; CEO/CTO have VIEW ALL; DM/PM/HR/Engineer have NONE — `shared/ACCESS-MATRIX.md` (`invoicing`)
