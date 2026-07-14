import { test, expect, type APIRequestContext } from "@playwright/test";
import { apiGet, apiPost, apiPut } from "../../../utils/api";
import { apiLoginAs } from "../../../utils/api-auth";
import {
  apiLoginAsScoped,
  createResource,
  createScopedUser,
} from "../../../utils/api-scoped-user";

function uniqueId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

async function createClient(request: APIRequestContext) {
  const resp = await apiPost(request, "/clients", {
    name: `Project Test Client ${uniqueId("C")}`,
  });
  return (await resp.json()).data.id as string;
}

async function createProject(
  request: APIRequestContext,
  overrides: Partial<{
    clientId: string;
    dmId: string;
    pmId: string;
    type: string;
    contractEndDate: string;
  }> = {}
) {
  const clientId = overrides.clientId ?? (await createClient(request));
  const dmId = overrides.dmId ?? (await createResource(request));
  const pmId = overrides.pmId ?? (await createResource(request));

  const resp = await apiPost(request, "/projects", {
    name: `Regression Project ${uniqueId("P")}`,
    client_id: clientId,
    type: overrides.type ?? "FIXED_PRICE",
    dm_id: dmId,
    pm_id: pmId,
    contract_end_date: overrides.contractEndDate,
  });
  return { resp, body: await resp.json(), clientId, dmId, pmId };
}

