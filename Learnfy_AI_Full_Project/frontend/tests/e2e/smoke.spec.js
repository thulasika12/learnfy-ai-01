import { expect, test } from "@playwright/test";

test("public shell renders in bundled Chromium", async ({ page }) => {
  await page.goto("/about");
  await expect(page.getByRole("heading", { name: "About Learnfy AI" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Privacy Policy" })).toBeVisible();
});
