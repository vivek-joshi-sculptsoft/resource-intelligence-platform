# Alerts & Notifications — Dependencies

## Must Be Built Before This Module

| Module | What's Needed | Why |
|---|---|---|
| 01-auth-and-roles | Role, RolePermission, User entities | Alert recipients are determined by role (CEO, CTO, DM, PM, HR). User entity provides `recipient_user_id` for each alert row. RolePermission governs the `alerts` data type visibility. |
| 02-client-management | Client entity | Client context is needed for deep-linking from contract expiry alerts to the relevant project/client. |
| 03-project-management | Project entity (`contract_end_date`, `dm_id`, `pm_id`, `status`) | CONTRACT_EXPIRY alert checks `contract_end_date` on T&M and Onboarding projects. `dm_id` and `pm_id` determine alert recipients with OWN_PORTFOLIO scope. Project status filters active projects. |
| 04-resource-management | Resource entity (`date_of_joining`, `is_active`) | BENCH_DURATION alert needs `date_of_joining` as fallback bench start date for resources never assigned. Active resource filtering. |
| 05-allocation-tracking | Assignment entity (`allocation_pct`, `status`, `end_date`, `released_at`) | OVER_ALLOCATION alert fires when total `allocation_pct` > 100% for a resource. ASSIGNMENT_AUTO_RELEASED alert is triggered by the auto-release job. Bench detection (0 ACTIVE assignments) feeds BENCH_DURATION. |
| 06-non-human-costs | NonHumanCost entity | Recurring cost processing scheduled job (monthly, 1st) is defined alongside alert jobs in the system's scheduled jobs infrastructure. |
| 07-utilization-dashboards | Utilization calculations | UTILIZATION_DROP alert fires when company utilization falls below `alert.utilization_threshold_pct`. Requires utilization rate computation from dashboard logic. |
| 08-financial-engine | Utilization and financial calculations | Company utilization calculation is needed for UTILIZATION_DROP threshold comparison. |
| 09-invoicing | Milestone entity (`planned_delivery_date`, `status`) | MILESTONE_OVERDUE alert fires when `planned_delivery_date < today AND status = PLANNED`. Daily scheduled job reads milestone data. |
| 10-bench-forecasting | Bench start date computation | BENCH_DURATION alert needs bench start date logic (max of released_at or date_of_joining) to calculate days on bench and compare against threshold. |

## Modules That Depend on This Module

| Module | What They Need |
|---|---|
| 05-allocation-tracking | Auto-release job creates ASSIGNMENT_AUTO_RELEASED alerts. The Alert entity and creation logic must be available. |
| 08-financial-engine | SystemConfig entity provides `system.working_days_per_month` and `system.working_hours_per_day` used in revenue and cost calculations. |
| 10-bench-forecasting | SystemConfig entity provides thresholds. Bench duration threshold (`alert.bench_threshold_days`) is defined here. |
| 13-audit-history | SystemConfig changes are audit logged. Alert creation is part of system operations tracked by audit infrastructure. |

## Shared References Used
- `shared/ENTITIES.md` — Alert (2.13) with type, severity, recipient, deep-linking fields; SystemConfig (2.14) with 7 default configuration keys for thresholds and system constants
- `shared/BUSINESS-RULES.md` — Utilization Rate (7.1) for UTILIZATION_DROP threshold; Bench Cost (7.6) for bench start date computation used by BENCH_DURATION; Auto-Release Logic (8) for ASSIGNMENT_AUTO_RELEASED trigger
- `shared/ACCESS-MATRIX.md` — `alerts` data type: CEO/CTO VIEW ALL, DM/PM VIEW OWN_PORTFOLIO, HR VIEW ALL, Finance VIEW ALL, Engineer NONE; Alert Recipients Quick Reference maps each alert type to specific role-based recipients
