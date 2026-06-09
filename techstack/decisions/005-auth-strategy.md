# ADR-005: Authentication Strategy

**Status:** Accepted
**Date:** 2026-06-09
**Deciders:** Engineering Team

---

## Context

The platform needs authentication for ~30-40 internal users across 7 roles. Access is email/password only — no social login, no SSO/SAML, no public registration. Authorization is complex (105 RolePermission rows across 15 data types with 3 scope levels) but authentication is simple.

## Decision

> We will build **custom JWT authentication** using python-jose for tokens and argon2-cffi for password hashing, with RBAC enforced via the RolePermission database table.

## Rationale

- Authentication is simple (email/password for 30-40 users) — a managed provider adds cost and complexity for no benefit
- Authorization is complex but database-driven (RolePermission table with 105 rows). No managed provider handles this custom RBAC model — we'd build the authorization layer ourselves regardless.
- Zero vendor dependency or external API calls for auth — everything runs locally
- argon2id is the OWASP-recommended password hashing algorithm (2024), stronger than bcrypt against GPU attacks
- httpOnly cookies for token storage prevent XSS-based token theft

## Alternatives Considered

| Alternative | Why Rejected |
|-------------|-------------|
| Auth0 | Excellent for social login and SSO, but overkill for internal email/password. Free tier covers our user count, but adds vendor dependency for the simplest possible auth flow. Still need custom RBAC layer. |
| AWS Cognito | AWS-native but notoriously poor DX. Complex pricing model. Still need custom RBAC layer on top. |
| Supabase Auth | Good if using Supabase for everything, but we're on RDS. Adding Supabase just for auth means a second database dependency. |
| Django Auth | Would require switching to Django framework. Auth alone doesn't justify the framework change. |

## Consequences

**Positive:**
- Zero external dependencies for auth — works offline, no API latency
- Full control over token lifetimes, rotation, blacklisting
- RBAC logic lives next to the data it protects (same DB, same process)

**Negative / Trade-offs:**
- Security is entirely on us — no managed provider catches misconfigurations
- No SSO/SAML support. If enterprise SSO is needed later, significant rework or adding Auth0 on top.
- No self-service password reset UI (admin resets passwords directly in Phase 1)

**Neutral:**
- Token format (JWT) is standard — any future service can validate tokens independently

## Review Trigger

Revisit if SSO/SAML becomes a requirement (e.g., parent company mandates it) or if security audit recommends a managed provider.
