import { test, expect } from "../../../fixtures";

test.describe("S2-07: Resource Create/Edit Form", () => {
  test.beforeEach(async ({ page, loginAs }) => {
    await loginAs("CEO");
  });

  test("create form renders with all fields", async ({ page }) => {
    await page.goto("/resources/new");
    await expect(page.getByText(/add resource/i).first()).toBeVisible();
    await expect(page.getByLabel(/name/i).first()).toBeVisible();
    await expect(page.getByLabel(/employee id/i)).toBeVisible();
    await expect(page.getByLabel(/designation/i)).toBeVisible();
    await expect(
      page.getByRole("button", { name: /create resource/i })
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: /cancel/i })
    ).toBeVisible();
  });

  test("create resource with valid data succeeds", async ({ page }) => {
    await page.goto("/resources/new");
    const uniqueId = `EMP-${Date.now()}`;
    await page.getByLabel(/name/i).first().fill("E2E Test Resource");
    await page.getByLabel(/employee id/i).fill(uniqueId);
    await page.getByLabel(/designation/i).fill("Software Engineer");

    await page.getByRole("button", { name: /create resource/i }).click();
    // Should redirect to profile or list on success
    await expect(page).toHaveURL(/\/resources\/[a-f0-9-]+/, {
      timeout: 10_000,
    });
  });

  test("required field validation blocks submission", async ({ page }) => {
    await page.goto("/resources/new");
    // Leave all fields empty and try to submit
    await page.getByRole("button", { name: /create resource/i }).click();
    // Should stay on the form (validation prevents submission)
    await expect(page).toHaveURL(/\/resources\/new/);
  });

  test("duplicate employee ID shows error", async ({ page }) => {
    // First create a resource
    await page.goto("/resources/new");
    const uniqueId = `DUP-${Date.now()}`;
    await page.getByLabel(/name/i).first().fill("First Resource");
    await page.getByLabel(/employee id/i).fill(uniqueId);
    await page.getByLabel(/designation/i).fill("Developer");
    await page.getByRole("button", { name: /create resource/i }).click();
    await page.waitForURL(/\/resources\/[a-f0-9-]+/, { timeout: 10_000 });

    // Try to create another with the same employee ID
    await page.goto("/resources/new");
    await page.getByLabel(/name/i).first().fill("Second Resource");
    await page.getByLabel(/employee id/i).fill(uniqueId);
    await page.getByLabel(/designation/i).fill("Developer");
    await page.getByRole("button", { name: /create resource/i }).click();
    // Should show error about duplicate
    await expect(page.getByText(/already|duplicate|exists/i)).toBeVisible({
      timeout: 5_000,
    });
  });

  test("edit form pre-populates fields", async ({ page }) => {
    // Navigate to first resource's edit page
    await page.goto("/resources");
    await page.waitForResponse(
      (r) => r.url().includes("/resources") && r.ok()
    );
    const firstRow = page.locator("tbody tr").first();
    const rowCount = await page.locator("tbody tr").count();
    if (rowCount === 0) return test.skip();
    await firstRow.click();
    await page.waitForURL(/\/resources\/[a-f0-9-]+/);
    await page.getByRole("button", { name: /edit/i }).first().click();
    await page.waitForURL(/\/resources\/[a-f0-9-]+\/edit/);

    await expect(page.getByText(/edit resource/i)).toBeVisible();
    // Name field should have a value
    const nameInput = page.getByLabel(/name/i).first();
    await expect(nameInput).not.toHaveValue("");
  });

  test("cancel returns to resource list", async ({ page }) => {
    await page.goto("/resources/new");
    await page.getByRole("button", { name: /cancel/i }).click();
    await expect(page).toHaveURL(/\/resources/);
  });
});

test.describe("S2-07: Resource Form — Access Control", () => {
  test("PM cannot access resource create form", async ({
    page,
    loginAs,
  }) => {
    await loginAs("PM");
    await page.goto("/resources/new");
    // Should be blocked by RoleGuard
    await expect(page).not.toHaveURL(/\/resources\/new$/);
  });
});
