# ADR-003: Backend Framework

**Status:** Accepted
**Date:** 2026-06-09
**Deciders:** Engineering Team

---

## Context

We need a backend framework for a REST API serving 14 entities with RBAC, financial calculations, background jobs, and audit logging. The team prefers Python. The project is built primarily by Claude Code, so framework familiarity in training data matters. Timeline is ~1 week for Phase 1 MVP.

## Decision

> We will use **Python 3.12 + FastAPI** as the backend framework.

## Rationale

- FastAPI auto-generates OpenAPI documentation from type hints — zero manual API doc maintenance
- Pydantic v2 integration handles request validation and response serialization, including field-level nulling for RBAC
- Native async support via uvicorn — handles concurrent requests without threading complexity
- Claude Code has excellent coverage of FastAPI patterns, maximizing AI-assisted development speed
- Lightweight — no ORM/auth/admin opinions baked in, so we choose SQLAlchemy + custom JWT without fighting the framework

## Alternatives Considered

| Alternative | Why Rejected |
|-------------|-------------|
| Django + DRF | Batteries-included (admin, ORM, auth) is appealing, but Django's sync-first model adds complexity for async Celery integration. Django admin is a crutch that doesn't match our custom RBAC model. Heavier framework means more boilerplate for a 1-week build. |
| Node.js + NestJS | Would enable TypeScript end-to-end with the React frontend. Rejected because team prefers Python, and the financial calculation logic is simpler in Python (native Decimal support). |
| Go + Gin | Excellent performance but slower development velocity. No ORM as mature as SQLAlchemy. Overkill for 20 concurrent users. |
| Flask | Simpler than FastAPI but lacks automatic OpenAPI generation, async support, and Pydantic integration. FastAPI is strictly better for API-first applications. |

## Consequences

**Positive:**
- API documentation is always up-to-date (generated from code)
- Strong typing via Pydantic catches schema mismatches at request time
- Async-ready for future performance optimization

**Negative / Trade-offs:**
- No built-in admin panel (unlike Django). Acceptable — the React frontend IS the admin interface.
- Smaller ecosystem than Django for pre-built integrations. Mitigated by the project's minimal integration needs.

**Neutral:**
- SQLAlchemy 2.0 works identically with FastAPI or Django. Database layer is framework-independent.

## Review Trigger

Revisit if the team grows to include multiple Python-specialist backend engineers who prefer Django's conventions.
