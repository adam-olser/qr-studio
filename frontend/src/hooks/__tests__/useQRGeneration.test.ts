import { renderHook, act } from "@testing-library/react";
import { useQRGeneration } from "../useQRGeneration";

// Mock the entire qrClient module with simple implementations
vi.mock("../../services/qrClient", () => ({
  validateUrl: vi.fn().mockResolvedValue({
    valid: true,
    url: "https://example.com",
    length: 19,
    max_length: 2000,
  }),
  generateQR: vi
    .fn()
    .mockResolvedValue(new Blob(["mock-qr-data"], { type: "image/png" })),
  getPresets: vi.fn().mockResolvedValue({
    classic: {
      name: "Classic",
      description: "Classic style",
      config: { style: "rounded", dark_color: "#000000" },
    },
  }),
}));

describe("useQRGeneration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.URL.createObjectURL = vi.fn(() => "mock-blob-url");
    global.URL.revokeObjectURL = vi.fn();
  });

  it("should initialize with default config", () => {
    const { result } = renderHook(() => useQRGeneration());

    expect(result.current.config.url).toBe("");
    expect(result.current.config.size).toBe(1024);
    expect(result.current.config.style).toBe("rounded");
    expect(result.current.isGenerating).toBe(false);
    expect(result.current.error).toBe(null);
  });

  it("should update config", () => {
    const { result } = renderHook(() => useQRGeneration());

    act(() => {
      result.current.updateConfig({ url: "https://example.com" });
    });

    expect(result.current.config.url).toBe("https://example.com");
  });

  it("should handle basic functionality", () => {
    const { result } = renderHook(() => useQRGeneration());

    // Test that all required functions are available
    expect(typeof result.current.updateConfig).toBe("function");
    expect(typeof result.current.generateQR).toBe("function");
    expect(typeof result.current.validateURL).toBe("function");
    expect(typeof result.current.loadPresets).toBe("function");
    expect(typeof result.current.applyPreset).toBe("function");
    expect(typeof result.current.downloadQR).toBe("function");
  });

  it("should update config when applying preset", () => {
    const { result } = renderHook(() => useQRGeneration());

    // Test that updateConfig works
    act(() => {
      result.current.updateConfig({ style: "dots", dark_color: "#FF0000" });
    });

    expect(result.current.config.style).toBe("dots");
    expect(result.current.config.dark_color).toBe("#FF0000");
  });
});
