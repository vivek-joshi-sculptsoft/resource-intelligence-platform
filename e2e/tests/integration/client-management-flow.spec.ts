import { test, expect } from "../../fixtures";

test.describe("Client Management — Full Lifecycle", () => {
  test("CEO creates client, views detail, edits, deactivates", async ({
    page,
    loginAs,
  }) => {
    await loginAs("CEO");

    // Step 1: Create a client
    await page.goto("/clients/new");
    const uniqueName = `IntegClient ${Date.now()}`;
    await page.getByLabel(/client name|name/i).first().fill(uniqueName);
    await page.getByLabel(/industry/i).fill("Healthcare");
    await page.getByLabel(/contact name/i).fill("Dr. Smith");
    await page.getByLabel(/contact email/i).fill("smith@hospital.com");
    await page.getByLabel(/contact phone/i).fill("+91-8888888888");
    await page.getByRole("button", { name: /create client/i }).click();
    await page.waitForURL(/\/clients\/[a-f0-9-]+/, { timeout: 10_000 });

    // Step 2: Verify detail page shows correct data
    await expect(page.getByText(uniqueName)).toBeVisible();
    await expect(page.getByText("Healthcare")).toBeVisible();
    await expect(page.getByText("Dr. Smith")).toBeVisible();
    await expect(page.getByText("smith@hospital.com")).toBeVisible();
    await expect(page.getByText(/no projects yet/i)).toBeVisible();

    // Step 3: Edit the client
    await page.getByRole("button", { name: /edit/i }).first().click();
    await page.waitForURL(/\/edit/);
    await page.getByLabel(/industry/i).clear();
    await page.getByLabel(/industry/i).fill("Pharma");
    await page.getByRole("button", { name: /save client/i }).click();
    await page.waitForURL(/\/clients\/[a-f0-9-]+$/);
    await expect(page.getByText("Pharma")).toBeVisible();

    // Step 4: Deactivate
    await page.getByRole("button", { name: /deactivate/i }).click();
    const confirmBtn = page
      .getByRole("button", { name: /deactivate/i })
      .last();
    await confirmBtn.click();
    await expect(page.getByText(/inactive/i)).toBeVisible({ timeout: 5_000 });
  });

  test("client appears in list after creation and is searchable", async ({
    page,
    loginAs,
  }) => {
    await loginAs("CEO");

    // Create client
    await page.goto("/clients/new");
    const uniqueName = `SearchClient ${Date.now()}`;
    await page.getByLabel(/client name|name/i).first().fill(uniqueName);
    await page.getByRole("button", { name: /create client/i }).click();
    await page.waitForURL(/\/clients\/[a-f0-9-]+/);

    // Search in list
    await page.goto("/clients");
    await page.waitForResponse(
      (r) => r.url().includes("/clients") && r.ok()
    );
    await page.getByPlaceholder(/search/i).fill(uniqueName);
    await page.waitForResponse(
      (r) => r.url().includes("/clients") && r.ok()
    );
    await expect(page.getByText(uniqueName)).toBeVisible();
  });
});

test.describe("Client Management — Cross-Role Access", () => {
  test("FINANCE can view clients but not create", async ({
    page,
    loginAs,
  }) => {
    await loginAs("FINANCE");
    await page.goto("/clients");
    await page.waitForResponse(
      (r) => r.url().includes("/clients") && r.ok()
    );
    await expect(page.getByText("Client Management")).toBeVisible();
    await expect(
      page.getByRole("button", { name: /add client/i })
    ).not.toBeVisible();
  });

  test("CTO can create and manage clients", async ({ page, loginAs }) => {
    await loginAs("CTO");
    await page.goto("/clients/new");
    const uniqueName = `CTO-Client ${Date.now()}`;
    await page.getByLabel(/client name|name/i).first().fill(uniqueName);
    await page.getByRole("button", { name: /create client/i }).click();
    await page.waitForURL(/\/clients\/[a-f0-9-]+/, { timeout: 10_000 });
    await expect(page.getByText(uniqueName)).toBeVisible();
  });
});
