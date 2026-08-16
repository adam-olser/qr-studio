import { test, expect } from "@playwright/test";
import { mockBackend } from "./mocks";

test.beforeEach(async ({ page }) => {
  await mockBackend(page);
  await page.goto("/");
});

test("initial empty state renders and matches snapshot", async ({ page }) => {
  await expect(page.getByText("Start by entering a URL")).toBeVisible();
  await expect(page).toHaveScreenshot("empty-state.png");
});

test("generates a QR code from a valid URL", async ({ page }) => {
  await page.locator("#url-input").fill("https://example.com");

  await expect(page.getByAltText("QR Code Preview")).toBeVisible({ timeout: 10000 });
  await expect(page).toHaveScreenshot("generated-qr.png");
});

test("shows validation feedback for an invalid URL", async ({ page }) => {
  await page.locator("#url-input").fill("not-a-valid-url");

  await expect(page.getByText(/enter a valid url/i)).toBeVisible({ timeout: 10000 });
});

test("applying a preset updates the generated QR", async ({ page }) => {
  await page.locator("#url-input").fill("https://example.com");
  await expect(page.getByAltText("QR Code Preview")).toBeVisible({ timeout: 10000 });

  await page.getByRole("button", { name: "Ocean" }).click();
  await expect(page.getByAltText("QR Code Preview")).toBeVisible({ timeout: 10000 });
  await expect(page).toHaveScreenshot("preset-applied.png");
});
