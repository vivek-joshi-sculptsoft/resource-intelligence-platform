# Backend Test Ticket — Heuristics

Detection recipes and worked examples for the `backend-test-ticket` skill. These are generic techniques — apply them to whatever repo you're in, don't assume any specific stack beyond Python + pytest.

## Detecting the test setup

Before writing a single test, learn how this repo already tests itself:

- **Runner/config.** Read `pyproject.toml` for `[tool.pytest.ini_options]`; if absent, check `pytest.ini`, `setup.cfg`, or `tox.ini`. Record the exact invocation the repo expects (`pytest`, `python -m pytest`, any custom markers, coverage flags, `testpaths`).
- **Test layout.** Locate the tests root and its naming convention — `tests/`, `test_*.py` vs `*_test.py`, and whether test files mirror the source package structure or sit in a flatter directory.
- **Fixtures.** Read every `conftest.py` in scope. Identify the HTTP client fixture, the db/session fixture, and any auth/login helper (e.g. a `login_as` fixture or token factory). These are the seams new tests must reuse — never hand-roll a client or session when a fixture already exists.
- **Style.** Detect async vs sync test style — `pytest.mark.asyncio` / `async def test_...` / an async HTTP client, versus a synchronous `TestClient`. Detect the web framework (FastAPI, Flask, Django, etc.) and the ORM in use, since both shape how tests set up data and assert responses.

Do not guess any of the above from convention alone — open the files and confirm.

## Locating the code delta

The whole point of this skill is to test the *change*, not the module in general. Find it precisely:

- **Find the ticket's branch or commits.** Try `git branch -a --list "*PROJ-123*"` for a branch, or `git log --all --oneline --grep "PROJ-123"` for commits referencing the key.
- **Diff against main.** Detect the repo's main branch (`git symbolic-ref refs/remotes/origin/HEAD`, falling back to `main` or `master` if that's unset), then run `git diff <main>...<ticket-ref> --name-only` for the file list, followed by a per-file `git diff` to see the actual changes.
- **Fallback with no branch or commits.** If nothing in git references the ticket, parse the ticket description for module/file/endpoint names and `grep` (or use a code-graph tool, if available) to resolve those references to real files.
- **Filter the changed set.** Keep only source files under the application package. Drop test files, migrations, `*.md`, and config files — those are not what you're testing against.

## Create vs Update: worked examples

**CREATE example.** The diff introduces a new endpoint or function with no matching `test_*` anywhere in the repo. There is nothing to extend, so create a new test file mirroring the source file's path (e.g. a new `app/modules/billing/service.py::apply_discount` function gets a new `tests/test_billing/test_apply_discount.py`), reuse the detected client and auth fixtures, and cover the happy path plus each new error branch the diff introduces.

**UPDATE example.** An existing function gains environment-dependent behavior — for instance, a cookie-setting helper's `secure` flag changes from always-`True` to `not DEBUG and not TESTING`. A test for that helper already exists. Do not create a second file next to it — **UPDATE** the existing test: add a regression case that asserts the new behavior under the new condition (e.g. `secure=False` when `TESTING=True`), leaving the existing assertions for the unchanged paths in place.

**NO-OP example.** A function is renamed internally, or its body is refactored to extract a helper, but its signature, return shape, and observable behavior are unchanged. Report this symbol as NO-OP — the existing tests already cover it and still pass unmodified.

> The two examples above are illustrative, not prescriptive. In a project like the Resource Intelligence Platform, a CREATE might instead look like a new `POST /api/assignments` endpoint gaining its first test in `backend/tests/test_allocations/`, and an UPDATE might look like an existing `test_projects_api.py` gaining a case for a new status-transition branch. Apply the same CREATE/UPDATE/NO-OP logic regardless of the project's actual module names.

## Self-heal policy

- After writing tests, run only the affected tests first for fast feedback, then widen to the containing file or module.
- If a test fails because the *test* is wrong — a stale expectation, a misused fixture, an incorrect assumption about the response shape — fix the test and re-run.
- If a test fails because the *code* is wrong, stop editing tests. Report the suspected product bug: the failing assertion, the actual vs expected value, and a minimal reproduction. Never modify feature code to force a test to pass — that hides the bug instead of surfacing it.
- Loop steps above until every affected test is green, or until a genuine product bug has been isolated and reported.
