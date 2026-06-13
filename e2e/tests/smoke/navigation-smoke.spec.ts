import { test, expect } from "../../fixtures";

test.describe("Navigation Smoke", () => {
  test("sidebar navigation works across all pages", async ({
    page,
    loginAs,
  }) => {
    await loginAs("CEO");

    // Dashboard
    await page.goto("/dashboard");
    await expect(page.getByText(/dashboard/i).first()).toBeVisible();

    // Resources
    await page.goto("/resources");
    await expect(page.getByText("Resource Management")).toBeVisible();

    // Clients
    await page.goto("/clients");
    await expect(page.getByText("Client Management")).toBeVisible();

    // Users
    await page.goto("/admin/users");
    await expect(page.getByText("User Management")).toBeVisible();

    // Roles
    await page.goto("/admin/roles");
    await expect(page.getByText("Role Management")).toBeVisible();
  });
});
