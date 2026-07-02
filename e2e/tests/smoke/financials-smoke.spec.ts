import { test, expect } from "../../fixtures";

// Phase 2 critical paths — VRIP-109.
// Financial widgets on the company dashboard, receivables page, and
// role-based visibility of financial navigation.
test.describe("Financials Smoke", () => {
  test("company dashboard shows financial widgets for CEO", async ({
    page,
    loginAs,
  }) => {
    await loginAs("CEO");
    await page.goto("/dashboard");
    await expect(page.getByText("Company Margin")).toBeVisible();
    await expect(page.getByText("Total Cost").first()).toBeVisible();
  });

  test("receivables page loads for CEO", async ({ page, loginAs }) => {
    await loginAs("CEO");
    await page.goto("/receivables");
    await expect(
      page.getByRole("heading", { name: "Receivables" }),
    ).toBeVisible();
  });

  test("receivables page loads for FINANCE", async ({ page, loginAs }) => {
    await loginAs("FINANCE");
    await page.goto("/receivables");
    await expect(
      page.getByRole("heading", { name: "Receivables" }),
    ).toBeVisible();
  });

  test("engineer does not see Receivables navigation", async ({
    page,
    loginAs,
  }) => {
    await loginAs("ENGINEER");
    await page.goto("/dashboard");
    await expect(page.getByRole("link", { name: "Receivables" })).toHaveCount(
      0,
    );
  });
});
