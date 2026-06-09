# ADR Template

Architecture Decision Records capture the WHY behind major technical choices. One file per decision. Keep each under one page.

---

## File Naming

```
decisions/001-backend-framework.md
decisions/002-database.md
decisions/003-frontend-framework.md
decisions/004-hosting-provider.md
decisions/005-auth-strategy.md
decisions/006-api-design.md
decisions/007-background-jobs.md
decisions/008-monolith-vs-microservices.md
```

Number sequentially. Use kebab-case slugs that describe the decision, not the outcome.

---

## ADR Status Values

| Status | Meaning |
|--------|---------|
| `Proposed` | Under discussion, not yet decided |
| `Accepted` | Decision made, in effect |
| `Deprecated` | Was accepted, no longer applies |
| `Superseded by ADR-XXX` | Replaced by a newer decision |

---

## Template

```markdown
# ADR-{NNN}: {Decision Title}

**Status:** Accepted  
**Date:** {YYYY-MM-DD}  
**Deciders:** {Names or "Engineering Team"}

---

## Context

{1–3 sentences describing the situation and why a decision was needed. What problem were we solving? What constraints existed?}

## Decision

{1–2 sentences stating exactly what was decided. Be specific — name the technology/approach chosen.}

> We will use **{choice}** for {purpose}.

## Rationale

{3–5 bullet points explaining why this choice was made. Focus on the specific reasons it beats the alternatives for THIS project — not generic comparisons.}

- {Reason 1}
- {Reason 2}
- {Reason 3}

## Alternatives Considered

| Alternative | Why Rejected |
|-------------|-------------|
| {Option A} | {Specific reason it lost — not "worse than chosen option"} |
| {Option B} | {Specific reason it lost} |

## Consequences

**Positive:**
- {Good outcome 1}
- {Good outcome 2}

**Negative / Trade-offs:**
- {Trade-off 1 — be honest}
- {Trade-off 2}

**Neutral:**
- {Side effect that's neither good nor bad}

## Review Trigger

{When should this decision be revisited? e.g., "Revisit if team grows past 10 engineers" or "Revisit if monthly active users exceed 100K"}
```

---

## Filled Example

```markdown
# ADR-002: Primary Database

**Status:** Accepted  
**Date:** 2026-06-08  
**Deciders:** Engineering Team

---

## Context

We need a primary database for the resource management platform. The data model is highly relational (resources, projects, allocations, clients, invoices) with complex reporting queries. The team has 4 engineers — 3 full-stack JS, 1 Python. MVP target is 8 weeks. Expected scale: ~500 concurrent users at launch, ~5K within 12 months.

## Decision

> We will use **PostgreSQL hosted on Supabase** as the primary database.

## Rationale

- Data model is relational — allocations reference resources, projects, and clients with foreign key integrity. A document DB would require application-level joins.
- Supabase provides managed PostgreSQL with zero DevOps overhead, which matches our timeline and no-DevOps-engineer constraint.
- Row-level security (RLS) in PostgreSQL maps directly to our multi-tenant RBAC requirements.
- Supabase free tier covers MVP; Pro tier at $25/mo handles growth phase.
- Team has existing PostgreSQL experience.

## Alternatives Considered

| Alternative | Why Rejected |
|-------------|-------------|
| MongoDB | Data is highly relational. Would fight the document model for joins and transactions. Rejected for this domain. |
| AWS RDS PostgreSQL | Same database, but higher ops overhead and cost vs Supabase at MVP scale. Migrate to RDS if we need more control later. |
| DynamoDB | Key-value model doesn't fit complex reporting queries. Would require separate analytics DB immediately. |

## Consequences

**Positive:**
- Zero DB ops burden — Supabase handles backups, scaling, point-in-time recovery.
- Supabase Auth + Storage + Realtime available if needed, all on same infra.
- Prisma ORM integrates natively with PostgreSQL.

**Negative / Trade-offs:**
- Vendor dependency on Supabase. Mitigation: standard PostgreSQL — can migrate to RDS with minimal friction.
- Supabase free tier has connection limits (100 direct connections). Supavisor pooler resolves this.

**Neutral:**
- Migrations managed via Prisma Migrate.

## Review Trigger

Revisit if we need >10K concurrent DB connections, multi-region write requirements, or if Supabase pricing becomes a concern past $500/mo.
```

---

## Which Decisions Get ADRs

Generate an ADR for every decision where:
- There were real alternatives considered
- The choice is hard to reverse later
- A future engineer might question "why did they pick this?"

Typical ADRs for a greenfield project:

| # | Decision | Reversibility |
|---|----------|--------------|
| 001 | Backend language & framework | Low — hard to switch after 6 months |
| 002 | Primary database | Low — data migration is painful |
| 003 | Frontend framework | Low — rewrite cost |
| 004 | Hosting provider | Medium — possible with infra-as-code |
| 005 | Authentication strategy | Low — auth changes affect all users |
| 006 | API design (REST vs GraphQL vs tRPC) | Medium — client contracts must change |
| 007 | Background job strategy | Medium — worker replacement |
| 008 | Monolith vs microservices | Low — splitting a monolith is expensive |

Skip ADRs for commodity choices with obvious defaults (e.g., "we use Git" doesn't need an ADR).
