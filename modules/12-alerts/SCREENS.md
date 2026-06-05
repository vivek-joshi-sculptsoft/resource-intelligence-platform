# Module 12: Alerts — Screen Specifications

## Component: Notification Bell (Global — in Header)
**Route:** Present on all authenticated pages
**Audience:** All users with alert access (not Engineer — NONE for alerts)
**Layout:** Bell icon in top navigation bar.

### Components
- Bell icon with unread count badge
- Dropdown panel (click to open)

### Alert Panel Data

| Field | Source | Notes |
|---|---|---|
| Title | Alert.title | Short summary |
| Message snippet | Alert.message | Truncated 1-2 lines |
| Severity | Alert.severity | Color-coded: INFO=blue, WARNING=yellow, CRITICAL=red |
| Timestamp | Alert.created_at | Relative ("2 hours ago") |
| Deep-link | entity_type + entity_id | Clickable → navigates to entity |

### Actions
- Click alert → navigate to entity (deep-link) + mark as read
- "Mark all read" button in panel header
- "View all alerts" link → `/alerts`

### Empty State
"You're all caught up — no new alerts."

### Access Restrictions
Engineers see no bell (NONE for alerts data type). Other roles see only their own alerts.

---

## Screen: Alert List Page
**Route:** `/alerts`
**Audience:** CEO, CTO, DM, PM, Finance, HR (Engineer: no access)
**Layout:** Full-width list with filter bar.

### Components
- Filters: type dropdown, severity dropdown, read/unread/dismissed toggle
- Bulk "Mark all read" button
- Alert list sorted by created_at DESC

### Data Displayed

| Field | Notes |
|---|---|
| Type badge | CONTRACT_EXPIRY, BENCH_DURATION, etc. |
| Severity | Color-coded badge |
| Title | Bold if unread |
| Message | Truncated |
| Entity Link | "View Project" / "View Resource" deep-link |
| Timestamp | Full date + time |
| Read/Dismiss buttons | Per row |

### Actions
- Click alert row → mark as read + navigate to entity
- Mark as read (individual)
- Dismiss (individual)
- Bulk mark all read

### Empty State
"No alerts to show. Adjust filters or check back later."

### Access Restrictions
Each user sees only their own alerts.

---

## Screen: SystemConfig Admin
**Route:** `/admin/system-config`
**Audience:** CEO, CTO only
**Layout:** Settings table.

### Components
- Key-value form table: each config key shows label, current value, description, edit field
- Save button per row or bulk save
- Last updated timestamp per key

### Data Displayed

| Key | Label | Current Value | Description |
|---|---|---|---|
| alert.contract_expiry_days | Contract Expiry Warning (days) | 30 | Days before contract end for first alert |
| alert.contract_expiry_urgent_days | Contract Expiry Urgent (days) | 7 | Days for urgent alert |
| alert.bench_threshold_days | Bench Alert After (days) | 7 | Days on bench before alert |
| alert.utilization_threshold_pct | Utilization Alert Below (%) | 70 | Threshold for company utilization alert |
| system.working_days_per_month | Working Days / Month | 22 | Used in revenue calculations |
| system.working_hours_per_day | Working Hours / Day | 8 | Used in revenue calculations |
| system.default_currency | Default Currency | INR | Default for new projects |

### Actions
- Edit value → validate → PUT /api/system-config/:key
- Cancel edit → revert to saved value

### Access Restrictions
CEO and CTO only.
