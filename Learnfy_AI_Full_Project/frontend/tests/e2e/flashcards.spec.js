import { expect, test } from "@playwright/test";

const user = { id: 1, name: "Test Student", email: "student@example.com", role: "student", is_active: true };

test.beforeEach(async ({ page }, testInfo) => {
  await page.addInitScript(({ dark, userData }) => {
    localStorage.setItem("learnfy_token", "test-token");
    localStorage.setItem("learnfy_user", JSON.stringify(userData));
    localStorage.setItem("learnfy_theme", dark ? "dark" : "light");
    // Avoid OS speech services in deterministic browser tests.
    Object.defineProperty(window, "speechSynthesis", { configurable: true, value: {
      speak: () => {}, cancel: () => {}, pause: () => {}, resume: () => {}, getVoices: () => [],
    } });
    window.SpeechSynthesisUtterance = class { constructor(text) { this.text = text; } };
  }, { dark: testInfo.project.name.includes("dark"), userData: user });

  // Block every unmatched backend call so tests never contact real services.
  // Playwright evaluates routes in reverse registration order, so the specific
  // mocks below take precedence over this safe fallback.
  await page.route("http://localhost:8000/**", (route) => route.fulfill({
    status: 404, contentType: "application/json", body: JSON.stringify({ detail: "Not mocked in E2E" }),
  }));
  await page.route("**/users/profile*", (route) => route.fulfill({ json: user }));
  await page.route("**/notifications/unread-count*", (route) => route.fulfill({ json: { unread_count: 0 } }));
  await page.route("**/notifications*", (route) => route.fulfill({ json: [] }));
  await page.route("**/academic/levels*", (route) => route.fulfill({ json: [
    { id: 99, code: "SELF", name_en: "Self-directed learning", name_ta: "சுய கற்றல்", name_si: "ස්වයං අධ්‍යයනය" },
  ] }));
  await page.route("**/flashcards/dashboard/stats*", (route) => route.fulfill({ json: { total_sets: 0, total_cards_studied: 0, average_score: 0, revision_streak: 0 } }));
  await page.route("**/flashcards/reminders*", (route) => route.fulfill({ json: null }));
  await page.route("**/flashcards/sets*", (route) => route.fulfill({ json: [] }));
  await page.route("**/notes/**", (route) => route.fulfill({ json: [] }));
  await page.route("**/flashcards/generate*", (route) => route.fulfill({ json: {
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
  // The first project also warms Vite's lazy route chunk; allow for that cold compile.
  await expect(page.getByRole("heading", { name: "AI Flashcards" })).toBeVisible({ timeout: 15_000 });
  await expect(page.locator("html")).toHaveClass(testInfo.project.name.includes("dark") ? /dark/ : /^(?!.*dark)/);

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(1);

  await page.getByRole("button", { name: "Create New Flashcards" }).click();
  await page.getByLabel("Topic").fill("Python");
  const generator = page.locator("form");
  await generator.locator("select").nth(0).selectOption("99");
  await generator.locator("select").nth(1).selectOption("en");
  await page.getByPlaceholder("Enter subject name").fill("ICT");
  await page.getByRole("combobox", { name: "Difficulty", exact: true }).selectOption("easy");
  await page.getByRole("combobox", { name: "Language", exact: true }).selectOption("en");
  await page.getByRole("button", { name: "Generate Flashcards" }).click();
  await expect(page.getByText("What is a variable?")).toBeVisible();
  await page.getByTitle("Flip card").click();
  await expect(page.getByText("A named storage location.")).toBeVisible();
  await page.waitForTimeout(600);
  await expect(page.getByTitle("Read card aloud")).toBeEnabled();

  const finalOverflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(finalOverflow).toBeLessThanOrEqual(1);
  expect(pageErrors).toEqual([]);
});
