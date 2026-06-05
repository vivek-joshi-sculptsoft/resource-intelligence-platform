# Product Requirements Document

## Resource Intelligence & Project Economics Platform

*Operational visibility for IT services — resources, projects, clients, and financials in one place.*

| | |
|---|---|
| **Version** | 1.1 |
| **Date** | June 2026 |
| **Status** | Draft — Revision 1 |
| **Confidentiality** | Internal Use Only |

---

## 1. Executive Summary

This platform replaces the current Google Sheets-based system used to track resource allocations, project delivery, and client billing across the organization. It provides a single, role-aware interface where delivery managers, project managers, leadership, HR, and finance can see real-time data about who is working on what, at what cost, and at what margin.

The system is designed for an IT services company with approximately 30–40 active resources, managing multiple clients with concurrent projects across three engagement models: Fixed Price, Time & Material, and Client Onboarding. It supports multi-currency billing with INR normalization for all internal reporting.

> **Core Problem**
> Resource allocations, billability, shadow utilization, and project financials are tracked in disconnected spreadsheets. This creates delayed visibility, manual reconciliation overhead, and invisible cost leakage — particularly from shadow resources, non-human project costs, and bench time.

---

## 2. Objectives & Success Criteria

| Objective | Success Criteria |
|---|---|
| Centralized resource tracking | 100% of active resources and their allocations managed in-system, zero reliance on spreadsheets |
| Real-time utilization visibility | Any stakeholder can see current company-wide and individual billable utilization without asking anyone |
| Shadow cost transparency | Shadow resource effort is tracked and reflected in true project margin calculations |
| Complete project cost picture | Non-human costs (tools, cloud, devices) tracked alongside resource costs for accurate margin |
| Proactive planning | Upcoming resource releases visible 30/60/90 days out, bench resources identified immediately |
| Financial accuracy | Projected revenue (from billability) and actual revenue (from invoices) tracked separately with margin for both |
| Faster decision making | Resource allocation decisions informed by data, not tribal knowledge or stale spreadsheets |

---

## 3. User Roles & Personas

| Role | Primary Use | Key Decisions | Data Sensitivity |
|---|---|---|---|
| CEO | Company-wide health dashboard | Strategic direction, client relationships | Full access to all data |
| CTO | Resource allocation, delivery oversight | Who goes where, capacity planning | Full access to all data |
| Delivery Manager | Portfolio management across assigned projects | Resource allocation, release planning, bench management | All data for their portfolio; CTC/margins configurable |
| Project Manager | Day-to-day project resource management | Allocation setup, non-human cost entry, milestone tracking | Project-level allocations and billability; no CTC or margins |
| Finance | Billing, invoicing, cost tracking | Invoice generation with exchange rates, margin analysis | Full financial data: CTC, billing rates, margins, exchange rates |
| HR | Resource profiles, availability, bench tracking | Onboarding, skill mapping | Resource profiles and availability; no financial data |
| Engineer | Personal assignments, worklog entry | Daily worklog hours (when enabled) | Own assignments, own worklogs, company-wide resource availability |

> **Access Model**
> Sensitive data (CTC, loaded costs, billing rates, margins) is visible only to CEO, CTO, and Finance by default. Access for other roles is configurable per data type. Resource availability (who is free, who is on which project) is visible to all users including employees.

---

## 4. Module-Wise Feature Descriptions

### 4.1 Client Management

Clients are the top-level entity. Every project belongs to a client, and every financial metric rolls up to the client level.

| Capability | Details |
|---|---|
| Client Profile | Name, industry, primary point of contact, engagement start date, notes |
| Multi-Project View | A client can have multiple active projects of different types (FP, T&M, Onboarding) simultaneously |
| Client Dashboard | Consolidated view: total active resources deployed, total monthly billing (INR), total cost, aggregate margin, project count by type |
| Client History | Revenue and engagement trends since the client was added (built organically from transactional data) |

### 4.2 Project Management

