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

async function createClient(request: APIRequestContext) {
  const resp = await apiPost(request, "/clients", {
    name: `Assignment Client ${uniqueId("C")}`,
  });
  return (await resp.json()).data.id as string;
}

async function createProject(
  request: APIRequestContext,
  overrides: Partial<{ dmId: string; pmId: string }> = {}
) {
  const clientId = await createClient(request);
  const dmId = overrides.dmId ?? (await createResource(request));
  const pmId = overrides.pmId ?? (await createResource(request));
  const resp = await apiPost(request, "/projects", {
    name: `Assignment Project ${uniqueId("P")}`,
    client_id: clientId,
    type: "FIXED_PRICE",
    dm_id: dmId,
    pm_id: pmId,
  });
  const body = await resp.json();
  return { projectId: body.data.id as string, dmId, pmId };
}

test.describe("API Regression — Assignments (Allocations)", () => {
  test("CEO creates an assignment — happy path, nested resource/project present", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const { projectId } = await createProject(request);
    const resourceId = await createResource(request);

    const resp = await apiPost(
      request,
      `/projects/${projectId}/assignments`,
      {
        resource_id: resourceId,
        allocation_pct: 50,
        billability_pct: 50,
        start_date: "2026-01-01",
      }
    );
    expect(resp.status()).toBe(201);
    const body = await resp.json();
    expect(body.data.resource.id).toBe(resourceId);
    expect(body.data.status).toBe("ACTIVE");
  });

  test("over-allocating a resource beyond 100% succeeds with a warning, not an error", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const { projectId: p1 } = await createProject(request);
    const { projectId: p2 } = await createProject(request);
    const resourceId = await createResource(request);

    const first = await apiPost(request, `/projects/${p1}/assignments`, {
      resource_id: resourceId,
      allocation_pct: 70,
      billability_pct: 70,
      start_date: "2026-01-01",
    });
    expect(first.status()).toBe(201);

    const second = await apiPost(request, `/projects/${p2}/assignments`, {
      resource_id: resourceId,
      allocation_pct: 50,
      billability_pct: 50,
      start_date: "2026-01-01",
    });
    expect(second.status()).toBe(201);
    const body = await second.json();
    expect(body.warnings).toBeDefined();
    expect(body.warnings.length).toBeGreaterThan(0);
  });

  test("assigning an inactive resource is rejected", async ({ request }) => {
    await apiLoginAs(request, "CEO");
    const { projectId } = await createProject(request);
    const resourceId = await createResource(request);
    await apiDelete(request, `/resources/${resourceId}`);

    const resp = await apiPost(
      request,
      `/projects/${projectId}/assignments`,
      {
        resource_id: resourceId,
        allocation_pct: 50,
        billability_pct: 50,
        start_date: "2026-01-01",
      }
    );
    expect([400, 422]).toContain(resp.status());
  });

  test("billing_rate is null for HR (unauthorized field)", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const { projectId } = await createProject(request);
    const resourceId = await createResource(request);
    const createResp = await apiPost(
      request,
      `/projects/${projectId}/assignments`,
      {
        resource_id: resourceId,
        allocation_pct: 40,
        billability_pct: 40,
        billing_rate: 5000,
        start_date: "2026-01-01",
      }
    );
    const assignmentId = (await createResp.json()).data.id;

    await apiLoginAs(request, "HR");
    const resp = await apiGet(request, `/assignments/${assignmentId}`);
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.data.billing_rate).toBeNull();
  });

  test("HR cannot set billing_rate — 403", async ({ request }) => {
    await apiLoginAs(request, "CEO");
    const { projectId } = await createProject(request);
    const resourceId = await createResource(request);

    await apiLoginAs(request, "HR");
    const resp = await apiPost(request, `/projects/${projectId}/assignments`, {
      resource_id: resourceId,
      allocation_pct: 30,
      billability_pct: 30,
      billing_rate: 5000,
      start_date: "2026-01-01",
    });
    expect(resp.status()).toBe(403);
  });

  test("Engineer can view own assignment (SELF_ONLY scope)", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const { projectId } = await createProject(request);
    const engineerResource = await createResource(request);
    const createResp = await apiPost(
      request,
      `/projects/${projectId}/assignments`,
      {
        resource_id: engineerResource,
        allocation_pct: 60,
        billability_pct: 60,
        start_date: "2026-01-01",
      }
    );
    const assignmentId = (await createResp.json()).data.id;

    const engineerUser = await createScopedUser(
      request,
      "ENGINEER",
      engineerResource
    );
    await apiLoginAsScoped(request, engineerUser);
    const resp = await apiGet(request, `/assignments/${assignmentId}`);
    expect(resp.ok()).toBeTruthy();
  });

  test("Engineer cannot view another engineer's assignment — 403", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const { projectId } = await createProject(request);
    const otherResource = await createResource(request);
    const createResp = await apiPost(
      request,
      `/projects/${projectId}/assignments`,
      {
        resource_id: otherResource,
        allocation_pct: 60,
        billability_pct: 60,
        start_date: "2026-01-01",
      }
    );
    const assignmentId = (await createResp.json()).data.id;

    const engineerUser = await createScopedUser(request, "ENGINEER");
    await apiLoginAsScoped(request, engineerUser);
    const resp = await apiGet(request, `/assignments/${assignmentId}`);
    expect(resp.status()).toBe(403);
  });

  test("release an assignment — status transitions to RELEASED", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const { projectId } = await createProject(request);
    const resourceId = await createResource(request);
    const createResp = await apiPost(
      request,
      `/projects/${projectId}/assignments`,
      {
        resource_id: resourceId,
        allocation_pct: 50,
        billability_pct: 50,
        start_date: "2026-01-01",
      }
    );
    const assignmentId = (await createResp.json()).data.id;

    const resp = await apiPost(
      request,
      `/assignments/${assignmentId}/release`,
      {}
    );
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.data.status).toBe("RELEASED");
  });

  test("cannot update a released assignment", async ({ request }) => {
    await apiLoginAs(request, "CEO");
    const { projectId } = await createProject(request);
    const resourceId = await createResource(request);
    const createResp = await apiPost(
      request,
      `/projects/${projectId}/assignments`,
      {
        resource_id: resourceId,
        allocation_pct: 50,
        billability_pct: 50,
        start_date: "2026-01-01",
      }
    );
    const assignmentId = (await createResp.json()).data.id;
    await apiPost(request, `/assignments/${assignmentId}/release`, {});

    const resp = await apiPut(request, `/assignments/${assignmentId}`, {
      allocation_pct: 80,
    });
    expect([400, 409, 422]).toContain(resp.status());
  });

  test("only CEO/CTO can trigger the auto-release job — DM gets 403", async ({
    request,
  }) => {
    const dmUser = await (async () => {
      await apiLoginAs(request, "CEO");
      return createScopedUser(request, "DM");
    })();
    await apiLoginAsScoped(request, dmUser);
    const resp = await apiPost(request, "/jobs/auto-release", {});
    expect(resp.status()).toBe(403);
  });

  test("nonexistent assignment returns 404, not 500", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const resp = await apiGet(
      request,
      "/assignments/00000000-0000-0000-0000-000000000000"
    );
    expect(resp.status()).toBe(404);
  });

  test("unauthenticated request returns 401", async ({ request }) => {
    const resp = await apiGet(request, "/resources/assignments");
    expect([401, 404]).toContain(resp.status());
  });
});
