# Prompt: Create the `new-requirement` Claude Code Skill

Create a Claude Code skill called `new-requirement` that enforces a strict gated workflow whenever a user describes a new requirement, change request, or feature addition to any software project.

## Skill Identity

- **Name:** `new-requirement`
- **Trigger phrases:** "new requirement", "add feature", "change request", "I need to add", "we need a new", "add this capability", "add a command", "support X", "we need to handle", or when a user describes new functionality that doesn't exist in the current project
- **Description:** Enforces a gated workflow: analyze requirement → update documentation/specs → create tickets → ask about scheduling → optionally implement with ticket status transitions. Prevents ad-hoc coding without a documentation/ticket trail. Works with any project type — web apps, CLI tools, libraries, data pipelines, mobile apps, microservices.

## File Structure

Generate these files:

```
new-requirement/
├── SKILL.md                          # Main skill instructions (Claude Code)
├── SETUP.md                          # Setup guide
├── claude-ai-project-prompt.md       # Condensed version for Claude.ai projects
└── references/
    └── workflow-checklist.md          # Step-by-step checklist the skill follows
```

## Design Principles

1. **Project-agnostic.** The skill must work with ANY project — different tech stacks, folder structures, issue trackers, methodologies, and scales. It discovers project conventions at runtime. Never embed project-specific values.

2. **Convention discovery over hardcoding.** Don't embed file paths, issue tracker keys, field IDs, transition IDs, tech stack choices, or folder layouts. Instead:
   - Read CLAUDE.md / .claude/instructions / README.md to learn conventions
   - Scan the repo structure to find documentation, spec, and ticket directories
   - Detect available MCP tools to determine issue tracker integration
   - Adapt output format to match existing patterns in the project
   - Match the project's language — if docs/tickets are in a language other than English, follow that language

3. **Issue tracker agnostic.** Detect which MCP tools are available at runtime: Atlassian (JIRA/Confluence), Linear, GitHub Issues, GitLab Issues, Azure DevOps, or others. If none are connected, fall back to creating local markdown files.

4. **Methodology agnostic.** Don't assume Scrum. The project might use Kanban (no sprints/iterations), Scrum (sprints with story points), continuous flow, or no methodology at all. Discover from the tracker and existing tickets.

5. **Scale-appropriate.** A one-file script getting a new flag doesn't need the same ceremony as a monorepo getting a new microservice. Scale the workflow formality to the project's complexity, detected in Phase 0.

6. **Graceful degradation.** Each capability works independently:
   - No spec/doc files? → Skip Phase 2, go straight to tickets
   - No issue tracker MCP? → Create tickets as local markdown files
   - No codebase yet? → Ask user: scaffold project or stop after tickets
   - No CLAUDE.md? → Ask the user about project conventions
   - No tests infrastructure? → Ask user before creating tests
   - No linter configured? → Skip lint step

## The Workflow (5 Phases — Strictly Sequential)

### Phase 0: Project Discovery (runs once per session)

On first invocation, build a project profile:

1. **Read project instructions** — look for CLAUDE.md, .claude/instructions, README.md, CONTRIBUTING.md, or similar
2. **Identify project type** — web app, CLI tool, library/SDK, data pipeline, mobile app, microservices, monorepo, single script, or other. Determines what "component," "interface," and "implementation" mean.
3. **Scan for documentation/spec files** — find directories containing requirements, schemas, API specs, interface definitions, proto files, etc. (could be `modules/`, `specs/`, `docs/`, `api/`, or none)
4. **Scan for ticket/task files** — sprint plans, story breakdowns, changelogs, TODO files (could be `tickets/`, `stories/`, `CHANGELOG.md`, or none)
5. **Detect issue tracker** — scan all available MCP tools for issue/project management capabilities. Look for tool names containing: jira, atlassian, linear, github (issue/PR related), gitlab, azure, shortcut, notion, asana, trello. If multiple found, ask the user which to use.
6. **Detect methodology** — from tracker: does it have sprints/iterations/cycles? Story points? Or flat task lists (Kanban/continuous flow)?
7. **Detect tech stack** — scan for build files (package.json, pyproject.toml, go.mod, Cargo.toml, Makefile, Dockerfile, *.csproj, etc.). If multiple found, determine if monorepo with multiple services or single project with layers. Note all stacks and which directories they apply to.
8. **Detect infrastructure** — does the project have: test framework? linter config? CI/CD? versioning/changelog? access control system? audit logging? These determine which Phase 5 steps apply.
9. **Determine formality level:**
   - **Full** — project has spec files, issue tracker, test suite, CI → run all phases with detailed gates
   - **Standard** — project has some of the above → run all phases, skip what's missing
   - **Lightweight** — single-file or small project with no specs/tracker/tests → compress Phases 1-3 into a single confirmation before implementing
