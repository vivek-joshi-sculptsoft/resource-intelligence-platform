import { test, expect } from "../../../fixtures";

test.describe("S2-06: Resource Profile Screen", () => {
  let resourceUrl: string;

  test.beforeEach(async ({ page, loginAs }) => {
    await loginAs("CEO");
    await page.goto("/resources");
    await page.waitForResponse(
      (r) => r.url().includes("/resources") && r.ok()
    );
    // Navigate to the first resource's profile
    const firstRow = page.locator("tbody tr").first();
    const rowCount = await page.locator("tbody tr").count();
    if (rowCount > 0) {
      await firstRow.click();
      await page.waitForURL(/\/resources\/[a-f0-9-]+/);
      resourceUrl = page.url();
    }
  });

  test("profile header shows resource details", async ({ page }) => {
    if (!resourceUrl) return test.skip();
    // Name should be visible as heading
    await expect(page.locator("h1").first()).toBeVisible();
    // Breadcrumb should show "Resources"
    await expect(page.getByText("Resources").first()).toBeVisible();
  });

  test("profile shows allocation stats", async ({ page }) => {
    if (!resourceUrl) return test.skip();
    // Allocation percentage should be visible
    await expect(page.getByText(/%/).first()).toBeVisible();
  });

  test("edit button is visible for CEO", async ({ page }) => {
    if (!resourceUrl) return test.skip();
    await expect(
      page.getByRole("button", { name: /edit/i }).first()
    ).toBeVisible();
  });

  test("deactivate button is visible for CEO", async ({ page }) => {
    if (!resourceUrl) return test.skip();
    await expect(
      page.getByRole("button", { name: /deactivate/i })
    ).toBeVisible();
  });

  test("tags section is visible", async ({ page }) => {
    if (!resourceUrl) return test.skip();
    await expect(page.getByText(/tags/i).first()).toBeVisible();
  });

  test("assignments section shows empty state or list", async ({ page }) => {
    if (!resourceUrl) return test.skip();
    const assignmentsHeading = page.getByText(/active assignments/i);
    await expect(assignmentsHeading).toBeVisible();
  });

  test("edit button navigates to edit form", async ({ page }) => {
    if (!resourceUrl) return test.skip();
    await page.getByRole("button", { name: /edit/i }).first().click();
    await expect(page).toHaveURL(/\/resources\/[a-f0-9-]+\/edit/);
  });

  test("deactivate shows confirmation modal", async ({ page }) => {
    if (!resourceUrl) return test.skip();
    await page.getByRole("button", { name: /deactivate/i }).click();
    await expect(page.getByText(/deactivate resource/i)).toBeVisible();
    await expect(
      page.getByRole("button", { name: /cancel/i })
    ).toBeVisible();
  });

  test("breadcrumb navigates back to list", async ({ page }) => {
    if (!resourceUrl) return test.skip();
    await page.getByText("Resources").first().click();
    await expect(page).toHaveURL(/\/resources$/);
  });
});
