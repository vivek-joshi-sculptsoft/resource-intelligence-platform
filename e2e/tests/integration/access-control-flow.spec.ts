import { test, expect } from "../../fixtures";

test.describe("Access Control — Cross-Module Role Enforcement", () => {
  test("CEO has full access to all modules", async ({ page, loginAs }) => {
    await loginAs("CEO");

    // Resources
    await page.goto("/resources");
    await expect(page.getByText("Resource Management")).toBeVisible();
    await expect(
      page.getByRole("button", { name: /add resource/i })
    ).toBeVisible();

    // Clients
    await page.goto("/clients");
    await expect(page.getByText("Client Management")).toBeVisible();
    await expect(
      page.getByRole("button", { name: /add client/i })
    ).toBeVisible();

    // Users
    await page.goto("/admin/users");
    await expect(page.getByText("User Management")).toBeVisible();

    // Roles
    await page.goto("/admin/roles");
    await expect(page.getByText("Role Management")).toBeVisible();
  });

  test("ENGINEER has minimal access — resources only (self)", async ({
    page,
    loginAs,
  }) => {
    await loginAs("ENGINEER");

    // Resources — can view but limited
    await page.goto("/resources");
    await expect(
      page.getByRole("button", { name: /add resource/i })
    ).not.toBeVisible();

    // Clients — blocked
    await page.goto("/clients");
    await expect(page).not.toHaveURL(/\/clients$/);

    // Users — blocked
    await page.goto("/admin/users");
    await expect(page).not.toHaveURL(/\/admin\/users$/);

    // Roles — blocked
    await page.goto("/admin/roles");
    await expect(page).not.toHaveURL(/\/admin\/roles$/);
  });

  test("HR can create resources but not clients", async ({
    page,
    loginAs,
  }) => {
    await loginAs("HR");

    // Resources — can create
    await page.goto("/resources");
    await expect(
      page.getByRole("button", { name: /add resource/i })
    ).toBeVisible();

    // Clients — can view but not create
    await page.goto("/clients");
    await page.waitForResponse(
      (r) => r.url().includes("/clients") && r.ok()
    );
    await expect(
      page.getByRole("button", { name: /add client/i })
    ).not.toBeVisible();
  });

  test("PM can view resources and clients but not create either", async ({
    page,
    loginAs,
  }) => {
    await loginAs("PM");

    // Resources — view only
    await page.goto("/resources");
    await expect(
      page.getByRole("button", { name: /add resource/i })
    ).not.toBeVisible();

    // Clients — view only
    await page.goto("/clients");
    await page.waitForResponse(
      (r) => r.url().includes("/clients") && r.ok()
    );
    await expect(
      page.getByRole("button", { name: /add client/i })
    ).not.toBeVisible();
  });
});
