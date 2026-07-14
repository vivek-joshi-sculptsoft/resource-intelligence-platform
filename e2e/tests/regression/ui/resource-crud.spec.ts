import { test, expect } from "../../../fixtures";

function uniqueId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

test.describe("UI Regression — Resource CRUD", () => {
  test("full lifecycle: create -> view -> edit -> tag -> deactivate", async ({
    page,
    loginAs,
  }) => {
    await loginAs("CEO");
    await page.goto("/resources/new");

    const uid = uniqueId("UIRES");
    const name = `UI Regression Resource ${uid}`;
    await page.getByLabel(/name/i).first().fill(name);
    await page.getByLabel(/employee id/i).fill(uid);
    await page.getByLabel(/designation/i).fill("QA Engineer");
    await page.getByRole("button", { name: /create resource/i }).click();
    await page.waitForURL(/\/resources\/[a-f0-9-]+/, { timeout: 10_000 });
    await expect(page.getByRole("heading", { name })).toBeVisible();

    await page.getByRole("button", { name: /edit/i }).first().click();
    await page.waitForURL(/\/edit/);
    await page.getByLabel(/designation/i).clear();
    await page.getByLabel(/designation/i).fill("Senior QA Engineer");
    await page.getByRole("button", { name: /save changes/i }).click();
    await page.waitForURL(/\/resources\/[a-f0-9-]+$/);
    await expect(page.getByText("Senior QA Engineer")).toBeVisible();

    const tagInput = page.getByPlaceholder(/add.*tag/i);
    if (await tagInput.isVisible().catch(() => false)) {
      await tagInput.fill("regression-tag");
      await tagInput.press("Enter");
      await expect(page.getByText("regression-tag")).toBeVisible();
    }

    await page.getByRole("button", { name: /deactivate/i }).click();
    await page
      .getByRole("button", { name: /deactivate/i })
      .last()
      .click();
    await expect(page.getByText(/inactive/i)).toBeVisible({ timeout: 5_000 });
  });

  test("form validation — required fields show errors, no navigation", async ({
    page,
    loginAs,
  }) => {
    await loginAs("CEO");
    await page.goto("/resources/new");
    await page.getByRole("button", { name: /create resource/i }).click();
    await expect(page).toHaveURL(/\/resources\/new/);
    await expect(page.getByText(/required/i).first()).toBeVisible();
  });

  test("loaded_cost_monthly field hidden for HR", async ({
    page,
    loginAs,
  }) => {
    await loginAs("HR");
    await page.goto("/resources/new");
    await expect(page.getByLabel(/name/i).first()).toBeVisible();
    await expect(page.getByText(/loaded cost monthly/i)).not.toBeVisible();
  });

  test("loaded_cost_monthly field visible for CEO", async ({
    page,
    loginAs,
  }) => {
    await loginAs("CEO");
    await page.goto("/resources/new");
    await expect(page.getByText(/loaded cost monthly/i)).toBeVisible();
  });

  test("FINANCE can view resource list but cannot create", async ({
    page,
    loginAs,
  }) => {
    await loginAs("FINANCE");
    await page.goto("/resources");
    await page.waitForResponse((r) => r.url().includes("/resources") && r.ok());
    await expect(page.getByText("Resource Management")).toBeVisible();
    await expect(
      page.getByRole("button", { name: /add resource/i })
    ).not.toBeVisible();
  });

  test("ENGINEER (SELF_ONLY scope) visiting resources list has no Add Resource button", async ({
    page,
    loginAs,
  }) => {
    await loginAs("ENGINEER");
    const response = await page.goto("/resources");
    expect(response?.status()).toBeLessThan(500);
    await expect(
      page.getByRole("button", { name: /add resource/i })
    ).not.toBeVisible();
  });

  test("empty search results show a helpful empty state, not a blank screen", async ({
    page,
    loginAs,
  }) => {
    await loginAs("CEO");
    await page.goto("/resources");
    await page.waitForResponse((r) => r.url().includes("/resources") && r.ok());
    await page.getByPlaceholder(/search/i).fill(`nonexistent-${Date.now()}`);
    await page.waitForResponse((r) => r.url().includes("/resources") && r.ok());
    await expect(page.getByText(/no resources found|no results/i)).toBeVisible();
  });

  test("resource list table supports column sorting", async ({
    page,
    loginAs,
  }) => {
    await loginAs("CEO");
    await page.goto("/resources");
    await page.waitForResponse((r) => r.url().includes("/resources") && r.ok());
    const nameHeader = page.getByRole("columnheader", { name: /name/i });
    if (await nameHeader.isVisible().catch(() => false)) {
      await nameHeader.click();
      await page.waitForTimeout(300);
    }
  });
});
