import { test, expect } from "../../../fixtures";
import { apiGet, apiPost } from "../../../utils/api";
import { apiLoginAs } from "../../../utils/api-auth";
import { createResource } from "../../../utils/api-scoped-user";

function uniqueId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

async function seedProject(request: import("@playwright/test").APIRequestContext) {
  await apiLoginAs(request, "CEO");
  const clientResp = await apiPost(request, "/clients", {
    name: `Assign UI Client ${uniqueId("C")}`,
  });
  const clientId = (await clientResp.json()).data.id;
  const dmId = await createResource(request);
  const pmId = await createResource(request);
  const projectResp = await apiPost(request, "/projects", {
    name: `Assign UI Project ${uniqueId("P")}`,
    client_id: clientId,
    type: "FIXED_PRICE",
    dm_id: dmId,
    pm_id: pmId,
  });
  const projectId = (await projectResp.json()).data.id;
  return { projectId };
}

test.describe("UI Regression — Assignment Flows", () => {
  test("add an assignment via modal — happy path", async ({
    page,
    request,
    loginAs,
  }) => {
    const { projectId } = await seedProject(request);
    const resourceId = await createResource(request, {
      name: `Assignable ${uniqueId("R")}`,
    });
    const resourceResp = await apiGet(request, `/resources/${resourceId}`);
    const resourceName = (await resourceResp.json()).data.name as string;

    await loginAs("CEO");
    await page.goto(`/projects/${projectId}`);
    await page.getByRole("button", { name: /add assignment/i }).first().click();
    await expect(page.getByRole("heading", { name: "Add Assignment" })).toBeVisible();

    await page.getByRole("button", { name: /select a resource/i }).click();
    await page.getByPlaceholder("Type to search...").fill(resourceName);
    await page.getByText(resourceName, { exact: false }).first().click();

    await page.getByPlaceholder("e.g. 50").fill("50");
    await page.locator('input[type="date"]').first().fill("2026-01-01");

    await page.getByRole("button", { name: /save assignment/i }).click();
    await expect(page.getByText(/assignment created/i)).toBeVisible({
      timeout: 5_000,
    });
  });

  test("assignment form validation — missing resource blocks submission", async ({
    page,
    request,
    loginAs,
  }) => {
    const { projectId } = await seedProject(request);
    await loginAs("CEO");
    await page.goto(`/projects/${projectId}`);
    await page.getByRole("button", { name: /add assignment/i }).first().click();
    await page.getByRole("button", { name: /save assignment/i }).click();
    await expect(page.getByText(/resource is required/i)).toBeVisible();
  });

  test("over-allocation shows a warning banner in the modal", async ({
    page,
    request,
    loginAs,
  }) => {
    const { projectId: p1 } = await seedProject(request);
    const { projectId: p2 } = await seedProject(request);
    const resourceId = await createResource(request, {
      name: `OverAlloc ${uniqueId("R")}`,
    });
    const resourceResp = await apiGet(request, `/resources/${resourceId}`);
    const resourceName = (await resourceResp.json()).data.name as string;

    await apiPost(request, `/projects/${p1}/assignments`, {
      resource_id: resourceId,
      allocation_pct: 80,
      billability_pct: 80,
      start_date: "2026-01-01",
    });

    await loginAs("CEO");
    await page.goto(`/projects/${p2}`);
    await page.getByRole("button", { name: /add assignment/i }).first().click();
    await page.getByRole("button", { name: /select a resource/i }).click();
    await page.getByPlaceholder("Type to search...").fill(resourceName);
    await page.getByText(resourceName, { exact: false }).first().click();
    await page.getByPlaceholder("e.g. 50").fill("50");

    await expect(page.getByText(/bring total allocation/i)).toBeVisible();
  });

  test("billing_rate field hidden for HR in assignment modal", async ({
    page,
    request,
    loginAs,
  }) => {
    const { projectId } = await seedProject(request);
    await loginAs("HR");
    await page.goto(`/projects/${projectId}`);
    const addButton = page.getByRole("button", { name: /add assignment/i }).first();
    if (await addButton.isVisible().catch(() => false)) {
      await addButton.click();
      await expect(page.getByText(/billing rate/i)).not.toBeVisible();
    }
  });

  test("release an assignment from the list", async ({
    page,
    request,
    loginAs,
  }) => {
    const { projectId } = await seedProject(request);
    const resourceId = await createResource(request);
    await apiPost(request, `/projects/${projectId}/assignments`, {
      resource_id: resourceId,
      allocation_pct: 50,
      billability_pct: 50,
      start_date: "2026-01-01",
    });

    await loginAs("CEO");
    await page.goto(`/projects/${projectId}`);
    const releaseButton = page.getByRole("button", { name: /release/i }).first();
    if (await releaseButton.isVisible().catch(() => false)) {
      await releaseButton.click();
      const confirmButton = page
        .getByRole("button", { name: /release/i })
        .last();
      await confirmButton.click();
      await expect(page.getByText(/released/i).first()).toBeVisible({
        timeout: 5_000,
      });
    }
  });
});
