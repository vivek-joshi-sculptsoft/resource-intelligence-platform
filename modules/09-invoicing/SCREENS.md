# Module 09: Invoicing — Screen Specifications

## Screen: Milestones Tab (within FP Project Detail)
**Route:** `/projects/:id` → Milestones tab (shown only for FIXED_PRICE projects)
**Audience:** CEO, CTO, DM (own portfolio), PM (own portfolio), Finance
**Layout:** Ordered table with status lifecycle actions.

### Components
- Milestone table ordered by sort_order (draggable to reorder — PM/DM only)
- Status transition buttons per row (based on allowed transitions for current user role)
- Delivery delay indicator (highlighted row when actual_delivery_date > planned_delivery_date)
- "Add Milestone" button (PM, DM, CEO, CTO)

### Data Displayed

| Field | Source | Notes |
|---|---|---|
| # | sort_order | Drag handle for reordering |
| Name | Milestone.name | |
| Amount | Milestone.amount + currency | In project billing currency |
| Planned Date | Milestone.planned_delivery_date | |
| Actual Date | Milestone.actual_delivery_date | Set on delivery |
| Status | Milestone.status | Colored badge |
| Delay | Computed | "Delayed X days" if actual > planned |

### Actions
- Add Milestone → form (inline or modal)
- Click row → edit milestone form
- Status buttons: "Mark Delivered" (PM/DM), "Approve" (PM/DM), "Invoice" (Finance → opens invoice form), "Mark Paid" (Finance)
- Backward: "Reject" (revert DELIVERED → PLANNED), "Withdraw Approval" (revert APPROVED → DELIVERED)

### Empty State
"No milestones yet. Add milestones to track deliverables."

### Access Restrictions
Finance manages APPROVED→INVOICED and INVOICED→PAID. PM/DM manage up to APPROVED.

---

## Screen: Invoices Tab (within Project Detail)
**Route:** `/projects/:id` → Invoices tab
**Audience:** CEO, CTO, Finance
**Layout:** Table with action bar.

### Components
- Invoice table (see data below)
- "Create Invoice" button (Finance only)
- Status filter

### Data Displayed

| Field | Source | Notes |
|---|---|---|
| Invoice Date | Invoice.invoice_date | |
| Milestone | Milestone.name (if FP) | "—" for T&M/Onboarding |
| Billing Period | billing_period_start – billing_period_end | T&M/Onboarding only |
| Amount | Invoice.amount + currency | e.g., "$5,000 USD" |
| Exchange Rate | Invoice.exchange_rate | |
| Amount INR | Invoice.amount_inr | "₹4,17,500" |
| Status | Invoice.status | Colored badge |
| Notes | Invoice.notes | Truncated |

### Actions
- Create Invoice → invoice create form
- Click row → view/edit invoice (Finance only; draft status only for edits)
- Status transition buttons: Submit, Approve, Mark Paid (Finance only)

### Empty State
"No invoices yet. Create an invoice to begin tracking revenue."

### Access Restrictions
CEO and CTO can view. Finance can view and edit. DM and PM have no access to invoices tab.

---

## Screen: Invoice Create / Edit Form
**Route:** Modal within `/projects/:id`
**Audience:** Finance only
**Layout:** Form in modal.

### Components
- Invoice Date picker (required)
- Amount input (required, positive)
- Currency field (read-only — copied from project)
- Exchange Rate input (disabled and auto-set to 1.0 for INR; required positive for other currencies)
- INR Preview: live-computed `amount × exchange_rate` (read-only)
- Milestone dropdown (required for FP) — shows APPROVED milestones only
- Billing Period Start / End (for T&M/Onboarding)
- Notes textarea

### Validation Messages (FSD §11)
- "Invoice amount must be positive"
- "Exchange rate must be positive"
- "Fixed price invoices must be linked to a milestone"
- "Milestone must be approved before invoicing"

### Actions
- Save → POST (create) or PUT (edit) → update invoice table
- Cancel → close modal

### Empty State
N/A.
