/**
 * QR Generator - Main Interface
 *
 * The primary component that orchestrates QR code generation with a modern,
 * intuitive interface for URL input, styling, logo upload, and preview.
 */

import { useEffect, useState, useCallback, useRef } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../ui/card";
import { Button } from "../ui/button";
import { URLInput } from "./URLInput";
import { LogoUpload } from "./LogoUpload";
import { StyleControls } from "./StyleControls";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import {
  Download,
  RotateCcw,
  Wand2,
  Image as ImageIcon,
  QrCode,
  Palette,
  AlertCircle,
  CheckCircle,
} from "lucide-react";
import { useQRGeneration } from "../../hooks/useQRGeneration";

export function QRGenerator() {
  const {
    // State
    config,
    isGenerating,
    error,
    previewUrl,
    logoFile,
    logoPreview,
    selectedPreset,
    availablePresets,
    presetsLoading,
    urlValidation,
    isValidatingUrl,

    // Actions
    updateConfig,
    resetConfig,
    applyPreset,
    loadPresets,
    setLogoFile,
    generateQR,
    downloadQR,
    validateURL,
    clearError,
    setUrlValidation,
  } = useQRGeneration();

  const [activeTab, setActiveTab] = useState("logo");

  // Ref to track the last generated config to prevent infinite loops
  const lastGeneratedConfigRef = useRef<string>("");

  // Load presets on mount
  useEffect(() => {
    loadPresets();
  }, [loadPresets]);

  // Auto-validate URL when it changes (with debouncing)
  useEffect(() => {
    if (config.url.trim()) {
      const timer = setTimeout(() => {
        validateURL(config.url);
      }, 300); // Debounce validation

      return () => {
        clearTimeout(timer);
      };
    } else {
      setUrlValidation(null);
    }
  }, [config.url]); // Removed validateURL dependency to prevent infinite loop

  // Auto-generate QR when URL is valid or config changes (with debouncing)
  useEffect(() => {
    // Create a config hash to track changes (including logo)
    const configHash = JSON.stringify({
      url: config.url,
      size: config.size,
      border: config.border,
      style: config.style,
      dark_color: config.dark_color,
      light_color: config.light_color,
      ec_level: config.ec_level,
      eye_radius: config.eye_radius,
      eye_scale_x: config.eye_scale_x,
      eye_scale_y: config.eye_scale_y,
      eye_shape: config.eye_shape,
      eye_style: config.eye_style,
      logo_scale: config.logo_scale,
      bg_padding: config.bg_padding,
      bg_radius: config.bg_radius,
      qr_radius: config.qr_radius,
      compress_level: config.compress_level,
      quantize_colors: config.quantize_colors,
      logoFile: logoFile?.name || null, // Include logo file name
    });

    // Check if we've already generated for this exact config
    if (configHash === lastGeneratedConfigRef.current) {
      return;
    }

    if (config.url.trim() && urlValidation?.valid && !isGenerating && !error) {
      const timer = setTimeout(() => {
        lastGeneratedConfigRef.current = configHash;
        generateQR();
      }, 800); // Longer delay to avoid too frequent generations

      return () => {
        clearTimeout(timer);
      };
    }
  }, [
    config.url,
    config.size,
    config.border,
    config.style,
    config.dark_color,
    config.light_color,
    config.ec_level,
    config.eye_radius,
    config.eye_scale_x,
    config.eye_scale_y,
    config.eye_shape,
    config.eye_style,
    config.logo_scale,
    config.bg_padding,
    config.bg_radius,
    config.qr_radius,
    config.compress_level,
    config.quantize_colors,
    logoFile, // Include logo file changes
    urlValidation?.valid,
    isGenerating,
    error,
  ]); // Include all config properties that affect QR generation

  const handleQuickPreset = (presetName: string) => {
    // Clear the config hash to ensure regeneration with new preset
    lastGeneratedConfigRef.current = "";
    applyPreset(presetName);
  };

  const handleDownload = async () => {
    const filename = `qr_${Date.now()}_${config.size}x${config.size}.png`;
    await downloadQR(filename);
  };

  const handleReset = () => {
    resetConfig();
    clearError();
  };

  const canGenerate =
    config.url.trim() && urlValidation?.valid && !isGenerating;

  // Memoize the onChange handler to prevent unnecessary re-renders
  const handleUrlChange = useCallback(
    (url: string) => {
      // Clear the last generated config when URL changes
      lastGeneratedConfigRef.current = "";
      updateConfig({ url });
    },
    [updateConfig]
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="w-full max-w-7xl mx-auto p-4 space-y-8">
        {/* Header */}
        <div className="text-center space-y-3 pt-6 pb-6">
          <div className="flex items-center justify-center gap-3 mb-2">
            <div className="relative">
              <QrCode className="h-8 w-8 text-blue-600" />
              <div className="absolute -top-1 -right-1 h-2 w-2 bg-purple-500 rounded-full animate-pulse" />
            </div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              QR Studio
            </h1>
          </div>
          <p className="text-base text-gray-600 max-w-xl mx-auto">
            Create QR codes with custom styling, logos, and advanced features.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Panel - Configuration */}
          <div className="space-y-6 lg:pr-4">
            {/* URL Input - First Step */}
            <Card className="border-0 shadow-lg bg-white/80 backdrop-blur-sm hover:shadow-xl transition-all duration-300">
              <CardHeader className="pb-4">
                <CardTitle className="text-xl flex items-center gap-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <QrCode className="h-5 w-5 text-blue-600" />
                  </div>
                  URL or Text
                  <span className="ml-auto text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full font-medium">
                    Step 1
                  </span>
                </CardTitle>
                <CardDescription className="text-base">
                  Enter the URL or text you want to encode in the QR code
                </CardDescription>
              </CardHeader>
              <CardContent>
                <URLInput
                  value={config.url}
                  onChange={handleUrlChange}
                  validation={urlValidation}
                  isValidating={isValidatingUrl}
                  disabled={isGenerating}
                />
              </CardContent>
            </Card>

            {/* Quick Presets */}
            {Object.keys(availablePresets).length > 0 && (
              <Card className="border-0 shadow-lg bg-white/80 backdrop-blur-sm hover:shadow-xl transition-all duration-300">
                <CardHeader className="pb-4">
                  <CardTitle className="text-xl flex items-center gap-3">
                    <div className="p-2 bg-purple-100 rounded-lg">
                      <Wand2 className="h-5 w-5 text-purple-600" />
                    </div>
                    Quick Presets
                    <span className="ml-auto text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded-full font-medium">
                      Step 2
                    </span>
                  </CardTitle>
                  <CardDescription className="text-base">
                    Choose a preset style or customize below
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    {Object.entries(availablePresets).map(([key, preset]) => (
                      <Button
                        key={key}
                        variant={selectedPreset === key ? "default" : "outline"}
                        size="sm"
                        onClick={() => handleQuickPreset(key)}
                        disabled={presetsLoading}
                        className={`relative overflow-hidden transition-all duration-200 ${
                          selectedPreset === key
                            ? "bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg scale-105"
                            : "hover:bg-blue-50 hover:border-blue-300 hover:scale-105"
                        }`}
                      >
                        {preset.name}
                        {selectedPreset === key && (
                          <div className="absolute inset-0 bg-white/20 animate-pulse" />
                        )}
                      </Button>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Advanced Configuration Tabs */}
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid w-full grid-cols-2 bg-white/80 backdrop-blur-sm border-0 shadow-lg h-12">
                <TabsTrigger
                  value="logo"
                  className="flex items-center gap-2 data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-purple-600 data-[state=active]:text-white transition-all duration-200"
                >
                  <ImageIcon className="h-4 w-4" />
                  <span className="hidden sm:inline">Logo</span>
                </TabsTrigger>
                <TabsTrigger
                  value="style"
                  className="flex items-center gap-2 data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-purple-600 data-[state=active]:text-white transition-all duration-200"
                >
                  <Palette className="h-4 w-4" />
                  <span className="hidden sm:inline">Advanced</span>
                </TabsTrigger>
              </TabsList>

              {/* Logo Upload Tab */}
              <TabsContent value="logo" className="space-y-4 mt-6">
                <Card className="border-0 shadow-lg bg-white/80 backdrop-blur-sm hover:shadow-xl transition-all duration-300">
                  <CardHeader className="pb-4">
                    <CardTitle className="text-xl flex items-center gap-3">
                      <div className="p-2 bg-green-100 rounded-lg">
                        <ImageIcon className="h-5 w-5 text-green-600" />
                      </div>
                      Logo Upload
                    </CardTitle>
                    <CardDescription className="text-base">
                      Add your logo to the center of the QR code (optional)
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <LogoUpload
                      logoFile={logoFile}
                      logoPreview={logoPreview}
                      onLogoChange={setLogoFile}
                      logoScale={config.logo_scale}
                      onLogoScaleChange={(scale) =>
                        updateConfig({ logo_scale: scale })
                      }
                      bgPadding={config.bg_padding}
                      onBgPaddingChange={(padding) =>
                        updateConfig({ bg_padding: padding })
                      }
                      bgRadius={config.bg_radius}
                      onBgRadiusChange={(radius) =>
                        updateConfig({ bg_radius: radius })
                      }
                      disabled={isGenerating}
                    />
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Style Tab */}
              <TabsContent value="style" className="space-y-4 mt-6">
                <StyleControls
                  config={config}
                  onConfigChange={updateConfig}
                  disabled={isGenerating}
                />
              </TabsContent>
            </Tabs>

            {/* Action Buttons */}
            <div className="flex gap-3">
              <Button
                onClick={generateQR}
                disabled={!canGenerate}
                className="flex-1 h-12 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white shadow-lg hover:shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                size="lg"
              >
                {isGenerating ? (
                  <div className="flex items-center gap-2">
                    <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full" />
                    <span className="font-medium">Generating...</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <QrCode className="h-5 w-5" />
                    <span className="font-medium">Generate QR Code</span>
                  </div>
                )}
              </Button>

              <Button
                variant="outline"
                onClick={handleReset}
                disabled={isGenerating}
                size="lg"
                className="h-12 px-4 border-gray-300 hover:bg-gray-50 hover:border-gray-400 transition-all duration-200"
              >
                <RotateCcw className="h-5 w-5" />
              </Button>
            </div>

            {/* Error Display */}
            {error && (
              <Card className="border-0 shadow-lg bg-red-50/80 backdrop-blur-sm">
                <CardContent className="p-6">
                  <div className="flex items-start gap-4">
                    <div className="p-2 bg-red-100 rounded-lg">
                      <AlertCircle className="h-5 w-5 text-red-600" />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-semibold text-red-900 mb-1">
                        Generation Failed
                      </h4>
                      <p className="text-sm text-red-700 mb-3">{error}</p>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={clearError}
                        className="text-red-700 border-red-300 hover:bg-red-100 hover:border-red-400 transition-all duration-200"
                      >
                        Dismiss
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Right Panel - Preview */}
          <div className="space-y-6 lg:sticky lg:top-8 lg:self-start">
            <Card className="border-0 shadow-xl bg-white/80 backdrop-blur-sm">
              <CardHeader className="pb-4">
                <CardTitle className="text-xl flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-100 rounded-lg">
                      <QrCode className="h-5 w-5 text-blue-600" />
                    </div>
                    <span>QR Code Preview</span>
                  </div>
                  {previewUrl && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleDownload}
                      disabled={isGenerating}
                      className="bg-green-50 border-green-300 hover:bg-green-100 hover:border-green-400 text-green-700 shadow-sm transition-all duration-200"
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Download
                    </Button>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="aspect-square bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl border-2 border-dashed border-gray-300 flex items-center justify-center relative overflow-hidden">
                  {isGenerating ? (
                    <div className="text-center">
                      <div className="relative">
                        <div className="animate-spin h-12 w-12 border-3 border-blue-200 border-t-blue-600 rounded-full mx-auto mb-4" />
                        <div className="absolute inset-0 animate-ping h-12 w-12 border border-blue-300 rounded-full mx-auto opacity-20" />
                      </div>
                      <p className="text-base font-medium text-gray-700 mb-1">
                        Generating QR code...
                      </p>
                      <p className="text-sm text-gray-500">
                        This usually takes just a moment
                      </p>
                    </div>
                  ) : previewUrl ? (
                    <div className="p-6 w-full">
                      <div className="relative group">
                        <img
                          src={previewUrl}
                          alt="QR Code Preview"
                          className="w-full h-full object-contain rounded-lg shadow-lg group-hover:scale-105 transition-transform duration-200"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200 rounded-lg" />
                      </div>
                    </div>
                  ) : config.url.trim() ? (
                    <div className="text-center">
                      <div className="relative mb-4">
                        <QrCode className="h-12 w-12 text-gray-400 mx-auto" />
                        <div className="absolute -top-1 -right-1 h-3 w-3 bg-blue-500 rounded-full animate-pulse" />
                      </div>
                      <p className="text-base font-medium text-gray-700 mb-1">
                        {urlValidation?.valid
                          ? "Ready to Generate!"
                          : "Enter a valid URL"}
                      </p>
                      <p className="text-sm text-gray-500">
                        {urlValidation?.valid
                          ? "Click the generate button to create your QR code"
                          : "We'll validate your URL automatically"}
                      </p>
                    </div>
                  ) : (
                    <div className="text-center">
                      <QrCode className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-base font-medium text-gray-700 mb-1">
                        Start by entering a URL
                      </p>
                      <p className="text-sm text-gray-500">
                        Your QR code preview will appear here
                      </p>
                    </div>
                  )}
                </div>

                {/* QR Info */}
                {previewUrl && (
                  <div className="mt-6 p-4 bg-gradient-to-r from-green-50 to-blue-50 rounded-xl border border-green-200">
                    <div className="flex items-center gap-2 text-sm text-green-800 mb-2">
                      <CheckCircle className="h-4 w-4" />
                      <span className="font-medium">
                        QR code generated successfully!
                      </span>
                    </div>
                    <div className="text-xs text-green-700 space-y-1">
                      <p>
                        Size: {config.size}×{config.size}px • Style:{" "}
                        {config.style} • Error Correction: {config.ec_level}
                      </p>
                      {logoFile && (
                        <p>
                          Logo: {logoFile.name} (
                          {Math.round(config.logo_scale * 100)}% scale)
                        </p>
                      )}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
