import { test as setup, expect, type APIRequestContext } from "@playwright/test";

const API = "http://localhost:8000";

// Users the loginAs() fixture expects (see fixtures/auth.ts).
const E2E_USERS: { email: string; name: string; role: string }[] = [
  { email: "admin@riplatform.com", name: "E2E CEO", role: "CEO" },
  { email: "cto@riplatform.com", name: "E2E CTO", role: "CTO" },
  { email: "dm@riplatform.com", name: "E2E DM", role: "DM" },
  { email: "pm@riplatform.com", name: "E2E PM", role: "PM" },
  { email: "finance@riplatform.com", name: "E2E Finance", role: "FINANCE" },
  { email: "hr@riplatform.com", name: "E2E HR", role: "HR" },
  { email: "engineer@riplatform.com", name: "E2E Engineer", role: "ENGINEER" },
];
const E2E_PASSWORD = "admin123";

// Bootstrap admin seeded by the backend (app/modules/auth/seed.py).
const SEED_ADMIN = { email: "admin@ri-platform.com", password: "ChangeMe123!" };

setup("verify backend health", async ({ request }) => {
  const response = await request.get(`${API}/api/v1/health`);
  expect(response.ok()).toBeTruthy();
});

setup("verify frontend is serving", async ({ page }) => {
  await page.goto("http://localhost:5173");
  await expect(page).not.toHaveTitle("");
});

async function loginAsAdmin(request: APIRequestContext): Promise<boolean> {
  for (const creds of [
    SEED_ADMIN,
    { email: E2E_USERS[0].email, password: E2E_PASSWORD },
  ]) {
    const resp = await request.post(`${API}/api/v1/auth/login`, {
      data: creds,
    });
    if (resp.ok()) return true;
  }
  return false;
}

setup("seed e2e role users", async ({ request }) => {
  // Idempotent: create the 7 role users loginAs() needs if they don't exist.
  expect(
    await loginAsAdmin(request),
    "cannot log in with seed admin or e2e CEO — check backend seed",
  ).toBeTruthy();

  const rolesResp = await request.get(`${API}/api/v1/roles`);
  expect(rolesResp.ok()).toBeTruthy();
  const roleIdByCode: Record<string, string> = {};
  for (const role of (await rolesResp.json()).data) {
    roleIdByCode[role.code] = role.id;
  }

  const existing = new Set<string>();
  for (let page = 1; page <= 10; page++) {
    const usersResp = await request.get(
      `${API}/api/v1/users?page=${page}&limit=100`,
    );
    expect(usersResp.ok()).toBeTruthy();
    const body = await usersResp.json();
    for (const user of body.data) existing.add(user.email);
    if (body.data.length < 100) break;
  }

  for (const user of E2E_USERS) {
    if (existing.has(user.email)) continue;
    const resp = await request.post(`${API}/api/v1/users`, {
      data: {
        email: user.email,
        name: user.name,
        password: E2E_PASSWORD,
        role_id: roleIdByCode[user.role],
      },
    });
    expect(resp.status(), `creating ${user.email}: ${await resp.text()}`).toBe(
      201,
    );
  }
});
