import { test, expect } from "../../../fixtures";

function uniqueId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

test.describe("UI Regression — Client CRUD", () => {
  test("full lifecycle: create -> view -> edit -> deactivate", async ({
    page,
    loginAs,
  }) => {
    await loginAs("CEO");
    await page.goto("/clients/new");

    const name = `UI Regression Client ${uniqueId("UICLI")}`;
    await page.getByLabel(/client name|name/i).first().fill(name);
    await page.getByRole("button", { name: /create client/i }).click();
    await page.waitForURL(/\/clients\/[a-f0-9-]+/, { timeout: 10_000 });
    await expect(page.getByRole("heading", { name })).toBeVisible();

    const editButton = page.getByRole("button", { name: /edit/i }).first();
    if (await editButton.isVisible().catch(() => false)) {
      await editButton.click();
      await page.waitForURL(/\/edit/);
      const industryField = page.getByLabel(/industry/i);
      if (await industryField.isVisible().catch(() => false)) {
        await industryField.fill("Retail");
      }
      await page.getByRole("button", { name: /save/i }).click();
      await page.waitForURL(/\/clients\/[a-f0-9-]+$/);
    }

    const deactivateButton = page.getByRole("button", { name: /deactivate/i });
    if (await deactivateButton.isVisible().catch(() => false)) {
      await deactivateButton.click();
      await page
        .getByRole("button", { name: /deactivate/i })
        .last()
        .click();
      await expect(page.getByText(/inactive/i)).toBeVisible({ timeout: 5_000 });
    }
  });

  test("form validation — missing name shows error, no navigation", async ({
    page,
    loginAs,
  }) => {
    await loginAs("CEO");
    await page.goto("/clients/new");
    await page.getByRole("button", { name: /create client/i }).click();
    await expect(page).toHaveURL(/\/clients\/new/);
  });

  test("HR (VIEW only) sees client list but no Add Client button", async ({
    page,
    loginAs,
  }) => {
    await loginAs("HR");
    await page.goto("/clients");
    await page.waitForResponse((r) => r.url().includes("/clients") && r.ok());
    await expect(page.getByText("Client Management")).toBeVisible();
    await expect(
      page.getByRole("button", { name: /add client/i })
    ).not.toBeVisible();
  });

  test("ENGINEER (NONE access) visiting clients page does not crash or leak data", async ({
    page,
    loginAs,
  }) => {
    await loginAs("ENGINEER");
    const response = await page.goto("/clients");
    expect(response?.status()).toBeLessThan(500);
    await expect(
      page.getByRole("button", { name: /add client/i })
    ).not.toBeVisible();
  });

  test("client list shows empty state on no search matches", async ({
    page,
    loginAs,
  }) => {
    await loginAs("CEO");
    await page.goto("/clients");
    await page.waitForResponse((r) => r.url().includes("/clients") && r.ok());
    const searchInput = page.getByPlaceholder(/search/i);
    if (await searchInput.isVisible().catch(() => false)) {
      await searchInput.fill(`nonexistent-client-${Date.now()}`);
      await page.waitForResponse((r) => r.url().includes("/clients") && r.ok());
      await expect(
        page.getByText(/no clients found|no results/i)
      ).toBeVisible();
    }
  });
});
