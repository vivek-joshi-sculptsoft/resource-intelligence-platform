# PRD Structure & Template Guide

This reference guides PRD generation. The structure is NOT a fixed template — sections are chosen dynamically based on what emerged from the conversation.

---

## Core Principle

A PRD should be **scannable, precise, and role-aware.**

- **Scannable**: Tables over paragraphs. No walls of text. A CEO should skim the summary and phasing in 3 minutes. A developer should find business rules and get unambiguous definitions.
- **Precise**: Terms defined once, used consistently. Calculations explicit. Edge cases documented. "The system should handle billing" is not a requirement. "Revenue = billable hours × per-resource billing rate" is.
- **Role-aware**: Each stakeholder should see themselves in the document.

---

## Section Selection: How to Decide What Goes In

The PRD is assembled from a pool of section types. Pick sections based on what the conversation covered. The guiding question for each section: **"Did the brainstorming session produce meaningful content for this?"** If yes, include it. If not, skip it.

### Always Include (Foundation)

These sections appear in every PRD because every product needs them:

| Section Type | Purpose | Naming Guidance |
|---|---|---|
| Executive Summary | What, why, who — the 3-minute overview | Always called "Executive Summary" |
| Objectives & Success | What does "done" look like | "Objectives & Success Criteria", "Goals & KPIs", "Success Metrics" — pick what fits the tone |
| User Roles | Who uses it, what they care about, what they decide | "User Roles & Personas", "Stakeholders", "Actors & Permissions" |
| Assumptions & Scope | What's in, what's out, what's assumed true | "Assumptions & Constraints", "Scope & Boundaries", "Scope Definition" |
| Phasing / Roadmap | What to build first, second, third | "Phasing & Roadmap", "Release Plan", "Build Sequence", "Implementation Phases" |
| Glossary | Canonical term definitions | "Glossary", "Key Definitions", "Terminology" |

### Include When Relevant (Contextual)

Pick from these based on what the conversation revealed:

| Section Type | Include When... | Naming Examples |
|---|---|---|
| Feature Modules | Always — but the module NAMES are dynamic (see below) | Named after the actual functional areas discussed |
| Business Rules & Calculations | Financial calculations, complex logic, or state machines exist | "Business Rules", "Calculation Logic", "Core Formulas" |
| Access / Permissions Matrix | Multiple roles with different data visibility needs | "Role-Based Access Matrix", "Permissions Model", "Data Access Rules" |
| Data Model / Entity Relationships | Complex relationships between core entities | "Data Model", "Entity Relationships", "Information Architecture" |
| Workflows & Lifecycle | Entities go through multi-step state transitions | "Workflows", "Lifecycle Stages", "Process Flows" |
| Integration Requirements | System needs to connect with external tools | "Integrations", "External Systems", "API Requirements" |
| Alerts / Notifications | Proactive alerts or notification rules discussed | "Alerts & Notifications", "Notification Rules", "Event Triggers" |
| Compliance & Regulatory | Legal, regulatory, or industry compliance requirements | "Compliance", "Regulatory Requirements", "Legal Constraints" |
| Security Requirements | Authentication, encryption, data protection specifics | "Security Model", "Data Protection", "Security Requirements" |
| Reporting & Analytics | Specific reporting needs beyond dashboards | "Reporting", "Analytics Requirements", "Data & Insights" |
| Migration / Transition | Moving from an existing system, data migration needed | "Migration Plan", "Transition Strategy", "Data Migration" |
| Trust & Safety | Marketplace or platform with abuse/fraud risks | "Trust & Safety", "Abuse Prevention", "Content Moderation" |
| Billing & Pricing Model | Complex pricing, metering, or subscription logic | "Pricing Model", "Billing Logic", "Monetization" |
| Device / Hardware | IoT, firmware, physical device management | "Device Management", "Hardware Lifecycle", "Firmware & OTA" |
| Performance & Scale | Specific performance requirements or scale targets | "Performance Requirements", "Scale Considerations" |
| Open Questions | Unresolved items from the conversation | "Open Questions", "Parking Lot", "To Be Decided" |
| Sign-Off | Formal approval needed before development | "Sign-Off", "Approval" |
| Competitor Landscape | Research phase produced relevant competitive insights | "Competitive Landscape", "Market Context" |

