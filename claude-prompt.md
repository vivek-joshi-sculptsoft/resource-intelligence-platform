Regression tests failed on a push to main (Jira ticket VRIP-142).

Full failure details are in `regression-failures.md` at the repo root — read it first.

Your task:
1. For each failure, determine whether the root cause is a bug in the
   application code (backend/ or frontend/) or a bug in the test itself
   (e2e/tests/regression/). Prefer fixing application code — only change
   a test if the test's assertion is factually wrong about intended
   product behavior (check shared/BUSINESS-RULES.md and
   shared/ACCESS-MATRIX.md as the source of truth for business rules and
   access control before concluding a test is wrong).
2. Fix the root cause with the smallest correct change. Do not refactor
   unrelated code or add speculative abstractions — see CLAUDE.md's
   engineering conventions.
3. After fixing, verify: run `cd backend && python -m pytest tests/ -q`
   if you touched backend code. Do not attempt to run the e2e suite
   (no browser/servers available in this step).
4. Do not touch files outside backend/, frontend/, or e2e/tests/regression/
   unless the failure clearly originates elsewhere.
5. Reference "See VRIP-142" in a code comment only if the
   fix includes a non-obvious workaround — otherwise no comment is needed
   per CLAUDE.md's no-comments-by-default convention.