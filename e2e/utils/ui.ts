import { type Page } from "@playwright/test";

/**
 * Interacts with the custom SearchableSelect component (shared/components/SearchableSelect.tsx),
 * which renders a <button> trigger (accessible name = placeholder or selected label) and an
 * autocomplete dropdown — not a native <select>, so getByLabel doesn't apply here.
 */
export async function selectSearchable(
  page: Page,
  triggerName: string | RegExp,
  optionText: string
) {
  await page.getByRole("button", { name: triggerName }).click();
  await page.getByPlaceholder("Type to search...").fill(optionText);
  await page
    .locator("div")
    .filter({ hasText: new RegExp(`^${optionText}$`) })
    .last()
    .click();
}