test.describe("API Regression — Projects", () => {
  test("CEO creates a project — happy path, nested client/dm/pm present", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const { resp, body } = await createProject(request);
    expect(resp.status()).toBe(201);
    expect(body.data.client.id).toBeDefined();
    expect(body.data.dm.id).toBeDefined();
    expect(body.data.pm.id).toBeDefined();
    expect(body.data.status).toBe("ACTIVE");
  });

  test("TIME_AND_MATERIAL project requires contract_end_date — 400 without it", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const clientId = await createClient(request);
    const dmId = await createResource(request);
    const pmId = await createResource(request);
    const resp = await apiPost(request, "/projects", {
      name: `TM Project ${uniqueId("P")}`,
      client_id: clientId,
      type: "TIME_AND_MATERIAL",
      dm_id: dmId,
      pm_id: pmId,
    });
    expect([400, 422]).toContain(resp.status());
  });

  test("invalid client_id (nonexistent) returns 404, not 500", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const dmId = await createResource(request);
    const pmId = await createResource(request);
    const resp = await apiPost(request, "/projects", {
      name: `Bad Client ${uniqueId("P")}`,
      client_id: "00000000-0000-0000-0000-000000000000",
      type: "FIXED_PRICE",
      dm_id: dmId,
      pm_id: pmId,
    });
    expect(resp.status()).toBe(404);
  });

  test("PM role cannot create a project — 403", async ({ request }) => {
    await apiLoginAs(request, "CEO");
    const dmId = await createResource(request);
    const pmUser = await createScopedUser(request, "PM", dmId);
    const clientId = await createClient(request);

    await apiLoginAsScoped(request, pmUser);
    const resp = await apiPost(request, "/projects", {
      name: `PM Attempt ${uniqueId("P")}`,
      client_id: clientId,
      type: "FIXED_PRICE",
      dm_id: dmId,
      pm_id: pmUser.resourceId,
    });
    expect(resp.status()).toBe(403);
  });

  test("DM creating a project auto-sets dm_id to self", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const dmUser = await createScopedUser(request, "DM");
    const clientId = await createClient(request);
    const otherPm = await createResource(request);

    await apiLoginAsScoped(request, dmUser);
    const resp = await apiPost(request, "/projects", {
      name: `DM Self Project ${uniqueId("P")}`,
      client_id: clientId,
      type: "FIXED_PRICE",
      dm_id: "00000000-0000-0000-0000-000000000000", // ignored, forced to self
      pm_id: otherPm,
    });
    expect(resp.status()).toBe(201);
    const body = await resp.json();
    expect(body.data.dm.id).toBe(dmUser.resourceId);
  });

  test("DM outside portfolio cannot view another DM's project — 403", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const { body } = await createProject(request);
    const projectId = body.data.id;

    const outsideDm = await createScopedUser(request, "DM");
    await apiLoginAsScoped(request, outsideDm);
    const resp = await apiGet(request, `/projects/${projectId}`);
    expect(resp.status()).toBe(403);
  });

  test("DM within portfolio (dm_id = self) can view project", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const dmUser = await createScopedUser(request, "DM");
    const { body } = await createProject(request, { dmId: dmUser.resourceId });
    const projectId = body.data.id;

    await apiLoginAsScoped(request, dmUser);
    const resp = await apiGet(request, `/projects/${projectId}`);
    expect(resp.ok()).toBeTruthy();
  });

  test("PM can only edit worklog_enabled and notes — other fields rejected", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const pmUser = await createScopedUser(request, "PM");
    const { body } = await createProject(request, { pmId: pmUser.resourceId });
    const projectId = body.data.id;

    await apiLoginAsScoped(request, pmUser);
    const allowedResp = await apiPut(request, `/projects/${projectId}`, {
      notes: "PM allowed update",
    });
    expect(allowedResp.ok()).toBeTruthy();

    const disallowedResp = await apiPut(request, `/projects/${projectId}`, {
      name: "PM should not rename",
    });
    expect(disallowedResp.status()).toBe(403);
  });

  test("PM cannot transition project status — 403", async ({ request }) => {
    await apiLoginAs(request, "CEO");
    const pmUser = await createScopedUser(request, "PM");
    const { body } = await createProject(request, { pmId: pmUser.resourceId });
    const projectId = body.data.id;

    await apiLoginAsScoped(request, pmUser);
    const resp = await apiPut(request, `/projects/${projectId}/status`, {
      status: "ON_HOLD",
    });
    expect(resp.status()).toBe(403);
  });

  test("valid status transition ACTIVE -> ON_HOLD -> ACTIVE succeeds", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const { body } = await createProject(request);
    const projectId = body.data.id;

    const toHold = await apiPut(request, `/projects/${projectId}/status`, {
      status: "ON_HOLD",
    });
    expect(toHold.ok()).toBeTruthy();
    expect((await toHold.json()).data.status).toBe("ON_HOLD");

    const backToActive = await apiPut(request, `/projects/${projectId}/status`, {
      status: "ACTIVE",
    });
    expect(backToActive.ok()).toBeTruthy();
    expect((await backToActive.json()).data.status).toBe("ACTIVE");
  });

  test("invalid status transition COMPLETED -> ACTIVE is rejected", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const { body } = await createProject(request);
    const projectId = body.data.id;

    await apiPut(request, `/projects/${projectId}/status`, {
      status: "COMPLETED",
    });
    const resp = await apiPut(request, `/projects/${projectId}/status`, {
      status: "ACTIVE",
    });
    expect([400, 409, 422]).toContain(resp.status());
  });

  test("update project client_id — nested client object updates", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const { body } = await createProject(request);
    const projectId = body.data.id;
    const newClientId = await createClient(request);

    const resp = await apiPut(request, `/projects/${projectId}`, {
      client_id: newClientId,
    });
    expect(resp.ok()).toBeTruthy();
    const updated = await resp.json();
    expect(updated.data.client.id).toBe(newClientId);
  });

  test("Engineer has no access to project_details — 403", async ({
    request,
  }) => {
    await apiLoginAs(request, "ENGINEER");
    const resp = await apiGet(request, "/projects");
    expect(resp.status()).toBe(403);
  });

  test("GET nonexistent project returns 404, not 500", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const resp = await apiGet(
      request,
      "/projects/00000000-0000-0000-0000-000000000000"
    );
    expect(resp.status()).toBe(404);
  });

  test("list supports filter by client_id, status, type", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const { clientId } = await createProject(request);
    const resp = await apiGet(request, "/projects", {
      client_id: clientId,
      status: "ACTIVE",
      type: "FIXED_PRICE",
    });
    expect(resp.ok()).toBeTruthy();
  });

  test("unauthenticated request returns 401", async ({ request }) => {
    const resp = await apiGet(request, "/projects");
    expect(resp.status()).toBe(401);
  });
});
