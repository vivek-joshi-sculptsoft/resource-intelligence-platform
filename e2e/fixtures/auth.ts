import { test as base, expect, type Page } from "@playwright/test";

type RoleCode = "CEO" | "CTO" | "DM" | "PM" | "FINANCE" | "HR" | "ENGINEER";

interface AuthFixtures {
  loginAs: (role: RoleCode) => Promise<void>;
  authenticatedPage: Page;
}

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

export const test = base.extend<AuthFixtures>({
  loginAs: async ({ page }, use) => {
    const login = async (role: RoleCode) => {
      const creds = ROLE_CREDENTIALS[role];
      if (!creds) throw new Error(`Unknown role: ${role}`);

      // The login page redirects away immediately if a session is already
      // authenticated, so switching roles mid-test needs the old cookies cleared
      // first — otherwise the email field never renders and fill() hangs.
      await page.context().clearCookies();
      await page.goto("/login");
      await page.getByRole("textbox", { name: /email/i }).fill(creds.email);
      await page.getByRole("textbox", { name: /password/i }).fill(creds.password);
      await page.getByRole("button", { name: /sign in|log in|login/i }).click();
      await page.waitForURL(/\/(dashboard|resources|clients|projects)/);
    };
    await use(login);
  },

  authenticatedPage: async ({ page }, use) => {
    const creds = ROLE_CREDENTIALS.CEO;
    await page.goto("/login");
    await page.getByRole("textbox", { name: /email/i }).fill(creds.email);
    await page.getByRole("textbox", { name: /password/i }).fill(creds.password);
    await page.getByRole("button", { name: /sign in|log in|login/i }).click();
    await page.waitForURL(/\/(dashboard|resources|clients|projects)/);
    await use(page);
  },
});

export { expect };
export type { RoleCode };
