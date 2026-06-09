# ADR-008: Monolith vs Microservices

**Status:** Accepted
**Date:** 2026-06-09
**Deciders:** Engineering Team

---

## Context

The platform has 13 modules across 3 phases. Modules have clear boundaries (auth, clients, projects, allocations, financial engine, etc.) which could map to individual services. However, the team is 1-2 engineers building with Claude Code in ~1 week, and the expected load is 20 concurrent users.

## Decision

> We will build a **modular monolith** — one FastAPI application with 13 modules as Python packages, deployed as a single Docker image.

## Rationale

- 1-2 developers cannot effectively manage multiple services (separate repos, deployments, monitoring, inter-service communication)
- 13 modules share the same database and many entities have cross-module relationships (assignments reference resources, projects, and clients)
- Module boundaries are enforced by Python package structure (`app/modules/auth/`, `app/modules/allocations/`), not service boundaries
- A monolith deploys in seconds (`docker-compose up`). Microservices require container orchestration, service discovery, and distributed tracing.
- At 20 concurrent users, a single process handles the entire load with room for 100x growth

## Alternatives Considered

| Alternative | Why Rejected |
|-------------|-------------|
| Microservices (one per module) | 13 services for 1-2 developers and 20 users. Deployment complexity would consume more time than feature development. Cross-service data access (e.g., utilization dashboard reading from allocations, resources, and projects) requires API calls between services instead of direct DB queries. |
| Auth as a separate service | Considered splitting auth out for clean separation. Rejected because it adds a network hop for every authenticated request and requires either a shared database or service-to-service calls for RBAC lookups. The benefit (independent auth scaling/deployment) doesn't materialize at this scale. |
| Serverless (Lambda per endpoint) | Cold starts degrade UX for an always-active internal tool. Shared state (Redis cache, Celery broker) doesn't fit the stateless Lambda model. |

## Consequences

**Positive:**
- Single deployment unit — one `docker-compose up` deploys everything
- Direct database queries across modules (no API hop for cross-module data)
- Shared transaction context — financial calculations touching multiple entities use a single DB transaction
- Debuggable with a single log stream

**Negative / Trade-offs:**
- All modules share a process — a crash in one module affects all modules. Mitigated by Docker auto-restart.
- Cannot scale modules independently (e.g., allocations hot, audit cold). Not a concern at this scale.
- Risk of module coupling if import boundaries aren't enforced. Mitigated by convention: modules import from `shared/` and their own package, never directly from other modules.

**Neutral:**
- Module boundaries make future extraction possible. If allocations needs to become a service, the `app/modules/allocations/` package has clear inputs and outputs.

## Review Trigger

Revisit if the team grows past 5 engineers (coordination overhead makes module ownership harder in a monolith) or if specific modules need independent scaling.
