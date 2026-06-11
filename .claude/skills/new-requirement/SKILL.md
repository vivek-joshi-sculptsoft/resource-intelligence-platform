---
name: new-requirement
description: "Enforces a strict gated workflow whenever a user describes a new requirement, change request, or feature addition to any software project. Triggers on: 'new requirement', 'add feature', 'change request', 'I need to add', 'we need a new', 'add this capability', 'add a command', 'support X', 'we need to handle', or any description of new functionality that doesn't exist yet. Workflow: analyze → update docs/specs → create tickets → ask about scheduling → optionally implement. Prevents ad-hoc coding without a documentation and ticket trail. Works with any project type — web apps, CLI tools, libraries, data pipelines, mobile apps, microservices, monorepos — and any issue tracker."
---

# New Requirement Skill

You enforce a strict gated workflow whenever a user describes new functionality. No ad-hoc coding. Every requirement goes through analysis, documentation, and ticketing before a single line of code is written.

You are not a code generator with a wrapper. You are a disciplined engineering process that ensures every change is analyzed, documented, tracked, and reviewed before implementation.

---

## Design Principles

**Project-agnostic.** Never hardcode paths, issue tracker keys, transition IDs, state names, field names, tech stacks, or folder structures. Discover everything at runtime.

**Convention discovery over assumption.** Read CLAUDE.md, README.md, existing tickets, existing spec files. Match whatever format already exists. If no format exists, ask.

**Graceful degradation.** No spec system → skip Phase 2. No issue tracker MCP → create local markdown files. No test infrastructure → ask before adding any. No CLAUDE.md → ask about conventions. Each phase degrades independently.

**Scale-appropriate ceremony.** A one-file script getting a new flag is not the same as a new microservice in a monorepo. Lightweight projects get compressed confirmation. Full-formality projects get all gates.

---

## Phase 0: Project Discovery

*Runs once per session. Cache the result — don't re-run for subsequent requirements in the same session.*

### 0.1 Read Project Instructions
Look for (in priority order): `CLAUDE.md`, `.claude/instructions`, `.claude/CLAUDE.md`, `README.md`, `CONTRIBUTING.md`. Read the first one found.

### 0.2 Identify Project Type
Detect from build files, directory structure, and project instructions:

| Signal | Project Type |
|---|---|
| `package.json` with `bin` field, `cobra`, `click`, `argparse`, `clap` | CLI tool |
| `package.json` without `bin`, React/Vue/Angular | Web app (frontend) |
| Express/FastAPI/Django/Rails/Spring/Go HTTP handlers | Web app (backend/API) |
| Both frontend and backend present | Web app (full-stack) |
| `pyproject.toml` + src layout, `go.mod` with exported packages, no main entry | Library/SDK |
| DAG files, `airflow`, `prefect`, `dagster`, `dbt` | Data pipeline |
| `pubspec.yaml`, `*.xcodeproj`, Kotlin/Swift sources | Mobile app |
| Multiple `Dockerfile`s or services, docker-compose with 3+ services | Microservices |
| Multiple apps/packages under one root with a workspace config | Monorepo |
| `.proto` files | gRPC service |
| `firebase.json`, `supabase/config.toml`, `amplify.yml` | BaaS-backed app |
| Single script file or very small directory | Single script / small project |

This determines vocabulary for "component," "interface," and "implementation" throughout the workflow.

### 0.3 Scan for Documentation / Spec Files
Look for directories or files containing: requirements, schemas, API specs, interface definitions, proto files, data models, architecture docs. Common patterns: `modules/`, `specs/`, `docs/`, `api/`, `schema/`, `proto/`, `architecture/`, `design/`, `ADRs/`, `rfcs/`. Note every file that exists.

### 0.4 Scan for Ticket / Task Files
Look for: `tickets/`, `stories/`, `tasks/`, `.tasks/`, `CHANGELOG.md`, `TODO.md`, `ROADMAP.md`, sprint plan files, or similar. Note every file that exists.

### 0.5 Detect Issue Tracker MCP
Scan all available MCP tool names for issue/project management capabilities:

| Tool name contains | Tracker |
|---|---|
| `atlassian`, `jira` | Jira (Atlassian) |
| `linear` | Linear |
| `github` (issue/PR tools) | GitHub Issues |
| `gitlab` | GitLab Issues |
| `azure`, `devops` | Azure DevOps |
| `shortcut` | Shortcut |
| `notion` | Notion |
| `asana` | Asana |
| `trello` | Trello |

If multiple trackers detected, ask: "I see multiple issue trackers available ({list}). Which should I use?"
If none detected, fall back to local markdown ticket files.

### 0.6 Detect Methodology
From the tracker or existing ticket files: does the project use sprints/cycles/iterations with story points? Or flat task lists (Kanban/continuous flow)? Or no formal methodology? This controls Phase 4 vocabulary.

### 0.7 Detect Tech Stack Details
Scan for build and config files. Note all stacks and which directories they apply to (important for monorepos). Record:
- Language(s) and runtimes
- Test framework (if any): Jest, pytest, Go test, RSpec, JUnit, etc.
- Linter config (if any): `.eslintrc*`, `pyproject.toml [tool.ruff]`, `.golangci.yml`, etc.
- CI/CD config: `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, etc.
- Changelog/versioning: `CHANGELOG.md`, version fields in manifests

### 0.8 Determine Formality Level

| Condition | Formality |
|---|---|
| Has spec files AND issue tracker AND test suite | **Full** — all phases, all gates |
| Has some of the above | **Standard** — all phases, skip what's missing |
| Single-file or tiny project, no specs, no tracker, no tests | **Lightweight** — compress Phases 1-3 into one confirmation |

### 0.9 Handle Missing Docs System
If no spec/doc system found, ask:
```
I don't see a documentation system in this project. How should I document this requirement?
  a) Create spec files (I'll set up a structure)
  b) Just create tickets — no docs needed
  c) Tell me about your project structure
```

---

## Phase 1: Analyze & Classify

Read the requirement. Classify, identify, estimate, present. Then wait for confirmation.

### 1.1 Change Type
Use vocabulary appropriate to the project type from Phase 0:

| Type | When |
|---|---|
| `NEW_COMPONENT` | Entirely new top-level unit (module, service, command, package, screen, DAG) |
| `EXTEND_COMPONENT` | New feature within an existing component |
| `CROSS_CUTTING` | Spans multiple components |
| `DATA_MODEL_CHANGE` | New/modified data structures (schema, proto, type defs, config schema) |
| `LOGIC_CHANGE` | New calculation, validation, algorithm, or business constraint |
| `INTERFACE_ONLY` | Change only to the external surface (API endpoint, CLI flag, library export, event schema, UI screen) |
| `CONFIG_CHANGE` | Configuration or environment change only |

### 1.2 Affected Files
List every spec/doc/ticket file that needs updating. If no spec system, note "no specs to update."

### 1.3 Dependencies
Does this require components/entities/services that don't exist yet? List them. If dependencies are missing, flag that Phase 2 may need to create prerequisite specs first.

### 1.4 Scope Estimate
Use the project's existing estimation format if one is in use. Otherwise:
- `straightforward` — well-understood, clear scope, no new dependencies
- `moderate` — touches multiple files, some design decisions needed
- `significant` — new component, multiple cross-cutting concerns, or ambiguous requirements

### 1.5 Conflict Check
If the requirement conflicts with something in existing spec/doc files, flag it explicitly. Ask the user how to resolve before proceeding.

### 1.6 Present Analysis

**Full/Standard formality:**
```
## Requirement Analysis

**Type:** {change type} — {affected component or area}
**Scope:** {estimate}
**Affected docs:** {list of files, or "none"}
**Dependencies:** {list, or "None"}
**Risk:** {Low/Medium/High} — {one-line reason}
**Conflicts:** {describe any, or "None"}

Proceed with documentation updates?
```

**Lightweight:**
```
I'll {description of change} in {file(s)}. This is a {complexity} change.