Projects are the operational unit. Each project has a type that determines its billing model, delivery structure, and tracking mechanics.

> **Project-Level Settings**
> Every project has a billing currency (USD, EUR, GBP, INR, etc.). All internal reporting converts to INR using the exchange rate entered manually at invoice time. Projects can also optionally enable or disable the employee worklog feature.

#### 4.2.1 Fixed Price Projects

| Attribute | Details |
|---|---|
| Contract Value | Total fixed price for the project, specified in the project's billing currency |
| Milestones | Custom milestones with individual payment amounts (not necessarily equal). Can be modified during the project. |
| Milestone Lifecycle | Planned → Delivered → Approved by Client → Invoiced → Paid. Each transition tracked with timestamp. |
| Timeline | Planned start and end dates per milestone. Delivery delay flagged when actual exceeds planned. |
| Revenue Recognition | Actual revenue = invoice amount (in billing currency, converted to INR). Projected revenue derived from billability of assigned resources. |

#### 4.2.2 Time & Material Projects

| Attribute | Details |
|---|---|
| Billing Model | Billed based on actual resource hours consumed. Rate is per-resource and per-project (fully variable). Specified in project billing currency. |
| Contract End Date | Tracked for expiry alerts and renewal planning |
| Invoicing Flow | Monthly timesheets submitted to client → Client approves → Invoice raised with actual amount and exchange rate → INR equivalent recorded. |
| Revenue | Projected = billability % × billing rate. Actual = invoice amount entered during invoicing. |

#### 4.2.3 Client Onboarding Projects

| Attribute | Details |
|---|---|
| Nature | Dedicated resources embedded at the client. Functions similarly to T&M but resources are exclusive. |
| Contract End Date | Tracked for expiry alerts |
| Leave Impact | Unlike FP and T&M, leaves directly affect billing. System accounts for this in projected revenue. |
| Invoicing | Same flow as T&M. Invoice amount is actual revenue; billability-based calculation is projected. |

> **Across All Project Types**
> Every project tracks: assigned resources with allocation %, billability %, shadow flag, and planned end dates. Project-level cost = resource costs + non-human costs. Revenue has two views: projected (from billability) and actual (from invoices). Margin is calculated for both.

### 4.3 Resource Management

A resource is any person in the organization who can be assigned to projects.

| Attribute | Details |
|---|---|
| Profile | Name, employee ID, designation, date of joining, reporting manager |
| Technical Expertise | Attached to designation. Example: "Tech Lead — Python Backend", "Senior Developer — React". Can be overridden per project at the assignment level. Non-technical roles may not have this. |
| Tags | Flexible labels: skills, domain experience, certifications, past client exposure. Examples: "AWS Certified", "Healthcare Domain", "Worked with Client A". |
| Loaded Cost | CTC + overhead costs. Company's true cost for this resource. Restricted to CEO, CTO, Finance. |
| Current Assignments | All active project assignments with allocation %, billability %, shadow flag, and planned end date per project |
| Total Allocation | Sum of allocation % across all projects. Over 100% = over-allocation risk. Under capacity = spare availability. |

### 4.4 Allocation & Billability Tracking

This is the operational core. It captures who is working on what, how much of their time is allocated, and how much is billable.

> **Key Distinction**
> Allocation % and Billability % are independent. A resource can be 100% allocated to a project but only 50% billable (the client pays for half). The gap represents cost absorbed by the company. This separation is fundamental to accurate margin calculation.

#### Per-Resource Per-Project Assignment

| Field | Description | Example |
|---|---|---|
| Allocation % | How much of the resource's total capacity is consumed by this project | 60% |
| Billability % | How much of their time on this project is billed to the client | 50% |
| Shadow Flag | Whether the resource is working without the client's knowledge (not billed) | Yes / No |
| Billing Rate | Client-specific rate in the project's billing currency. Fully variable. | $45/hr |
| Start Date | When this resource's assignment begins | 01 Jul 2026 |
| End Date (Optional) | When the assignment ends. If set, resource auto-releases on this date. If blank, runs indefinitely until manually changed. | 31 Mar 2028 |

