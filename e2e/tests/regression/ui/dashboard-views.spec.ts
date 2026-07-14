import { test, expect } from "../../../fixtures";
import { apiLoginAs } from "../../../utils/api-auth";
import { createScopedUser } from "../../../utils/api-scoped-user";

test.describe("UI Regression — Dashboard Views", () => {
  test("CEO sees Company Dashboard", async ({ page, loginAs }) => {
    await loginAs("CEO");
    await page.goto("/dashboard");
    await page.waitForResponse(
      (r) => r.url().includes("/dashboard/company") && r.ok()
    );
    await expect(page.getByText("Company Dashboard")).toBeVisible();
  });

  test("CTO sees Company Dashboard", async ({ page, loginAs }) => {
    await loginAs("CTO");
    await page.goto("/dashboard");
    await expect(page.getByText("Company Dashboard")).toBeVisible();
  });

  test("DM with a linked resource sees Portfolio Dashboard", async ({
    page,
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const dmUser = await createScopedUser(request, "DM");

    await page.goto("/login");
    await page.getByLabel(/email/i).fill(dmUser.email);
    await page
      .getByRole("textbox", { name: /password/i })
      .fill(dmUser.password);
    await page.getByRole("button", { name: /sign in/i }).click();
    await page.waitForURL(/\/(dashboard|availability)/);

    await page.goto("/dashboard");
    await expect(page.getByText("Portfolio Dashboard")).toBeVisible();
  });

  test("ENGINEER is redirected from /dashboard to /availability", async ({
    page,
    loginAs,
  }) => {
    await loginAs("ENGINEER");
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/availability/);
    await expect(page.getByText("Resource Availability")).toBeVisible();
  });

  test("HR is redirected from /dashboard to /availability", async ({
    page,
    loginAs,
  }) => {
    await loginAs("HR");
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/availability/);
  });

  test("availability page loads for PM", async ({ page, loginAs }) => {
    await loginAs("PM");
    await page.goto("/availability");
    await expect(page.getByText("Resource Availability")).toBeVisible();
  });

  test("availability page loads for FINANCE", async ({ page, loginAs }) => {
    await loginAs("FINANCE");
    await page.goto("/availability");
    await expect(page.getByText("Resource Availability")).toBeVisible();
  });
});
