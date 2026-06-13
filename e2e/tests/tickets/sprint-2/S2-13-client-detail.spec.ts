import { test, expect } from "../../../fixtures";

test.describe("S2-13: Client Detail Screen", () => {
  test.beforeEach(async ({ page, loginAs }) => {
    await loginAs("CEO");
    // Create a client so we have one to view
    await page.goto("/clients/new");
    const uniqueName = `E2E Client ${Date.now()}`;
    await page.getByLabel(/client name|name/i).first().fill(uniqueName);
    await page.getByRole("button", { name: /create client/i }).click();
    await page.waitForURL(/\/clients\/[a-f0-9-]+/, { timeout: 10_000 });
  });

  test("client detail shows header with name", async ({ page }) => {
    await expect(page.locator("h1").first()).toBeVisible();
    await expect(page.getByText("Clients").first()).toBeVisible();
  });

  test("contact info section displays", async ({ page }) => {
    // Contact labels should be visible even if empty
    await expect(page.getByText(/contact/i).first()).toBeVisible();
  });

  test("stats row shows project and resource counts", async ({ page }) => {
    await expect(page.getByText(/active projects/i)).toBeVisible();
    await expect(page.getByText(/active resources/i)).toBeVisible();
  });

  test("projects section shows empty state", async ({ page }) => {
    await expect(page.getByText(/no projects yet/i)).toBeVisible();
  });

  test("edit button is visible for CEO", async ({ page }) => {
    await expect(
      page.getByRole("button", { name: /edit/i }).first()
    ).toBeVisible();
  });

  test("deactivate button is visible for CEO", async ({ page }) => {
    await expect(
      page.getByRole("button", { name: /deactivate/i })
    ).toBeVisible();
  });

  test("edit button navigates to edit form", async ({ page }) => {
    await page.getByRole("button", { name: /edit/i }).first().click();
    await expect(page).toHaveURL(/\/clients\/[a-f0-9-]+\/edit/);
  });

  test("deactivate shows confirmation modal", async ({ page }) => {
    await page.getByRole("button", { name: /deactivate/i }).click();
    // Should show confirmation dialog
    await expect(
      page.getByText(/deactivate/i).nth(1)
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: /cancel/i })
    ).toBeVisible();
  });

  test("breadcrumb navigates back to list", async ({ page }) => {
    await page.getByText("Clients").first().click();
    await expect(page).toHaveURL(/\/clients$/);
  });
});
