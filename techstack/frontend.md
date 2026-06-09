# Frontend — React + Vite

## Framework & Version

**React 19** with **Vite 6** as the build tool.

Chosen over Next.js because this is an internal SPA with zero SEO requirements. All API logic lives in FastAPI — the frontend is purely a client-side data consumer. Vite provides fast HMR, simple config, and builds to static files for S3+CloudFront deployment.

---

## Key Libraries

| Category | Library | Version | Why |
|----------|---------|---------|-----|
| UI Components | shadcn/ui | latest | Copy-paste components, full control, built on Radix primitives |
| Styling | Tailwind CSS | 4 | Utility-first, design tokens via CSS variables, no runtime CSS |
| Routing | React Router | v7 | Standard SPA routing, nested layouts, route-based code splitting |
| Server State | TanStack Query | v5 | API response caching, background refetch, loading/error states |
| Client State | Zustand | v5 | Lightweight, no boilerplate — for UI state (active role, filters, sidebar) |
| Forms | React Hook Form + Zod | latest | Performant forms with schema-based validation matching FSD rules |
| Tables | TanStack Table | v8 | Headless table logic — sorting, filtering, pagination |
| HTTP Client | Axios | latest | Interceptors for JWT refresh, consistent error handling |
| Date Handling | date-fns | latest | Tree-shakeable, no moment.js bloat |
| Icons | Lucide React | latest | Consistent icon set, pairs with shadcn/ui |
| Charts | Recharts | latest | React-native charting for utilization dashboards |
| Toasts | sonner | latest | Minimal toast notifications |

---

## Folder Structure

Feature-based organization. Each module from the spec is a folder:

```
src/
├── app/
│   ├── routes/                    # React Router route definitions
│   │   ├── _layout.tsx            # Root layout (sidebar + role bar)
│   │   ├── login.tsx
│   │   ├── dashboard.tsx
│   │   ├── admin/
│   │   │   ├── users.tsx
│   │   │   └── roles.tsx
│   │   ├── clients/
│   │   ├── projects/
│   │   ├── resources/
│   │   ├── allocations/
│   │   ├── utilization/
│   │   └── worklogs/
│   └── App.tsx                    # Router provider + query provider
├── modules/                       # Feature modules (mirrors backend)
│   ├── auth/
│   │   ├── api.ts                 # API calls (login, me, refresh)
│   │   ├── hooks.ts               # useAuth, useCurrentUser
│   │   ├── store.ts               # Zustand auth store
│   │   └── components/
│   │       ├── LoginForm.tsx
│   │       └── RoleGuard.tsx
│   ├── users/
│   │   ├── api.ts
│   │   ├── hooks.ts
│   │   └── components/
│   ├── clients/
│   ├── projects/
│   ├── resources/
│   ├── allocations/
│   ├── utilization/
│   └── worklogs/
├── shared/
│   ├── components/                # Reusable UI (DataTable, PageHeader, StatusBadge)
│   ├── hooks/                     # useDebounce, usePagination, useRBAC
│   ├── lib/                       # axios instance, date utils, currency formatter
│   ├── types/                     # Shared TypeScript types
│   └── constants/                 # Roles, statuses, data types
├── styles/
│   └── globals.css                # Tailwind imports + CSS variables
├── main.tsx                       # Entry point
└── vite-env.d.ts
```

---

## Build & Bundler

**Vite 6** with default React plugin.

```ts
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') }
  },
  server: {
    proxy: {
      '/api': 'http://localhost:8000'  // FastAPI dev server
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
})
```

Build output is a static `dist/` folder deployed to S3.

---

## Testing Stack

| Type | Tool | Scope |
|------|------|-------|
| Unit | Vitest | Utility functions, hooks, store logic |
| Component | Vitest + Testing Library | Component rendering, user interactions |
| E2E | Playwright | Critical flows: login, create assignment, role switching |

---

## Code Quality

- **TypeScript strict mode** — `"strict": true` in tsconfig
- **ESLint** — `eslint-config-react-app` + import ordering
- **Prettier** — consistent formatting, 100 char line width
- **Husky + lint-staged** — pre-commit checks

---

## Performance Considerations

All pages are CSR (client-side rendered). No SSR needed.

| Technique | Applied Where |
|-----------|---------------|
| Code splitting | React Router lazy routes — each module loads on demand |
| Query caching | TanStack Query — staleTime of 30s for list views, 5min for config data |
| Virtualization | TanStack Virtual for tables with 100+ rows (resource list, audit log) |
| Debounced search | 300ms debounce on search inputs to reduce API calls |

---

## Environment Variables

All prefixed with `VITE_` (Vite convention for client-exposed vars):

| Variable | Purpose | Public? |
|----------|---------|---------|
| `VITE_API_URL` | FastAPI backend URL | Yes (client-side) |
| `VITE_APP_NAME` | Display name | Yes |
| `VITE_SENTRY_DSN` | Sentry error tracking | Yes |

No secrets in the frontend. All sensitive operations are server-side.
