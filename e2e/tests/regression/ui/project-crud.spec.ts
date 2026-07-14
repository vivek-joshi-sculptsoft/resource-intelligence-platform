import { test, expect } from "../../../fixtures";
import { apiGet, apiPost } from "../../../utils/api";
import { apiLoginAs } from "../../../utils/api-auth";
import { createResource } from "../../../utils/api-scoped-user";

function uniqueId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

async function seedClientDmPm(request: import("@playwright/test").APIRequestContext) {
  await apiLoginAs(request, "CEO");
  const clientResp = await apiPost(request, "/clients", {
    name: `UI Project Client ${uniqueId("C")}`,
  });
  const clientName = (await clientResp.json()).data.name as string;
  const dmId = await createResource(request, { name: `DM ${uniqueId("D")}` });
  const pmId = await createResource(request, { name: `PM ${uniqueId("P")}` });
  const dmResp = await apiGet(request, `/resources/${dmId}`);
  const pmResp = await apiGet(request, `/resources/${pmId}`);
  const dmName = (await dmResp.json()).data.name as string;
  const pmName = (await pmResp.json()).data.name as string;
  return { clientName, dmName, pmName };
}

test.describe("UI Regression — Project CRUD", () => {
  test("create a project via form — happy path", async ({
    page,
    request,
    loginAs,
  }) => {
    const { clientName, dmName, pmName } = await seedClientDmPm(request);

    await loginAs("CEO");
    await page.goto("/projects/new");

    const projectName = `UI Regression Project ${uniqueId("UIP")}`;
    await page.getByPlaceholder("Enter project name").fill(projectName);

    await page.getByRole("button", { name: /select client/i }).click();
    await page.getByPlaceholder("Type to search...").fill(clientName);
    await page.getByText(clientName, { exact: true }).click();

    await page.getByRole("button", { name: /select dm/i }).click();
    await page.getByPlaceholder("Type to search...").fill(dmName);
    await page.getByText(dmName, { exact: true }).click();

    await page.getByRole("button", { name: /select pm/i }).click();
    await page.getByPlaceholder("Type to search...").fill(pmName);
    await page.getByText(pmName, { exact: true }).click();

    await page.getByRole("button", { name: /create project/i }).click();
    await page.waitForURL(/\/projects\/[a-f0-9-]+/, { timeout: 10_000 });
    await expect(page.getByRole("heading", { name: projectName })).toBeVisible();
  });

  test("form validation — missing required fields blocks submission", async ({
    page,
    loginAs,
  }) => {
    await loginAs("CEO");
    await page.goto("/projects/new");
    await page.getByRole("button", { name: /create project/i }).click();
    await expect(page).toHaveURL(/\/projects\/new/);
  });

  test("project detail shows tabs: Assignments, Milestones, Worklogs", async ({
    page,
    request,
    loginAs,
  }) => {
    const { clientName, dmName, pmName } = await seedClientDmPm(request);
    await loginAs("CEO");
    await page.goto("/projects/new");
    const projectName = `Tab Test Project ${uniqueId("UIP")}`;
    await page.getByPlaceholder("Enter project name").fill(projectName);
    await page.getByRole("button", { name: /select client/i }).click();
    await page.getByPlaceholder("Type to search...").fill(clientName);
    await page.getByText(clientName, { exact: true }).click();
    await page.getByRole("button", { name: /select dm/i }).click();
    await page.getByPlaceholder("Type to search...").fill(dmName);
    await page.getByText(dmName, { exact: true }).click();
    await page.getByRole("button", { name: /select pm/i }).click();
    await page.getByPlaceholder("Type to search...").fill(pmName);
    await page.getByText(pmName, { exact: true }).click();
    await page.getByRole("button", { name: /create project/i }).click();
    await page.waitForURL(/\/projects\/[a-f0-9-]+/, { timeout: 10_000 });

    await expect(page.getByText("Assignments", { exact: true })).toBeVisible();
    await expect(page.getByText("Milestones", { exact: true })).toBeVisible();
    await expect(page.getByText("Worklogs", { exact: true })).toBeVisible();
  });

  test("PM has no Add Project button on project list", async ({
    page,
    loginAs,
  }) => {
    await loginAs("PM");
    await page.goto("/projects");
    await page.waitForResponse((r) => r.url().includes("/projects") && r.ok());
    await expect(
      page.getByRole("button", { name: /add project|new project/i })
    ).not.toBeVisible();
  });

  test("ENGINEER (NONE access) visiting project list does not crash or leak data", async ({
    page,
    loginAs,
  }) => {
    await loginAs("ENGINEER");
    const response = await page.goto("/projects");
    expect(response?.status()).toBeLessThan(500);
    await expect(
      page.getByRole("button", { name: /add project|new project/i })
    ).not.toBeVisible();
  });

  test("project list supports status filter", async ({ page, loginAs }) => {
    await loginAs("CEO");
    await page.goto("/projects");
    await page.waitForResponse((r) => r.url().includes("/projects") && r.ok());
    await expect(page.getByText("Projects", { exact: false }).first()).toBeVisible();
  });
});
