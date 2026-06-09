# Gap Analysis Checklist

After reading the PRD, systematically check each category below. For every gap found, decide: resolve it yourself (standard architectural decisions), ask the stakeholder (business-impactful decisions), or document as an edge case (unlikely scenarios).

---

## 1. Entity Completeness

For every noun in the PRD that stores data:

- [ ] Is there an explicit entity for it, or is it embedded in another entity?
- [ ] Does it need a separate join table? (tags, permissions, multi-select attributes)
- [ ] Is there a system entity the PRD doesn't mention? (AuditLog, SystemConfig, Alert, Session)
- [ ] Does the entity need soft delete (is_active) or hard delete?
- [ ] Who creates this entity? Who can edit it? Who can delete it?
- [ ] What happens when this entity is deactivated/deleted but other entities reference it?

**Common missing entities the PRD won't mention:**
- AuditLog — if history/reconstruction is needed
- Alert/Notification — if the PRD mentions alerts
- SystemConfig — if the PRD mentions configurable thresholds
- Role/Permission tables — if the PRD uses role names as ENUMs
- File/Attachment — if documents can be uploaded
- Comment/Note — if entities have discussion threads
- Tag/Label — if flexible categorization is mentioned

---

## 2. Field-Level Gaps

For every attribute mentioned in the PRD:

- [ ] What is the exact data type and size?
- [ ] Is it required or optional?
- [ ] Does it have a default value?
- [ ] Is it unique? Unique within what scope?
- [ ] Is it computed or stored? If computed, what's the formula?
- [ ] What's the valid range? (min/max for numbers, min/max length for strings)
- [ ] Is it sensitive? (needs access restriction)
- [ ] Does it need indexing for search/filter performance?
- [ ] Can it change after creation, or is it immutable?
- [ ] If it's an ENUM, should it be a lookup table instead?

**Common field decisions the PRD leaves open:**
- Primary key type (UUID vs BIGINT)
- Timestamp precision (second vs millisecond)
- String encoding (UTF-8 always, but max byte length considerations)
- Money storage (DECIMAL precision, currency handling)
- Percentage storage (INTEGER 0-100 vs DECIMAL 0.00-1.00)

---

## 3. Relationship Gaps

For every "has many" or "belongs to" relationship:

- [ ] What's the exact cardinality? (1:1, 1:N, N:M)
- [ ] Is the FK nullable? (optional relationship)
- [ ] What happens on parent delete? (CASCADE, SET NULL, RESTRICT)
- [ ] Can the relationship change? (can a project be moved to a different client?)
- [ ] Are there constraints across relationships? (unique resource+project pair when active)
- [ ] Self-referencing relationships? (resource.reporting_manager → resource)

---

## 4. State Machine Gaps

For every entity with a status/lifecycle:

- [ ] Are all valid states listed? Or are there implied states?
- [ ] Which transitions are allowed? Draw the full transition map.
- [ ] Can states go backward? Which ones? Under what conditions?
- [ ] Which transitions are terminal (no further changes)?
- [ ] Who can trigger each transition? (role-based)
- [ ] What side effects fire on each transition?
- [ ] What happens to related entities on state change?
- [ ] Can multiple state changes happen simultaneously?
- [ ] Is there a "stuck" state? (entity can't progress due to missing data)

---

## 5. Calculation Gaps

For every metric, formula, or derived value:

- [ ] What are the exact input fields?
- [ ] What happens when inputs are null or zero?
- [ ] Division by zero handling?
- [ ] Rounding rules? (round up, round down, banker's rounding)
- [ ] Currency conversion — when and how?
- [ ] Time period boundaries — calendar month, rolling 30 days, custom period?
- [ ] Is it calculated on read (API computes) or stored (materialized, needs trigger/job)?
- [ ] At what level does it aggregate? (per-entity, per-parent, company-wide)
- [ ] Does historical recalculation work? (if a cost changes, do past margins update?)

---

## 6. Access Control Gaps

For every role mentioned in the PRD:

- [ ] What entities can they see? (scope: all, own portfolio, self only)
- [ ] What entities can they create/edit/delete?
- [ ] Which specific fields are hidden from them?
- [ ] Is access enforced at API level or just UI level?
- [ ] Are there configurable permissions? (admin can grant exceptions)
- [ ] What happens when a user's role changes? (immediate effect or end of session?)
- [ ] Can a user have multiple roles?
- [ ] Is there a super-admin that bypasses all restrictions?

---

## 7. Validation Gaps

For every business rule or constraint:

- [ ] Is it a hard block (prevent the action) or soft warning (allow but warn)?
- [ ] What's the exact error message?
- [ ] When is it checked? (on field change, on save, on submit)
- [ ] Client-side, server-side, or both?
- [ ] Can it be overridden by a higher-privilege role?
- [ ] Does it apply to creation only, or also to updates?

---

## 8. Scheduled Job Gaps

For every timed/automated process:

- [ ] How often does it run? (daily, hourly, weekly, on-demand)
- [ ] What time does it run? (timezone?)
- [ ] What does it process? (all records, or filtered subset)
- [ ] What happens if it fails mid-run? (retry, partial completion, rollback)
- [ ] What happens if two runs overlap?
- [ ] Does it produce alerts/notifications?
- [ ] Does it need to be idempotent? (safe to re-run)
- [ ] Who monitors it? Where are errors logged?

---

## 9. UI/View Gaps

For every dashboard or view:

- [ ] What data is shown? (exact fields, not vague "project details")
- [ ] What actions are available? (buttons, links, forms)
- [ ] What filters/sorting/pagination exist?
- [ ] What's the default sort order?
- [ ] Are there real-time updates or manual refresh?
- [ ] What does the empty state look like? (no data yet)
- [ ] What does the error state look like?
- [ ] Is it responsive/mobile-friendly?

---

## 10. Integration Gaps

For every external system connection:

- [ ] Which direction? (import, export, bidirectional)
- [ ] Real-time or batch?
- [ ] Authentication method? (API key, OAuth, webhook)
- [ ] Error handling? (retry, dead letter queue, alert)
- [ ] Data format? (JSON, CSV, XML)
- [ ] Rate limits?
- [ ] What if the external system is down?

---

## 11. Cross-Cutting Concerns

These apply to the entire system:

- [ ] Timezone handling — all UTC internally, convert on display?
- [ ] Multi-currency — store original + converted, or just one?
- [ ] Audit trail — what gets logged? How is history reconstructed?
- [ ] Data retention — how long is data kept? Archival strategy?
- [ ] Backup/recovery — any special considerations?
- [ ] Performance — any expected bottlenecks? (large dashboards, complex aggregations)
- [ ] Search — full-text search needed? On which fields?
- [ ] Bulk operations — can users import/export data in bulk?
- [ ] Concurrency — optimistic locking, pessimistic locking, or last-write-wins?

---

## Decision Framework

| Gap Type | Action | Example |
|---|---|---|
| Standard architectural | Decide and document | "Using UUID v4 for all PKs" |
| Has a clear best practice | Decide and document | "Soft delete via is_active flag" |
| Affects business behavior | Ask the stakeholder | "Can a milestone go from DELIVERED back to PLANNED?" |
| Multiple valid approaches | Decide, note trade-off | "Storing computed margins for performance; trade-off: need recalc trigger on cost change" |
| Unlikely scenario | Document as edge case | "If PM extends end_date after auto-release already happened: create new assignment" |
| Requires domain knowledge | Ask the stakeholder | "Do leaves affect billing for all project types or only onboarding?" |
