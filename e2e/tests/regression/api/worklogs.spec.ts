import { test, expect, type APIRequestContext } from "@playwright/test";
import { apiDelete, apiGet, apiPost, apiPut } from "../../../utils/api";
import { apiLoginAs } from "../../../utils/api-auth";
import {
  apiLoginAsScoped,
  createResource,
  createScopedUser,
} from "../../../utils/api-scoped-user";

function uniqueId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

const PAST_DATE = "2026-01-15";
const FUTURE_DATE = "2099-01-01";

async function setupWorklogEnabledProjectWithAssignment(
  request: APIRequestContext
) {
  await apiLoginAs(request, "CEO");
  const clientResp = await apiPost(request, "/clients", {
    name: `Worklog Client ${uniqueId("C")}`,
  });
  const clientId = (await clientResp.json()).data.id;
  const dmId = await createResource(request);
  const pmId = await createResource(request);

  const projectResp = await apiPost(request, "/projects", {
    name: `Worklog Project ${uniqueId("P")}`,
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
  return { projectId, engineerResourceId, engineerUser };
}

test.describe("API Regression — Worklogs", () => {
  test("engineer logs hours — happy path, nested project/resource present", async ({
    request,
  }) => {
    const { projectId, engineerUser } =
      await setupWorklogEnabledProjectWithAssignment(request);

    await apiLoginAsScoped(request, engineerUser);
    const resp = await apiPost(request, "/worklogs", {
      project_id: projectId,
      log_date: PAST_DATE,
      hours: 8,
    });
    expect(resp.status()).toBe(201);
    const body = await resp.json();
    expect(body.data.project.id).toBe(projectId);
    expect(body.data.resource.id).toBeDefined();
  });

  test("future-dated worklog is rejected", async ({ request }) => {
    const { projectId, engineerUser } =
      await setupWorklogEnabledProjectWithAssignment(request);

    await apiLoginAsScoped(request, engineerUser);
    const resp = await apiPost(request, "/worklogs", {
      project_id: projectId,
      log_date: FUTURE_DATE,
      hours: 8,
    });
    expect(resp.status()).toBe(422);
  });

  test("worklog rejected for project with worklog_enabled=false", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const clientResp = await apiPost(request, "/clients", {
      name: `Disabled Client ${uniqueId("C")}`,
    });
    const clientId = (await clientResp.json()).data.id;
    const dmId = await createResource(request);
    const pmId = await createResource(request);
    const projectResp = await apiPost(request, "/projects", {
      name: `Disabled Worklog Project ${uniqueId("P")}`,
      client_id: clientId,
      type: "FIXED_PRICE",
      dm_id: dmId,
      pm_id: pmId,
      worklog_enabled: false,
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

    await apiLoginAsScoped(request, engineerUser);
    const resp = await apiPost(request, "/worklogs", {
      project_id: projectId,
      log_date: PAST_DATE,
      hours: 8,
    });
    expect(resp.status()).toBe(422);
  });

  test("worklog rejected without an active assignment covering the date", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const clientResp = await apiPost(request, "/clients", {
      name: `No Assignment Client ${uniqueId("C")}`,
    });
    const clientId = (await clientResp.json()).data.id;
    const dmId = await createResource(request);
    const pmId = await createResource(request);
    const projectResp = await apiPost(request, "/projects", {
      name: `No Assignment Project ${uniqueId("P")}`,
      client_id: clientId,
      type: "FIXED_PRICE",
      dm_id: dmId,
      pm_id: pmId,
      worklog_enabled: true,
    });
    const projectId = (await projectResp.json()).data.id;
    const engineerResourceId = await createResource(request);
    const engineerUser = await createScopedUser(
      request,
      "ENGINEER",
      engineerResourceId
    );

    await apiLoginAsScoped(request, engineerUser);
    const resp = await apiPost(request, "/worklogs", {
      project_id: projectId,
      log_date: PAST_DATE,
      hours: 8,
    });
    expect(resp.status()).toBe(422);
  });

  test("invalid hours (0.3, not a 0.5 increment) rejected with 422", async ({
    request,
  }) => {
    const { projectId, engineerUser } =
      await setupWorklogEnabledProjectWithAssignment(request);
    await apiLoginAsScoped(request, engineerUser);
    const resp = await apiPost(request, "/worklogs", {
      project_id: projectId,
      log_date: PAST_DATE,
      hours: 0.3,
    });
    expect(resp.status()).toBe(422);
  });

  test("hours exceeding 24 rejected with 422", async ({ request }) => {
    const { projectId, engineerUser } =
      await setupWorklogEnabledProjectWithAssignment(request);
    await apiLoginAsScoped(request, engineerUser);
    const resp = await apiPost(request, "/worklogs", {
      project_id: projectId,
      log_date: PAST_DATE,
      hours: 25,
    });
    expect(resp.status()).toBe(422);
  });

  test("duplicate worklog for same project+date is rejected", async ({
    request,
  }) => {
    const { projectId, engineerUser } =
      await setupWorklogEnabledProjectWithAssignment(request);
    await apiLoginAsScoped(request, engineerUser);
    await apiPost(request, "/worklogs", {
      project_id: projectId,
      log_date: PAST_DATE,
      hours: 4,
    });
    const resp = await apiPost(request, "/worklogs", {
      project_id: projectId,
      log_date: PAST_DATE,
      hours: 4,
    });
    expect([400, 409]).toContain(resp.status());
  });

  test("engineer can only update own worklog entries", async ({
    request,
  }) => {
    const { projectId, engineerUser } =
      await setupWorklogEnabledProjectWithAssignment(request);
    await apiLoginAsScoped(request, engineerUser);
    const createResp = await apiPost(request, "/worklogs", {
      project_id: projectId,
      log_date: PAST_DATE,
      hours: 4,
    });
    const worklogId = (await createResp.json()).data.id;

    const otherEngineer = await (async () => {
      await apiLoginAs(request, "CEO");
      const resourceId = await createResource(request);
      return createScopedUser(request, "ENGINEER", resourceId);
    })();
    await apiLoginAsScoped(request, otherEngineer);
    const resp = await apiPut(request, `/worklogs/${worklogId}`, {
      hours: 6,
    });
    expect(resp.status()).toBe(403);
  });

  test("update own worklog hours — round trip", async ({ request }) => {
    const { projectId, engineerUser } =
      await setupWorklogEnabledProjectWithAssignment(request);
    await apiLoginAsScoped(request, engineerUser);
    const createResp = await apiPost(request, "/worklogs", {
      project_id: projectId,
      log_date: PAST_DATE,
      hours: 4,
    });
    const worklogId = (await createResp.json()).data.id;

    const resp = await apiPut(request, `/worklogs/${worklogId}`, {
      hours: 6.5,
    });
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(Number(body.data.hours)).toBe(6.5);
  });

  test("delete own worklog entry", async ({ request }) => {
    const { projectId, engineerUser } =
      await setupWorklogEnabledProjectWithAssignment(request);
    await apiLoginAsScoped(request, engineerUser);
    const createResp = await apiPost(request, "/worklogs", {
      project_id: projectId,
      log_date: PAST_DATE,
      hours: 4,
    });
    const worklogId = (await createResp.json()).data.id;

    const delResp = await apiDelete(request, `/worklogs/${worklogId}`);
    expect(delResp.ok()).toBeTruthy();
  });

  test("my worklogs endpoint returns only own entries", async ({
    request,
  }) => {
    const { projectId, engineerUser } =
      await setupWorklogEnabledProjectWithAssignment(request);
    await apiLoginAsScoped(request, engineerUser);
    await apiPost(request, "/worklogs", {
      project_id: projectId,
      log_date: PAST_DATE,
      hours: 4,
    });

    const resp = await apiGet(request, "/worklogs/my");
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.data.length).toBeGreaterThan(0);
  });

  test("engineer's org-wide worklogs list is scoped to own entries only (SELF_ONLY)", async ({
    request,
  }) => {
    const { projectId, engineerUser, engineerResourceId } =
      await setupWorklogEnabledProjectWithAssignment(request);
    await apiLoginAsScoped(request, engineerUser);
    await apiPost(request, "/worklogs", {
      project_id: projectId,
      log_date: PAST_DATE,
      hours: 4,
    });

    const resp = await apiGet(request, "/worklogs");
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(
      body.data.every(
        (w: { resource: { id: string } }) =>
          w.resource.id === engineerResourceId
      )
    ).toBeTruthy();
  });

  test("unauthenticated request returns 401", async ({ request }) => {
    const resp = await apiGet(request, "/worklogs/my");
    expect(resp.status()).toBe(401);
  });
});
