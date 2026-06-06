# Module 12: Alerts & Notifications -- JIRA Tickets

---

## Story: Create Alert and SystemConfig database tables and seed data
**Type:** Task
**Phase:** 3
**Module:** 12-alerts
**Priority:** P0
**Estimate:** S (1-2d)
**Depends On:** 01-auth-and-roles
**Labels:** backend, database

### Description
Create the database migration for the Alert table and verify/create the SystemConfig table. Alert stores one row per recipient per event with type, severity, deep-link info, and read/dismiss state. SystemConfig stores the 7 default key-value pairs for alert thresholds and system settings. Seed all 7 SystemConfig entries if not already present from Phase 1.

### Acceptance Criteria
- [ ] Alert table created: id (UUID PK), type (STRING(50)), severity (ENUM: INFO/WARNING/CRITICAL, default INFO), title (STRING(255)), message (TEXT), recipient_user_id (FK -> User), entity_type (STRING(50) NULLABLE), entity_id (UUID NULLABLE), is_read (BOOLEAN default false), is_dismissed (BOOLEAN default false), created_at (TIMESTAMP AUTO)
- [ ] DB indexes on Alert: recipient_user_id, type, is_read, is_dismissed, created_at
- [ ] SystemConfig table verified/created: key (STRING(100) PK), value (STRING(500)), description (STRING(500)), updated_at (TIMESTAMP AUTO)
- [ ] All 7 SystemConfig keys seeded with defaults: alert.contract_expiry_days (30), alert.contract_expiry_urgent_days (7), alert.bench_threshold_days (7), alert.utilization_threshold_pct (70), system.working_days_per_month (22), system.working_hours_per_day (8), system.default_currency (INR)
- [ ] Seed is idempotent (does not overwrite existing values)

---

## Story: Build alert core service (create, query, update)
**Type:** Feature
**Phase:** 3
**Module:** 12-alerts
**Priority:** P0
**Estimate:** M (3-5d)
**Depends On:** 12-alerts (DB tables)
**Labels:** backend

### Description
Build the core alert service layer: create alert (internal, used by scheduled jobs and event triggers), query alerts for a user, mark as read, dismiss, and bulk mark-all-read. The create function accepts type, severity, title, message, recipient list, entity_type, entity_id and creates one Alert row per recipient. Includes deduplication logic: skip creation if an unread alert of the same type + entity already exists for that recipient.

### Acceptance Criteria
- [ ] createAlert() function: accepts type, severity, title, message, recipients[], entity_type, entity_id
- [ ] Creates one Alert row per recipient
- [ ] Deduplication: does not re-create if unread alert of same type + entity_id exists for the same recipient
- [ ] GET /api/alerts returns paginated alerts for current user only (SELF_ONLY)
- [ ] GET supports filters: ?type, ?is_read, ?is_dismissed, ?page, ?limit
- [ ] GET /api/alerts/unread-count returns count of unread, non-dismissed alerts
- [ ] PUT /api/alerts/:id/read marks alert as read (owner only)
- [ ] PUT /api/alerts/:id/dismiss marks alert as dismissed (owner only)
- [ ] PUT /api/alerts/read-all marks all unread alerts as read for current user
- [ ] Unit tests for creation, deduplication, query, and state changes

---

## Story: Build contract expiry scheduled alert job
**Type:** Feature
**Phase:** 3
**Module:** 12-alerts
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** 12-alerts (core service), 03-project-management
**Labels:** backend, infrastructure

### Description
Implement the daily CONTRACT_EXPIRY alert job (`POST /api/jobs/alerts/contract-expiry`). Checks all T&M and ONBOARDING projects for contract_end_date within the configured thresholds (30 days and 7 days from SystemConfig). Creates alerts with WARNING severity at 30 days and CRITICAL at 7 days. Recipients: DM (own portfolio), CTO, CEO. Avoids duplicates.

### Acceptance Criteria
- [ ] Runs as a daily scheduled job
- [ ] Checks T&M and ONBOARDING projects with contract_end_date approaching
- [ ] Fires WARNING alert at alert.contract_expiry_days (default 30) days before expiry
- [ ] Fires CRITICAL alert at alert.contract_expiry_urgent_days (default 7) days before expiry
- [ ] Recipients: DM (of the project), CTO, CEO
- [ ] Does not fire for FIXED_PRICE projects
- [ ] Uses SystemConfig values (not hardcoded thresholds)
- [ ] Avoids duplicate alerts (deduplication via core service)
- [ ] Endpoint restricted to internal/admin access only
- [ ] Unit tests for threshold matching, recipient resolution, and deduplication

