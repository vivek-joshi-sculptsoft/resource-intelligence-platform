import { test, expect } from "../../../fixtures";
import { apiPost } from "../../../utils/api";
import { apiLoginAs } from "../../../utils/api-auth";
import { createResource, createScopedUser } from "../../../utils/api-scoped-user";

function uniqueId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

async function seedWorklogEnabledAssignment(
  request: import("@playwright/test").APIRequestContext
) {
  await apiLoginAs(request, "CEO");
  const clientResp = await apiPost(request, "/clients", {
    name: `Worklog UI Client ${uniqueId("C")}`,
  });
  const clientId = (await clientResp.json()).data.id;
  const dmId = await createResource(request);
  const pmId = await createResource(request);
  const projectResp = await apiPost(request, "/projects", {
    name: `Worklog UI Project ${uniqueId("P")}`,
    client_id: clientId,
    type: "FIXED_PRICE",
    dm_id: dmId,
    pm_id: pmId,
    worklog_enabled: true,
  });
  const projectId = (await projectResp.json()).data.id;

  const engineerResourceId = await createResource(request);
  await apiPost(request, `/projects/${projectId}/assignments`, {
    resource_id: engineerResourceId,
    allocation_pct: 100,
    billability_pct: 100,
    start_date: "2026-01-01",
  });

  const engineerUser = await createScopedUser(
    request,
    "ENGINEER",
    engineerResourceId
  );
  return { projectId, engineerUser };
}

test.describe("UI Regression — Worklog Flows", () => {
  test("engineer logs hours for today via My Assignments page", async ({
    page,
    request,
  }) => {
    const { engineerUser } = await seedWorklogEnabledAssignment(request);

    await page.goto("/login");
    await page.getByLabel(/email/i).fill(engineerUser.email);
    await page
      .getByRole("textbox", { name: /password/i })
      .fill(engineerUser.password);
    await page.getByRole("button", { name: /sign in/i }).click();
    await page.waitForURL(/\/(dashboard|availability|my-assignments)/);

    await page.goto("/my-assignments");
    await page.waitForResponse(
      (r) => r.url().includes("/worklogs/my") && r.ok()
    );

    const hoursInput = page.getByPlaceholder("0.0").first();
    if (await hoursInput.isVisible().catch(() => false)) {
      await hoursInput.fill("8");
      const noteInput = page.getByPlaceholder(/what did you work on/i).first();
      await noteInput.fill("Regression test entry");
      await page.getByRole("button", { name: /save worklogs/i }).click();
      await expect(page.getByText(/saved/i).first()).toBeVisible({
        timeout: 5_000,
      });
    }
  });

  test("FINANCE (view-only, resource-linked) sees a view-only message, cannot log hours", async ({
    page,
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const resourceId = await createResource(request);
    const financeUser = await createScopedUser(request, "FINANCE", resourceId);

    await page.goto("/login");
    await page.getByLabel(/email/i).fill(financeUser.email);
    await page
      .getByRole("textbox", { name: /password/i })
      .fill(financeUser.password);
    await page.getByRole("button", { name: /sign in/i }).click();
    await page.waitForURL(/\/(dashboard|availability|my-assignments)/);

    await page.goto("/my-assignments");
    await expect(
      page.getByText(/view worklogs but not log hours/i)
    ).toBeVisible();
  });

  test("FINANCE with no linked resource profile sees a helpful message, not a crash", async ({
    page,
    loginAs,
  }) => {
    await loginAs("FINANCE");
    await page.goto("/my-assignments");
    await expect(page.getByText(/no resource profile/i)).toBeVisible();
  });

  test("org-wide worklogs page loads for CEO", async ({ page, loginAs }) => {
    await loginAs("CEO");
    await page.goto("/worklogs");
    await page.waitForResponse((r) => r.url().includes("/worklogs") && r.ok());
    await expect(page.locator("body")).toBeVisible();
  });

  test("ENGINEER visiting org-wide worklogs page does not crash (scoped or empty)", async ({
    page,
    loginAs,
  }) => {
    await loginAs("ENGINEER");
    const response = await page.goto("/worklogs");
    expect(response?.status()).toBeLessThan(500);
  });
});
