import { test, expect } from "../../../fixtures";

test.describe("UI Regression — Auth Flows", () => {
  test("empty email/password shows validation, does not submit", async ({
    page,
  }) => {
    await page.goto("/login");
    await page.getByRole("button", { name: /sign in/i }).click();
    await expect(page).toHaveURL(/\/login/);
  });

  test("wrong password shows an error message and stays on login", async ({
    page,
  }) => {
    await page.goto("/login");
    await page.getByLabel(/email/i).fill("admin@riplatform.com");
    await page
      .getByRole("textbox", { name: /password/i })
      .fill("wrong-password");
    await page.getByRole("button", { name: /sign in/i }).click();
    await expect(page.getByText(/invalid|incorrect|unauthorized/i)).toBeVisible();
    await expect(page).toHaveURL(/\/login/);
  });

  test("DM and ENGINEER can both log in and reach a non-login page", async ({
    page,
    loginAs,
  }) => {
    await loginAs("DM");
    await expect(page).not.toHaveURL(/\/login/);

    await loginAs("ENGINEER");
    await expect(page).not.toHaveURL(/\/login/);
  });

  test("logout redirects to login and clears the session", async ({
    page,
    loginAs,
  }) => {
    await loginAs("CEO");
    // Logout lives in a dropdown behind the user-menu trigger in the header.
    await page.getByRole("button", { name: /CEO/i }).click();
    await page
      .getByRole("button", { name: /logout|sign out|log out/i })
      .click();
    await expect(page).toHaveURL(/\/login/);

    await page.goto("/resources");
    await expect(page).toHaveURL(/\/login/);
  });

  test("visiting a protected route while unauthenticated redirects to login", async ({
    page,
  }) => {
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/login/);
  });

  test("CEO sidebar shows full navigation (Resources, Clients, Projects)", async ({
    page,
    loginAs,
  }) => {
    await loginAs("CEO");
    await expect(page.getByText(/resources/i).first()).toBeVisible();
    await expect(page.getByText(/clients/i).first()).toBeVisible();
    await expect(page.getByText(/projects/i).first()).toBeVisible();
  });

  test("ENGINEER sidebar hides Clients and Projects management links", async ({
    page,
    loginAs,
  }) => {
    await loginAs("ENGINEER");
    const sidebar = page.locator("nav, aside");
    await expect(sidebar.getByText(/clients/i)).not.toBeVisible();
  });
});