10. **Cache this context** for subsequent invocations in the same session

If the project has no spec/doc system, ask:

```
I don't see a structured documentation system in this project. How should I document this requirement?
  a) Create spec files following a standard structure (I'll set one up)
  b) Just create tickets — no documentation needed
  c) Let me tell you about our project structure
```

### Phase 1: Analyze & Classify

Read the user's requirement. Then:

1. **Classify the change type** using vocabulary appropriate to the project type discovered in Phase 0:
   - `NEW_COMPONENT` — entirely new top-level unit (module, command, service, DAG, package export, screen — whatever the project calls its components)
   - `EXTEND_COMPONENT` — new feature within existing component
   - `CROSS_CUTTING` — spans multiple components
   - `DATA_MODEL_CHANGE` — new/modified data structures (DB schema, proto files, type definitions, config schema, Firestore rules, etc.)
   - `LOGIC_CHANGE` — new calculation, validation, algorithm, or business constraint
   - `INTERFACE_ONLY` — change only to the project's external surface (UI, CLI flags, API endpoints, library exports, event schemas)
   - `CONFIG_CHANGE` — configuration or environment change

2. **Identify affected files** — list every doc/spec file that needs updating (based on Phase 0 discovery). If the project has no spec system, note "no specs to update."

3. **Check dependencies** — does this require components/entities/services that don't exist yet?

4. **Estimate scope** — use the project's existing estimation format if one exists (story points, T-shirt sizes, hours). If no pattern exists, provide a brief complexity note ("straightforward", "moderate", "significant") without forcing a framework.

5. **Present analysis to user** — scale format to project complexity:

   **Full formality (projects with spec systems):**

   ```
   ## Requirement Analysis

   **Type:** EXTEND_COMPONENT ({affected component})
   **Scope:** {estimate}
   **Affected docs:** {list of files to update}
   **Dependencies:** {list or "None"}
   **Risk:** {Low/Medium/High — reason}

   Proceed with documentation updates?
   ```

   **Lightweight (small/simple projects):**

   ```
   I'll add {description} to {file(s)}. This is a {complexity} change. Proceed?
   ```

Wait for user confirmation.

### Phase 2: Update Documentation/Spec Files

*Skip this phase if Phase 0 found no spec system and user chose not to create one.*

For each affected file identified in Phase 1:

1. Read the current file
2. Make surgical updates — add/modify only what the requirement needs
3. **Match existing patterns exactly** — if the project uses a specific format for data definitions, interface specs, or component docs, follow that exact format. Don't impose a new structure.
4. Maintain cross-references — if you add a field in one place, update all files that reference it
5. If the change affects the project's external interface (API endpoints, CLI commands, library exports, gRPC proto files, event schemas, etc.), follow the project's existing interface conventions
6. If the project has versioning artifacts (CHANGELOG.md, version field in package manifests), include version/changelog updates
7. If the project uses a canonical spec document with numbered sections, add cross-references to relevant sections

