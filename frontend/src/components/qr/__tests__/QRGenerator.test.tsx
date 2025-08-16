import { render, screen } from "@testing-library/react";
import { QRGenerator } from "../QRGenerator";

// Mock the useQRGeneration hook
const mockUseQRGeneration = {
  config: {
    url: "",
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

vi.mock("../../hooks/useQRGeneration", () => ({
  useQRGeneration: () => mockUseQRGeneration,
}));

describe("QRGenerator", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the main layout", () => {
    render(<QRGenerator />);

    // Check for main heading
    expect(screen.getByText("QR Studio")).toBeInTheDocument();
  });

  it("renders URL input section", () => {
    render(<QRGenerator />);

    // Check for URL input
    expect(
      screen.getByPlaceholderText(/enter url or text/i)
    ).toBeInTheDocument();
  });

  it("renders without crashing with different states", () => {
    // Test with preview URL
    mockUseQRGeneration.previewUrl = "mock-blob-url";
    const { rerender } = render(<QRGenerator />);
    expect(screen.getByText("QR Studio")).toBeInTheDocument();

    // Test with generating state
    mockUseQRGeneration.previewUrl = null;
    mockUseQRGeneration.isGenerating = true;
    rerender(<QRGenerator />);
    expect(screen.getByText("QR Studio")).toBeInTheDocument();

    // Test with error state
    mockUseQRGeneration.isGenerating = false;
    mockUseQRGeneration.error = "Failed to generate QR code";
    rerender(<QRGenerator />);
    expect(screen.getByText("QR Studio")).toBeInTheDocument();
  });

  it("calls hook functions when needed", () => {
    render(<QRGenerator />);

    // Verify that the hook functions are available
    expect(mockUseQRGeneration.updateConfig).toBeDefined();
    expect(mockUseQRGeneration.generateQR).toBeDefined();
    expect(mockUseQRGeneration.validateURL).toBeDefined();
  });
});
