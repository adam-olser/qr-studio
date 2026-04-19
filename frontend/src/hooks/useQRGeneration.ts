/**
 * QR Generation Hook
 *
 * Custom React hook that manages QR code generation state and operations
 */

import { useState, useCallback, useRef, useEffect } from "react";
import {
  QRConfig,
  QRGenerationRequest,
  QRPresets,
  URLValidationResponse,
  DEFAULT_QR_CONFIG,
} from "../types/qr";
import { qrClient } from "../services/qrClient";

interface UseQRGenerationState {
  // Configuration
  config: QRConfig;

  // Generation state
  isGenerating: boolean;
  error: string | null;
  previewUrl: string | null;
  lastGeneratedBlob: Blob | null;

  // Logo state
  logoFile: File | null;
  logoPreview: string | null;

  // Presets
  selectedPreset: string | null;
  availablePresets: QRPresets;
  presetsLoading: boolean;

  // URL validation
  urlValidation: URLValidationResponse | null;
  isValidatingUrl: boolean;
}

interface UseQRGenerationActions {
  // Config management
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
  downloadQR: (filename?: string) => Promise<void>;
  regenerateQR: () => Promise<void>;

  // URL validation
  validateURL: (url?: string) => Promise<void>;
  setUrlValidation: (validation: URLValidationResponse | null) => void;

  // Error handling
  setError: (error: string | null) => void;
  clearError: () => void;

  // Cleanup
  cleanup: () => void;
}

type UseQRGenerationReturn = UseQRGenerationState & UseQRGenerationActions;

