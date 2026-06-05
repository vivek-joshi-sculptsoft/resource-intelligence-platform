# Module 12: Alerts & Notifications

## Overview

All alerts are in-app only (no email). This module manages scheduled alert jobs (contract expiry, bench duration, milestone overdue, utilization drop), event-triggered alerts (over-allocation, auto-release), an alert notification UI with read/dismiss, and the SystemConfig admin interface for configuring thresholds. One alert row is created per recipient per event.

## Phase

Phase 3.

## Dependencies

- All Phase 1 and Phase 2 modules — alerts reference data from every module

---

## Features

### Feature: Scheduled Alert Jobs
**Description:** Automated jobs that check conditions and create alert rows.
**Acceptance Criteria:**
- [ ] CONTRACT_EXPIRY: daily job, fires at 30d and 7d before `contract_end_date` for T&M and Onboarding projects. Recipients: DM (own portfolio), CTO, CEO.
- [ ] BENCH_DURATION: daily job, fires when resource is on bench > `alert.bench_threshold_days` (default 7). Recipients: DM (own portfolio), CTO, HR.
- [ ] MILESTONE_OVERDUE: daily job, fires when `planned_delivery_date < today AND status = PLANNED`. Recipients: PM (own portfolio), DM (own portfolio).
- [ ] UTILIZATION_DROP: weekly job (Monday), fires when company utilization < `alert.utilization_threshold_pct` (default 70%). Recipients: CTO, CEO.
- [ ] Each job avoids duplicate alerts: does not re-create if unread alert of same type+entity already exists for recipient

### Feature: Event-Triggered Alerts
**Description:** Alerts fired on specific user actions.
**Acceptance Criteria:**
- [ ] OVER_ALLOCATION: fires when an assignment is saved and total allocation > 100% for the resource. Recipients: PM (who saved), DM of the project.
- [ ] ASSIGNMENT_AUTO_RELEASED: fires by the auto-release job (Module 05). Recipients: PM, DM. (Defined here but triggered in Module 05.)

### Feature: Alert Notification Panel
**Description:** In-app notification bell accessible from any screen.
**Acceptance Criteria:**
- [ ] Notification bell in header shows count of unread alerts for current user
- [ ] Clicking bell opens panel showing recent alerts
- [ ] Each alert shows: title, message, severity, timestamp
- [ ] Mark single alert as read
- [ ] Dismiss (hide) single alert
- [ ] Deep-link: clicking alert navigates to relevant entity (project, resource, etc.)

### Feature: Alert List Page
**Description:** Full list of all alerts with filters.
**Acceptance Criteria:**
- [ ] List all alerts for current user (not other users' alerts)
- [ ] Filter by: type, severity, read/unread/dismissed
- [ ] Bulk mark-as-read
- [ ] Sorted by created_at DESC

### Feature: SystemConfig Admin UI
**Description:** Admin interface for configuring alert thresholds and system settings.
**Acceptance Criteria:**
- [ ] CEO and CTO can view and edit all 7 SystemConfig keys
- [ ] Validation: numeric fields must be positive integers
- [ ] Changes take effect on next scheduled job run
- [ ] All changes audit logged

---

## Validations

| Rule | Condition | Error |
|---|---|---|
| Config value positive | Numeric SystemConfig value ≤ 0 | "Value must be a positive number" |

---

## Business Rules

- One alert row per recipient per event — see FSD §12 Alert Specifications
- Thresholds from SystemConfig — never hardcode values
- Alert types: CONTRACT_EXPIRY, BENCH_DURATION, OVER_ALLOCATION, MILESTONE_OVERDUE, UTILIZATION_DROP, ASSIGNMENT_AUTO_RELEASED
- Recipients follow role scopes from `shared/ACCESS-MATRIX.md` Alert Recipients Quick Reference
- Scheduled job schedule from `CLAUDE.md` Scheduled Jobs section
