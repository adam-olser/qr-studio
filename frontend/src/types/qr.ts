/**
 * TypeScript types and interfaces for QR Studio
 */

export interface QRConfig {
  // Basic settings
  url: string;
  size: number;
  border: number;

  // Style settings
  style: QRStyle;
  dark_color: string;
  light_color: string;
  ec_level: ErrorCorrectionLevel;

  // Eye customization
  eye_radius: number;
  eye_scale_x: number;
  eye_scale_y: number;
  eye_shape: EyeShape;
  eye_style: EyeStyle;

  // Logo settings
  logo_scale: number;
  bg_padding: number;
  bg_radius: number;

  // Output settings
  qr_radius: number;
  compress_level: number;
  quantize_colors: number;
}

export type QRStyle =
  | "square"
  | "gapped"
  | "dots"
  | "rounded"
  | "bars-vertical"
  | "bars-horizontal";

export type ErrorCorrectionLevel = "L" | "M" | "Q" | "H";

export type EyeShape = "rect" | "rounded" | "circle";

export type EyeStyle = "standard" | "circle-ring";

export interface QRPreset {
  name: string;
  description: string;
  config: Partial<QRConfig>;
}

export interface QRPresets {
  [key: string]: QRPreset;
}

export interface QRGenerationRequest {
  url: string;
  size?: number;
  border?: number;
  style?: QRStyle;
  dark_color?: string;
  light_color?: string;
  ec_level?: ErrorCorrectionLevel;
  eye_radius?: number;
  eye_scale_x?: number;
  eye_scale_y?: number;
  eye_shape?: EyeShape;
  eye_style?: EyeStyle;
  logo_scale?: number;
  bg_padding?: number;
  bg_radius?: number;
  qr_radius?: number;
  compress_level?: number;
  quantize_colors?: number;
}

export interface QRGenerationResponse {
  message: string;
  size: number;
  format: string;
}

export interface URLValidationResponse {
  valid: boolean;
  url?: string;
  error?: string;
  warning?: string;
}

export interface QRStylesResponse {
  styles: QRStyle[];
  eye_shapes: EyeShape[];
  eye_styles: EyeStyle[];
  error_correction_levels: ErrorCorrectionLevel[];
  size_limits: {
    min: number;
    max: number;
  };
  file_limits: {
    max_size_mb: number;
    allowed_types: string[];
  };
}

export interface QRGenerationState {
  // Configuration
  config: QRConfig;

  // UI State
  isGenerating: boolean;
  error: string | null;
  previewUrl: string | null;

  // Logo
  logoFile: File | null;
  logoPreview: string | null;

  // Presets
  selectedPreset: string | null;
  availablePresets: QRPresets;

  // Validation
  urlValidation: URLValidationResponse | null;
}

export interface QRGenerationActions {
  // Config updates
  updateConfig: (updates: Partial<QRConfig>) => void;
  setConfig: (config: QRConfig) => void;
  resetConfig: () => void;

  // Preset management
  applyPreset: (presetName: string) => void;
  loadPresets: () => Promise<void>;

  // Logo management
  setLogoFile: (file: File | null) => void;
  clearLogo: () => void;

  // Generation
  generateQR: () => Promise<void>;
  downloadQR: () => Promise<void>;

  // Validation
  validateURL: (url: string) => Promise<void>;

  // UI state
  setError: (error: string | null) => void;
  clearError: () => void;
}

export type QRStore = QRGenerationState & QRGenerationActions;

// Default configuration
export const DEFAULT_QR_CONFIG: QRConfig = {
  url: "",
  size: 1024,
  border: 4,
  style: "rounded",
  dark_color: "#000000",
  light_color: "#FFFFFF",
  ec_level: "Q",
  eye_radius: 0.9,
  eye_scale_x: 1.0,
  eye_scale_y: 1.0,
  eye_shape: "rect",
  eye_style: "standard",
  logo_scale: 0.22,
  bg_padding: 20,
  bg_radius: 28,
  qr_radius: 0,
  compress_level: 9,
  quantize_colors: 64,
};

// Style options with labels for UI
export const QR_STYLE_OPTIONS: Array<{
  value: QRStyle;
  label: string;
  description: string;
}> = [
  { value: "square", label: "Square", description: "Classic square modules" },
  { value: "rounded", label: "Rounded", description: "Rounded corner modules" },
  { value: "dots", label: "Dots", description: "Circular dot modules" },
  { value: "gapped", label: "Gapped", description: "Square modules with gaps" },
  {
    value: "bars-vertical",
    label: "Vertical Bars",
    description: "Vertical bar modules",
  },
  {
    value: "bars-horizontal",
    label: "Horizontal Bars",
    description: "Horizontal bar modules",
  },
];

export const EYE_SHAPE_OPTIONS: Array<{ value: EyeShape; label: string }> = [
  { value: "rect", label: "Rectangle" },
  { value: "rounded", label: "Rounded" },
  { value: "circle", label: "Circle" },
];

export const EYE_STYLE_OPTIONS: Array<{ value: EyeStyle; label: string }> = [
  { value: "standard", label: "Standard" },
  { value: "circle-ring", label: "Circle Ring (iOS)" },
];

export const ERROR_CORRECTION_OPTIONS: Array<{
  value: ErrorCorrectionLevel;
  label: string;
  description: string;
}> = [
  { value: "L", label: "Low (L)", description: "~7% error correction" },
  { value: "M", label: "Medium (M)", description: "~15% error correction" },
  { value: "Q", label: "Quartile (Q)", description: "~25% error correction" },
  { value: "H", label: "High (H)", description: "~30% error correction" },
];

// Color presets
export const COLOR_PRESETS = {
  classic: { dark: "#000000", light: "#FFFFFF" },
  blue: { dark: "#2563eb", light: "#FFFFFF" },
  green: { dark: "#16a34a", light: "#FFFFFF" },
  purple: { dark: "#9333ea", light: "#FFFFFF" },
  red: { dark: "#dc2626", light: "#FFFFFF" },
  dark: { dark: "#1f2937", light: "#f9fafb" },
  gradient: { dark: "#6366f1", light: "#f8fafc" },
};
