import { Page } from "@playwright/test";

// 1x1 black PNG, used as a stand-in for generated QR images.
const PNG_1X1_BASE64 =
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=";

export const MOCK_PRESETS = {
  classic: {
    name: "Classic",
    description: "Simple black and white QR code",
    config: { style: "square", dark_color: "#000000", light_color: "#FFFFFF" },
  },
  ocean: {
    name: "Ocean",
    description: "Blue themed QR code",
    config: { style: "rounded", dark_color: "#2563eb", light_color: "#FFFFFF" },
  },
};

export async function mockBackend(page: Page) {
  await page.route("**/health/", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ status: "ok", timestamp: new Date().toISOString() }),
    })
  );

  await page.route("**/api/v1/qr/presets", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MOCK_PRESETS),
    })
  );

  await page.route("**/api/v1/qr/validate-url*", (route) => {
    const url = new URL(route.request().url()).searchParams.get("url") || "";
    const valid = /^https?:\/\/.+/i.test(url);
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ valid, url, error: valid ? undefined : "Invalid URL" }),
    });
  });

  await page.route("**/api/v1/qr/generate-form", (route) =>
    route.fulfill({
      status: 200,
      contentType: "image/png",
      body: Buffer.from(PNG_1X1_BASE64, "base64"),
    })
  );
}
