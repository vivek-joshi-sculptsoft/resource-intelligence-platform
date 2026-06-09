# Stack Options Catalog

Curated options per layer with tradeoffs and selection guidance. Use this during Phase 4 to form recommendations.

---

## Selection Heuristics

Apply these rules before looking at individual options:

| Signal | Implication |
|--------|------------|
| Team ≤ 4 engineers | Monolith. Microservices add coordination overhead that kills small teams. |
| MVP timeline ≤ 8 weeks | Managed services everywhere. Avoid anything with a steep ops learning curve. |
| Team is JS/TS-heavy | Node.js backend. TypeScript end-to-end reduces context switching. |
| Team is Python-heavy | FastAPI or Django. Don't fight the team's existing skills for greenfield. |
| B2B SaaS with roles/permissions | PostgreSQL + row-level security. Relational model fits multi-tenant RBAC. |
| Real-time features (chat, live updates) | WebSocket or SSE support needed. Next.js + Socket.io or Supabase Realtime. |
| Heavy file processing (video, PDFs) | Background workers + object storage. Don't do this synchronously. |
| India-based project / INR payments | Razorpay over Stripe (no foreign exchange friction, better INR support). |
| Mobile is primary surface | React Native (if JS team) or Flutter (if new team, want true native feel). |
| SEO is critical | SSR mandatory. Next.js or Nuxt. Not a pure SPA. |
| Internal tool / dashboard only | SPA is fine. Even Retool/Metabase might replace custom frontend entirely. |
| Enterprise SSO required | Auth0 or Cognito. Custom auth won't support SAML without significant effort. |
| No DevOps engineer on team | Vercel/Railway/Render. Avoid raw EC2, bare Kubernetes, or self-managed infra. |

---

## Frontend

### Web Frameworks

| Option | Best For | Avoid When |
|--------|----------|-----------|
| **Next.js 14** | SEO-important apps, full-stack teams, Vercel deployment, large ecosystem | Team is Vue/Angular, overkill for pure internal tools |
| **Nuxt 3** | Vue-leaning teams, European/French companies who prefer Vue's DX | Team doesn't know Vue |
| **SvelteKit** | Performance-critical apps, small bundle size priority, greenfield with flexibility | Large team (smaller community, fewer hiring options) |
| **React SPA (Vite)** | Internal tools, dashboards with no SEO need, teams that want full control | When SEO matters or you need SSR |
| **Angular** | Large enterprise teams with strict structure, legacy codebases | Startups and small teams (heavy boilerplate) |
| **Remix** | Form-heavy apps, progressive enhancement, web fundamentals focus | Teams not familiar with web standards patterns |

**Recommended default:** Next.js 14 (App Router) for most B2B SaaS products.

### UI Component Libraries

| Option | Best For |
|--------|----------|
| **shadcn/ui + Tailwind** | Custom design systems, copy-paste components, full control |
| **Mantine** | Feature-rich out of the box, good defaults, hooks included |
| **Ant Design** | Enterprise dashboards, data-dense UIs, Asian market conventions |
| **Chakra UI** | Accessible, theme-able, good for fast prototyping |
| **Material UI (MUI)** | Google design language, enterprise, large community |

### State Management

| Option | When |
|--------|------|
| **Zustand** | Default choice — simple, lightweight, no boilerplate |
| **TanStack Query** | Server state (API calls). Combine with Zustand for local state |
| **Jotai / Recoil** | Atomic state, fine-grained updates |
| **Redux Toolkit** | Only if the team already knows Redux or state is very complex |

### Mobile

| Option | Best For | Notes |
|--------|----------|-------|
| **React Native** | JS/TS team, shared logic with web, large ecosystem | Use Expo for faster setup |
| **Flutter** | True native performance, new team, cross-platform priority | Dart — separate language from web stack |
| **Native (Swift/Kotlin)** | Performance-critical, platform-specific features | Separate teams for iOS/Android |

---

## Backend

### Language + Framework

