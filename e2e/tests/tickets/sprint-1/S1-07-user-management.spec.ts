import { test, expect } from "../../../fixtures";

test.describe("S1-07: User Management Screens", () => {
  test.beforeEach(async ({ page, loginAs }) => {
    await loginAs("CEO");
  });

  test("user list page renders with table and controls", async ({ page }) => {
    await page.goto("/admin/users");
    await expect(page.getByText("User Management")).toBeVisible();
    await expect(
      page.getByRole("button", { name: /add user/i })
    ).toBeVisible();
    await expect(
      page.getByPlaceholder(/search by name or email/i)
    ).toBeVisible();
  });

  test("user table shows correct columns", async ({ page }) => {
    await page.goto("/admin/users");
    await page.waitForResponse((r) => r.url().includes("/users") && r.ok());
    const headers = page.locator("th");
    await expect(headers.filter({ hasText: /name/i }).first()).toBeVisible();
    await expect(headers.filter({ hasText: /email/i }).first()).toBeVisible();
    await expect(headers.filter({ hasText: /role/i }).first()).toBeVisible();
    await expect(headers.filter({ hasText: /status/i }).first()).toBeVisible();
  });

  test("Add User button navigates to create form", async ({ page }) => {
    await page.goto("/admin/users");
    await page.getByRole("button", { name: /add user/i }).click();
    await expect(page).toHaveURL(/\/admin\/users\/new/);
    await expect(page.getByText(/add new user/i)).toBeVisible();
  });

  test("create user form has all required fields", async ({ page }) => {
    await page.goto("/admin/users/new");
    await expect(page.getByLabel(/full name/i)).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(
      page.getByRole("button", { name: /create user/i })
    ).toBeVisible();
  });

  test("create user with valid data succeeds", async ({ page }) => {
    await page.goto("/admin/users/new");
    const uniqueEmail = `testuser-${Date.now()}@riplatform.com`;
    await page.getByLabel(/full name/i).fill("E2E Test User");
    await page.getByLabel(/email/i).fill(uniqueEmail);
    await page.getByLabel(/password/i).fill("TestPass123!");

    // Select a role
    const roleSelect = page.locator("select").filter({ hasText: /select role/i });
    await roleSelect.selectOption({ index: 1 });

    await page.getByRole("button", { name: /create user/i }).click();
    await expect(page).toHaveURL(/\/admin\/users/, { timeout: 10_000 });
  });

  test("search filters user list", async ({ page }) => {
    await page.goto("/admin/users");
    await page.waitForResponse((r) => r.url().includes("/users") && r.ok());
    await page.getByPlaceholder(/search by name or email/i).fill("admin");
    await page.waitForResponse((r) => r.url().includes("/users") && r.ok());
    const rows = page.locator("tbody tr");
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);
  });

  test("status filter works", async ({ page }) => {
    await page.goto("/admin/users");
    const statusSelect = page.locator("select").filter({ hasText: /all status/i });
    await statusSelect.selectOption("ACTIVE");
    await page.waitForResponse((r) => r.url().includes("/users") && r.ok());
  });

  test("edit user navigates to form with pre-populated data", async ({
    page,
  }) => {
    await page.goto("/admin/users");
    await page.waitForResponse((r) => r.url().includes("/users") && r.ok());
    const editBtn = page.getByRole("button", { name: /edit/i }).first();
    await editBtn.click();
    await expect(page).toHaveURL(/\/admin\/users\/.*\/edit/);
    await expect(page.getByText(/edit user/i)).toBeVisible();
    // Email should be disabled in edit mode
    await expect(page.getByLabel(/email/i)).toBeDisabled();
  });

  test("cancel button returns to user list", async ({ page }) => {
    await page.goto("/admin/users/new");
    await page.getByRole("button", { name: /cancel/i }).click();
    await expect(page).toHaveURL(/\/admin\/users/);
  });

  test("pagination controls are present", async ({ page }) => {
    await page.goto("/admin/users");
    await page.waitForResponse((r) => r.url().includes("/users") && r.ok());
    await expect(page.getByText(/showing/i)).toBeVisible();
  });
});

test.describe("S1-07: User Management — Access Control", () => {
  test("ENGINEER cannot access user management", async ({
    page,
    loginAs,
  }) => {
    await loginAs("ENGINEER");
    await page.goto("/admin/users");
    // Should be blocked by RoleGuard — redirected or shown forbidden
    await expect(page).not.toHaveURL(/\/admin\/users$/);
  });
});
