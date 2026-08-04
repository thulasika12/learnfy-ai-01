import { expect, test } from "@playwright/test";

const user = { id: 1, name: "Test Student", email: "student@example.com", role: "student", is_active: true };

test.beforeEach(async ({ page }, testInfo) => {
  await page.addInitScript(({ dark, userData }) => {
    localStorage.setItem("learnfy_token", "test-token");
    localStorage.setItem("learnfy_user", JSON.stringify(userData));
    localStorage.setItem("learnfy_theme", dark ? "dark" : "light");
  }, { dark: testInfo.project.name.includes("dark"), userData: user });

  await page.route("**/users/profile", (route) => route.fulfill({ json: user }));
  await page.route("**/flashcards/dashboard/stats", (route) => route.fulfill({ json: { total_sets: 0, total_cards_studied: 0, average_score: 0, revision_streak: 0 } }));
  await page.route("**/flashcards/reminders", (route) => route.fulfill({ json: null }));
  await page.route(/\/flashcards\/sets\?.*/, (route) => route.fulfill({ json: [] }));
  await page.route("**/notes/**", (route) => route.fulfill({ json: [] }));
  await page.route("**/flashcards/generate", (route) => route.fulfill({ json: {
    title: "Python Basics", subject: "ICT", language: "en", difficulty: "easy",
    source_type: "topic", source_name: null,
    cards: [
      { question: "What is a variable?", answer: "A named storage location.", image_suggestion: null },
      { question: "What is a list?", answer: "An ordered collection.", image_suggestion: null },
    ],
  } }));
});

test("flashcard workspace is responsive, themed, and interactive", async ({ page }, testInfo) => {
  const pageErrors = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await page.goto("/ai/flashcards");
  await expect(page.getByRole("heading", { name: "AI Flashcards" })).toBeVisible();
  await expect(page.locator("html")).toHaveClass(testInfo.project.name.includes("dark") ? /dark/ : /^(?!.*dark)/);

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(1);

  await page.getByRole("button", { name: "Create New Flashcards" }).click();
  await page.getByLabel("Topic").fill("Python");
  await page.getByRole("combobox", { name: "Subject", exact: true }).selectOption("ICT");
  await page.getByRole("combobox", { name: "Difficulty", exact: true }).selectOption("easy");
  await page.getByRole("combobox", { name: "Language", exact: true }).selectOption("en");
  await page.getByRole("button", { name: "Generate Flashcards" }).click();
  await expect(page.getByText("What is a variable?")).toBeVisible();
  await page.getByTitle("Flip card").click();
  await expect(page.getByText("A named storage location.")).toBeVisible();
  await page.waitForTimeout(600);
  await page.getByTitle("Read card aloud").click();

  const finalOverflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(finalOverflow).toBeLessThanOrEqual(1);
  expect(pageErrors).toEqual([]);
  await page.screenshot({ path: `test-results/${testInfo.project.name}-flashcards.png`, fullPage: true });
});
