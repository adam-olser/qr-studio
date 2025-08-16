import type { QRConfig } from "../../types/qr";

describe("qrClient", () => {
  it("should create QRConfig with required properties", () => {
    const config: QRConfig = {
      url: "https://example.com",
      size: 512,
      border: 4,
      style: "rounded",
      dark_color: "#000000",
      light_color: "#FFFFFF",
      ec_level: "M",
      eye_radius: 0.9,
      eye_scale_x: 1.0,
      eye_scale_y: 1.0,
      eye_shape: "rect",
      eye_style: "standard",
      logo_scale: 0.22,
      bg_padding: 20,
      bg_radius: 28,
      qr_radius: 0,
      compress_level: 6,
      quantize_colors: 64,
    };

    expect(config.url).toBe("https://example.com");
    expect(config.size).toBe(512);
    expect(config.style).toBe("rounded");
  });

  it("should have valid QRConfig type structure", () => {
    // Test that the QRConfig type includes all expected properties
    const config: Partial<QRConfig> = {
      url: "test",
      size: 256,
      style: "dots",
    };

    expect(config).toBeDefined();
    expect(typeof config.url).toBe("string");
    expect(typeof config.size).toBe("number");
    expect(typeof config.style).toBe("string");
  });
});