#### Recurring Allocation Model

> **How It Works**
> Allocations are set once and automatically carry forward month after month. PMs do NOT re-enter allocations monthly. An allocation runs from its start date until its end date (if set) or until a PM explicitly changes or removes it. If a resource is still needed beyond the original end date, the PM must explicitly extend the end date. This supports long-term assignments spanning more than a year with zero monthly overhead.

| Aspect | Details |
|---|---|
| Auto-Carry Forward | Once set, allocations persist automatically. No monthly re-entry needed. |
| Auto-Release | When an assignment's end date is reached, the system automatically removes the allocation and the resource becomes available. |
| Mid-Period Revisions | PMs can change allocation %, billability %, or dates at any time. ~25% of assignments change mid-month. |
| Visibility | DMs see all updates for their assigned projects. CTO/CEO see everything. |
| Change Logging | Every update is timestamped and logged. Old values preserved for historical reconstruction. |

#### Shadow Resources

A shadow resource is someone doing actual work on a project without being billed to the client. Their allocation % reflects real effort, but billability is 0%. The system tracks these explicitly so leadership can see the true delivery cost versus what the client pays for.

### 4.5 Non-Human Project Costs

Beyond resource costs, projects incur expenses on tools, cloud services, devices, and third-party subscriptions. These must be tracked against the project for accurate margin calculation.

| Field | Description | Example |
|---|---|---|
| Date | When the cost was incurred | 15 Jul 2026 |
| Description | What the cost is for | Claude API usage for code review |
| Category | Cost type for grouping and reporting | AI Tools / Cloud / Devices / License / Other |
| Amount | Cost in original currency | $200 |
| Currency | ISO 4217 code | USD |
| Exchange Rate | Manually entered. Auto 1.0 for INR. | 83.50 |
| Amount INR | Computed: amount × exchange rate | ₹16,700 |
| Recurring | One-time or monthly recurring cost | One-time / Monthly |
| Recurring End Date | For monthly costs, when the recurrence stops | 31 Dec 2026 |

> **Who Can Add Non-Human Costs**
> PMs, DMs, CTO, CEO, and Finance can add non-human costs to projects. Employees cannot. These costs flow into the project's total cost and affect both projected and actual margin calculations.

### 4.6 Utilization Dashboards

Dashboards provide at-a-glance visibility at every level. All metrics derived from live allocation and billability data.

| Level | Key Metrics | Audience |
|---|---|---|
| Company-Wide | Overall billable utilization %, total bench count, total shadow allocation, projected vs actual revenue summary | CEO, CTO |
| Delivery Manager | Aggregate utilization for assigned projects, resource availability, delivery delays | DMs, CTO |
| Client | Total resources deployed, billing (INR), cost, margin (if authorized), project breakdown | CEO, CTO, Finance |
| Project | Resource list with allocation/billability %, resource + non-human costs vs revenue, milestone status, shadow exposure | PMs, DMs |
| Individual | Total allocation, billability breakdown, assignment history, upcoming release date | DMs, HR, the resource themselves |

### 4.7 Financial Tracking

Connects resource costs, non-human costs, billing rates, and invoice data to give accurate margin visibility. All internal financials are in INR.

#### Cost Calculation

```
Total Project Cost = Resource Costs (Loaded Cost × Allocation %) + Non-Human Costs (INR)
```

Non-human costs are summed from all line items logged against the project (one-time + active recurring), converted to INR via their individual exchange rates.

#### Revenue: Projected vs Actual

| Revenue Type | Source | Purpose |
|---|---|---|
| Projected Revenue | Calculated from billability % × billing rate × working days. Converted to INR. | Forecasting, planning, expected income |
| Actual Revenue | The invoice amount entered during invoicing. Original currency + manually entered exchange rate = INR equivalent. | True financial reporting, actual margin |

#### Margin

