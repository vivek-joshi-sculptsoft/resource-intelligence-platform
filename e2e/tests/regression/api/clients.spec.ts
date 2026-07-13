import { test, expect } from "@playwright/test";
import { apiDelete, apiGet, apiPost, apiPut } from "../../../utils/api";
import { apiLoginAs } from "../../../utils/api-auth";

function uniqueId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

async function createClient(request: import("@playwright/test").APIRequestContext, name?: string) {
  const resp = await apiPost(request, "/clients", {
    name: name ?? `Regression Client ${uniqueId("CLI")}`,
    industry: "IT Services",
  });
  const body = await resp.json();
  return body.data.id as string;
}

test.describe("API Regression — Clients", () => {
  test("CEO creates a client — happy path", async ({ request }) => {
    await apiLoginAs(request, "CEO");
    const name = `Client ${uniqueId("C")}`;
    const resp = await apiPost(request, "/clients", {
      name,
      industry: "FinTech",
      contact_name: "Jane Doe",
      contact_email: "jane@example.com",
    });
    expect(resp.status()).toBe(201);
    const body = await resp.json();
    expect(body.data.name).toBe(name);
    expect(body.data.is_active).toBe(true);
    expect(body.data.projects).toEqual([]);
  });

  test("HR (VIEW only) cannot create a client — 403", async ({
    request,
  }) => {
    await apiLoginAs(request, "HR");
    const resp = await apiPost(request, "/clients", {
      name: "Should Fail",
    });
    expect(resp.status()).toBe(403);
  });

  test("HR can list clients (VIEW access)", async ({ request }) => {
    await apiLoginAs(request, "HR");
    const resp = await apiGet(request, "/clients");
    expect(resp.ok()).toBeTruthy();
  });

  test("Engineer has no access to clients — 403", async ({ request }) => {
    await apiLoginAs(request, "ENGINEER");
    const resp = await apiGet(request, "/clients");
    expect(resp.status()).toBe(403);
  });

  test("update client fields — round trip", async ({ request }) => {
    await apiLoginAs(request, "CEO");
    const clientId = await createClient(request);
    const resp = await apiPut(request, `/clients/${clientId}`, {
      industry: "Healthcare",
      notes: "Updated via regression test",
    });
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.data.industry).toBe("Healthcare");
    expect(body.data.notes).toBe("Updated via regression test");
  });

  test("client dashboard endpoint returns dashboard data", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const clientId = await createClient(request);
    const resp = await apiGet(request, `/clients/${clientId}/dashboard`);
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.data).toBeDefined();
  });

  test("deactivate client — soft delete, not hard delete", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const clientId = await createClient(request);
    const delResp = await apiDelete(request, `/clients/${clientId}`);
    expect(delResp.ok()).toBeTruthy();

    const getResp = await apiGet(request, `/clients/${clientId}`);
    expect(getResp.ok()).toBeTruthy();
    const body = await getResp.json();
    expect(body.data.is_active).toBe(false);
  });

  test("missing required name returns 422", async ({ request }) => {
    await apiLoginAs(request, "CEO");
    const resp = await apiPost(request, "/clients", { industry: "IT" });
    expect(resp.status()).toBe(422);
  });

  test("GET nonexistent client returns 404, not 500", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const resp = await apiGet(
      request,
      "/clients/00000000-0000-0000-0000-000000000000"
    );
    expect(resp.status()).toBe(404);
  });

  test("list supports status filter and search", async ({ request }) => {
    await apiLoginAs(request, "CEO");
    const name = `Searchable ${uniqueId("S")}`;
    await createClient(request, name);

    const resp = await apiGet(request, "/clients", {
      status: "ACTIVE",
      search: name,
    });
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(
      body.data.every((c: { name: string }) => c.name.includes(name))
    ).toBeTruthy();
  });

  test("unauthenticated request returns 401", async ({ request }) => {
    const resp = await apiGet(request, "/clients");
    expect(resp.status()).toBe(401);
  });
});
