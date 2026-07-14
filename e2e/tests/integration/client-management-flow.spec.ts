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
    // Industry/Contact fields have no htmlFor association in ClientForm — locate
    // via the sibling input immediately after each label instead of getByLabel.
    const industryInput = page
      .getByText("Industry", { exact: true })
      .locator("xpath=following-sibling::input[1]");
    await industryInput.fill("Healthcare");
    await page
      .getByText("Contact Name", { exact: true })
      .locator("xpath=following-sibling::input[1]")
      .fill("Dr. Smith");
    await page
      .getByText("Contact Email", { exact: true })
      .locator("xpath=following-sibling::input[1]")
      .fill("smith@hospital.com");
    await page
      .getByText("Contact Phone", { exact: true })
      .locator("xpath=following-sibling::input[1]")
      .fill("+91-8888888888");
    await page.getByRole("button", { name: /create client/i }).click();
    await page.waitForURL(/\/clients\/[a-f0-9-]+/, { timeout: 10_000 });

    // Step 2: Verify detail page shows correct data
    await expect(page.getByRole("heading", { name: uniqueName })).toBeVisible();
    await expect(page.getByText("Healthcare")).toBeVisible();
    await expect(page.getByText("Dr. Smith")).toBeVisible();
    await expect(page.getByText("smith@hospital.com")).toBeVisible();
    await expect(page.getByText(/no projects yet/i)).toBeVisible();

    // Step 3: Edit the client
    await page.getByRole("button", { name: /edit/i }).first().click();
    await page.waitForURL(/\/edit/);
    const editIndustryInput = page
      .getByText("Industry", { exact: true })
      .locator("xpath=following-sibling::input[1]");
    await editIndustryInput.clear();
    await editIndustryInput.fill("Pharma");
    await page.getByRole("button", { name: /save changes/i }).click();
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
    await expect(page.getByRole("heading", { name: uniqueName })).toBeVisible();
  });
});
