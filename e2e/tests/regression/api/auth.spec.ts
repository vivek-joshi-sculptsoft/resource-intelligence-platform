import { test, expect } from "@playwright/test";
import { apiGet, apiPost } from "../../../utils/api";
import { apiLoginAs } from "../../../utils/api-auth";

test.describe("API Regression — Auth", () => {
  test("login succeeds for every role and returns correct role code", async ({
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
      const response = await apiLoginAs(request, role);
      expect(response.ok()).toBeTruthy();
      const body = await response.json();
      expect(body.user.role.code).toBe(role);
    }
  });

  test("login rejects invalid credentials", async ({ request }) => {
    const response = await apiPost(request, "/auth/login", {
      email: "nobody@riplatform.com",
      password: "wrongpass",
    });
    expect(response.status()).toBe(401);
  });

  test("login rejects missing fields", async ({ request }) => {
    const response = await apiPost(request, "/auth/login", {
      email: "admin@riplatform.com",
    });
    expect(response.status()).toBe(422);
  });

  test("/me returns 401 without auth cookie", async ({ request }) => {
    const response = await apiGet(request, "/auth/me");
    expect(response.status()).toBe(401);
  });

  test("/me returns current user after login", async ({ request }) => {
    await apiLoginAs(request, "CEO");
    const response = await apiGet(request, "/auth/me");
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body.email).toBe("admin@riplatform.com");
    expect(body.role.code).toBe("CEO");
  });

  test("logout clears session — subsequent /me is 401", async ({
    request,
  }) => {
    await apiLoginAs(request, "CEO");
    const logoutResponse = await apiPost(request, "/auth/logout", {});
    expect(logoutResponse.ok()).toBeTruthy();

    const meResponse = await apiGet(request, "/auth/me");
    expect(meResponse.status()).toBe(401);
  });

  test("refresh issues a new access token", async ({ request }) => {
    await apiLoginAs(request, "CEO");
    const response = await apiPost(request, "/auth/refresh", {});
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body.user.role.code).toBe("CEO");
  });

  test("refresh without cookies is rejected", async ({ request }) => {
    const response = await apiPost(request, "/auth/refresh", {});
    expect(response.status()).toBe(401);
  });
});
