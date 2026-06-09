# Research Playbook

Use this reference when the conversation needs competitor analysis, feasibility evaluation, or alternative solution assessment. This phase is optional — only enter it when triggered by the stakeholder or when you detect it would add significant value.

---

## When to Trigger Research

**Stakeholder-initiated:**
- "Is there anything like this already?"
- "Have you seen similar tools?"
- "Should we build this or buy something?"
- "Is this even feasible?"
- "What are the alternatives?"

**Agent-initiated (you detect the need):**
- The system being described is clearly an established product category (CRM, ATS, helpdesk, project management). The stakeholder may not realize mature solutions exist.
- The stakeholder describes a feature that has known technical complexity they may not be aware of (real-time collaboration, AI-driven matching, complex permission systems).
- The build vs. buy question would save the stakeholder significant time/money if answered now rather than after building.
- The stakeholder's approach has a common alternative that might be simpler.

---

## Competitor Analysis

### How to Research

Use web search to find real products in the category. Search for:
1. The product category name + "software" or "tool" (e.g., "resource management software for IT services")
2. The core problem being solved (e.g., "track employee utilization and billability")
3. "Alternative to [known product]" if the stakeholder mentioned a specific tool
4. Industry-specific solutions (e.g., "PSA tools for IT staffing companies")
5. Review aggregator sites: G2, Capterra, TrustRadius for category overviews

### What to Extract

For each relevant competitor, capture:

- **Name and positioning**: What they call themselves, who they target
- **Core features**: What do they do that overlaps with the stakeholder's needs?
- **Gaps**: What does the stakeholder need that this tool doesn't do?
- **Pricing model**: Free, per-seat, per-project, enterprise-only?
- **Scale fit**: Is this for 5-person teams or 5000-person enterprises?
- **Integration surface**: What does it connect to?

### How to Present

Don't dump a feature comparison matrix. Instead, frame it as insight:

**Good:** "There are 3-4 tools in this space. Mavenlink and Kantata are the closest to what you're describing — they handle resource allocation and project financials for services firms. Where they fall short for your use case is the shadow resource tracking and the variable billability concept — those are genuinely custom to how your business operates. The commodity parts (client management, basic project tracking) exist off-the-shelf."

**Bad:** "Here are 10 competitors with their features listed..."

### Build vs. Buy Framework

Help the stakeholder think through this decision:

| Factor | Build | Buy |
|---|---|---|
| Core differentiator | The feature IS your competitive advantage or unique workflow | The feature is commodity / table-stakes |
| Data sensitivity | Highly sensitive data that can't leave your systems | Standard business data with adequate vendor security |
| Integration depth | Needs deep integration with internal systems | Standalone or light integration sufficient |
| Customization | Business rules are unique and change frequently | Standard workflows with minor configuration |
| Scale | Small team, specific needs, internal use | Growing team, standard processes |
| Maintenance | You have engineering capacity to maintain it | You don't want to maintain software |

Frame your recommendation clearly: "Based on what you've described, I'd recommend building X because [reason], but using an off-the-shelf tool for Y because [reason]."

---

## Feasibility Assessment

### Technical Feasibility

When the stakeholder describes a feature, assess whether it's:

- **Standard**: Well-known patterns, plenty of libraries/frameworks, no research required. Example: CRUD operations, dashboards, role-based access.
- **Achievable with effort**: Requires specific expertise or third-party services but is well-understood. Example: Real-time notifications, PDF generation, calendar integrations.
- **Complex**: Requires significant architecture thought, has failure modes, may need iteration. Example: Real-time collaborative editing, complex permission inheritance, offline-first sync.
- **Research-grade**: Uncertain outcomes, may not be possible or reliable. Example: AI-driven resource matching that accounts for personality fit, automatic scope estimation from requirements text.

Be honest about complexity. "This is doable but it's not a weekend project — the permission inheritance model alone needs careful design" is more useful than "yes, we can do that."

### Operational Feasibility

Even if technically possible, will it work in practice?

- **Data availability**: Does the organization actually have the data this feature needs? If the system calculates margin but nobody tracks CTC consistently, the feature is useless.
- **Process readiness**: Does the feature assume a process that doesn't exist yet? A timesheet approval workflow is useless if nobody submits timesheets today.
- **Adoption risk**: Will people actually use this? A beautiful dashboard that requires 30 minutes of daily data entry won't get adopted.
- **Change management**: How different is this from current workflow? Big changes need phased rollout.

### Scale Feasibility

Think about whether the solution works at the stakeholder's current scale AND their likely scale in 12-18 months:

- 10 users vs. 100 vs. 1000 — does the UX change?
- 100 records vs. 10,000 vs. 1M — does the data model hold?
- Single timezone/currency vs. multi — is this needed eventually?

Flag when "we can handle that later" is risky (e.g., multi-tenancy is very hard to add retroactively) vs. when it's fine (e.g., adding email notifications later is trivial).

---

## Alternative Solution Evaluation

When the stakeholder proposes an approach and you see a simpler, better, or more proven alternative:

### How to Suggest Alternatives

1. **Acknowledge the original approach**: "Your idea of X makes sense because..."
2. **Introduce the alternative**: "Another way to handle this is Y..."
3. **Compare trade-offs**: "X gives you [advantage] but costs [disadvantage]. Y gives you [advantage] but costs [disadvantage]."
4. **Recommend (with reasoning)**: "For your scale and timeline, I'd lean toward Y because..."

### Common Alternative Patterns

| Stakeholder Says | Consider Suggesting |
|---|---|
| "We need a custom notification system" | Start with in-app alerts + email digest. Custom notification engine is Phase 3. |
| "We need real-time dashboards" | Near-real-time (refresh every 5 min) covers 95% of use cases and is 10x simpler. |
| "We need AI-powered matching" | Rules-based matching with manual override first. AI later when you have training data. |
| "We need a mobile app" | Responsive web app first. Native mobile only if there's a clear offline or push notification need. |
| "We need to integrate with everything" | Identify the 2-3 must-have integrations. The rest are CSV import/export for now. |
| "We need role-based access from day one" | Start with 2-3 hard-coded roles. Configurable RBAC is Phase 2 when you know the real access patterns. |
| "Users should be able to customize everything" | Ship opinionated defaults that work for 80% of cases. Add configurability based on feedback. |

---

## Research Output Format

When presenting research findings in the conversation, structure it as:

**What exists:** Brief overview of the competitive landscape (2-3 most relevant products, not an exhaustive list).

**Where they fit:** Which of the stakeholder's needs they cover well.

**Where they fall short:** The gaps that justify custom development.

**Recommendation:** Build, buy, or hybrid — with clear reasoning.

**Risk flags:** Anything the stakeholder should know about complexity, timeline, or operational readiness.

Keep it concise. Research should inform the requirements conversation, not derail it. If the stakeholder wants deeper analysis, they'll ask.
