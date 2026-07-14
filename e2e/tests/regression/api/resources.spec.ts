import { test, expect } from "@playwright/test";
import { apiDelete, apiGet, apiPost, apiPut } from "../../../utils/api";
import { apiLoginAs } from "../../../utils/api-auth";
import { createResource } from "../../../utils/api-scoped-user";

function uniqueId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

test.describe("API Regression — Resources", () => {
  test("CEO creates a resource — happy path, returns correct shape", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const empId = uniqueId("EMP");
    const resp = await apiPost(request, "/resources", {
      employee_id: empId,
      name: "Regression Resource",
      designation: "Senior Engineer",
      technical_expertise: "Backend",
      loaded_cost_monthly: 150000,
    });
    expect(resp.status()).toBe(201);
    const body = await resp.json();
    expect(body.data.employee_id).toBe(empId);
    expect(body.data.loaded_cost_monthly).toBe(150000);
    expect(body.data.reporting_manager).toBeNull();
    expect(body.data.tags).toEqual([]);
  });

  test("create with reporting_manager_id set — response includes nested manager object", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const managerId = await createResource(request, {
      name: "Manager Resource",
    });

    const resp = await apiPost(request, "/resources", {
      employee_id: uniqueId("EMP"),
      name: "Reports To Manager",
      designation: "Engineer",
      reporting_manager_id: managerId,
    });
    expect(resp.status()).toBe(201);
    const body = await resp.json();
    expect(body.data.reporting_manager).not.toBeNull();
    expect(body.data.reporting_manager.id).toBe(managerId);
    expect(body.data.reporting_manager.name).toBe("Manager Resource");
  });

  test("update to set reporting_manager_id — nested object appears", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const resourceId = await createResource(request);
    const managerId = await createResource(request, { name: "New Manager" });

    const resp = await apiPut(request, `/resources/${resourceId}`, {
      reporting_manager_id: managerId,
    });
    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(body.data.reporting_manager.id).toBe(managerId);
  });

  test("update to null reporting_manager_id — no crash, returns null", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const managerId = await createResource(request);
    const resourceId = await createResource(request);
    await apiPut(request, `/resources/${resourceId}`, {
      reporting_manager_id: managerId,
    });

    const resp = await apiPut(request, `/resources/${resourceId}`, {
      reporting_manager_id: null,
    });
    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(body.data.reporting_manager).toBeNull();
  });

  test("GET detail with manager set includes nested object", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const managerId = await createResource(request);
    const resourceId = await createResource(request);
    await apiPut(request, `/resources/${resourceId}`, {
      reporting_manager_id: managerId,
    });

    const resp = await apiGet(request, `/resources/${resourceId}`);
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.data.reporting_manager.id).toBe(managerId);
  });

  test("GET list mixes resources with and without manager — both serialize", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    await createResource(request);
    const managerId = await createResource(request);
    const withManagerId = await createResource(request);
    await apiPut(request, `/resources/${withManagerId}`, {
      reporting_manager_id: managerId,
    });

    const resp = await apiGet(request, "/resources", { limit: "100" });
    expect(resp.ok()).toBeTruthy();
  });

  test("invalid reporting_manager_id (nonexistent) returns 404, not 500", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const resp = await apiPost(request, "/resources", {
      employee_id: uniqueId("EMP"),
      name: "Bad Manager Ref",
      designation: "Engineer",
      reporting_manager_id: "00000000-0000-0000-0000-000000000000",
    });
    expect([400, 404]).toContain(resp.status());
  });

  test("loaded_cost_monthly is null for HR (unauthorized field)", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const resourceId = await createResource(request);
    await apiPut(request, `/resources/${resourceId}`, {
      loaded_cost_monthly: 200000,
    });

    await apiLoginAs(request, "HR");
    const resp = await apiGet(request, `/resources/${resourceId}`);
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.data.loaded_cost_monthly).toBeNull();
    // Field present but null — not omitted.
    expect("loaded_cost_monthly" in body.data).toBeTruthy();
  });

  test("loaded_cost_monthly is visible for CEO/CTO/FINANCE", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const resourceId = await createResource(request);
    await apiPut(request, `/resources/${resourceId}`, {
      loaded_cost_monthly: 175000,
    });

    for (const role of ["CEO", "CTO", "FINANCE"] as const) {
      await apiLoginAs(request, role);
      const resp = await apiGet(request, `/resources/${resourceId}`);
      const body = await resp.json();
      expect(body.data.loaded_cost_monthly).toBe(175000);
    }
  });

  test("HR cannot set loaded_cost_monthly on create — 403", async ({
    request,
  }) => {
    await apiLoginAs(request, "HR");
    const resp = await apiPost(request, "/resources", {
      employee_id: uniqueId("EMP"),
      name: "HR Attempt",
      designation: "Engineer",
      loaded_cost_monthly: 100000,
    });
    expect(resp.status()).toBe(403);
  });

  test("Engineer has no edit access — create returns 403", async ({
    request,
  }) => {
    await apiLoginAs(request, "ENGINEER");
    const resp = await apiPost(request, "/resources", {
      employee_id: uniqueId("EMP"),
      name: "Should Fail",
      designation: "Engineer",
    });
    expect(resp.status()).toBe(403);
  });

  test("missing required fields returns 422", async ({ request }) => {
    await apiLoginAs(request, "CEO");
    const resp = await apiPost(request, "/resources", {
      name: "No Employee ID",
    });
    expect(resp.status()).toBe(422);
  });

  test("duplicate employee_id is rejected", async ({ request }) => {
    await apiLoginAs(request, "CEO");
    const empId = uniqueId("DUP");
    await apiPost(request, "/resources", {
      employee_id: empId,
      name: "First",
      designation: "Engineer",
    });
    const resp = await apiPost(request, "/resources", {
      employee_id: empId,
      name: "Second",
      designation: "Engineer",
    });
    expect([400, 409, 422]).toContain(resp.status());
  });

  test("resource cannot be its own reporting manager", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const resourceId = await createResource(request);
    const resp = await apiPut(request, `/resources/${resourceId}`, {
      reporting_manager_id: resourceId,
    });
    expect([400, 422]).toContain(resp.status());
  });

  test("add and remove tag round-trip", async ({ request }) => {
    await apiLoginAs(request, "CEO");
    const resourceId = await createResource(request);

    const addResp = await apiPost(request, `/resources/${resourceId}/tags`, {
      tag: "react",
    });
    expect(addResp.ok()).toBeTruthy();
    const addBody = await addResp.json();
    expect(addBody.data.tags).toContain("react");

    const removeResp = await apiDelete(
      request,
      `/resources/${resourceId}/tags/react`
    );
    expect(removeResp.ok()).toBeTruthy();
    const removeBody = await removeResp.json();
    expect(removeBody.data.tags).not.toContain("react");
  });

  test("deactivate (soft delete) — resource marked inactive, not hard-deleted", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const resourceId = await createResource(request);

    const delResp = await apiDelete(request, `/resources/${resourceId}`);
    expect(delResp.ok()).toBeTruthy();

    const getResp = await apiGet(request, `/resources/${resourceId}`);
    expect(getResp.ok()).toBeTruthy();
    const body = await getResp.json();
    expect(body.data.is_active).toBe(false);
  });

  test("pagination boundaries — page beyond total returns empty data, not error", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const resp = await apiGet(request, "/resources", {
      page: "9999",
      limit: "20",
    });
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.data).toEqual([]);
  });

  test("list filters by search term", async ({ request }) => {
    await apiLoginAs(request, "CEO");
    const uniqueName = `Findable ${uniqueId("SRCH")}`;
    await createResource(request, { name: uniqueName });

    const resp = await apiGet(request, "/resources", {
      search: uniqueName,
      limit: "20",
    });
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.data.length).toBeGreaterThan(0);
    expect(
      body.data.every((r: { name: string }) => r.name.includes(uniqueName))
    ).toBeTruthy();
  });

  test("GET nonexistent resource returns 404, not 500", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const resp = await apiGet(
      request,
      "/resources/00000000-0000-0000-0000-000000000000"
    );
    expect(resp.status()).toBe(404);
  });

  test("unauthenticated request returns 401", async ({ request }) => {
    const resp = await apiGet(request, "/resources");
    expect(resp.status()).toBe(401);
  });
});
