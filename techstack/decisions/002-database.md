# ADR-002: Primary Database

**Status:** Accepted
**Date:** 2026-06-09
**Deciders:** Engineering Team

---

## Context

The platform has 14 entities with complex relationships (resources → assignments → projects → clients → invoices). Financial calculations require DECIMAL precision. Audit logging needs JSONB for storing arbitrary old/new field values. The team already has an AWS account and plans to host infrastructure there.

## Decision

> We will use **PostgreSQL 16 hosted on AWS RDS** (db.t4g.micro) as the primary database.

## Rationale

- Highly relational data model with foreign keys, unique constraints, and cascading relationships — PostgreSQL's sweet spot
- DECIMAL(15,2) for all monetary fields, matching FSD requirements exactly
- JSONB columns for AuditLog old_value/new_value without schema overhead
- Native UUID generation via `gen_random_uuid()` for all primary keys
- `pg_trgm` extension for fuzzy search on resource/project names without additional infra
- RDS provides automated backups, point-in-time recovery, and encryption at rest

## Alternatives Considered

| Alternative | Why Rejected |
|-------------|-------------|
| Supabase (managed PostgreSQL) | Same database engine but adds Auth/Storage/Realtime features we don't need. Vendor dependency for the DB layer. RDS gives more control over extensions, connection limits, and parameter tuning. |
| MySQL (RDS) | PostgreSQL has better JSON support, better UUID handling, and richer full-text search. No MySQL-specific advantage for this workload. |
| MongoDB | Data is deeply relational (assignments join resources, projects, clients). Document model would require application-level joins and lose ACID guarantees on financial calculations. |
| DynamoDB | Key-value model doesn't fit complex reporting queries (utilization dashboards, margin calculations across entities). Would need a separate analytics DB immediately. |

## Consequences

**Positive:**
- Full ACID compliance for financial transactions
- RDS automated backups with 7-day retention and PITR
- Can scale vertically to db.t4g.large if needed without migration
- PostgreSQL extensions available (pg_trgm, pgcrypto, etc.)

**Negative / Trade-offs:**
- RDS costs money even at idle ($13/mo after free tier). Supabase free tier is $0.
- No serverless scale-to-zero — paying for the instance 24/7. Acceptable for an always-on internal tool.

**Neutral:**
- Alembic handles migrations the same way regardless of PostgreSQL hosting.

## Review Trigger

Revisit if monthly RDS cost exceeds $200/mo and a serverless option (Neon, Aurora Serverless) would be cheaper.