export function useQRGeneration(
  initialConfig?: Partial<QRConfig>
): UseQRGenerationReturn {
  // State
  const [config, setConfigState] = useState<QRConfig>(() => ({
    ...DEFAULT_QR_CONFIG,
    ...initialConfig,
  }));

  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [lastGeneratedBlob, setLastGeneratedBlob] = useState<Blob | null>(null);

  const [logoFile, setLogoFileState] = useState<File | null>(null);
  const [logoPreview, setLogoPreview] = useState<string | null>(null);

  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
  const [availablePresets, setAvailablePresets] = useState<QRPresets>({});
  const [presetsLoading, setPresetsLoading] = useState(false);

  const [urlValidation, setUrlValidation] =
    useState<URLValidationResponse | null>(null);
  const [isValidatingUrl, setIsValidatingUrl] = useState(false);

  // Refs for cleanup
  const previewUrlRef = useRef<string | null>(null);
  const logoPreviewRef = useRef<string | null>(null);
  const isGeneratingRef = useRef(false);

  // Cleanup function
  const cleanup = useCallback(() => {
    if (previewUrlRef.current) {
      qrClient.revokePreviewURL(previewUrlRef.current);
      previewUrlRef.current = null;
    }
    if (logoPreviewRef.current) {
      URL.revokeObjectURL(logoPreviewRef.current);
      logoPreviewRef.current = null;
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return cleanup;
  }, [cleanup]);

  // Actions
  const updateConfig = useCallback((updates: Partial<QRConfig>) => {
    setConfigState((prev) => ({ ...prev, ...updates }));
    setSelectedPreset(null); // Clear preset selection when manually changing config
    setError(null); // Clear any previous errors
  }, []);

  const setConfig = useCallback((newConfig: QRConfig) => {
    setConfigState(newConfig);
    setSelectedPreset(null);
    setError(null);
  }, []);

  const resetConfig = useCallback(() => {
    setConfigState({ ...DEFAULT_QR_CONFIG });
    setSelectedPreset(null);
    setError(null);
  }, []);

  const applyPreset = useCallback(
    (presetName: string) => {
      const preset = availablePresets[presetName];
      if (preset) {
        // Apply preset config without clearing the preset selection
        setConfigState((prev) => ({ ...prev, ...preset.config }));
        setSelectedPreset(presetName);
        setError(null); // Clear any previous errors
      }
    },
    [availablePresets]
  );

  const loadPresets = useCallback(async () => {
    setPresetsLoading(true);
    try {
      const presets = await qrClient.getPresets();
      setAvailablePresets(presets);
    } catch (err) {
      console.error("Failed to load presets:", err);
      // Don't set shared error — a preset load failure shouldn't block URL validation or generation
    } finally {
      setPresetsLoading(false);
    }
  }, []);

  const setLogoFile = useCallback((file: File | null) => {
    // Cleanup previous logo preview
    if (logoPreviewRef.current) {
      URL.revokeObjectURL(logoPreviewRef.current);
      logoPreviewRef.current = null;
    }

    setLogoFileState(file);

    if (file) {
      const previewUrl = URL.createObjectURL(file);
      setLogoPreview(previewUrl);
      logoPreviewRef.current = previewUrl;
    } else {
      setLogoPreview(null);
    }
  }, []);

  const clearLogo = useCallback(() => {
    setLogoFile(null);
  }, [setLogoFile]);

  const generateQR = useCallback(async () => {
    if (!config.url.trim()) {
      setError("Please enter a URL to generate QR code");
      return;
    }

    // Prevent multiple simultaneous generations
    if (isGeneratingRef.current) {
      return;
    }

    isGeneratingRef.current = true;
    setIsGenerating(true);
    setError(null);

    try {
      // Cleanup previous preview
      if (previewUrlRef.current) {
        qrClient.revokePreviewURL(previewUrlRef.current);
        previewUrlRef.current = null;
      }

      const request: QRGenerationRequest = { ...config };
      const blob = await qrClient.generateQR(request, logoFile || undefined);

      setLastGeneratedBlob(blob);

      const newPreviewUrl = qrClient.createPreviewURL(blob);
      setPreviewUrl(newPreviewUrl);
      previewUrlRef.current = newPreviewUrl;
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to generate QR code";
      console.error("QR generation error:", err);
      setError(errorMessage);
    } finally {
      setIsGenerating(false);
      isGeneratingRef.current = false;
    }
  }, [config, logoFile]);

  const regenerateQR = useCallback(async () => {
    await generateQR();
  }, [generateQR]);

  const downloadQR = useCallback(
    async (filename?: string) => {
      if (!config.url.trim()) {
        setError("Please enter a URL to generate QR code");
        return;
      }

      try {
        if (isGeneratingRef.current) {
          return;
        }
        isGeneratingRef.current = true;
        setIsGenerating(true);
        const request: QRGenerationRequest = { ...config };
        await qrClient.downloadQR(request, logoFile || undefined, filename);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to download QR code";
        setError(errorMessage);
        console.error("QR download error:", err);
      } finally {
        setIsGenerating(false);
        isGeneratingRef.current = false;
      }
    },
    [config, logoFile]
  );

  const validateURL = useCallback(
    async (url?: string) => {
      const urlToValidate = url ?? config.url;

      if (!urlToValidate.trim()) {
        setUrlValidation(null);
        return;
      }

      setIsValidatingUrl(true);

      try {
        const validation = await qrClient.validateURL(urlToValidate);
        setUrlValidation(validation);
      } catch (err) {
        console.error("URL validation error:", err);
        const fallbackValidation = {
          valid: urlToValidate.length > 0 && urlToValidate.length <= 2000,
          error:
            urlToValidate.length === 0
              ? "URL is required"
              : urlToValidate.length > 2000
              ? "URL too long (max 2000 characters)"
              : undefined,
          url: urlToValidate,
        };
        setUrlValidation(fallbackValidation);
      } finally {
        setIsValidatingUrl(false);
      }
    },
    [config.url]
  );

  const setErrorAction = useCallback((newError: string | null) => {
    setError(newError);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const setUrlValidationAction = useCallback(
    (validation: URLValidationResponse | null) => {
      setUrlValidation(validation);
    },
    []
  );

  return {
    // State
    config,
    isGenerating,
    error,
    previewUrl,
    lastGeneratedBlob,
    logoFile,
    logoPreview,
    selectedPreset,
    availablePresets,
    presetsLoading,
    urlValidation,
    isValidatingUrl,

    // Actions
    updateConfig,
    setConfig,
    resetConfig,
    applyPreset,
    loadPresets,
    setLogoFile,
    clearLogo,
    generateQR,
    downloadQR,
    regenerateQR,
    validateURL,
    setError: setErrorAction,
    clearError,
    setUrlValidation: setUrlValidationAction,
    cleanup,
  };
}

export default useQRGeneration;
