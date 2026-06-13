import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI
    ? [["html", { open: "never" }], ["github"]]
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
  ],

  webServer: [
    {
      command:
        "cd ../backend && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000",
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