Proceed?
```

**Wait for confirmation before Phase 2.**

---

## Phase 2: Update Documentation / Spec Files

*Skip if Phase 0 found no spec system and user chose not to create one.*

For each affected file from Phase 1:

1. Read the current file
2. Make surgical additions — only what the requirement needs
3. **Match the existing format exactly.** Infer required fields from existing entries in that file. Don't impose new structure.
4. Maintain cross-references — if a field appears in multiple files, update all of them consistently
5. For external-facing changes (API, CLI, library exports, event schemas, proto files), follow the project's existing interface conventions
6. If the project has access control or permission systems (detected in Phase 0), include permission specs for new interfaces
7. For versioned projects, include changelog or version update if the change warrants it (breaking change, new public API, etc.)
8. For gRPC/protobuf projects, treat `.proto` updates as part of this phase

**Rule: Never remove existing content without explicit user confirmation.** If removal is required, flag it in the summary and ask.

**Rule: If the project has no spec system and user chose option (a) in Phase 0.9**, set up a minimal structure appropriate to the project type. Ask the user to confirm the structure before creating it.

Present summary and wait for confirmation:
```
## Documentation Updated

{N} file(s) updated:
  + {filename} — {what was added/changed}
  ...

{If anything was flagged for removal}: ⚠ Removal needed: {description} — confirm?

Proceed to ticket creation?
```

---

## Phase 3: Create Tickets

Generate tickets following the project's established patterns.

### 3.1 Learn the Format
If local ticket files exist, read one to learn: structure, naming convention, field patterns, hierarchy. Match exactly.

### 3.2 Size the Work
Break into trackable units appropriate to the project's granularity norms. Typically 1-3 tickets. For a `NEW_COMPONENT`, may be more. For `CONFIG_CHANGE`, often just 1.

### 3.3 Issue Tracker MCP Path
If a tracker MCP is available:
1. Discover project config: project key/ID, available issue types, custom fields, workflow states, sprint/cycle field names. Check project files first, then query MCP tools, then ask user.
2. Create issues with proper hierarchy for the tracker:
   - Jira: story under epic (or whatever types the project uses)
   - Linear: issue under project
   - GitHub Issues: issue with labels + milestone
   - GitLab: issue with labels + milestone
   - Others: adapt to available hierarchy
3. Set: title, description with acceptance criteria, estimate/points (if used), labels/components
4. **Do NOT assign to sprint/iteration/cycle yet** — that is Phase 4

### 3.4 No Tracker MCP Path
Create or update local ticket markdown files. Follow the format of existing ticket files exactly. If none exist, use this minimal format and note it for future consistency:

```markdown
## {TICKET-ID}: {Title}

**Type:** {Story/Task/etc}
**Status:** Backlog
**Estimate:** {size}
**Labels:** {list}

### Description
{description}

### Acceptance Criteria
- [ ] {criterion}

### Dependencies
{list or None}
```

### 3.5 Update Local Files
If local ticket summary files exist (sprint plans, ROADMAP.md, CHANGELOG.md), append or update entries.

Present ticket summary and transition to Phase 4:
```
## Tickets Created

{table: ID | Title | Type | Estimate}

{If tracker MCP}: Created in {tracker name}. Not yet assigned to {sprint/cycle/iteration}.
{If local files}: Created in {filename}. Mark as TBD in {tracker} manually if needed.
```

---

## Phase 4: Scheduling Decision (User Gate — ALWAYS SHOWN)

Adapt terminology to the methodology discovered in Phase 0.

**Iteration-based (sprints/cycles):**
```
Should I implement this now?
  a) Yes — assign to current {sprint/cycle/iteration} and implement
  b) Assign to {sprint/cycle/iteration} — don't implement yet
  c) Leave in backlog
```

**Kanban / no iterations:**
```
Should I implement this now?
  a) Yes — start implementation
  b) No — leave in backlog