### Feature Modules — Naming is Dynamic

The "Feature Modules" section is never called "Module-Wise Feature Descriptions." Each module is named after the actual functional area from the conversation:

**Example — IT services platform:**
- Client Management
- Project Management (with sub-sections per project type)
- Resource Management
- Allocation & Billability Tracking
- Utilization Dashboards
- Financial Tracking
- Bench & Availability Forecasting

**Example — E-commerce marketplace:**
- Seller Onboarding & Storefront
- Product Catalog & Inventory
- Order Lifecycle
- Payments & Settlements
- Buyer Experience
- Reviews & Ratings
- Dispute Resolution

**Example — Healthcare scheduling app:**
- Patient Registration
- Provider Profiles & Availability
- Appointment Booking
- Consultation & Notes
- Prescription Management
- Insurance & Billing
- Patient Communication

The module names should use the stakeholder's own language. If they said "bench" throughout the conversation, the section is "Bench & Availability" — not "Unallocated Resource Pool."

---

## Section Formatting (Consistent Across All Sections)

Regardless of which sections are included, follow these formatting patterns:

### Tables
Use tables wherever data is structured: capabilities, rules, roles, comparisons, timelines. Two-column tables (Label | Details) are the workhorse format. Use three columns when a third dimension adds value (e.g., Capability | Details | Example).

### Callout Boxes
Use for critical business rules, important distinctions, or warnings. Types:
- **Info/Key Concept** (blue): Core distinctions stakeholders must understand
- **Warning/Caution** (yellow): Things that can go wrong, access restrictions, edge cases
- **Cross-cutting Rule** (green): Rules that apply across multiple modules

### Formulas
When a calculation exists, display it prominently in a formula block — not buried in a paragraph. Include a concrete example with numbers.

### Collapsible Sections (HTML only)
Use when a module has variants or sub-types. Each variant gets a collapsible panel with a color-coded tag. In Word, use sub-headings instead.

### Phase Visualization
Use a visual timeline (HTML) or phase cards (Word) — not just a bulleted list. Each phase gets: label, title, one-line positioning, and feature checklist.

### Out-of-Scope Items
Display as visual tags/chips that are immediately scannable — not buried in paragraphs.

---

## Formatting by Output Type

### Word Document (.docx)
- Professional color palette: navy headers, light blue table headers, subtle borders
- Alternating row shading in tables
- Callout boxes with left-border accent
- Header/footer with document title, version, page numbers
- Cover page with title, subtitle, version, date, status, confidentiality
- Proper heading styles for TOC support
- Body text 11-12pt, table text 10-11pt
- Sign-off table at the end

### Interactive HTML
- Fixed sidebar navigation with section numbers and scroll tracking
- Progress bar at top
- Collapsible sections for variants
- Color-coded tags for categories
- Visual timeline for phasing
- Responsive (must work on mobile)
- Hover-highlighting on table rows, sticky headers
- Callout boxes with icons
- Clean typography — never generic

### Both Formats
- Content is identical between Word and HTML
- All tables contain the same data
- Business rules and definitions are consistent
- Phasing matches exactly

---

## Quality Checklist Before Delivery

Before delivering any PRD:

- [ ] Section headers reflect the actual domain, not generic template names
- [ ] Every user role from the discussion appears in the document
- [ ] Every functional area discussed has a corresponding module section
- [ ] All calculations have explicit formulas
- [ ] Terms are consistent (same word doesn't change meaning across sections)
- [ ] Out-of-scope items are documented, not silently omitted
- [ ] Phasing has clear rationale
- [ ] Open questions are captured
- [ ] A reader who wasn't in the brainstorming session can understand the document
- [ ] Sensitive data is flagged with access restrictions
- [ ] No sections exist that have no meaningful content (don't include empty placeholders)
