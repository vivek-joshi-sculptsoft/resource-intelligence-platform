import { test, expect } from "../../fixtures";

test.describe("Clients Smoke", () => {
  test("client list loads for CEO", async ({ page, loginAs }) => {
    await loginAs("CEO");
    await page.goto("/clients");
    await expect(page.getByText("Client Management")).toBeVisible();
  });

  test("can create a client", async ({ page, loginAs }) => {
    await loginAs("CEO");
    await page.goto("/clients/new");
    await page
      .getByLabel(/client name|name/i)
      .first()
      .fill(`Smoke Client ${Date.now()}`);
    await page.getByRole("button", { name: /create client/i }).click();
    await expect(page).toHaveURL(/\/clients\/[a-f0-9-]+/, {
      timeout: 10_000,
    });
  });
});
