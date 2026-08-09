import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30_000,
  fullyParallel: false,
  workers: 1,
  reporter: "line",
  use: {
    baseURL: "http://127.0.0.1:5180",
    browserName: "chromium",
    screenshot: "only-on-failure",
  },
  webServer: {
    command: "npm run dev -- --host 127.0.0.1 --port 5180",
    url: "http://127.0.0.1:5180",
    reuseExistingServer: true,
    timeout: 120_000,
  },
  projects: [
    { name: "desktop-light", use: { viewport: { width: 1440, height: 1000 }, colorScheme: "light" } },
    { name: "tablet-dark", use: { viewport: { width: 820, height: 1180 }, colorScheme: "dark" } },
    { name: "mobile-light", use: { viewport: { width: 390, height: 844 }, colorScheme: "light" } },
  ],
});