---

## Story: Build bench duration scheduled alert job
**Type:** Feature
**Phase:** 3
**Module:** 12-alerts
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** 12-alerts (core service), 04-resource-management, 05-allocation-tracking
**Labels:** backend, infrastructure

### Description
Implement the daily BENCH_DURATION alert job (`POST /api/jobs/alerts/bench-duration`). Checks all resources on bench (0 ACTIVE assignments) whose days_on_bench exceeds the configured threshold (default 7 days from SystemConfig). Recipients: DM (of the resource's last project), CTO, HR. Avoids duplicates.

### Acceptance Criteria
- [ ] Runs as a daily scheduled job
- [ ] Detects resources on bench (0 ACTIVE assignments) for more than alert.bench_threshold_days (default 7)
- [ ] Creates WARNING severity alert per qualifying resource
- [ ] Recipients: DM (of the resource's most recent project), CTO, HR
- [ ] Uses SystemConfig threshold (not hardcoded)
- [ ] Avoids duplicate alerts
- [ ] Endpoint restricted to internal/admin access only
- [ ] Unit tests for bench duration detection, threshold matching, and recipient resolution

---

## Story: Build milestone overdue scheduled alert job
**Type:** Feature
**Phase:** 3
**Module:** 12-alerts
**Priority:** P1
**Estimate:** S (1-2d)
**Depends On:** 12-alerts (core service), 09-invoicing
**Labels:** backend, infrastructure

### Description
Implement the daily MILESTONE_OVERDUE alert job (`POST /api/jobs/alerts/milestone-overdue`). Checks all milestones with planned_delivery_date < today and status = PLANNED. Creates WARNING alerts. Recipients: PM (of the project), DM (of the project). Avoids duplicates.

### Acceptance Criteria
- [ ] Runs as a daily scheduled job
- [ ] Detects milestones where planned_delivery_date < today AND status = PLANNED
- [ ] Creates WARNING severity alert per overdue milestone
- [ ] Recipients: PM (of the milestone's project), DM (of the milestone's project)
- [ ] Avoids duplicate alerts
- [ ] Endpoint restricted to internal/admin access only
- [ ] Unit tests for overdue detection and recipient resolution

---

## Story: Build utilization drop weekly alert job
**Type:** Feature
**Phase:** 3
**Module:** 12-alerts
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** 12-alerts (core service), 07-utilization-dashboards
**Labels:** backend, infrastructure

### Description
Implement the weekly UTILIZATION_DROP alert job (`POST /api/jobs/alerts/utilization-drop`), running on Mondays. Computes company-wide billable utilization and fires a WARNING alert if it falls below alert.utilization_threshold_pct (default 70%). Recipients: CTO, CEO. Avoids duplicates.

### Acceptance Criteria
- [ ] Runs as a weekly scheduled job (Monday)
- [ ] Computes company utilization = SUM(all billable alloc) / (active_resource_count * 100) * 100%
- [ ] Fires WARNING alert if utilization < alert.utilization_threshold_pct (default 70%)
- [ ] Recipients: CTO, CEO
- [ ] Uses SystemConfig threshold (not hardcoded)
- [ ] Avoids duplicate alerts
- [ ] Endpoint restricted to internal/admin access only
- [ ] Unit tests for utilization calculation and threshold comparison

---

## Story: Build event-triggered over-allocation alert
**Type:** Feature
**Phase:** 3
**Module:** 12-alerts
**Priority:** P1
**Estimate:** S (1-2d)
**Depends On:** 12-alerts (core service), 05-allocation-tracking
**Labels:** backend

### Description
Wire the OVER_ALLOCATION alert to fire when an assignment is saved and the resource's total allocation exceeds 100%. This is triggered inline during assignment create/update (Module 05), not by a scheduled job. Recipients: the PM who saved the assignment and the DM of the project. Severity: WARNING.

### Acceptance Criteria
- [ ] Fires when assignment save results in resource total allocation > 100%
- [ ] Triggered inline during assignment create or update (not a scheduled job)
- [ ] Recipients: PM who performed the action, DM of the project
- [ ] Severity: WARNING
- [ ] Includes resource name and total allocation percentage in alert message
- [ ] Deep-links to the resource's assignment view
- [ ] Avoids duplicate alerts (deduplication via core service)
- [ ] Unit tests for over-allocation detection

---

## Story: Build event-triggered auto-release alert
**Type:** Feature
**Phase:** 3
**Module:** 12-alerts
**Priority:** P2
**Estimate:** S (1-2d)
**Depends On:** 12-alerts (core service), 05-allocation-tracking (auto-release job)
**Labels:** backend

### Description
Wire the ASSIGNMENT_AUTO_RELEASED alert to fire when the daily auto-release job (Module 05) releases an assignment. This alert is defined in Module 12 but triggered by Module 05's auto-release logic. Recipients: PM and DM of the project. Severity: INFO.

### Acceptance Criteria
- [ ] Fires when auto-release job sets assignment status to AUTO_RELEASED
- [ ] Triggered by Module 05 auto-release logic calling Module 12 alert creation
- [ ] Recipients: PM (of the project), DM (of the project)
- [ ] Severity: INFO
- [ ] Includes resource name, project name, and release date in alert message
- [ ] Deep-links to the assignment view
- [ ] Unit tests for alert creation on auto-release

---

## Story: Configure scheduled job runners for alert jobs
**Type:** Task
**Phase:** 3
**Module:** 12-alerts
**Priority:** P0
**Estimate:** M (3-5d)
**Depends On:** 12-alerts (all scheduled job implementations)
**Labels:** backend, infrastructure

### Description
Set up the job scheduling infrastructure (cron or equivalent) to run the 4 scheduled alert jobs automatically. Contract expiry: daily. Bench duration: daily. Milestone overdue: daily. Utilization drop: weekly (Monday). Jobs must be idempotent and safe to re-run. Include monitoring/logging for job execution.

### Acceptance Criteria
- [ ] Contract expiry job runs daily (midnight IST or configured time)
- [ ] Bench duration job runs daily
- [ ] Milestone overdue job runs daily
- [ ] Utilization drop job runs weekly on Monday
- [ ] Each job is idempotent and safe to re-run
- [ ] Job execution is logged (start time, end time, alerts created count)
- [ ] Failed jobs log errors and do not crash the application
- [ ] Jobs can be triggered manually via POST endpoints for testing

---

## Story: Build notification bell and alert panel UI
**Type:** Feature
**Phase:** 3
**Module:** 12-alerts
**Priority:** P1
**Estimate:** L (5-10d)
**Depends On:** 12-alerts (core service APIs)
**Labels:** frontend

### Description
Build the global notification bell component in the application header. Shows unread alert count badge, opens a dropdown panel on click with recent alerts (title, message snippet, severity color, relative timestamp, deep-link). Supports mark-single-as-read, dismiss, and "Mark all read". Panel includes a link to the full alert list page. Bell is hidden from Engineer role (NONE for alerts).

### Acceptance Criteria
- [ ] Bell icon in header with unread count badge (from GET /api/alerts/unread-count)
- [ ] Badge hidden when count = 0
- [ ] Click opens dropdown panel showing recent alerts (latest 10-15)
- [ ] Each alert shows: title, message snippet (truncated), severity (color-coded: INFO=blue, WARNING=yellow, CRITICAL=red), relative timestamp
- [ ] Click alert: navigates to entity (deep-link via entity_type + entity_id) and marks as read
- [ ] "Mark all read" button in panel header
- [ ] "View all alerts" link navigates to /alerts
- [ ] Bell hidden from Engineer role
- [ ] Empty state: "You're all caught up -- no new alerts."
- [ ] Polling or real-time updates for unread count

---

## Story: Build alert list page UI
**Type:** Feature
**Phase:** 3
**Module:** 12-alerts
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** 12-alerts (core service APIs)
**Labels:** frontend

### Description
Build the full `/alerts` page showing all alerts for the current user with filtering, sorting, and bulk actions. Filters: type dropdown, severity dropdown, read/unread/dismissed toggle. Sorted by created_at DESC. Supports bulk mark-as-read. Each alert row shows type badge, severity badge, title (bold if unread), message, entity deep-link, timestamp, and read/dismiss buttons.

### Acceptance Criteria
- [ ] Displays all alerts for current user (not other users')
- [ ] Filter by: type (dropdown), severity (dropdown), read/unread/dismissed (toggle)
- [ ] Sorted by created_at DESC
- [ ] Bulk "Mark all read" button
- [ ] Each row: type badge, severity badge, title (bold if unread), message (truncated), entity link ("View Project"/"View Resource"), full timestamp, read/dismiss buttons
- [ ] Click row navigates to entity and marks as read
- [ ] Pagination for large alert lists
- [ ] Accessible to CEO, CTO, DM, PM, Finance, HR (not Engineer)
- [ ] Empty state: "No alerts to show. Adjust filters or check back later."

---

## Story: Build SystemConfig admin UI
**Type:** Feature
**Phase:** 3
**Module:** 12-alerts
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** 12-alerts (SystemConfig API)
**Labels:** frontend

### Description
Build the `/admin/system-config` page for CEO and CTO to view and edit all 7 SystemConfig key-value pairs. Display each key with its label, current value, description, and an editable field. Validate that numeric fields are positive integers. Show last updated timestamp per key. All changes are audit logged.

### Acceptance Criteria
- [ ] Settings table showing all 7 config keys with friendly labels
- [ ] Each row: Key label, current value (editable), description, last updated timestamp
- [ ] Key labels: "Contract Expiry Warning (days)", "Contract Expiry Urgent (days)", "Bench Alert After (days)", "Utilization Alert Below (%)", "Working Days / Month", "Working Hours / Day", "Default Currency"
- [ ] Save per row or bulk save
- [ ] Validation: numeric fields must be positive integers
- [ ] Cancel edit reverts to saved value
- [ ] Accessible to CEO and CTO only
- [ ] All changes take effect on next scheduled job run
- [ ] Changes are audit logged

---

## Story: Build SystemConfig CRUD API
**Type:** Feature
**Phase:** 3
**Module:** 12-alerts
**Priority:** P0
**Estimate:** S (1-2d)
**Depends On:** 12-alerts (DB tables and seed)
**Labels:** backend

### Description
Implement `GET /api/system-config` (list all config entries) and `PUT /api/system-config/:key` (update a config value). GET is accessible to all roles for calculation-related keys (working_days, working_hours). PUT is restricted to CEO and CTO. Validate that numeric keys have positive integer values. All updates are audit logged.

### Acceptance Criteria
- [ ] GET /api/system-config returns all config key-value pairs with descriptions
- [ ] CEO and CTO can read all keys
- [ ] All roles can read system.working_days_per_month and system.working_hours_per_day (needed for calculations)
- [ ] PUT /api/system-config/:key updates a config value
- [ ] PUT restricted to CEO and CTO only
- [ ] Validation: numeric config values must be positive integers ("Value must be a positive number")
- [ ] All updates are audit logged
- [ ] Unit tests for CRUD, validation, and access control

---

## Story: Implement alerts access control
**Type:** Task
**Phase:** 3
**Module:** 12-alerts
**Priority:** P0
**Estimate:** S (1-2d)
**Depends On:** 01-auth-and-roles, 12-alerts (all APIs)
**Labels:** backend

### Description
Enforce access control across all alert endpoints per ACCESS-MATRIX.md. All roles except Engineer have VIEW access on alerts (SELF_ONLY -- each user sees only their own alerts). Engineer has NONE for alerts. SystemConfig: CEO and CTO have EDIT, all others have VIEW for calculation-related keys. Scheduled job endpoints are internal/admin only.

### Acceptance Criteria
- [ ] CEO, CTO, DM, PM, Finance, HR: VIEW SELF_ONLY on alerts (own alerts only)
- [ ] Engineer: NONE for alerts (403 on all alert endpoints)
- [ ] Users can never see other users' alerts
- [ ] SystemConfig: CEO, CTO have EDIT; calculation keys readable by all
- [ ] Scheduled job endpoints: internal/admin access only (not callable by regular users)
- [ ] Access control tests for all 7 roles on alert and SystemConfig endpoints
