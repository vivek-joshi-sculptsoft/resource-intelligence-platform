# Module 06: Non-Human Costs

## Overview

Projects incur expenses beyond resource salaries: AI tools, cloud infrastructure, test devices, and third-party licenses. These are tracked per-project as line items with currency and exchange rate support. One-time and monthly recurring costs are supported. This data feeds into project margin calculations in Module 08. Non-human costs are a Phase 2 feature.

## Phase

Phase 2.

## Dependencies

- Module 01 (Auth & Roles)
- Module 03 (Project Management)
- Module 08 (Financial Engine) — costs flow into margin calculations

---

## Features

### Feature: Cost Entry (Add / Edit / Delete)
**Description:** Add, update, or remove cost line items against a project.
**Acceptance Criteria:**
- [ ] Add cost with: description (required), category (required), amount (required, positive), currency (required, default INR), exchange_rate (auto-1.0 for INR, manual otherwise), cost_date (required), is_recurring, recurring_end_date (required if recurring), project (required)
- [ ] `amount_inr` auto-computed: `amount × exchange_rate`
- [ ] Edit any cost field; `amount_inr` recomputed on save
- [ ] Soft delete cost entries (or hard delete — these are line items without downstream FKs)
- [ ] All changes audit logged

### Feature: Recurring Cost Processing
**Description:** Active recurring costs automatically generate monthly entries.
**Acceptance Criteria:**
- [ ] Monthly scheduled job (1st of each month) creates new cost entry for each active recurring cost (where `cost_date <= today <= recurring_end_date`)
- [ ] Generated entries have same fields as parent; `cost_date = 1st of current month`
- [ ] Recurring stops after `recurring_end_date`

### Feature: Category Filtering
**Description:** Costs grouped and filterable by category.
**Acceptance Criteria:**
- [ ] Five categories: AI_TOOLS, CLOUD_INFRA, DEVICES, THIRD_PARTY_LICENSE, OTHER
- [ ] Filter cost list by category
- [ ] Category shown in all views

### Feature: Live INR Preview
**Description:** UI shows INR equivalent in real time as user enters amount and exchange rate.
**Acceptance Criteria:**
- [ ] INR preview updates live as user types amount or exchange rate
- [ ] For INR currency: exchange_rate field disabled, auto-set to 1.0
- [ ] Non-INR: exchange_rate field active, required

---

## Validations

FSD §11 Non-Human Cost validations:

| Rule | Condition | Error |
|---|---|---|
| Amount positive | amount ≤ 0 | "Cost amount must be positive" |
| Exchange rate positive | exchange_rate ≤ 0 | "Exchange rate must be positive" |
| INR auto-rate | currency = 'INR' | Auto-set exchange_rate = 1.0, disable field |
| Recurring needs end date | is_recurring = true AND recurring_end_date is null | "Recurring costs must have an end date" |
| End after start | recurring_end_date ≤ cost_date | "Recurring end date must be after cost date" |

---

## Business Rules

- `amount_inr = amount × exchange_rate` — from `shared/BUSINESS-RULES.md §7.7`
- Non-human costs feed into Total Project Cost: `shared/BUSINESS-RULES.md §7.2`
- Access: PM, DM, CTO, CEO, Finance can add/edit costs; HR and Engineer cannot — `shared/ACCESS-MATRIX.md` (`non_human_costs`)
- Monthly recurring job schedule: see `CLAUDE.md` Scheduled Jobs section
