# ADR-001: Frontend Framework

**Status:** Accepted
**Date:** 2026-06-09
**Deciders:** Engineering Team

---

## Context

We need a frontend framework for an internal resource management dashboard. The UI is data-heavy (tables, forms, dashboards) with no public-facing pages, no SEO requirements, and no server-side rendering needs. The API is a separate Python/FastAPI backend. The project is being built by 1-2 engineers using Claude Code in approximately one week.

## Decision

> We will use **React 19 + Vite 6** as a client-side SPA for the frontend.

## Rationale

- No SSR/SSG needed — internal tool behind authentication, zero SEO requirements
- Vite provides fastest HMR and build times, simpler configuration than Next.js
- Eliminates server/client component confusion — everything is client-side
- React has the largest ecosystem for data-heavy UIs (TanStack Table, shadcn/ui, React Hook Form)
- Claude Code has deepest training coverage on React, maximizing AI-assisted development speed
- Builds to static files for simple S3+CloudFront deployment

## Alternatives Considered

| Alternative | Why Rejected |
|-------------|-------------|
| Next.js 15 (App Router) | All server features (SSR, API routes, middleware) are unused — the API is FastAPI. Adds complexity (server vs client components) with no benefit for an internal SPA. |
| Vue / Nuxt | Smaller ecosystem for data-heavy components. Team preference is React. |
| Angular | Heavy boilerplate, slower to iterate, overkill for this team size and timeline. |
| SvelteKit | Smaller community, fewer UI component libraries for enterprise dashboards. |

## Consequences

**Positive:**
- Fastest possible build iteration (Vite HMR < 50ms)
- Simpler deployment (static files → S3)
- No framework lock-in beyond React itself

**Negative / Trade-offs:**
- No SSR if requirements change (would need to add Next.js or Remix later)
- Client-side routing means configuring S3 redirect rules for SPA fallback

**Neutral:**
- React Router v7 handles all routing needs equivalently to Next.js file-based routing

## Review Trigger

Revisit if the platform adds a public-facing marketing site or customer portal requiring SEO.
