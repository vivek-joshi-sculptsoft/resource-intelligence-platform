# Module 04: Resource Management

## Overview

A resource is any person in the organization who can be assigned to projects. This module manages resource profiles including designation, technical expertise, flexible tags, and availability. It also provides resource search and filtering for allocation decisions. The `loaded_cost_monthly` field is added in Phase 2 and restricted to CEO, CTO, and Finance. Resource deactivation cascades to release all active assignments.

## Phase

Phase 1 (without `loaded_cost_monthly`). Phase 2 adds the cost field.

## Dependencies

- Module 01 (Auth & Roles)

---

## Features

### Feature: Resource CRUD
**Description:** Create, view, update, and deactivate resource profiles.
**Acceptance Criteria:**
- [ ] Create resource: name (required), employee_id (required, unique), designation (required), technical_expertise, date_of_joining, reporting_manager (optional, self-referencing)
- [ ] Update any resource field
- [ ] Soft-delete resource (`is_active = false`) — never hard delete
- [ ] Deactivation cascades: all ACTIVE assignments released, resource cannot receive new assignments
- [ ] `loaded_cost_monthly` field visible/editable only to CEO, CTO, Finance (Phase 2)
- [ ] All changes audit logged (including `loaded_cost_monthly` changes)

### Feature: Tag Management
**Description:** Flexible label system for skills, domain experience, certifications.
**Acceptance Criteria:**
- [ ] Add one or more tags to a resource (e.g., "AWS Certified", "Healthcare Domain", "Worked with Client A")
- [ ] Remove a tag from a resource
- [ ] Tags are free-form strings — no predefined list
- [ ] Tags searchable in resource list filter

### Feature: Resource Profile View
**Description:** Full resource detail with assignments, availability, and history.
**Acceptance Criteria:**
- [ ] Show all resource fields (sensitive fields hidden per access control)
- [ ] Show all ACTIVE assignments with project name, allocation %, billability %, shadow flag, start/end dates
- [ ] Show total allocation % (sum across all ACTIVE assignments)
- [ ] Over-allocation indicator when total > 100%
- [ ] Show tags
- [ ] Show assignment history (released/auto-released)

### Feature: Resource List with Search and Filter
**Description:** Paginated, searchable list with multi-attribute filtering.
**Acceptance Criteria:**
- [ ] Filter by: designation, technical expertise, tags, availability (bench / partially available / fully allocated)
- [ ] Search by name or employee_id
- [ ] Show total allocation % for each resource in the list
- [ ] Sortable by name, designation, date_of_joining
- [ ] HR can see profiles but not financial fields

---

## Validations

| Rule | Condition | Error |
|---|---|---|
| Name required | name is blank | "Resource name is required" |
| Employee ID required | employee_id is blank | "Employee ID is required" |
| Employee ID unique | Duplicate employee_id | "This employee ID is already in use" |
| Designation required | designation is blank | "Designation is required" |
| Reporting manager loop | reporting_manager_id = self | "A resource cannot report to themselves" |

---

## Business Rules

- `loaded_cost_monthly` is the Phase 2 cost field — null in Phase 1, restricted to CEO/CTO/Finance
- Deactivation cascade: see FSD §14 edge case — "Resource deactivated while assigned"
- Designation resolution rule (FSD §11): `project_designation` if set else `resource.designation` — all views must respect this
- Access: HR has EDIT on resource_profiles (profiles); Engineer has VIEW SELF_ONLY; see `shared/ACCESS-MATRIX.md`
