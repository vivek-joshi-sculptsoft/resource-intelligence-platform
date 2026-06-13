Run Playwright E2E tests (3-tier: tickets / integration / smoke).

Argument: $ARGUMENTS

All commands run from `cd e2e &&`.

- Empty or "all": `npx playwright test`
- "smoke": `npx playwright test --project=smoke`
- "tickets": `npx playwright test --project=tickets`
- "integration": `npx playwright test --project=integration`
- "sprint-N" (e.g. "sprint-1", "sprint-2"): `npx playwright test tests/tickets/sprint-N/`
- A ticket ID (e.g. "S2-05"): `npx playwright test tests/tickets/sprint-*/S2-05*`
- "ui": `npx playwright test --ui`
- "headed": `npx playwright test --headed`
- "debug": `npx playwright test --debug`
- "codegen": `npx playwright codegen http://localhost:5173`
- "report": `npx playwright show-report`
- "list": `npx playwright test --list`
- Anything else: treat as a path/grep pattern and run `npx playwright test $ARGUMENTS`

Report pass/fail counts per project/file when running tests.
