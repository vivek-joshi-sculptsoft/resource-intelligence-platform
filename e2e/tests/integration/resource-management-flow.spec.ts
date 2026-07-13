import { test, expect } from "../../fixtures";

test.describe("Resource Management — Full Lifecycle", () => {
  test("CEO creates a resource, views profile, edits, adds tag, deactivates", async ({
    page,
    loginAs,
  }) => {
    await loginAs("CEO");

    // Step 1: Create a resource
    await page.goto("/resources/new");
    const uniqueId = `E2E-${Date.now()}`;
    const resourceName = `Integration Test ${uniqueId}`;
    await page.getByLabel(/name/i).first().fill(resourceName);
    await page.getByLabel(/employee id/i).fill(uniqueId);
    await page.getByLabel(/designation/i).fill("Senior Developer");
    await page.getByRole("button", { name: /create resource/i }).click();
    await page.waitForURL(/\/resources\/[a-f0-9-]+/, { timeout: 10_000 });

    // Step 2: Verify profile page shows correct data
    await expect(page.getByRole("heading", { name: resourceName })).toBeVisible();
    await expect(page.getByText(uniqueId, { exact: true })).toBeVisible();
    await expect(page.getByText("Senior Developer")).toBeVisible();

    // Step 3: Edit the resource
    await page.getByRole("button", { name: /edit/i }).first().click();
    await page.waitForURL(/\/edit/);
    await page.getByLabel(/designation/i).clear();
    await page.getByLabel(/designation/i).fill("Lead Developer");
    await page.getByRole("button", { name: /save changes/i }).click();
    await page.waitForURL(/\/resources\/[a-f0-9-]+$/);
    await expect(page.getByText("Lead Developer")).toBeVisible();

    // Step 4: Add a tag
    const tagInput = page.getByPlaceholder(/add.*tag/i);
    if (await tagInput.isVisible()) {
      await tagInput.fill("playwright-test");
      await tagInput.press("Enter");
      await expect(page.getByText("playwright-test")).toBeVisible();
    }

    // Step 5: Deactivate
    await page.getByRole("button", { name: /deactivate/i }).click();
    // Confirm in modal
    const confirmBtn = page
      .getByRole("button", { name: /deactivate/i })
      .last();
    await confirmBtn.click();
    // Should show inactive state
    await expect(page.getByText(/inactive/i)).toBeVisible({ timeout: 5_000 });
  });

  test("resource appears in list after creation", async ({
    page,
    loginAs,
  }) => {
    await loginAs("CEO");

    // Create resource
    await page.goto("/resources/new");
    const uniqueId = `LIST-${Date.now()}`;
    const resourceName = `List Check ${uniqueId}`;
    await page.getByLabel(/name/i).first().fill(resourceName);
    await page.getByLabel(/employee id/i).fill(uniqueId);
    await page.getByLabel(/designation/i).fill("QA Engineer");
    await page.getByRole("button", { name: /create resource/i }).click();
    await page.waitForURL(/\/resources\/[a-f0-9-]+/);

    // Go to list and search for it
    await page.goto("/resources");
    await page.waitForResponse(
      (r) => r.url().includes("/resources") && r.ok()
    );
    await page.getByPlaceholder(/search/i).fill(uniqueId);
    await page.waitForResponse(
      (r) => r.url().includes("/resources") && r.ok()
    );
    await expect(page.getByText(resourceName)).toBeVisible();
  });
});

test.describe("Resource Management — Cross-Role Interaction", () => {
  test("HR creates resource, PM can view but not edit", async ({
    page,
    loginAs,
  }) => {
    // HR creates a resource
    await loginAs("HR");
    await page.goto("/resources/new");
    const uniqueId = `HR-${Date.now()}`;
    await page.getByLabel(/name/i).first().fill("HR Created Resource");
    await page.getByLabel(/employee id/i).fill(uniqueId);
    await page.getByLabel(/designation/i).fill("Analyst");
    await page.getByRole("button", { name: /create resource/i }).click();
    await page.waitForURL(/\/resources\/[a-f0-9-]+/);
    const resourceUrl = page.url();

    // PM views the resource
    await loginAs("PM");
    await page.goto(resourceUrl);
    await expect(
      page.getByRole("heading", { name: "HR Created Resource" })
    ).toBeVisible();
    // PM should NOT see edit button
    await expect(
      page.getByRole("button", { name: /edit/i })
    ).not.toBeVisible();
  });
});