**Rules:**
- Never remove existing content unless the requirement explicitly replaces something. If removal is needed, flag it explicitly in the summary and get user confirmation.
- For each affected spec, add entries following the project's existing format — don't invent field checklists. Infer required fields from existing entries in that file.
- If the project has an access control system (discovered in Phase 0), include permission specifications for new interfaces.
- For gRPC/protobuf projects, treat .proto file updates as part of this phase.

Present summary and wait for confirmation:

```
## Documentation Updates Complete

Updated N files:
  + {file} — {what changed}
  ...

Proceed to ticket creation?
```

### Phase 3: Create Tickets

Generate tickets following the project's established patterns:

1. **Read existing ticket files** (if any) to learn the format — structure, naming convention, field patterns, hierarchy model
2. **Size the work** into a reasonable number of trackable units (typically 1-3, but adapt to the project's granularity norms)
3. **Match the project's ticket format exactly** — don't invent a new structure
4. **Use the issue hierarchy the tracker supports:**
   - JIRA: epic/story/task (or whatever issue types exist in the project)
   - Linear: project/issue/sub-issue
   - GitHub: issue with labels, optionally linked to milestones
   - GitLab: epic/issue or just issues
   - Flat trackers: simple task items
   - Discover from existing tickets, don't assume a hierarchy
5. **If issue tracker MCP is available:**
   - Discover project-specific config (project key, available issue types, custom fields, workflow states) by querying the MCP tools, checking project memory, or asking the user
   - Create issues with proper hierarchy
   - Set estimates/labels/description
   - DO NOT assign to iteration/sprint/cycle yet (that's Phase 4)
6. **If no issue tracker MCP:**
   - Create/update local ticket markdown files
   - Note issue keys as "TBD — create manually in {tracker}"
7. **Update local ticket files** if they exist — append items, update summary tables and totals

Present ticket summary and ask the Phase 4 question.

### Phase 4: Scheduling Decision (USER GATE)

Adapt terminology to the project's methodology (discovered in Phase 0):

**For projects with iterations (sprints/cycles):**

```
Should I implement this now?
  a) Yes — assign to current {sprint/cycle/iteration} and start implementation
  b) Assign to {sprint/cycle/iteration} but don't implement yet
  c) Leave in backlog — implement later
```

**For Kanban / no-iteration projects:**

```
Should I implement this now?
  a) Yes — start implementation now
  b) No — leave in backlog for later
```

- **Implement now**: Assign to iteration (if tracker supports it), transition to the project's "active work" state (discovered via tracker API — not hardcoded), proceed to Phase 5
- **Schedule only**: Assign to iteration, stop
- **Backlog**: Stop, tickets stay unscheduled

### Phase 5: Implement

If the user chose to implement:

1. **Transition tickets** to the project's "active/in-progress" state (via MCP if available, discovered from tracker workflow states — don't hardcode state names). If the tracker doesn't support transitions (e.g., GitHub Issues), skip.
2. **Build according to project conventions** discovered in Phase 0. The specific artifacts depend on the project type — follow CLAUDE.md / project instructions for coding standards. Common patterns include:
   - Data model changes (DB migrations, proto file updates, type definitions, config schemas, Firestore rules — whatever the project uses)
   - Core logic implementation
   - Interface/surface changes (API handlers, CLI command handlers, library exports, UI components, DAG definitions — whatever the project exposes)
   - Integration points and cross-service concerns
   - For gRPC projects: regenerate stubs after proto changes
   - For BaaS projects (Firebase/Supabase/Amplify): update client code + service config (security rules, cloud functions)
3. **Write tests** — IF the project has existing test infrastructure (test framework, test directory, test runner configured). Follow existing test patterns and naming conventions. If no tests exist, ask: "This project has no test setup. Should I (a) add tests and set up the test infrastructure, (b) skip tests for now, or (c) add a test TODO to the ticket?"
4. **Run tests** — all existing + new tests must pass. Skip if no test runner exists.
5. **Run linters** — if the project has them configured (detected via .eslintrc, pyproject.toml [tool.ruff], .golangci.yml, etc.). Skip if none configured.
6. **Update versioning artifacts** — if CHANGELOG.md or version fields exist and the change warrants it
7. **Transition tickets** to the project's "completed/done" state (via MCP if available). For GitHub Issues, close the issue. If no tracker, note completion in local files.

Present completion summary with files changed, test results (if applicable), and ticket statuses.

## Critical Rules

1. **NEVER skip to implementation without analysis.** For full/standard formality projects, run Phases 1-3 first. For lightweight projects (Phase 0 detected no specs, no tracker, small scope), compress Phases 1-3 into a single confirmation.
2. **NEVER create tickets without updating specs/docs first** (unless the project has no documentation system).
3. **NEVER modify spec/doc files without showing the user what changed.** Present summaries at each gate.
4. **Wait for explicit user confirmation** between Phase 1→2, Phase 2→3, and at Phase 4. Phases within 3 and 5 can flow continuously.
5. **Discover, don't assume.** Read the project's actual files to learn conventions. Never hardcode project-specific values (keys, IDs, paths, states, tech choices, field names).
6. **If the requirement conflicts with existing specs/docs**, flag the conflict in Phase 1 and ask the user how to resolve before proceeding.
7. **Follow ALL project-level coding conventions** during implementation.
8. **Match existing patterns.** If the project's ticket files use a specific format, use that format. If tests follow a naming convention, follow it. If specs use a template, use that template.
9. **Scale ceremony to project complexity.** A one-line config change in a small project should not require the same overhead as a new microservice in a monorepo.

## Issue Tracker MCP Detection

At runtime, scan all available MCP tools for issue/project management capabilities. Look for tool names or prefixes containing:

- `atlassian` / `jira` → JIRA (create issues, set sprint field, transition statuses)
- `linear` → Linear (create issues, set cycle, update status)
- `github` (issue/PR tools) → GitHub Issues (create issues, set labels/milestones, close)
- `gitlab` → GitLab Issues (create issues, set milestones, labels)
- `azure` / `devops` → Azure DevOps (create work items)
- `shortcut` / `notion` / `asana` / `trello` → respective trackers

If multiple trackers are detected, ask the user which one to use. If none detected, fall back to local markdown files.

For the chosen tracker, discover project-specific config (project key, available issue types, custom fields, workflow states, sprint/cycle/iteration field names, transition IDs) by:

1. Checking project memory files
2. Checking CLAUDE.md or project docs
3. Querying the MCP tools (list projects, get available transitions/states, etc.)
4. Asking the user as last resort

## Multi-Repo Awareness

In Phase 0, detect if the project is part of a multi-repo setup (references to sibling repos, monorepo with multiple services, or Git submodules). If a requirement spans multiple repos/services:

- Identify affected repos in Phase 1
- Note that implementation may require changes across repos
- Track which repo each ticket/change belongs to

## SETUP.md Content

The setup guide should explain:

- This skill works with any project type and structure — it discovers conventions at runtime
- For full issue tracker integration, connect the appropriate MCP (Atlassian, Linear, GitHub, GitLab, etc.)
- The skill reads from and writes to the project's documentation, spec files, ticket files, and codebase
- It works in degraded mode without any MCP — creating local ticket files instead
- It scales its formality to the project's complexity — lightweight for small projects, full ceremony for large ones
- List the trigger phrases
- Show usage examples across different project types:
  - "New requirement: users should be able to set notification preferences" (web app)
  - "Add a `--dry-run` flag to the deploy command" (CLI tool)
  - "We need a new data source connector for Salesforce" (data pipeline)
  - "Add a `.groupBy()` method to the Collection class" (library)
  - "Change request: support multi-region failover in the auth service" (microservices)

## Tone

Be structured and methodical. Present clear summaries at each gate. Use tables for listings. Don't be verbose in analysis — classify, list affected files, estimate, and move on. The user wants a reliable process, not a conversation. Scale communication formality to the project's complexity.
