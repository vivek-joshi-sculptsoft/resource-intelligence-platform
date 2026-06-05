# Module 13: Audit History — Screen Specifications

## Phase 1

No UI screens. Phase 1 implements only the server-side audit logging infrastructure. No user-visible screens.

---

## Phase 3 Screens

## Screen: Audit Log Viewer
**Route:** `/audit`
**Audience:** CEO, CTO (full history); DM, PM (own portfolio entities only)
**Layout:** Full-width table with filter bar.

### Components
- Entity type filter dropdown: All / Assignment / Project / Resource / Milestone / Invoice / NonHumanCost
- Changed By user filter dropdown
- Date range filter (start/end date)
- Search by entity name or ID
- Audit table sorted by changed_at DESC

### Data Displayed

| Field | Source | Notes |
|---|---|---|
| When | AuditLog.changed_at | Full date + time |
| Who | changed_by.name | |
| Entity Type | AuditLog.entity_type | Badge |
| Entity | Resolved entity name | Link to entity detail |
| Action | AuditLog.action | CREATE / UPDATE / DELETE badge |
| Field Changed | AuditLog.field_name | |
| Old Value | AuditLog.old_value | Formatted / truncated |
| New Value | AuditLog.new_value | Formatted / truncated |

### Actions
- Click entity name → navigate to current entity detail
- Filter controls update table
- Export (future scope)

### Empty State
"No audit log entries match your filters."

### Access Restrictions
CEO and CTO see all history. DM and PM see only entities within their portfolio scope.

---

## Screen: Change History Panel (within Entity Detail Views)
**Route:** Embedded tab/section within `/projects/:id`, `/resources/:id`, `/projects/:id/assignments` etc.
**Audience:** CEO, CTO, DM, PM (own portfolio)
**Layout:** Compact timeline or table at bottom of entity detail.

### Components
- List of last 20 changes for this entity
- Field name, old value → new value, who changed it, when

### Data Displayed

| Field | Notes |
|---|---|
| Timestamp | Relative ("3 days ago") |
| Changed By | User name |
| Field | e.g., "allocation_pct" |
| Change | "60% → 80%" |

### Actions
- "View full history" → `/audit?entity_type=X&entity_id=Y`

### Empty State
"No changes recorded yet."

---

## Screen: Point-in-Time Reconstruction (Admin Tool)
**Route:** `/audit/reconstruct`
**Audience:** CEO, CTO only
**Layout:** Simple query form + result display.

### Components
- Entity Type dropdown
- Entity ID input
- Target Date picker
- "Reconstruct" button
- Result: JSON or formatted entity state display

### Actions
- Submit → GET /api/audit-logs/:entityType/:entityId/point-in-time?date=<date>
- Display reconstructed entity state

### Empty State
"Enter an entity type, ID, and date to reconstruct its state."

### Access Restrictions
CEO and CTO only.
