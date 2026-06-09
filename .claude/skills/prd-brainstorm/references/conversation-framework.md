# Conversation Framework

This reference helps you ask informed, domain-aware questions during the deep dive phase. It's organized by domain patterns — once you identify which pattern the project fits, use the corresponding question set as a starting point.

You will rarely use all questions from a domain. Pick the ones that are relevant based on what the stakeholder has already shared. Skip anything they've already answered.

---

## Domain Detection

Listen for these signals in the stakeholder's initial description to identify the domain pattern:

| Signal Words/Phrases | Likely Domain |
|---|---|
| resources, allocation, bench, utilization, billing, staffing, projects, contractors | Resource Management / Professional Services |
| orders, cart, checkout, products, catalog, inventory, shipping, SKU | E-Commerce / Retail |
| patients, appointments, records, prescriptions, compliance, HIPAA | Healthcare |
| listings, buyers, sellers, commission, trust, reviews, matching | Marketplace |
| tickets, incidents, SLA, escalation, resolution, knowledge base | Support / Helpdesk |
| leads, pipeline, deals, contacts, opportunities, CRM | Sales / CRM |
| content, publishing, editorial, workflow, approval, draft, review | Content Management |
| fleet, routes, drivers, deliveries, tracking, dispatch, ETAs | Logistics / Delivery |
| students, courses, enrollment, grades, curriculum, LMS | Education / EdTech |
| tenants, leases, properties, maintenance, rent, units | Property Management |
| candidates, interviews, hiring, job posts, applications, ATS | Recruitment / HR |
| transactions, accounts, ledger, reconciliation, compliance, audit | Finance / Accounting |
| devices, sensors, telemetry, firmware, alerts, monitoring, OTA | IoT / Hardware |
| API, rate limits, keys, usage, quotas, developer portal | Platform / API Product |
| subscribers, plans, tiers, usage, upgrades, churn, MRR | SaaS / Subscription |
| workflows, approvals, forms, automation, tasks, notifications | Internal Workflow Tool |

If the project spans multiple domains (common — e.g., a marketplace with logistics), identify the primary domain and use the secondary domain questions where relevant.

---

## Domain-Specific Deep Dive Questions

### Resource Management / Professional Services

**Business model clarity:**
- What types of engagements do you run? (fixed price, time-based, retainer, dedicated, hybrid?)
- How does billing work for each type? Same model or different per engagement type?
- What's the relationship between resource allocation and billing? Are they always 1:1, or can someone be allocated but not billed (or vice versa)?

**Resource complexity:**
- When you assign someone to a project, is it always full-time, or do you split people across projects? If split, how granular? (50-50, or down to 10% increments?)
- What defines a resource beyond their name? Role, seniority, skills, certifications, cost rate, billing rate?
- Do billing rates vary by client, project, resource, or some combination?

**Planning and forecasting:**
- How far ahead do you plan resource allocations? Weekly? Monthly? Quarterly?
- How often does the plan change after it's set?
- What happens when a project ends unexpectedly or a resource becomes available early?

**Financial visibility:**
- Who needs to see cost data vs. billing data vs. margin?
- How do you calculate profitability today? Per project? Per client? Per resource?
- Is there a concept of "hidden cost" — work done that the client doesn't know about?

### E-Commerce / Retail

**Catalog and inventory:**
- How many products/SKUs? Single category or multi-category?
- Who manages the catalog? One team or distributed (e.g., vendors)?
- Inventory tracking needed? Single warehouse or multi-location?
- Do products have variants (size, color)?

**Order lifecycle:**
- Walk me through from "customer clicks buy" to "order complete." What are all the steps?
- What can go wrong? (Cancellations, returns, partial fulfillment, payment failures)
- Who handles exceptions? Is there a support team, or is it self-serve?

**Pricing and payments:**
- Simple pricing or complex? (Discounts, bundles, subscriptions, dynamic pricing, B2B tiered?)
- Which payment methods? Any regulatory constraints (currency, region)?
- How are refunds processed?