| Option | Best For | Avoid When |
|--------|----------|-----------|
| **Node.js + NestJS** | JS/TS teams, REST + GraphQL, structured architecture, microservices | Team hates decorators/Angular-style DI |
| **Node.js + Express/Fastify** | Lightweight services, teams that want minimal framework | Large codebase (no structure → chaos at scale) |
| **Python + FastAPI** | Python teams, ML/AI integration, async APIs, rapid prototyping | Team is JS-only |
| **Python + Django** | Batteries-included, admin panel, Python ORM, traditional web | Async-heavy or high-throughput APIs |
| **Go + Gin/Fiber** | High-throughput services, microservices, teams with Go experience | Greenfield with no Go expertise (steep learning curve) |
| **Ruby + Rails** | Rapid prototyping, CRUD-heavy, strong conventions | High-throughput or real-time systems |
| **Java + Spring Boot** | Enterprise, existing Java ecosystem, strict typing, large teams | Startups — heavy, slow to iterate |

**Recommended defaults:**
- JS/TS team → Node.js + NestJS
- Python team → FastAPI
- New project, performance matters → Go + Gin

### API Design

| Style | Best For | Avoid When |
|-------|----------|-----------|
| **REST** | Standard CRUD, simple resource model, broad client support | Highly connected data with complex queries |
| **GraphQL** | Complex data graphs, multiple clients with different data needs, mobile | Simple CRUD apps — over-engineering |
| **tRPC** | Full-stack TypeScript monorepo — type-safe end-to-end, no codegen | Non-TypeScript teams, separate frontend repo |
| **gRPC** | Internal microservice-to-microservice communication, high throughput | Public APIs, browser clients (requires grpc-web) |

**Recommended default:** REST with OpenAPI documentation for most products.

---

## Database

### Primary Database

| Option | Best For | Avoid When |
|--------|----------|-----------|
| **PostgreSQL** | Relational data, complex queries, ACID, JSONB for semi-structured data, multi-tenant | Document-heavy data with no relations |
| **MySQL** | Existing MySQL teams, simple relational data | PostgreSQL is generally preferred for new projects |
| **MongoDB** | True document data (CMS, product catalogs), flexible schema, horizontal scale | Highly relational data — you'll regret it |
| **DynamoDB** | AWS-native, key-value + simple queries, extreme scale, serverless | Complex queries, ad-hoc reporting |
| **Supabase (PostgreSQL)** | Managed PostgreSQL + Auth + Storage + Realtime in one, fast setup | Need total control over DB config |

**Recommended default:** PostgreSQL. If on AWS and want managed, use RDS. If want full managed + extras, Supabase.

### ORM / Query Builder

| Option | Language | Notes |
|--------|----------|-------|
| **Prisma** | Node.js/TS | Best DX, type-safe queries, migrations built-in. Recommended for Node. |
| **TypeORM** | Node.js/TS | More control than Prisma, decorator-based, pairs well with NestJS |
| **Drizzle** | Node.js/TS | Lightweight, SQL-like syntax, fast, growing ecosystem |
| **SQLAlchemy** | Python | Standard for Python, powerful, supports async |
| **Django ORM** | Python | Built-in with Django, excellent for standard CRUD |
| **GORM** | Go | Standard Go ORM, mature |

### Caching

| Option | Best For | Notes |
|--------|----------|-------|
| **Redis** | Sessions, rate limiting, job queues, hot data cache | Use Upstash for serverless/managed Redis |
| **Memcached** | Simple key-value cache, high throughput | No persistence, no pub/sub — limited use cases |
| **In-process cache** | Single-instance, low volume | Node-cache, Python's functools.lru_cache |

### Search

| Option | Best For | Notes |
|--------|----------|-------|
| **PostgreSQL full-text** | Basic search on existing data, no extra infra | Good enough for most apps under 1M records |
| **Typesense** | Self-hosted/cloud, typo-tolerant, fast, easy setup | Best starting point for dedicated search |
| **Algolia** | Managed, generous free tier, excellent DX | Cost scales quickly at high query volume |
| **Elasticsearch** | Enterprise-scale, complex queries, log search | Heavy ops burden — don't self-host unless needed |

