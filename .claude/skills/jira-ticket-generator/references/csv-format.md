# JIRA CSV Import Format

## Column Mapping

When generating CSV for JIRA import, use these exact column headers. JIRA maps them automatically during import.

```csv
Summary,Issue Type,Description,Priority,Labels,Component,Story Points,Sprint,Epic Link,Depends On
```

### Column Definitions

| Column | JIRA Field | Values | Notes |
|---|---|---|---|
| Summary | Summary | Story title | Max 255 chars |
| Issue Type | Issue Type | Epic / Story / Sub-task / Task | Must match JIRA project config |
| Description | Description | Full description + acceptance criteria | Supports JIRA markdown |
| Priority | Priority | Blocker / Critical / Major / Minor / Trivial | Maps to P0-P4 |
| Labels | Labels | Comma-separated: backend,frontend,phase-1 | No spaces around commas |
| Component | Component/s | Module name: allocation-tracking | Must pre-exist in JIRA |
| Story Points | Story Points | 1 / 2 / 3 / 5 / 8 | Fibonacci |
| Sprint | Sprint | Sprint 1 / Sprint 2 / Backlog | Must pre-exist in JIRA |
| Epic Link | Epic Link | Epic summary text | Links story to its epic |
| Depends On | Linked Issues (blocks) | Summary of blocking story | Creates "is blocked by" link |

### Description Format

Use the format matching the user's description format preference (question 6 from the preference questionnaire). Team-managed / next-gen Jira projects use markdown; company-managed / classic projects use wiki markup.

**Markdown format (team-managed projects):**

```
## Context (read before starting)

* `modules/{mod}/API.md` — endpoint definitions
* `modules/{mod}/REQUIREMENTS.md` — validation rules

**As a {role}**, I want to {capability} so that {benefit}.

## Acceptance Criteria

- [ ] {criterion 1}
- [ ] {criterion 2}
- [ ] {criterion 3}

## Out of Scope

* {what this story does NOT cover}

**Depends On:** {story titles}
```

**Wiki markup format (company-managed projects):**

```
h3. Context (read before starting)
* {{modules/{mod}/API.md}} — endpoint definitions
* {{modules/{mod}/REQUIREMENTS.md}} — validation rules

h2. As a {role}, I want to {capability} so that {benefit}.

h3. Acceptance Criteria
* {criterion 1}
* {criterion 2}
* {criterion 3}

h3. Out of Scope
* {what this story does NOT cover}

*Depends On:* {story titles}
```

### Priority Mapping

| Agent Priority | JIRA Priority |
|---|---|
| P0 — Blocker | Blocker |
| P1 — Critical | Critical |
| P2 — Major | Major |
| P3 — Minor | Minor |
| P4 — Trivial | Trivial |

### Size → Story Points

| Agent Size | Story Points |
|---|---|
| XS | 1 |
| S | 2 |
| M | 3 |
| L | 5 |
| XL | 8 |

---

## Example CSV Row (Markdown format)

```csv
"Assignment CRUD — create, read, update, release with validations",Story,"## Context (read before starting)

* `modules/05-allocation-tracking/API.md` — endpoint definitions
* `modules/05-allocation-tracking/REQUIREMENTS.md` — validation rules
* `shared/ACCESS-MATRIX.md` — role-based access

**As a project manager**, I want to create and manage resource assignments so that I can track team allocation across projects.

## Acceptance Criteria

- [ ] GET /api/assignments returns paginated list filtered by project, resource, status
- [ ] POST /api/assignments creates with allocation_pct, billability_pct, shadow, dates
- [ ] PUT /api/assignments/:id updates any field with validation
- [ ] Billability cannot exceed allocation (hard block)
- [ ] Shadow assignments must have 0% billability
- [ ] Over-allocation triggers warning (soft, not blocking)
- [ ] All changes logged to audit log

## Out of Scope

* Financial calculations on assignments (handled by financial module)
* Bulk assignment operations (Phase 2)

**Depends On:** Project CRUD, Resource CRUD, Auth middleware",Critical,"backend,phase-1,sprint-2,must-have",allocation-tracking,5,Sprint 2,"Allocation Tracking","Project CRUD"
```

---

## Import Steps (JIRA)

1. Go to JIRA → Project → Import Issues → CSV
2. Upload the generated CSV file
3. Map columns (JIRA auto-maps most standard column names)
4. For "Epic Link" — select "Epic Name" mapping
5. For "Depends On" — select "Linked Issues (blocks)" or import separately
6. Preview and import
7. After import, manually verify epic linking and dependencies

---

## Pre-Import Checklist

Before importing, ensure these exist in JIRA:
- [ ] Project created with correct issue types (Epic, Story, Sub-task, Task)
- [ ] Components created (one per module name)
- [ ] Sprints created in the board
- [ ] Custom field "Story Points" enabled
- [ ] Labels don't need pre-creation (JIRA auto-creates them)

---

## Alternative: JSON Format for JIRA API

For programmatic creation via JIRA REST API:

```json
{
  "fields": {
    "project": { "key": "PROJECT_KEY" },
    "summary": "Assignment CRUD with validations",
    "issuetype": { "name": "Story" },
    "description": "...",
    "priority": { "name": "Critical" },
    "labels": ["backend", "phase-1"],
    "components": [{ "name": "allocation-tracking" }],
    "customfield_10016": 5,
    "customfield_10014": "EPIC-KEY"
  }
}
```

Note: `customfield_10016` for Story Points and `customfield_10014` for Epic Link vary by JIRA instance. User must check their JIRA's field IDs.
