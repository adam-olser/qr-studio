import { render, RenderOptions } from "@testing-library/react";
import { ReactElement } from "react";

// Mock QR generation hook for testing
export const mockUseQRGeneration = {
  config: {
    url: "",
    size: 512,
    border: 4,
    style: "rounded" as const,
    dark_color: "#000000",
    light_color: "#FFFFFF",
    ec_level: "M" as const,
    eye_radius: 0.9,
    eye_scale_x: 1.0,
    eye_scale_y: 1.0,
    eye_shape: "rect" as const,
    eye_style: "standard" as const,
    logo_scale: 0.22,
    bg_padding: 20,
    bg_radius: 28,
    qr_radius: 0,
    compress_level: 6,
    quantize_colors: 64,
  },
  logoFile: null,
  previewUrl: null,
  isGenerating: false,
  error: null,
  urlValid: false,
  urlValidation: null,
  presets: {},
  selectedPreset: null,
  updateConfig: vi.fn(),
  setLogoFile: vi.fn(),
  generateQR: vi.fn(),
  downloadQR: vi.fn(),
  validateURL: vi.fn(),
  loadPresets: vi.fn(),
  applyPreset: vi.fn(),
};

// Custom render function
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, "wrapper">
) => render(ui, options);

export * from "@testing-library/react";
export { customRender as render };
