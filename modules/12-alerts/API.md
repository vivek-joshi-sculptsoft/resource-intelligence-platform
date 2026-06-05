# Module 12: Alerts — API Endpoints

## Alert Endpoints

### GET /api/alerts
**Description:** List all alerts for the current user.
**Auth:** All authenticated roles with VIEW access on `alerts`. Reference `shared/ACCESS-MATRIX.md`.
**Scope:** SELF_ONLY (only own alerts — never another user's)
**Response:** Paginated: `[{ id, type, severity, title, message, entity_type, entity_id, is_read, is_dismissed, created_at }]`
**Notes:** `?type=CONTRACT_EXPIRY&is_read=false&is_dismissed=false&page=1&limit=20`

---

### GET /api/alerts/unread-count
**Description:** Count of unread, non-dismissed alerts for the notification bell.
**Auth:** All authenticated roles
**Scope:** SELF_ONLY
**Response:** `{ "count": int }`

---

### PUT /api/alerts/:id/read
**Description:** Mark an alert as read.
**Auth:** The alert's recipient only
**Scope:** SELF_ONLY
**Response:** `{ "success": true }`

---

### PUT /api/alerts/:id/dismiss
**Description:** Dismiss (hide) an alert.
**Auth:** The alert's recipient only
**Scope:** SELF_ONLY
**Response:** `{ "success": true }`

---

### PUT /api/alerts/read-all
**Description:** Mark all current user's unread alerts as read.
**Auth:** Any authenticated user
**Scope:** SELF_ONLY
**Response:** `{ "updated_count": int }`

---

## Scheduled Job Endpoints

### POST /api/jobs/alerts/contract-expiry
**Description:** Daily job checking contract end dates.
**Auth:** Internal/admin only
**Notes:** Creates CONTRACT_EXPIRY alerts for T&M and ONBOARDING projects expiring within `alert.contract_expiry_days` (30d) and `alert.contract_expiry_urgent_days` (7d). No duplicate if unread alert already exists.

---

### POST /api/jobs/alerts/bench-duration
**Description:** Daily job checking bench duration.
**Auth:** Internal/admin only
**Notes:** Creates BENCH_DURATION alerts for resources on bench > `alert.bench_threshold_days`.

---

### POST /api/jobs/alerts/milestone-overdue
**Description:** Daily job checking overdue milestones.
**Auth:** Internal/admin only
**Notes:** Creates MILESTONE_OVERDUE alerts for FP milestones with planned_delivery_date < today and status = PLANNED.

---

### POST /api/jobs/alerts/utilization-drop
**Description:** Weekly job (Monday) checking company utilization.
**Auth:** Internal/admin only
**Notes:** Creates UTILIZATION_DROP alert if company billable utilization < `alert.utilization_threshold_pct`.

---

## SystemConfig Endpoints

### GET /api/system-config
**Description:** Get all SystemConfig key-value pairs.
**Auth:** CEO, CTO (EDIT); all roles can read working_days/hours keys needed for calculations
**Scope:** ALL
**Response:** `[{ key, value, description }]`

---

### PUT /api/system-config/:key
**Description:** Update a SystemConfig value.
**Auth:** CEO, CTO only
**Scope:** ALL
**Request Body:** `{ "value": "string*" }`
**Validations:** Numeric keys must be positive integers.
**Notes:** Audit logged.
