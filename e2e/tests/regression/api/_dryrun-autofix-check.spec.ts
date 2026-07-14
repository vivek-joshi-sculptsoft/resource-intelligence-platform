import { test, expect } from "@playwright/test";
import { apiLoginAs } from "../../../utils/api-auth";

// Intentional, deliberately-wrong assertion — used once to dry-run the
// regression-autofix pipeline end-to-end (Jira ticket -> branch -> Claude
// Code fix -> PR). Safe to delete once the dry run is verified.
test.describe("Dry-Run Autofix Pipeline Check", () => {
  test("CEO login returns the wrong role code (deliberately broken)", async ({
    request,
  }) => {
    const response = await apiLoginAs(request, "CEO");
    const body = await response.json();
    expect(body.user.role.code).toBe("NOT_A_REAL_ROLE");
  });
});