### File/Object Storage

| Option | Best For | Notes |
|--------|----------|-------|
| **AWS S3** | AWS deployments, standard, huge ecosystem | Correct choice for most AWS stacks |
| **Supabase Storage** | Already using Supabase, S3-compatible API | Zero-config if on Supabase |
| **Cloudinary** | Media-heavy apps (images, video), on-the-fly transforms | Premium pricing for transforms |
| **Backblaze B2** | Cost-sensitive, S3-compatible, cheaper than S3 | Smaller ecosystem |

---

## Authentication

| Option | Best For | Avoid When |
|--------|----------|-----------|
| **Auth0** | Enterprise SSO/SAML, social login, managed, quick setup | Budget-sensitive (expensive at scale) |
| **AWS Cognito** | AWS stacks, enterprise, federated identity | Complex pricing, poor DX compared to Auth0 |
| **Supabase Auth** | Already using Supabase, simple email/social auth | Enterprise SSO requirements |
| **NextAuth.js / Auth.js** | Next.js apps, social providers, simple self-hosted | Complex enterprise auth |
| **Clerk** | Excellent DX, prebuilt UI components, fast integration | Cost at scale |
| **Custom JWT** | Total control, no vendor lock-in, specific requirements | Team inexperience — security risk |

**Recommended default:** Supabase Auth (if on Supabase) or Clerk (great DX, fast) for startups. Auth0 when enterprise SSO is a hard requirement.

---

## Background Jobs

| Option | Best For | Notes |
|--------|----------|-------|
| **BullMQ (Redis)** | Node.js, reliable queues, job scheduling, retries | Requires Redis. Best for Node. |
| **Celery (Python)** | Python workers, distributed tasks, cron | Requires Redis or RabbitMQ as broker |
| **Temporal** | Complex workflows, long-running processes, durable execution | Overhead for simple queues — use BullMQ first |
| **AWS SQS + Lambda** | Serverless, AWS-native, auto-scaling | Cold starts, per-invocation pricing |
| **Inngest** | Event-driven workflows, serverless, excellent DX, free tier | Vendor lock-in |
| **Sidekiq** | Ruby on Rails background jobs | Ruby only |

**Recommended default:** BullMQ for Node.js stacks. Celery for Python stacks.

---

## Hosting & Deployment

### Frontend Hosting

| Option | Best For | Notes |
|--------|----------|-------|
| **Vercel** | Next.js (first-party), zero-config, edge network | Best DX for Next.js |
| **Netlify** | JAMstack, static sites, serverless functions | Good for Gatsby/Hugo |
| **Cloudflare Pages** | Edge-first, fast, generous free tier | Good alternative to Vercel |
| **AWS S3 + CloudFront** | AWS stacks, full control, cost-effective at scale | More ops work |

### Backend Hosting

| Option | Best For | Notes |
|--------|----------|-------|
| **Railway** | Startups, fast deploy, good DX, reasonable cost | Dockerfile or buildpacks, volumes, cron |
| **Render** | Heroku alternative, good free tier, web services + workers | Slightly slower cold starts |
| **Fly.io** | Edge deployment, Dockerized apps, global distribution | More control than Railway/Render |
| **AWS ECS / Fargate** | AWS stacks, production-scale, managed containers | More ops complexity |
| **AWS Lambda** | Event-driven, serverless, pay-per-request | Cold starts, stateless only |
| **GCP Cloud Run** | Containerized serverless, auto-scale to zero | GCP stacks |
| **DigitalOcean App Platform** | Simple, affordable, good for small teams | Less ecosystem than AWS |

### Database Hosting

| Option | Notes |
|--------|-------|
| **Supabase** | Managed PostgreSQL, free tier, Auth + Storage included |
| **Neon** | Serverless PostgreSQL, scale-to-zero, branching |
| **PlanetScale** | MySQL-compatible, serverless, schema branching |
| **AWS RDS** | Managed PostgreSQL/MySQL, production-grade, expensive |
| **AWS Aurora** | High-performance managed PostgreSQL/MySQL, auto-scaling |
| **MongoDB Atlas** | Managed MongoDB, global clusters |

