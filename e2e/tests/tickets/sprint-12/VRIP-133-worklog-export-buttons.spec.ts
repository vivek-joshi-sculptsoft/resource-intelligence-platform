import { test, expect } from "../../../fixtures";

const API = "http://localhost:8000/api/v1";
const RUN_ID = Date.now().toString(36);

test.describe("VRIP-133: Worklog Export Buttons", () => {
  test.describe.configure({ mode: "serial" });

  let projectId: string;
  let resourceId: string;

  test("seed test data", async ({ request }) => {
    // Log in as admin (CEO)
    const loginResp = await request.post(`${API}/auth/login`, {
      data: { email: "admin@riplatform.com", password: "admin123" },
    });
    expect(loginResp.ok(), "admin login failed").toBeTruthy();

    // Create resource (will be used as engineer, dm, pm)
    const resResp = await request.post(`${API}/resources`, {
      data: {
        employee_id: `EXP-${RUN_ID}`,
        name: `Export Eng ${RUN_ID}`,
        designation: "Developer",
        date_of_joining: "2025-01-01",
      },
    });
    expect(resResp.ok(), `resource create: ${resResp.status()} ${await resResp.text()}`).toBeTruthy();
    const resBody = await resResp.json();
    resourceId = resBody.data.id;

    // Create client
    const clientResp = await request.post(`${API}/clients`, {
      data: { name: `Export Client ${RUN_ID}` },
    });
    expect(clientResp.ok(), `client create: ${clientResp.status()}`).toBeTruthy();
    const clientId = (await clientResp.json()).data.id;

    // Create project with worklog_enabled (dm_id and pm_id required)
    const projResp = await request.post(`${API}/projects`, {
      data: {
        name: `Export Project ${RUN_ID}`,
        client_id: clientId,
        type: "TIME_AND_MATERIAL",
        dm_id: resourceId,
        pm_id: resourceId,
        worklog_enabled: true,
        contract_end_date: "2030-12-31",
      },
    });
    expect(projResp.ok(), `project create: ${projResp.status()} ${await projResp.text()}`).toBeTruthy();
    projectId = (await projResp.json()).data.id;

    // Create assignment under the project
    const assignResp = await request.post(
      `${API}/projects/${projectId}/assignments`,
      {
        data: {
          resource_id: resourceId,
          allocation_pct: 100,
          billability_pct: 100,
          start_date: "2025-01-01",
        },
      },
    );
    expect(assignResp.ok(), `assignment create: ${assignResp.status()} ${await assignResp.text()}`).toBeTruthy();

    // Link engineer user to this resource
    const usersResp = await request.get(`${API}/users?limit=100`);
    const users = (await usersResp.json()).data;
    const engUser = users.find(
      (u: { email: string }) => u.email === "engineer@riplatform.com",
    );
    if (engUser) {
      await request.put(`${API}/users/${engUser.id}`, {
        data: { resource_id: resourceId },
      });
    }

    // Log in as engineer to create worklogs
    const engLogin = await request.post(`${API}/auth/login`, {
      data: { email: "engineer@riplatform.com", password: "admin123" },
    });
    expect(engLogin.ok(), "engineer login failed").toBeTruthy();

    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const twoDaysAgo = new Date();
    twoDaysAgo.setDate(twoDaysAgo.getDate() - 2);

    const w1 = await request.post(`${API}/worklogs`, {
      data: {
        project_id: projectId,
        log_date: yesterday.toISOString().split("T")[0],
        hours: 4.0,
        note: "Export test day 1",
      },
    });
    expect(w1.ok(), `worklog 1: ${w1.status()} ${await w1.text()}`).toBeTruthy();

    const w2 = await request.post(`${API}/worklogs`, {
      data: {
        project_id: projectId,
        log_date: twoDaysAgo.toISOString().split("T")[0],
        hours: 3.0,
        note: "Export test day 2",
      },
    });
    expect(w2.ok(), `worklog 2: ${w2.status()} ${await w2.text()}`).toBeTruthy();
  });

  test("Export button on /worklogs downloads xlsx", async ({
    page,
    loginAs,
  }) => {
    await loginAs("CEO");
    await page.goto("/worklogs");
    await page.waitForSelector("table", { timeout: 10_000 });

    const exportBtn = page.getByRole("button", { name: /export/i });
    await expect(exportBtn).toBeVisible();
    await expect(exportBtn).toBeEnabled();

    const [download] = await Promise.all([
      page.waitForEvent("download"),
      exportBtn.click(),
    ]);
    expect(download.suggestedFilename()).toMatch(/\.xlsx$/);
  });

  test("Export button disabled when list is empty", async ({
    page,
    loginAs,
  }) => {
    await loginAs("CEO");
    await page.goto("/worklogs");
    await page.waitForSelector("table", { timeout: 10_000 });

    // Filter to empty range
    const fromInput = page.locator('input[type="date"]').first();
    await fromInput.fill("2020-01-01");
    const toInput = page.locator('input[type="date"]').nth(1);
    await toInput.fill("2020-01-02");

    // Wait for empty state
    await expect(
      page.getByText(/no worklog entries/i),
    ).toBeVisible({ timeout: 5_000 });

    const exportBtn = page.getByRole("button", { name: /export/i });
    await expect(exportBtn).toBeDisabled();
  });

  test("Export button on Project Detail Worklogs tab", async ({
    page,
    loginAs,
  }) => {
    expect(projectId, "projectId should be set by seed step").toBeTruthy();

    await loginAs("CEO");
    await page.goto(`/projects/${projectId}`);

    // Click Worklogs tab
    const worklogsTab = page
      .getByRole("tab", { name: /worklogs/i })
      .or(page.locator('[role="tab"]').filter({ hasText: /worklogs/i }))
      .or(page.getByText("Worklogs", { exact: false }));
    await worklogsTab.first().click();

    // Wait for worklog table
    await page.waitForSelector("table", { timeout: 10_000 });

    const exportBtn = page.getByRole("button", { name: /export/i });
    await expect(exportBtn).toBeVisible();
    await expect(exportBtn).toBeEnabled();

    const [download] = await Promise.all([
      page.waitForEvent("download"),
      exportBtn.click(),
    ]);
    expect(download.suggestedFilename()).toMatch(/\.xlsx$/);
  });

  test("Export button on My Assignments page", async ({ page, loginAs }) => {
    await loginAs("ENGINEER");
    await page.goto("/my-assignments");

    // Wait for Recent Entries section
    await expect(
      page.getByText("Recent Entries", { exact: false }),
    ).toBeVisible({ timeout: 10_000 });

    const exportBtn = page.getByRole("button", { name: /export/i });
    await expect(exportBtn).toBeVisible();
    await expect(exportBtn).toBeEnabled();

    const [download] = await Promise.all([
      page.waitForEvent("download"),
      exportBtn.click(),
    ]);
    expect(download.suggestedFilename()).toMatch(/\.xlsx$/);
  });

  test("Export filename includes date range when filtered", async ({
    page,
    loginAs,
  }) => {
    await loginAs("CEO");
    await page.goto("/worklogs");
    await page.waitForSelector("table", { timeout: 10_000 });

    const fromInput = page.locator('input[type="date"]').first();
    await fromInput.fill("2025-01-01");
    const toInput = page.locator('input[type="date"]').nth(1);
    await toInput.fill("2030-12-31");

    // Wait for data refresh
    await page.waitForTimeout(500);

    const exportBtn = page.getByRole("button", { name: /export/i });
    await expect(exportBtn).toBeEnabled();

    const [download] = await Promise.all([
      page.waitForEvent("download"),
      exportBtn.click(),
    ]);

    const filename = download.suggestedFilename();
    expect(filename).toContain("2025-01-01");
    expect(filename).toContain("2030-12-31");
  });

  test("FINANCE role can export worklogs", async ({ page, loginAs }) => {
    await loginAs("FINANCE");
    await page.goto("/worklogs");
    await page.waitForSelector("table", { timeout: 10_000 });

    const exportBtn = page.getByRole("button", { name: /export/i });
    await expect(exportBtn).toBeEnabled();

    const [download] = await Promise.all([
      page.waitForEvent("download"),
      exportBtn.click(),
    ]);
    expect(download.suggestedFilename()).toMatch(/\.xlsx$/);
  });
});