```

- **Option a**: If tracker supports it, assign to current iteration. Transition tickets to the "active/in-progress" state (discovered from tracker — not hardcoded). Proceed to Phase 5.
- **Option b**: Assign to iteration (if applicable). Stop.
- **Option c**: Stop. Tickets stay unscheduled.

---

## Phase 5: Implement

Only runs on explicit user choice from Phase 4.

### 5.1 Transition Tickets to Active State
Via MCP if available. Discover the "in-progress" state name from the tracker's workflow states — do not hardcode. For GitHub Issues, no transition needed (add a label if applicable). For local files, update the `Status` field.

### 5.2 Build
Follow ALL conventions from CLAUDE.md / project instructions. Adapt to the project type discovered in Phase 0:

| Project type | What "implement" means |
|---|---|
| Web app (backend) | Route handler, service/domain logic, repository/query, request validation, response schema |
| Web app (frontend) | Component(s), state management, API integration, routing |
| Web app (full-stack) | All of the above |
| CLI tool | Command handler, flag/arg parsing, help text update |
| Library/SDK | Public API (exports), implementation, type definitions |
| Data pipeline | DAG definition, operators/tasks, transformation logic |
| Mobile app | Screen/component, navigation, API client, state |
| Microservices | Service logic, API contract, event publishing/consuming |
| gRPC service | Proto file update, stub regeneration, handler implementation |
| BaaS-backed | Client-side logic + service config (security rules, cloud functions) |

For gRPC projects: regenerate stubs after any `.proto` changes before writing handlers.
For BaaS projects (Firebase/Supabase/Amplify): update both client code and service-side config.

### 5.3 Tests
**Only if the project has existing test infrastructure** (test framework, test directory, configured runner — detected in Phase 0).
- Follow existing test patterns and naming conventions exactly
- Cover: happy path, edge cases, error cases relevant to the requirement
- If no test infrastructure exists, ask: "This project has no test setup. Should I (a) add tests and set up the test infrastructure, (b) skip tests, or (c) add a test TODO to the ticket?"

### 5.4 Run Tests
Only if a test runner is configured. All existing + new tests must pass. Report failures before declaring done.

### 5.5 Run Linter
Only if a linter is configured (detected in Phase 0). Fix any issues introduced by the new code.

### 5.6 Versioning Artifacts
If CHANGELOG.md or version fields exist and the change is user-visible or public-API-affecting, add a changelog entry following the existing format.

### 5.7 Transition Tickets to Done
Via MCP if available. Discover the "done/completed" state name from the tracker. For GitHub Issues, close the issue. For local files, update `Status` to `Done`.

### 5.8 Completion Summary
```
## Implementation Complete

**Tickets:** {IDs} → {done state}

**Files changed:**
  {filename} — {what changed}
  ...

**Tests:** {N passed / skipped — reason}
**Lint:** {clean / skipped — reason}
**Changelog:** {updated / skipped — reason}
```

---

## Critical Rules

1. **Never skip to implementation.** Full/Standard projects: run Phases 1-3 first. Lightweight projects: compress Phases 1-3 into one confirmation.
2. **Never create tickets without updating specs first** — unless the project has no documentation system.
3. **Never modify spec files without showing the user what changed.** Show summary at each phase gate.
4. **Wait for explicit confirmation** between Phase 1→2, Phase 2→3, and at Phase 4. Steps within Phases 3 and 5 flow continuously.
5. **Discover, don't assume.** Read actual project files. Never hardcode keys, IDs, state names, paths, or field names.
6. **Conflict = stop.** Flag it in Phase 1, resolve before proceeding.
7. **Follow all project coding conventions** found in CLAUDE.md or project instructions.
8. **Match existing patterns.** Ticket format, test naming, spec template — whatever exists, follow it.
9. **Scale ceremony to complexity.** Config flag in a small script ≠ new microservice in a monorepo.
10. **Multi-repo awareness.** If the requirement spans multiple repos, identify affected repos in Phase 1, note cross-repo work in tickets, track per-repo ownership.

---

## Reference Files

| File | When to Read |
|---|---|
| `references/workflow-checklist.md` | At the start of every invocation — use as a runtime checklist to ensure no step is skipped |
