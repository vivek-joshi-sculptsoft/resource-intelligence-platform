# Database — PostgreSQL 16

## Primary Database

**PostgreSQL 16** hosted on **AWS RDS** (db.t4g.micro).

Chosen for: native UUID support, DECIMAL(15,2) precision for financial calculations, JSONB columns for audit log old/new values, robust foreign key constraints for the 14-entity relational model, and full-text search capability without additional infrastructure.

**Connection pooling:** SQLAlchemy's built-in async pool with `pool_size=10, max_overflow=5`. At 20 concurrent users, this is sufficient. Add PgBouncer if connection exhaustion occurs.

---

## Schema Approach

### Migrations

**Alembic** for schema migrations, auto-generated from SQLAlchemy models.

```bash
alembic revision --autogenerate -m "add assignment table"
alembic upgrade head
```

Migrations run automatically on deploy (in the Docker entrypoint).

### Naming Conventions

| Object | Convention | Example |
|--------|-----------|---------|
| Tables | snake_case, plural | `assignments`, `role_permissions` |
| Columns | snake_case | `billing_rate`, `is_active` |
| Primary keys | `id` (UUID v4) | `id UUID DEFAULT gen_random_uuid()` |
| Foreign keys | `{entity}_id` | `project_id`, `resource_id` |
| Indexes | `ix_{table}_{column}` | `ix_assignments_resource_id` |
| Unique constraints | `uq_{table}_{columns}` | `uq_role_permissions_role_id_data_type` |
| Enums | UPPER_SNAKE_CASE values | `ACTIVE`, `FIXED_PRICE`, `AUTO_RELEASED` |

### Standard Columns

Every table includes:
```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
created_at TIMESTAMP NOT NULL DEFAULT NOW(),
updated_at TIMESTAMP NOT NULL DEFAULT NOW()  -- trigger or app-level
```

User-facing entities also include:
```sql
is_active BOOLEAN NOT NULL DEFAULT true  -- soft delete
```

### Indexes

All foreign keys and status/filter columns are indexed:
```sql
CREATE INDEX ix_assignments_project_id ON assignments(project_id);
CREATE INDEX ix_assignments_resource_id ON assignments(resource_id);
CREATE INDEX ix_assignments_status ON assignments(status);
CREATE INDEX ix_projects_client_id ON projects(client_id);
CREATE INDEX ix_projects_status ON projects(status);
CREATE INDEX ix_audit_logs_entity_type_entity_id ON audit_logs(entity_type, entity_id);
```

---

## Caching Layer

**Redis 7** running in Docker on the same EC2 instance.

| What's Cached | TTL | Invalidation |
|---------------|-----|-------------|
| RolePermission lookups | 5 min | On permission update (Phase 3) |
| SystemConfig values | 10 min | On config update |
| Dashboard aggregate queries | 30 sec | Time-based expiry |
| User session data | Matches JWT lifetime | On logout |

Cache is optional at MVP scale — PostgreSQL handles 20 users without breaking a sweat. Redis is primarily there as the Celery broker; caching is a bonus.

---

## Search

**PostgreSQL full-text search** for resource/project/client name lookups.

```sql
-- GIN index on resource name for fast search
CREATE INDEX ix_resources_name_trgm ON resources USING gin (name gin_trgm_ops);
```

Uses `pg_trgm` extension for fuzzy/partial matching. No need for Elasticsearch or Typesense at this scale.

---

## File/Blob Storage

**AWS S3** — for any future file uploads (profile photos, invoice PDFs, report exports).

| Bucket | Purpose | Access |
|--------|---------|--------|
| `ri-platform-uploads` | User-uploaded files | Private, pre-signed URLs |
| `ri-platform-exports` | Generated reports/CSVs | Private, time-limited download links |

Not needed in Phase 1 MVP. Provisioned when file features are added.

---

## Backup & Recovery

| Setting | Value |
|---------|-------|
| Automated backups | RDS automated, 7-day retention |
| Point-in-time recovery | Enabled (RDS default, 5-minute granularity) |
| Manual snapshots | Before major migrations |
| RTO target | < 1 hour (internal tool, not mission-critical SLA) |
| RPO target | < 5 minutes (RDS PITR) |

---

## Data Retention

| Entity | Retention Policy |
|--------|-----------------|
| AuditLog | Never deleted. Append-only. Partition by month if table exceeds 10M rows. |
| Active entities | Soft delete (`is_active = false`). Never hard delete user-facing data. |
| Alerts | Retain 1 year. Archived alerts can be purged after 12 months. |
| SystemConfig | Never deleted. |

---

## Multi-Tenancy

**Not applicable.** This is a single-company internal tool. No tenant isolation needed. All data in one schema, one database.
