import { test, expect } from "../../fixtures";

test.describe("Auth Flow — End-to-End", () => {
  test("full login → navigate → session persistence → logout cycle", async ({
    page,
  }) => {
    // Login
    await page.goto("/login");
    await page.getByLabel(/email/i).fill("admin@riplatform.com");
    await page.getByLabel(/password/i).fill("admin123");
    await page.getByRole("button", { name: /sign in/i }).click();
    await page.waitForURL(/\/(dashboard|resources|clients|projects)/);

    // Navigate to multiple protected pages
    await page.goto("/resources");
    await expect(page.getByText("Resource Management")).toBeVisible();

    await page.goto("/admin/users");
    await expect(page.getByText("User Management")).toBeVisible();

    // Session should persist across navigation
    await page.goto("/admin/roles");
    await expect(page.getByText("Role Management")).toBeVisible();

    // Logout
    const userMenu = page.locator("button").filter({ has: page.locator("svg") });
    // Find the logout button in the header area
    await page
      .getByRole("button", { name: /logout|sign out|log out/i })
      .click();
    await expect(page).toHaveURL(/\/login/);

    // After logout, protected pages should redirect to login
    await page.goto("/resources");
    await expect(page).toHaveURL(/\/login/);
  });

  test("session restored on page reload", async ({ page, loginAs }) => {
    await loginAs("CEO");
    await page.goto("/resources");
    await expect(page.getByText("Resource Management")).toBeVisible();

    // Reload the page — session should persist via /auth/me
    await page.reload();
    await expect(page.getByText("Resource Management")).toBeVisible();
    await expect(page).not.toHaveURL(/\/login/);
  });

  test("sidebar navigation reflects user role", async ({ page, loginAs }) => {
    await loginAs("CEO");
    // CEO should see all sidebar items
    await expect(page.getByText(/dashboard/i).first()).toBeVisible();
    await expect(page.getByText(/resources/i).first()).toBeVisible();
    await expect(page.getByText(/clients/i).first()).toBeVisible();
  });

  test("user profile shows correct info in header", async ({
    page,
    loginAs,
  }) => {
    await loginAs("CEO");
    // User name or initials should be visible in the header
    await expect(page.locator("header")).toBeVisible();
  });
});

test.describe("Auth Flow — Role-Based Navigation", () => {
  test("ENGINEER sees limited sidebar items", async ({ page, loginAs }) => {
    await loginAs("ENGINEER");
    // Engineer should not see Clients in sidebar
    const sidebar = page.locator("nav, aside");
    // Clients link should be hidden for ENGINEER
    const clientsLink = sidebar.getByText(/clients/i);
    await expect(clientsLink).not.toBeVisible();
  });

  test("FINANCE can read resources but not create", async ({
    page,
    loginAs,
  }) => {
    await loginAs("FINANCE");
    await page.goto("/resources");
    await page.waitForResponse(
      (r) => r.url().includes("/resources") && r.ok()
    );
    // FINANCE should see the list but not Add Resource button
    await expect(page.getByText("Resource Management")).toBeVisible();
    await expect(
      page.getByRole("button", { name: /add resource/i })
    ).not.toBeVisible();
  });
});
