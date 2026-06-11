# New Requirement — Runtime Workflow Checklist

Read this at the start of every invocation. Use it as a live checklist to ensure no step is skipped.

---

## Phase 0: Project Discovery
*(Run once per session. If already cached, skip.)*

- [ ] Read CLAUDE.md / .claude/instructions / README.md / CONTRIBUTING.md (first found)
- [ ] Identify project type (CLI / web app / library / data pipeline / mobile / microservices / monorepo / single script)
- [ ] Scan for documentation/spec directories and files — note every one found
- [ ] Scan for ticket/task directories and files — note every one found
- [ ] Scan MCP tool names for issue tracker signals (atlassian/jira / linear / github / gitlab / azure / shortcut / notion / asana / trello)
  - If multiple found → ask user which to use
  - If none found → fall back to local markdown files
- [ ] Detect methodology from tracker or ticket files (sprint-based / Kanban / none)
- [ ] Detect tech stack from build files (language, framework, runtime)
- [ ] Detect test framework (Jest / pytest / go test / RSpec / JUnit / none)
- [ ] Detect linter config (.eslintrc / pyproject.toml[ruff] / .golangci.yml / none)
- [ ] Detect CI/CD config (GitHub Actions / GitLab CI / Jenkins / none)
- [ ] Detect versioning artifacts (CHANGELOG.md / version in manifest / none)
- [ ] Determine formality level: Full / Standard / Lightweight
- [ ] Handle missing docs system if needed (ask user: create structure / tickets only / tell me more)
- [ ] Cache all of the above for this session

**Formality gate:**
- Lightweight project → compress Phases 1-3 into single confirmation, then jump to Phase 4
- Full/Standard → proceed through each phase with gates

---

## Phase 1: Analyze & Classify
*(Wait for user confirmation at end)*

- [ ] Classify change type: NEW_COMPONENT / EXTEND_COMPONENT / CROSS_CUTTING / DATA_MODEL_CHANGE / LOGIC_CHANGE / INTERFACE_ONLY / CONFIG_CHANGE
- [ ] List affected documentation/spec files (use vocabulary from Phase 0 project type)
- [ ] Check for prerequisite dependencies — do any required components/entities/services not yet exist?
- [ ] Estimate scope using project's format (or: straightforward / moderate / significant)
- [ ] Check for conflicts with existing specs — if any, flag and STOP until resolved
- [ ] Present analysis table to user
- [ ] **WAIT FOR CONFIRMATION** before Phase 2

---

## Phase 2: Update Documentation / Spec Files
*(Skip if no docs system. Wait for confirmation at end.)*

For each affected file:
- [ ] Read the current file first
- [ ] Make surgical additions — only what the requirement needs
- [ ] Match the existing format exactly (infer fields from existing entries, not from generic templates)
- [ ] Update cross-references across all files consistently
- [ ] For external interface changes: follow existing interface conventions
- [ ] For access-controlled interfaces: include permission specs
- [ ] For proto/gRPC files: treat as spec update (do NOT regenerate stubs yet — that's Phase 5)
- [ ] For versioned projects: include changelog/version update if change is user-visible or public-API-affecting
- [ ] Flag any required removals — do NOT remove without explicit user confirmation
- [ ] Present update summary
- [ ] **WAIT FOR CONFIRMATION** before Phase 3

---

## Phase 3: Create Tickets
*(Flows continuously after Phase 2 confirmation)*

- [ ] Read existing ticket files (if any) to learn exact format
- [ ] Size the work into appropriate trackable units (1-3 typical; adapt to project norms)
- [ ] Determine ticket hierarchy from tracker type (epic/story/task / project/issue/sub-issue / flat issues)

**If tracker MCP available:**
- [ ] Discover project config: project key/ID, issue types, custom fields, workflow states, sprint/cycle field names (check project files → query MCP → ask user)
- [ ] Create issues with correct hierarchy and all required fields
- [ ] Set: title, description with AC, estimate, labels/components
- [ ] **Do NOT assign to sprint/cycle/iteration** — that is Phase 4

**If no tracker MCP:**
- [ ] Create/update local ticket markdown files
- [ ] Follow existing ticket file format exactly
- [ ] Note "TBD — create manually in {tracker}" for IDs if known tracker exists

**Both paths:**
- [ ] Update any local summary files (sprint plans, ROADMAP.md, CHANGELOG.md) if they exist
- [ ] Present ticket summary table (ID / Title / Type / Estimate)
- [ ] Transition directly to Phase 4 (no additional gate — ticket summary IS the gate prompt)

---

## Phase 4: Scheduling Decision
*(ALWAYS shown — user picks one option)*

- [ ] Present options using correct methodology vocabulary (sprint/cycle/iteration OR just "now / backlog")
- [ ] Wait for user choice

**Choice a — implement now:**
- [ ] Assign to current iteration (if tracker + iteration-based)
- [ ] Transition tickets to "active/in-progress" state (discover state name from tracker — do NOT hardcode)
- [ ] Proceed to Phase 5

**Choice b — schedule only:**
- [ ] Assign to iteration (if applicable)
- [ ] STOP — do not proceed to Phase 5

**Choice c — backlog:**
- [ ] STOP — tickets stay unscheduled

---

## Phase 5: Implement
*(Only if user chose option a in Phase 4)*

- [ ] Confirm tickets are in "active" state (via MCP or local file update)
- [ ] Read CLAUDE.md / project instructions for coding conventions before writing any code
- [ ] Build per project type (route + service + repo / command handler + help text / exported function + types / DAG + operator / etc.)
  - gRPC: update .proto → regenerate stubs → write handler
  - BaaS: update client code AND service-side config (rules/functions)
- [ ] Tests — if test infrastructure exists:
  - [ ] Write tests matching existing patterns and naming conventions
  - [ ] Cover: happy path, edge cases, error cases
  - If no test infrastructure: ask user (add setup / skip / add TODO to ticket)
- [ ] Run tests — all must pass before declaring done
- [ ] Run linter — if configured; fix any new issues
- [ ] Update versioning artifacts (CHANGELOG.md / version field) — if applicable
- [ ] Transition tickets to "done/completed" state (discover state name / close GitHub issue / update local file)
- [ ] Present completion summary (ticket statuses / files changed / test results / lint status / changelog status)

---

## Quick Reference: Graceful Degradation

| Missing | What to do |
|---|---|
| No CLAUDE.md or instructions | Ask user about conventions before Phase 5 |
| No spec/doc system | Skip Phase 2 (or set one up if user chose option a in Phase 0.9) |
| No issue tracker MCP | Create local markdown ticket files |
| No test infrastructure | Ask user: add setup / skip / add TODO |
| No linter | Skip lint step |
| No CI/CD | Skip CI-related notes |
| No CHANGELOG.md | Skip versioning update |
| No codebase yet | After Phase 3, ask: scaffold project or stop after tickets? |
| Multi-repo requirement | Note affected repos in Phase 1; track per-repo ownership in tickets |

---

## Formality Levels at a Glance

| Level | Trigger | Behavior |
|---|---|---|
| **Full** | Has spec files + issue tracker + test suite | All phases, all gates, full detail |
| **Standard** | Has some of the above | All phases, skip what's missing, adapt detail |
| **Lightweight** | Single-file/tiny project, nothing | Phases 1-3 compressed to one confirmation, then Phase 4 |
