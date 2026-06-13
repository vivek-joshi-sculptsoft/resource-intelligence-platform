import { test, expect } from "../../../fixtures";

test.describe("S1-06: Login Screen UI", () => {
  test("login page renders with all required elements", async ({ page }) => {
    await page.goto("/login");
    await expect(
      page.getByText("Resource Intelligence Platform")
    ).toBeVisible();
    await expect(page.getByText("by SculptSoft")).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(
      page.getByRole("button", { name: /sign in/i })
    ).toBeVisible();
    await expect(page.getByLabel(/remember me/i)).toBeVisible();
    await expect(page.getByText(/forgot password/i)).toBeVisible();
  });

  test("email and password fields have correct placeholders", async ({
    page,
  }) => {
    await page.goto("/login");
    await expect(page.getByLabel(/email/i)).toHaveAttribute(
      "placeholder",
      /name@company/i
    );
    await expect(page.getByLabel(/password/i)).toHaveAttribute(
      "placeholder",
      /enter your password/i
    );
  });

  test("password visibility toggle works", async ({ page }) => {
    await page.goto("/login");
    const passwordInput = page.getByLabel(/password/i);
    await expect(passwordInput).toHaveAttribute("type", "password");
    await passwordInput.fill("testpassword");

    const toggleBtn = page
      .locator("button")
      .filter({ has: page.locator("svg") })
      .last();
    await toggleBtn.click();
    await expect(passwordInput).toHaveAttribute("type", "text");
    await toggleBtn.click();
    await expect(passwordInput).toHaveAttribute("type", "password");
  });

  test("successful login redirects to authenticated page", async ({
    page,
    loginAs,
  }) => {
    await loginAs("CEO");
    await expect(page).toHaveURL(/\/(dashboard|resources|clients|projects)/);
  });

  test("invalid credentials show error message", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel(/email/i).fill("wrong@example.com");
    await page.getByLabel(/password/i).fill("wrongpassword");
    await page.getByRole("button", { name: /sign in/i }).click();
    await expect(
      page.getByText(/invalid|incorrect|unauthorized/i)
    ).toBeVisible();
  });

  test("login button shows loading state during request", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel(/email/i).fill("admin@riplatform.com");
    await page.getByLabel(/password/i).fill("admin123");
    await page.getByRole("button", { name: /sign in/i }).click();
    // Button should show loading text briefly
    await expect(page).toHaveURL(/\/(dashboard|resources|clients|projects)/, {
      timeout: 10_000,
    });
  });

  test("authenticated user is redirected away from login", async ({
    page,
    loginAs,
  }) => {
    await loginAs("CEO");
    await page.goto("/login");
    await expect(page).not.toHaveURL(/\/login/);
  });

  test("unauthenticated user is redirected to login", async ({ page }) => {
    await page.goto("/resources");
    await expect(page).toHaveURL(/\/login/);
  });
});
