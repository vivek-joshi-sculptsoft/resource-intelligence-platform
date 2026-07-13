import { type APIRequestContext } from "@playwright/test";
import { apiLogin } from "./api";
import type { RoleCode } from "../fixtures";

const ROLE_CREDENTIALS: Record<RoleCode, { email: string; password: string }> =
  {
    CEO: { email: "admin@riplatform.com", password: "admin123" },
    CTO: { email: "cto@riplatform.com", password: "admin123" },
    DM: { email: "dm@riplatform.com", password: "admin123" },
    PM: { email: "pm@riplatform.com", password: "admin123" },
    FINANCE: { email: "finance@riplatform.com", password: "admin123" },
    HR: { email: "hr@riplatform.com", password: "admin123" },
    ENGINEER: { email: "engineer@riplatform.com", password: "admin123" },
  };

/**
 * Logs in as the given role on the provided request context. Auth cookies
 * (httpOnly) are stored on the context and carried automatically by every
 * subsequent call made with the same `request` fixture.
 */
export async function apiLoginAs(request: APIRequestContext, role: RoleCode) {
  const creds = ROLE_CREDENTIALS[role];
  const response = await apiLogin(request, creds.email, creds.password);
  if (!response.ok()) {
    throw new Error(
      `Login failed for role ${role}: ${response.status()} ${await response.text()}`
    );
  }
  return response;
}
