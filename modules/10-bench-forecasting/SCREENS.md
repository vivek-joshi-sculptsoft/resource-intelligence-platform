# Module 10: Bench & Availability Forecasting — Screen Specifications

## Screen: Resource Availability View
**Route:** `/availability`
**Audience:** All authenticated roles including Engineer
**Layout:** Four tabbed sections: Bench | Partially Available | Releasing Soon | Fully Allocated

### Components
- Tab bar: Bench / Partial / Releasing Soon / Fully Allocated
- 30 / 60 / 90 day filter (active on Releasing Soon tab)
- Search input: by resource name
- Summary bar: bench count, bench cost total (Phase 2, restricted)

### Section: Bench

| Field | Notes |
|---|---|
| Name | Link to profile (if role permits) |
| Designation | |
| Expertise | |
| Days on Bench | |
| Tags | Pill badges |
| Bench Cost (Phase 2) | Daily / Total — visible to CEO/CTO/Finance only |

### Section: Partially Available

| Field | Notes |
|---|---|
| Name | |
| Total Allocation % | |
| Spare Capacity % | |
| Current Projects | Project names |

### Section: Releasing Soon

| Field | Notes |
|---|---|
| Name | |
| Project | Project name |
| Allocation % | |
| Release Date | |
| Days Remaining | Countdown |

### Section: Fully Allocated

| Field | Notes |
|---|---|
| Name | |
| Total Allocation % | May show >100% if over-allocated |
| Projects | Project names |

### Actions
- Click resource name → resource profile (if role has access)
- Click project name → project detail (if role has access)
- Switch day-window filter (30/60/90) on Releasing Soon tab

### Empty State
Per section: "No resources currently on bench." / "No resources releasing in the next 30 days."

### Access Restrictions
Project names and allocation % visible to all. Billing rates, billability %, CTC, shadow status, bench cost NOT shown to Engineer or HR. Engineer sees their own name in availability sections.

---

## Widget: Bench Summary (within Company Dashboard)
**Route:** `/dashboard` — bench widget
**Audience:** CEO, CTO
**Layout:** Compact widget card.

### Components
- Bench count (large number)
- Expandable list of benched resource names with days on bench
- Total bench cost INR (Phase 2)
- Link to full availability view

### Access Restrictions
Bench cost visible to CEO and CTO only.
