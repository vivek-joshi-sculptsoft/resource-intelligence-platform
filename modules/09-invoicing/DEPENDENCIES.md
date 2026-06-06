# Invoicing — Dependencies

## Must Be Built Before This Module

| Module | What's Needed | Why |
|---|---|---|
| 01-auth-and-roles | Role, RolePermission, User entities | Access control: Finance has EDIT ALL for invoicing; CEO/CTO have VIEW ALL; all other roles have NONE. RolePermission governs the `invoicing` data type. |
| 02-client-management | Client entity | Outstanding receivables are grouped by client. Client-level revenue aggregations require client data via Project. |
| 03-project-management | Project entity (`type`, `billing_currency`, `status`, `client_id`) | Milestones are linked only to FIXED_PRICE projects. Invoice currency is copied from `project.billing_currency`. T&M and Onboarding projects use billing period fields instead of milestones. |

## Modules That Depend on This Module

| Module | What They Need |
|---|---|
| 08-financial-engine | Actual Revenue = `SUM(invoice.amount_inr)` where status is APPROVED or PAID. Actual Margin = Actual Revenue minus Total Project Cost. All financial reporting depends on invoice data. |
| 12-alerts | MILESTONE_OVERDUE alert checks milestones where `planned_delivery_date < today AND status = PLANNED`. Scheduled daily job reads Milestone entity. |
| 13-audit-history | Milestone and Invoice are tracked entities. Audit logging captures status transitions, amount changes, and exchange rate changes. |

## Shared References Used
- `shared/ENTITIES.md` — Milestone (2.8) status lifecycle and field definitions; Invoice (2.9) with multi-currency support and computed `amount_inr`; Project (2.6) for type and billing currency
- `shared/BUSINESS-RULES.md` — Exchange Rate Conversion (7.7) for `amount_inr = amount x exchange_rate`; Actual Revenue (7.4) formula aggregating approved/paid invoices
- `shared/ACCESS-MATRIX.md` — `invoicing` data type permissions: Finance EDIT ALL, CEO/CTO VIEW ALL, all others NONE; `exchange_rate` write access restricted to Finance
