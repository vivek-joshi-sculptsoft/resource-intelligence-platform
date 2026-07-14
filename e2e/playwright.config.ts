import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI
    ? [
        ["html", { open: "never" }],
        ["github"],
        ["json", { outputFile: "test-results/results.json" }],
      ]
    : [["html", { open: "on-failure" }]],

  use: {
    baseURL: "http://localhost:5173",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },

  projects: [
    // --- Setup: health checks ---
    {
      name: "setup",
      testDir: ".",
      testMatch: /global\.setup\.ts/,
    },

    // --- Tier 1: Ticket-wise tests (one spec per Jira ticket) ---
    {
      name: "tickets",
      testDir: "./tests/tickets",
      use: { ...devices["Desktop Chrome"] },
      dependencies: ["setup"],
    },

    // --- Tier 2: Integration tests (cross-module flows) ---
    {
      name: "integration",
      testDir: "./tests/integration",
      use: { ...devices["Desktop Chrome"] },
      dependencies: ["setup"],
    },

    // --- Tier 3: Smoke tests (fast critical-path, runs in CI) ---
    {
      name: "smoke",
      testDir: "./tests/smoke",
      use: { ...devices["Desktop Chrome"] },
      dependencies: ["setup"],
    },

    // --- Tier 4a: API regression (full endpoint coverage, no browser) ---
    {
      name: "api-regression",
      testDir: "./tests/regression/api",
      dependencies: ["setup"],
    },

    // --- Tier 4b: UI regression (full CRUD + role visibility flows) ---
    {
      name: "ui-regression",
      testDir: "./tests/regression/ui",
      use: { ...devices["Desktop Chrome"] },
      dependencies: ["setup"],
    },
  ],

  webServer: [
    {
      // TESTING=1 disables the login rate limiter (app/modules/auth/router.py) —
      // the suite logs in more than 10×/minute across tests.
      command:
        "cd ../backend && TESTING=1 python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000",
      url: "http://localhost:8000/api/v1/health",
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
    },
    {
      command: "cd ../frontend && npm run dev",
      url: "http://localhost:5173",
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
    },
  ],
});