```
Projected Margin = Projected Revenue (INR) − Total Project Cost
Actual Margin = Actual Revenue (invoice INR) − Total Project Cost
```

Both are tracked. Leadership can compare projected vs actual to identify invoice-time adjustments, discounts, or scope changes affecting revenue.

#### Multi-Currency & Invoicing

| Attribute | Details |
|---|---|
| Project Billing Currency | Set at project level (USD, EUR, GBP, INR, etc.). All billing rates for resources on this project are in this currency. |
| Invoice Amount | Entered in the project's billing currency at the time of invoicing. This is the actual revenue. |
| Exchange Rate | Manually entered at invoice time. Applied to convert billing currency to INR. |
| INR Equivalent | Automatically calculated: invoice amount × exchange rate. Shown in UI alongside original amount. |
| Internal Reporting | All dashboards, margins, and financial summaries are in INR. |

#### Invoicing Visibility

| Project Type | Workflow |
|---|---|
| Fixed Price | Per-milestone: Delivered → Approved → Invoiced (amount + exchange rate entered) → Paid. Outstanding receivables tracked in INR. |
| T&M / Onboarding | Monthly: Timesheet Submitted → Approved → Invoice Raised (amount + exchange rate entered). Status tracked per month. |

### 4.8 Bench & Availability Forecasting

Bench = resources with 0% total allocation. Bench time is direct cost with zero revenue offset.

| Capability | Details |
|---|---|
| Current Bench | List of all resources at 0% allocation with duration on bench and daily bench cost |
| Upcoming Availability | Resources with assignment end dates in 30 / 60 / 90 days. Auto-release happens on the end date. |
| Partial Availability | Resources under 100% total allocation — spare capacity that can be utilized |
| Bench Cost | Loaded cost per day × days on bench. Visible at individual and aggregate level. |
| Early Release | Logged as a resource event when someone is released before planned end date. Feeds availability pool. |

> **Visibility**
> Resource availability (bench status, upcoming releases, partial availability, project names) is visible to ALL users including employees. Anyone can see who is free or freeing up without asking a manager.

### 4.9 Employee Worklog

A lightweight, optional daily time-logging feature. Employees record how many hours they spent on each assigned project per day. Deliberately decoupled from billing, allocation, and invoicing — it does not block or feed into any financial workflow.

| Attribute | Details |
|---|---|
| Scope | Per-project, per-day. Employee selects a project from their active assignments and logs hours worked. |
| Who Logs | Employees log their own hours only |
| Who Views | PMs can view worklogs for their projects. DMs, CTO, CEO can view across their visibility scope. |
| Project-Level Toggle | Worklog can be enabled or disabled per project. When disabled, employees don't see the worklog option. |
| Decoupled by Design | Worklog data does NOT affect allocation %, billability %, invoicing, or any automated process. Purely informational. |
| Fields | Date, Project, Hours, Optional note/description |

> **Why Decoupled?**
> Worklog is a self-reporting accountability tool, not a billing input. Tying it to invoicing would create friction and data entry pressure. By keeping it separate, teams can adopt it at their own pace without affecting project operations.

### 4.10 Alerts & Notifications

All alerts are in-app only (no email). Thresholds are configurable.

| Alert | Trigger | Audience |
|---|---|---|
| Contract Expiry | T&M or Onboarding contract end date within 30 days | DM, CTO, CEO |
| Bench Duration | Resource at 0% allocation for more than configured days (default: 7) | DM, CTO, HR |
| Over-Allocation | Resource total allocation exceeds 100% | DM, PM |
| Milestone Overdue | FP milestone delivery date passed without status change | PM, DM |
| Utilization Drop | Billable utilization falls below configurable threshold (e.g. 70%) | CTO, CEO |
| Assignment Auto-Release | Resource assignment end date reached; resource automatically released | PM, DM |
| Margin Erosion | FP project cost exceeding proportional milestone value | *Future Scope* |

---

## 5. Business Rules & Key Definitions