### Marketplace

**Supply and demand:**
- Who are the two (or more) sides? How do they find each other?
- Is matching manual (browse/search) or algorithmic?
- What's the trust mechanism? Reviews, verification, escrow?

**Transactions and take rate:**
- How do you make money? Commission per transaction? Subscription? Lead fee?
- Who pays whom? Does money flow through your platform, or is it direct between parties?
- What happens when a transaction goes wrong? Dispute resolution flow?

**Cold start:**
- Which side do you seed first? How do you handle the chicken-and-egg problem?
- Any content or catalog that exists before launch?

### SaaS / Subscription

**User model:**
- B2B or B2C? If B2B, multi-tenant? What's the tenant boundary?
- How many plan tiers? What differs between them? (Features, usage limits, support level?)
- Self-serve signup or sales-led?

**Core value loop:**
- What's the single action a user takes that delivers value? How quickly can a new user get there?
- What does daily/weekly usage look like for an active user?
- What triggers churn? What triggers expansion?

**Billing and metering:**
- Flat fee, per-seat, usage-based, or hybrid?
- If usage-based, what's the unit? How is it metered?
- Free trial? Freemium? What converts?

### Internal Workflow Tool

**Process mapping:**
- Walk me through the workflow as it happens today. Every step, every handoff, every decision point.
- Where are the bottlenecks? Where do things get stuck or lost?
- What are the approval chains? Who can approve what, and what happens when they're unavailable?

**Integration surface:**
- What other systems does this touch? (Email, Slack, ERP, CRM, file storage?)
- Which integrations are "must have" vs. "nice to have"?
- Is there a master data source, or is data scattered?

**Compliance and audit:**
- Do you need audit trails? Who needs to see them?
- Any regulatory requirements (data retention, access controls, reporting)?
- Any data that's particularly sensitive?

---

## Universal Deep Dive Questions (Apply to Any Domain)

Use these regardless of domain, but only the ones that haven't been covered by domain-specific questions:

**Users and access:**
- How many distinct user types? What does each one care about?
- What should each role NOT see? (This reveals data sensitivity better than asking what they should see.)
- Is there a hierarchy? Do managers see their team's data?

**Scale and growth:**
- What's the current scale? (Users, transactions, data volume)
- What's the realistic scale in 12-18 months?
- Is this internal-only, or could it become a product?

**Current pain:**
- What's the single biggest pain point today? If we only solved that one thing, would it be worth building?
- What manual workaround are people doing right now that the system should automate?

**History and reporting:**
- Do you need to look backwards? (Historical reports, trend analysis, audit trail)
- If so, do you migrate existing data or start fresh?
- What decisions does reporting inform? (This determines what metrics matter.)

**Notifications and alerts:**
- When something important happens, how should people know? (In-app, email, Slack, SMS?)
- What are the "fire alarm" events — things that need immediate attention?

**Edge cases to probe (things stakeholders often forget):**
- What happens when someone leaves the company / changes role?
- What happens when a client / project / entity is deactivated but has historical data?
- What happens at month-end / quarter-end / year-end?
- Is there any seasonality that affects usage patterns?
- Multi-timezone, multi-currency, or multi-language needs?

---

## Conversation Anti-Patterns (Avoid These)

- **The questionnaire:** Asking 6+ questions in one message with no context for why. Feels like a form, not a conversation.
- **The parrot:** Repeating back exactly what the stakeholder said without adding any insight. "So you want a dashboard" — yes, they just said that.
- **The premature solutioner:** Jumping to architecture, tech stack, or UI before understanding the full problem.
- **The scope creep enabler:** Saying yes to everything without flagging complexity or suggesting phasing.
- **The yes-man:** Never pushing back, never suggesting the stakeholder might be over-engineering or under-thinking something.
- **The robot:** Asking generic questions that don't build on previous answers. Every question should demonstrate you were listening.
