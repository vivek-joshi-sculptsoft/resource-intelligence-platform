import { test as setup, expect } from "@playwright/test";

setup("verify backend health", async ({ request }) => {
  const response = await request.get(
    "http://localhost:8000/api/v1/health"
  );
  expect(response.ok()).toBeTruthy();
});

setup("verify frontend is serving", async ({ page }) => {
  await page.goto("http://localhost:5173");
  await expect(page).not.toHaveTitle("");
});