| Term | Definition |
|---|---|
| Allocation % | Percentage of a resource's total monthly capacity consumed by a specific project. Set once, carries forward automatically until changed or end date reached. |
| Billability % | Percentage of time on a project billed to the client. Independent of allocation. Can be lower than allocation but not higher. |
| Shadow Resource | Resource performing actual work but not billed. Allocation > 0%, Billability = 0%. Tracked for true margin. |
| Loaded Cost | CTC + all overhead (seat, licenses, management, benefits). Used for all cost calculations. |
| Non-Human Cost | Project expenses beyond resource costs: tools (Claude, ChatGPT), cloud infrastructure, test devices, third-party licenses. Logged as line items with currency and exchange rate. |
| Bench | Resource with 0% total allocation. Available but generating cost with no revenue. |
| Projected Revenue | Revenue calculated from billability % × billing rate × working days. What you expect to earn before invoicing. |
| Actual Revenue | The invoice amount entered during invoicing. What the client actually pays. Source of truth for reporting. |
| Projected Margin | Projected Revenue − Total Cost (resource + non-human + shadow). Forecast profitability. |
| Actual Margin | Actual Revenue (invoice INR) − Total Cost. True profitability after invoicing. |
| Utilization Rate | Billable allocation ÷ total available capacity, as a percentage. |
| Exchange Rate | Manually entered at invoice/cost entry time to convert billing currency to INR. Not auto-fetched. |
| Worklog | Optional daily hours logged by employees per project. Informational only — decoupled from billing. |
| Auto-Release | When an assignment's end date is reached, the system automatically removes the allocation. |

---

## 6. Role-Based Access Matrix

Default access levels. Configurable by CEO, CTO, and system admins.

**V** = View, **E** = Edit, **—** = No Access, **⚙️** = Configurable

| Data Type | CEO | CTO | DM | PM | Finance | HR | Engineer |
|---|---|---|---|---|---|---|---|
| Client Profiles | V/E | V/E | V* | V* | V | V | — |
| Project Details | V/E | V/E | V/E* | V/E* | V | V | — |
| Resource Profiles | V/E | V/E | V* | V* | V | V/E | V† |
| Allocation % | V/E | V/E | V* | V/E* | V | V | V† |
| Billability % | V/E | V/E | V* | V/E* | V | — | — |
| Billing Rates | V | V | ⚙️ | — | V | — | — |
| CTC / Loaded Cost | V | V | — | — | V | — | — |
| Project Margin | V | V | ⚙️ | — | V | — | — |
| Non-Human Costs | V/E | V/E | V/E* | V/E* | V/E | — | — |
| Shadow Assignments | V | V | V* | V* | V | — | — |
| Resource Availability | V | V | V | V | V | V | V |
| Bench Data | V | V | V | — | V | V | V |
| Invoicing / Exchange Rate | V | V | — | — | V/E | — | — |
| Worklogs | V | V | V* | V* | — | — | V/E† |
| Alerts | V | V | V* | V* | V* | V* | — |

**\*** = own portfolio/projects only · **†** = own data only · **⚙️** = configurable

---

## 7. Phasing & Roadmap

Three phases, each delivering standalone value.

### Phase 1 — Foundation & Visibility

*Replaces Google Sheets entirely. The operational backbone.*

| Module | Scope |
|---|---|
| Client Management | Full client profiles with multi-project support |
| Project Management | All three project types with billing currency |
| Resource Management | Profiles, designations, technical expertise, tags |
| Allocation & Billability | Recurring allocation model with auto-release, shadow flagging, change logging |
| Utilization Dashboards | Company-wide, per-DM, per-client, per-project, per-resource views |
| Resource Availability | Visible to all users including employees, with project names |
| Employee Worklog | Optional per-project daily hour logging, project-level toggle, decoupled from billing |

### Phase 2 — Financial Engine

*Adds the money layer. Projected vs actual revenue, multi-currency, and full margin visibility.*

