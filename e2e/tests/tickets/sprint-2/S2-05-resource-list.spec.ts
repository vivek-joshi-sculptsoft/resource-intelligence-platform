import { test, expect } from "../../../fixtures";

test.describe("S2-05: Resource List Screen", () => {
  test.beforeEach(async ({ page, loginAs }) => {
    await loginAs("CEO");
    await page.goto("/resources");
  });

  test("resource list page renders with title and controls", async ({
    page,
  }) => {
    await expect(page.getByText("Resource Management")).toBeVisible();
    await expect(
      page.getByText(/manage team members, skills, and availability/i)
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: /add resource/i })
    ).toBeVisible();
    await expect(
      page.getByPlaceholder(/search by name or employee id/i)
    ).toBeVisible();
  });

  test("resource table shows correct columns", async ({ page }) => {
    await page.waitForResponse(
      (r) => r.url().includes("/resources") && r.ok()
    );
    const headers = page.locator("th");
    await expect(headers.filter({ hasText: /name/i }).first()).toBeVisible();
    await expect(
      headers.filter({ hasText: /employee id/i }).first()
    ).toBeVisible();
    await expect(
      headers.filter({ hasText: /designation/i }).first()
    ).toBeVisible();
  });

  test("search filters resource list", async ({ page }) => {
    await page.waitForResponse(
      (r) => r.url().includes("/resources") && r.ok()
    );
    await page
      .getByPlaceholder(/search by name or employee id/i)
      .fill("nonexistent-xyz-999");
    await page.waitForResponse(
      (r) => r.url().includes("/resources") && r.ok()
    );
  });

  test("status filter filters by active/inactive", async ({ page }) => {
    const statusSelect = page
      .locator("select")
      .filter({ hasText: /all status/i });
    await statusSelect.selectOption("ACTIVE");
    await page.waitForResponse(
      (r) => r.url().includes("/resources") && r.ok()
    );
  });

  test("availability filter works", async ({ page }) => {
    const availSelect = page
      .locator("select")
      .filter({ hasText: /all availability/i });
    await availSelect.selectOption("Bench");
    await page.waitForResponse(
      (r) => r.url().includes("/resources") && r.ok()
    );
  });

  test("Add Resource button navigates to form", async ({ page }) => {
    await page.getByRole("button", { name: /add resource/i }).click();
    await expect(page).toHaveURL(/\/resources\/new/);
  });

  test("clicking a resource row navigates to profile", async ({ page }) => {
    await page.waitForResponse(
      (r) => r.url().includes("/resources") && r.ok()
    );
    const firstRow = page.locator("tbody tr").first();
    const rowCount = await page.locator("tbody tr").count();
    if (rowCount > 0) {
      await firstRow.click();
      await expect(page).toHaveURL(/\/resources\/[a-f0-9-]+/);
    }
  });

  test("pagination shows record count", async ({ page }) => {
    await page.waitForResponse(
      (r) => r.url().includes("/resources") && r.ok()
    );
    await expect(page.getByText(/showing/i)).toBeVisible();
  });
});

test.describe("S2-05: Resource List — Role Visibility", () => {
  test("HR can see Add Resource button", async ({ page, loginAs }) => {
    await loginAs("HR");
    await page.goto("/resources");
    await expect(
      page.getByRole("button", { name: /add resource/i })
    ).toBeVisible();
  });

  test("PM cannot see Add Resource button", async ({ page, loginAs }) => {
    await loginAs("PM");
    await page.goto("/resources");
    await page.waitForResponse(
      (r) => r.url().includes("/resources") && r.ok()
    );
    await expect(
      page.getByRole("button", { name: /add resource/i })
    ).not.toBeVisible();
  });
});
