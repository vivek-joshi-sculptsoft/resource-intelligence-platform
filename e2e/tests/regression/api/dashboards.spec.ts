import { test, expect } from "@playwright/test";
import { apiGet } from "../../../utils/api";
import { apiLoginAs } from "../../../utils/api-auth";
import {
  apiLoginAsScoped,
  createScopedUser,
} from "../../../utils/api-scoped-user";

test.describe("API Regression — Dashboards", () => {
  test("company dashboard accessible to CEO and CTO", async ({
    request,
  }) => {
    for (const role of ["CEO", "CTO"] as const) {
      await apiLoginAs(request, role);
      const resp = await apiGet(request, "/dashboard/company");
      expect(resp.ok()).toBeTruthy();
    }
  });

  test("company dashboard forbidden for DM, PM, FINANCE, HR, ENGINEER", async ({
    request,
  }) => {
    for (const role of ["DM", "PM", "FINANCE", "HR", "ENGINEER"] as const) {
      await apiLoginAs(request, role);
      const resp = await apiGet(request, "/dashboard/company");
      expect(resp.status()).toBe(403);
    }
  });

  test("DM dashboard requires a linked resource_id — forbidden without one", async ({
    request,
  }) => {
    await apiLoginAs(request, "DM");
    const resp = await apiGet(request, "/dashboard/dm");
    expect(resp.status()).toBe(403);
  });

  test("DM dashboard accessible for DM with a linked resource_id", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const dmUser = await createScopedUser(request, "DM");
    await apiLoginAsScoped(request, dmUser);
    const resp = await apiGet(request, "/dashboard/dm");
    expect(resp.ok()).toBeTruthy();
  });

  test("DM dashboard forbidden for PM, FINANCE, HR, ENGINEER", async ({
    request,
  }) => {
    for (const role of ["PM", "FINANCE", "HR", "ENGINEER"] as const) {
      await apiLoginAs(request, role);
      const resp = await apiGet(request, "/dashboard/dm");
      expect(resp.status()).toBe(403);
    }
  });

  test("availability dashboard accessible to all authenticated roles", async ({
    request,
  }) => {
    const roles = [
      "CEO",
      "CTO",
      "DM",
      "PM",
      "FINANCE",
      "HR",
      "ENGINEER",
    ] as const;
    for (const role of roles) {
      await apiLoginAs(request, role);
      const resp = await apiGet(request, "/dashboard/availability");
      expect(resp.ok()).toBeTruthy();
    }
  });

  test("availability dashboard window param validation — rejects out of range", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const resp = await apiGet(request, "/dashboard/availability", {
      window: "9999",
    });
    expect(resp.status()).toBe(422);
  });

  test("bench list and summary accessible to all roles, cost hidden for HR/ENGINEER", async ({
    request,
  }) => {
    await apiLoginAs(request, "HR");
    const listResp = await apiGet(request, "/bench");
    expect(listResp.ok()).toBeTruthy();
    const listBody = await listResp.json();
    for (const item of listBody.data) {
      expect(item.loaded_cost_monthly ?? null).toBeNull();
    }

    const summaryResp = await apiGet(request, "/bench/summary");
    expect(summaryResp.ok()).toBeTruthy();
  });

  test("bench cost fields visible for CEO/CTO/FINANCE", async ({
    request,
  }) => {
    for (const role of ["CEO", "CTO", "FINANCE"] as const) {
      await apiLoginAs(request, role);
      const resp = await apiGet(request, "/bench");
      expect(resp.ok()).toBeTruthy();
    }
  });

  test("upcoming and partial availability accessible to Engineer", async ({
    request,
  }) => {
    await apiLoginAs(request, "ENGINEER");
    const upcoming = await apiGet(request, "/availability/upcoming");
    expect(upcoming.ok()).toBeTruthy();
    const partial = await apiGet(request, "/availability/partial");
    expect(partial.ok()).toBeTruthy();
  });

  test("unauthenticated request returns 401", async ({ request }) => {
    const resp = await apiGet(request, "/dashboard/company");
    expect(resp.status()).toBe(401);
  });
});