---

## Monitoring & Observability

### Error Tracking

| Option | Notes |
|--------|-------|
| **Sentry** | Standard choice. Supports every language. Free tier generous. |
| **Bugsnag** | Alternative to Sentry, strong mobile support |
| **Rollbar** | Similar to Sentry |

### APM / Metrics

| Option | Notes |
|--------|-------|
| **Datadog** | Full-featured, expensive, enterprise standard |
| **New Relic** | Alternative to Datadog, generous free tier |
| **Grafana + Prometheus** | Self-hosted, full control, common in Kubernetes setups |
| **CloudWatch** | AWS-native, free with AWS, less powerful than Datadog |

### Logging

| Option | Notes |
|--------|-------|
| **Logtail (Better Stack)** | Excellent DX, affordable, SQL-queryable logs |
| **Datadog Logs** | If already using Datadog |
| **AWS CloudWatch Logs** | AWS-native, free with AWS |
| **Papertrail** | Simple, affordable log aggregation |

### Uptime Monitoring

| Option | Notes |
|--------|-------|
| **Better Uptime** | Good free tier, incident management, status page |
| **Checkly** | Code-first monitoring, E2E checks as code |
| **UptimeRobot** | Simple, free tier for basics |

---

## Email / SMS / Notifications

| Service | Option | Notes |
|---------|--------|-------|
| **Transactional Email** | Resend | Best DX, React Email templates, modern API |
| | SendGrid | Battle-tested, large free tier |
| | AWS SES | Cheapest at volume, no frills |
| | Postmark | Excellent deliverability, developer-friendly |
| **SMS** | Twilio | Standard, global coverage, reliable |
| | AWS SNS | AWS-native, cheaper, less DX |
| | MSG91 | India-specific, good INR pricing |
| **Push Notifications** | Firebase FCM | Standard for mobile push, free |
| **In-App Notifications** | Novu | Open-source notification infrastructure |

---

## Payments

| Option | Best For | Notes |
|--------|----------|-------|
| **Stripe** | Global, USD/EUR, SaaS subscriptions, excellent API | Foreign exchange fees for INR transactions |
| **Razorpay** | India-based businesses, INR, UPI, netbanking, EMI | Best choice for Indian market |
| **PayU** | India alternative to Razorpay | Less developer-friendly than Razorpay |
| **Cashfree** | India, fast settlements, good API | Growing competitor to Razorpay |

**For Indian projects:** Default to Razorpay. Add Stripe only if accepting international payments.

---

## CI/CD

| Option | Best For | Notes |
|--------|----------|-------|
| **GitHub Actions** | GitHub repos, standard, large marketplace | Default choice for most teams |
| **GitLab CI** | GitLab repos, self-hosted option | Built-in container registry |
| **CircleCI** | Mature, parallelism, orbs ecosystem | Slightly more setup than GitHub Actions |
| **Jenkins** | Self-hosted, enterprise, total control | Heavy ops burden — avoid for small teams |

---

## Compatibility Matrix

Quick-reference for common stack combinations that work well together:

| Stack Name | Frontend | Backend | DB | Hosting | Auth |
|-----------|----------|---------|-----|---------|------|
| **T3 Stack** | Next.js + tRPC | Node.js + tRPC | PostgreSQL (Prisma) | Vercel + PlanetScale | NextAuth |
| **Supabase Stack** | Next.js | Node.js / Supabase Edge | Supabase (PostgreSQL) | Vercel | Supabase Auth |
| **MERN** | React | Node.js + Express | MongoDB | Render / Railway | Custom JWT |
| **Django Stack** | React / Next.js | Python + Django | PostgreSQL | Railway / AWS | Django Auth |
| **FastAPI Stack** | Next.js / React | Python + FastAPI | PostgreSQL | Railway / AWS | Auth0 / Supabase Auth |
| **Enterprise AWS** | React (CloudFront) | NestJS (ECS) | RDS PostgreSQL | AWS | Cognito |
