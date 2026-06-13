import { test, expect } from "../../../fixtures";

test.describe("S1-08: Role Management Screen", () => {
  test.beforeEach(async ({ page, loginAs }) => {
    await loginAs("CEO");
    await page.goto("/admin/roles");
  });

  test("role management page renders with split layout", async ({ page }) => {
    await expect(page.getByText("Role Management")).toBeVisible();
    await expect(page.getByText(/select a role to view/i)).toBeVisible();
  });

  test("role list shows all 7 roles", async ({ page }) => {
    await page.waitForResponse((r) => r.url().includes("/roles") && r.ok());
    await expect(page.getByText("CEO")).toBeVisible();
    await expect(page.getByText("CTO")).toBeVisible();
    await expect(page.getByText("DM").first()).toBeVisible();
    await expect(page.getByText("PM").first()).toBeVisible();
    await expect(page.getByText("FINANCE")).toBeVisible();
    await expect(page.getByText("HR")).toBeVisible();
    await expect(page.getByText("ENGINEER")).toBeVisible();
  });

  test("clicking a role shows permission matrix", async ({ page }) => {
    await page.waitForResponse((r) => r.url().includes("/roles") && r.ok());
    await page.getByText("CEO").first().click();
    await expect(page.getByText(/permissions/i).first()).toBeVisible();
    // Permission table should show data types
    await expect(page.getByText(/client profiles/i)).toBeVisible();
    await expect(page.getByText(/resource profiles/i)).toBeVisible();
  });

  test("permission matrix shows access level badges", async ({ page }) => {
    await page.waitForResponse((r) => r.url().includes("/roles") && r.ok());
    await page.getByText("CEO").first().click();
    // CEO should have EDIT access to most things
    await expect(page.getByText("EDIT").first()).toBeVisible();
  });

  test("permission matrix shows scope badges", async ({ page }) => {
    await page.waitForResponse((r) => r.url().includes("/roles") && r.ok());
    await page.getByText("CEO").first().click();
    await expect(page.getByText("ALL").first()).toBeVisible();
  });

  test("ENGINEER role shows restricted permissions", async ({ page }) => {
    await page.waitForResponse((r) => r.url().includes("/roles") && r.ok());
    await page.getByText("ENGINEER").first().click();
    // Engineer should have NONE or VIEW SELF_ONLY
    await expect(page.getByText("SELF_ONLY").first()).toBeVisible();
  });

  test("editing info banner is shown", async ({ page }) => {
    await page.waitForResponse((r) => r.url().includes("/roles") && r.ok());
    await page.getByText("CEO").first().click();
    await expect(
      page.getByText(/editing permissions will be available/i)
    ).toBeVisible();
  });
});

test.describe("S1-08: Role Management — Access Control", () => {
  test("ENGINEER cannot access role management", async ({
    page,
    loginAs,
  }) => {
    await loginAs("ENGINEER");
    await page.goto("/admin/roles");
    await expect(page).not.toHaveURL(/\/admin\/roles$/);
  });
});