| Module | Scope |
|---|---|
| Resource Costing | Loaded cost (CTC + overhead) per resource |
| Non-Human Costs | Line items per project: tools, cloud, devices, licenses. Currency + exchange rate. One-time and recurring. |
| Billing Rates | Variable rates per resource per project in project billing currency |
| Revenue Tracking | Projected (from billability) and actual (from invoices) tracked separately |
| Multi-Currency Invoicing | Invoice in billing currency + manual exchange rate = INR equivalent. UI shows both. |
| Margin Calculation | Projected and actual margin per project, per client, company-wide. Includes shadow + non-human costs. |
| Milestone Tracking | Full lifecycle: Planned → Delivered → Approved → Invoiced (with amount + rate) → Paid |
| Financial Dashboards | Revenue, cost, margin views for Finance, CEO, CTO |

### Phase 3 — Intelligence & Alerts

*Proactive insights and access controls. Turns data into decisions.*

| Module | Scope |
|---|---|
| Bench Management | Current bench list with cost, bench duration tracking |
| Availability Forecasting | 30/60/90 day upcoming release view (auto-release aware), partial availability identification |
| Alerts Engine | Contract expiry, over-allocation, milestone overdue, utilization threshold, bench duration, auto-release alerts |
| Role-Based Access | Configurable data sensitivity per role |
| Historical Queries | Point-in-time reconstruction: view system state as of any past date |

---

## 8. Assumptions & Constraints

### Assumptions

- The system is for internal use only. No multi-tenancy or external user access required.
- Scale is approximately 30–40 active resources.
- No historical data migration. System starts fresh and builds history from first use.
- Working days per month assumed at 22 (no holiday calendar in initial scope).
- All internal financial reporting is in INR. Exchange rates are entered manually, not auto-fetched.
- Clear hierarchy: CEO → CTO → DM → PM → Engineer. DMs assigned to fixed project sets.

### Explicitly Out of Scope

- Sales pipeline and pre-sales opportunity tracking
- Email notifications (in-app alerts only for all phases)
- Integration with external tools (HRMS, accounting software, Slack, etc.)
- Margin alerts on Fixed Price projects based on cost burn rate (parked for future)
- What-if scenario planner for resource reallocation (parked for future)
- Leave management or attendance tracking
- Automatic exchange rate fetching (manual entry only)
- Worklog-to-billing integration (worklogs are deliberately decoupled)

---

## 9. Open Questions & Parking Lot

| Item | Context | Status |
|---|---|---|
| Margin alerts for FP projects | Alert when accumulated cost exceeds proportional milestone value | Future Scope |
| What-if resource planner | Simulate financial impact of moving resources between projects | Future Scope |

---

## 10. Glossary

| Term | Definition |
|---|---|
| FP | Fixed Price — project with fixed scope, budget, timeline, milestone-based delivery |
| T&M | Time & Material — billed based on resource hours consumed |
| CTC | Cost to Company — total annual compensation of an employee |
| Loaded Cost | CTC plus overhead (seat, licenses, management). True per-resource cost. |
| DM | Delivery Manager — oversees a project portfolio and resource allocation decisions |
| PM | Project Manager — manages individual project execution and planning |
| Bench | State where a resource has zero project allocation |
| Shadow Resource | Working on a project but not billed to the client |
| Projected Revenue | Expected revenue calculated from billability and rates before invoicing |
| Actual Revenue | Invoice amount — what the client actually pays |
| INR | Indian Rupee — the standard currency for all internal reporting |
| Exchange Rate | Manually entered conversion rate from billing currency to INR at invoice time |
| Worklog | Optional daily hours logged by employees per project. Not connected to billing. |
| Auto-Release | System automatically removes allocation when assignment end date is reached |
| Non-Human Cost | Project expenses for tools, cloud, devices, or licenses — not resource salaries |

---

## Sign-Off

| Role | Name | Signature | Date |
|---|---|---|---|
| CEO | | | |
| CTO | | | |
| Delivery Manager | | | |
| Finance Lead | | | |
