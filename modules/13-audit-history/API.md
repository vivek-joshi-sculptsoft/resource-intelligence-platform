# Module 13: Audit History — API Endpoints

## Phase 1 (Logging Infrastructure — No User-Facing Endpoints)

Phase 1 provides only the internal audit logging wrapper used by all other modules. There are no user-facing API endpoints in Phase 1. The wrapper is a server-side function (not an HTTP endpoint) that must be called by every write operation.

### Internal Audit Logging Wrapper (not an HTTP endpoint)

```
auditLog({
  entity_type: string,
  entity_id: uuid,
  action: CREATE | UPDATE | DELETE,
  changes: [{ field_name, old_value, new_value }],
  changed_by: user_id,
  changed_at: timestamp (= now())
})
```

For UPDATE: pass one entry per changed field.
For CREATE: pass one entry per field with old_value = null.
For DELETE: pass `field_name = null`, `old_value = serialized entity state`.

---

## Phase 3 Endpoints

### GET /api/audit-logs
**Description:** Query audit history with filters.
**Auth:** CEO, CTO (ALL); DM (OWN_PORTFOLIO entities only); PM (OWN_PORTFOLIO entities only)
**Scope:** ALL for CEO/CTO; OWN_PORTFOLIO for DM/PM (filtered by their project assignments)
**Response:** Paginated:
```json
[{
  "id": bigint,
  "entity_type": string,
  "entity_id": uuid,
  "entity_name": string,   // resolved display name for the entity
  "action": string,
  "field_name": string,
  "old_value": string,
  "new_value": string,
  "changed_by": { "id", "name" },
  "changed_at": timestamp
}]
```
**Notes:** `?entity_type=Assignment&entity_id=<uuid>&changed_by=<uuid>&start_date=<date>&end_date=<date>&page=1&limit=50`

---

### GET /api/audit-logs/:entityType/:entityId
**Description:** Full audit history for one specific entity record.
**Auth:** CEO, CTO (ALL); DM/PM (own portfolio entities only)
**Scope:** Per role
**Response:** All audit rows for the entity sorted by changed_at DESC.

---

### GET /api/audit-logs/:entityType/:entityId/point-in-time
**Description:** Reconstruct entity state as of a given date.
**Auth:** CEO, CTO only
**Scope:** ALL
**Query:** `?date=<ISO-date>`
**Response:** Reconstructed entity state as a JSON object.
**Notes:** Algorithm per FSD §13: get current state, apply all changes after target date in reverse order (set field = old_value).
