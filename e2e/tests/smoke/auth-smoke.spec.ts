import { test, expect } from "../../fixtures";

test.describe("Auth Smoke", () => {
  test("login page loads", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByRole("button", { name: /sign in/i })).toBeVisible();
  });

  test("CEO can log in", async ({ page, loginAs }) => {
    await loginAs("CEO");
    await expect(page).toHaveURL(/\/(dashboard|resources|clients|projects)/);
  });

  test("invalid credentials rejected", async ({ page }) => {
    await page.goto("/login");
    await page.getByRole("textbox", { name: /email/i }).fill("bad@bad.com");
    await page.getByRole("textbox", { name: /password/i }).fill("wrong");
    await page.getByRole("button", { name: /sign in/i }).click();
    await expect(
      page.getByText(/invalid|incorrect|unauthorized/i)
    ).toBeVisible();
  });

  test("protected route redirects to login", async ({ page }) => {
    await page.goto("/resources");
    await expect(page).toHaveURL(/\/login/);
  });
});
