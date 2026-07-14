import { type APIRequestContext } from "@playwright/test";
import { apiGet, apiPost } from "./api";
import { apiLoginAs } from "./api-auth";

/**
 * The 7 seeded e2e role users (see global.setup.ts) have no linked resource_id,
 * so OWN_PORTFOLIO/SELF_ONLY scope checks can't be exercised through them directly.
 * These helpers spin up a disposable resource + user (as CEO) linked to a given
 * role and resource, for tests that need real portfolio/self scoping.
 */

let roleIdCache: Record<string, string> | undefined;

async function getRoleId(
  request: APIRequestContext,
  code: string
): Promise<string> {
  if (!roleIdCache) {
    const resp = await apiGet(request, "/roles");
    const body = await resp.json();
    roleIdCache = {};
    for (const role of body.data) roleIdCache[role.code] = role.id;
  }
  const id = roleIdCache[code];
  if (!id) throw new Error(`Unknown role code: ${code}`);
  return id;
}

export async function createResource(
  request: APIRequestContext,
  overrides: Partial<{
    name: string;
    employee_id: string;
    designation: string;
  }> = {}
): Promise<string> {
  const uniqueId = `SCOPED-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
  const resp = await apiPost(request, "/resources", {
    employee_id: overrides.employee_id ?? uniqueId,
    name: overrides.name ?? `Scoped Resource ${uniqueId}`,
    designation: overrides.designation ?? "Engineer",
  });
  if (!resp.ok()) {
    throw new Error(`Failed to create resource: ${await resp.text()}`);
  }
  const body = await resp.json();
  return body.data.id;
}

export interface ScopedUser {
  id: string;
  email: string;
  password: string;
  resourceId: string;
}

/**
 * As CEO: creates a resource (unless resourceId given) and a user of the given
 * role linked to it. Returns credentials — call apiLoginAsScoped to switch the
 * current request context to this user.
 */
export async function createScopedUser(
  request: APIRequestContext,
  roleCode: "DM" | "PM" | "ENGINEER" | "FINANCE" | "HR",
  resourceId?: string
): Promise<ScopedUser> {
  await apiLoginAs(request, "CEO");

  const finalResourceId = resourceId ?? (await createResource(request));
  const roleId = await getRoleId(request, roleCode);
  const uniqueId = `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
  const email = `scoped-${roleCode.toLowerCase()}-${uniqueId}@riplatform.com`;
  const password = "admin123456";

  const resp = await apiPost(request, "/users", {
    email,
    name: `Scoped ${roleCode} ${uniqueId}`,
    password,
    role_id: roleId,
    resource_id: finalResourceId,
  });
  if (!resp.ok()) {
    throw new Error(`Failed to create scoped user: ${await resp.text()}`);
  }
  const body = await resp.json();
  return { id: body.data.id, email, password, resourceId: finalResourceId };
}

export async function apiLoginAsScoped(
  request: APIRequestContext,
  user: ScopedUser
) {
  const resp = await apiPost(request, "/auth/login", {
    email: user.email,
    password: user.password,
  });
  if (!resp.ok()) {
    throw new Error(`Login failed for scoped user ${user.email}`);
  }
  return resp;
}
