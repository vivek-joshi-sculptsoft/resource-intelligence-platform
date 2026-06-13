import { test, expect } from "../../fixtures";

test.describe("Resources Smoke", () => {
  test("resource list loads for CEO", async ({ page, loginAs }) => {
    await loginAs("CEO");
    await page.goto("/resources");
    await expect(page.getByText("Resource Management")).toBeVisible();
  });

  test("can create a resource", async ({ page, loginAs }) => {
    await loginAs("CEO");
    await page.goto("/resources/new");
    await page.getByLabel(/name/i).first().fill(`Smoke ${Date.now()}`);
    await page.getByLabel(/employee id/i).fill(`SMK-${Date.now()}`);
    await page.getByLabel(/designation/i).fill("Dev");
    await page.getByRole("button", { name: /create resource/i }).click();
    await expect(page).toHaveURL(/\/resources\/[a-f0-9-]+/, {
      timeout: 10_000,
    });
  });
});
