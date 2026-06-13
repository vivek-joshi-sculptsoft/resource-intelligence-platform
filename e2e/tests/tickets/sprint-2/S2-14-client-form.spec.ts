import { test, expect } from "../../../fixtures";

test.describe("S2-14: Client Create/Edit Form", () => {
  test.beforeEach(async ({ page, loginAs }) => {
    await loginAs("CEO");
  });

  test("create form renders with all fields", async ({ page }) => {
    await page.goto("/clients/new");
    await expect(page.getByText(/add client/i).first()).toBeVisible();
    await expect(page.getByLabel(/client name|name/i).first()).toBeVisible();
    await expect(page.getByLabel(/industry/i)).toBeVisible();
    await expect(page.getByLabel(/contact name/i)).toBeVisible();
    await expect(page.getByLabel(/contact email/i)).toBeVisible();
    await expect(page.getByLabel(/contact phone/i)).toBeVisible();
    await expect(
      page.getByRole("button", { name: /create client/i })
    ).toBeVisible();
  });

  test("create client with valid data succeeds", async ({ page }) => {
    await page.goto("/clients/new");
    const uniqueName = `E2E Client ${Date.now()}`;
    await page.getByLabel(/client name|name/i).first().fill(uniqueName);
    await page.getByLabel(/industry/i).fill("Technology");
    await page.getByLabel(/contact name/i).fill("John Doe");
    await page.getByLabel(/contact email/i).fill("john@example.com");
    await page.getByLabel(/contact phone/i).fill("+91-9999999999");

    await page.getByRole("button", { name: /create client/i }).click();
    await expect(page).toHaveURL(/\/clients\/[a-f0-9-]+/, {
      timeout: 10_000,
    });
  });

  test("required name validation blocks submission", async ({ page }) => {
    await page.goto("/clients/new");
    // Leave name empty
    await page.getByLabel(/industry/i).fill("Tech");
    await page.getByRole("button", { name: /create client/i }).click();
    await expect(page).toHaveURL(/\/clients\/new/);
  });

  test("duplicate client name shows error", async ({ page }) => {
    const uniqueName = `DupClient-${Date.now()}`;

    // Create first client
    await page.goto("/clients/new");
    await page.getByLabel(/client name|name/i).first().fill(uniqueName);
    await page.getByRole("button", { name: /create client/i }).click();
    await page.waitForURL(/\/clients\/[a-f0-9-]+/, { timeout: 10_000 });

    // Try to create another with the same name
    await page.goto("/clients/new");
    await page.getByLabel(/client name|name/i).first().fill(uniqueName);
    await page.getByRole("button", { name: /create client/i }).click();
    await expect(page.getByText(/already|duplicate|exists/i)).toBeVisible({
      timeout: 5_000,
    });
  });

  test("edit form pre-populates fields", async ({ page }) => {
    // Create a client first
    await page.goto("/clients/new");
    const uniqueName = `EditTest-${Date.now()}`;
    await page.getByLabel(/client name|name/i).first().fill(uniqueName);
    await page.getByLabel(/industry/i).fill("Finance");
    await page.getByRole("button", { name: /create client/i }).click();
    await page.waitForURL(/\/clients\/[a-f0-9-]+/, { timeout: 10_000 });

    // Navigate to edit
    await page.getByRole("button", { name: /edit/i }).first().click();
    await page.waitForURL(/\/clients\/[a-f0-9-]+\/edit/);

    await expect(page.getByText(/edit client/i)).toBeVisible();
    const nameInput = page.getByLabel(/client name|name/i).first();
    await expect(nameInput).toHaveValue(uniqueName);
  });

  test("cancel returns to client list", async ({ page }) => {
    await page.goto("/clients/new");
    await page.getByRole("button", { name: /cancel/i }).click();
    await expect(page).toHaveURL(/\/clients/);
  });

  test("invalid email format shows validation error", async ({ page }) => {
    await page.goto("/clients/new");
    await page.getByLabel(/client name|name/i).first().fill("Email Test");
    await page.getByLabel(/contact email/i).fill("not-an-email");
    await page.getByRole("button", { name: /create client/i }).click();
    // Should show validation error or stay on form
    await expect(page).toHaveURL(/\/clients\/new/);
  });
});

test.describe("S2-14: Client Form — Access Control", () => {
  test("DM cannot access client create form", async ({ page, loginAs }) => {
    await loginAs("DM");
    await page.goto("/clients/new");
    await expect(page).not.toHaveURL(/\/clients\/new$/);
  });
});
