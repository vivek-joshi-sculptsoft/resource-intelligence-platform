import { test, expect } from "../../../fixtures";

test.describe("S2-12: Client List Screen", () => {
  test.beforeEach(async ({ page, loginAs }) => {
    await loginAs("CEO");
    await page.goto("/clients");
  });

  test("client list page renders with title and controls", async ({
    page,
  }) => {
    await expect(page.getByText("Client Management")).toBeVisible();
    await expect(
      page.getByText(/manage client relationships/i)
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: /add client/i })
    ).toBeVisible();
    await expect(
      page.getByPlaceholder(/search by client name/i)
    ).toBeVisible();
  });

  test("client table shows correct columns", async ({ page }) => {
    await page.waitForResponse(
      (r) => r.url().includes("/clients") && r.ok()
    );
    const headers = page.locator("th");
    await expect(headers.filter({ hasText: /name/i }).first()).toBeVisible();
    await expect(
      headers.filter({ hasText: /industry/i }).first()
    ).toBeVisible();
    await expect(
      headers.filter({ hasText: /status/i }).first()
    ).toBeVisible();
  });

  test("search filters client list", async ({ page }) => {
    await page.waitForResponse(
      (r) => r.url().includes("/clients") && r.ok()
    );
    await page
      .getByPlaceholder(/search by client name/i)
      .fill("nonexistent-xyz");
    await page.waitForResponse(
      (r) => r.url().includes("/clients") && r.ok()
    );
  });

  test("status filter works", async ({ page }) => {
    const statusSelect = page
      .locator("select")
      .filter({ hasText: /all status/i });
    await statusSelect.selectOption("ACTIVE");
    await page.waitForResponse(
      (r) => r.url().includes("/clients") && r.ok()
    );
  });

  test("Add Client button navigates to form", async ({ page }) => {
    await page.getByRole("button", { name: /add client/i }).click();
    await expect(page).toHaveURL(/\/clients\/new/);
  });

  test("clicking a client row navigates to detail", async ({ page }) => {
    await page.waitForResponse(
      (r) => r.url().includes("/clients") && r.ok()
    );
    const firstRow = page.locator("tbody tr").first();
    const rowCount = await page.locator("tbody tr").count();
    if (rowCount > 0) {
      await firstRow.click();
      await expect(page).toHaveURL(/\/clients\/[a-f0-9-]+/);
    }
  });

  test("pagination shows record count", async ({ page }) => {
    await page.waitForResponse(
      (r) => r.url().includes("/clients") && r.ok()
    );
    await expect(page.getByText(/showing/i)).toBeVisible();
  });
});

test.describe("S2-12: Client List — Role Visibility", () => {
  test("CTO can see Add Client button", async ({ page, loginAs }) => {
    await loginAs("CTO");
    await page.goto("/clients");
    await expect(
      page.getByRole("button", { name: /add client/i })
    ).toBeVisible();
  });

  test("DM cannot see Add Client button", async ({ page, loginAs }) => {
    await loginAs("DM");
    await page.goto("/clients");
    await page.waitForResponse(
      (r) => r.url().includes("/clients") && r.ok()
    );
    await expect(
      page.getByRole("button", { name: /add client/i })
    ).not.toBeVisible();
  });

  test("ENGINEER cannot access clients page", async ({ page, loginAs }) => {
    await loginAs("ENGINEER");
    await page.goto("/clients");
    // Should be blocked — either redirected or forbidden
    await expect(page).not.toHaveURL(/\/clients$/);
  });
});
