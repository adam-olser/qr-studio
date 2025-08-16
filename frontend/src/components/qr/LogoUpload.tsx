/**
 * Logo Upload Component
 *
 * Handles logo file upload with drag & drop, preview, and validation
 */

import React, { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Button } from "../ui/button";
import { Card, CardContent } from "../ui/card";
import { Label } from "../ui/label";
import { Slider } from "../ui/slider";
import {
  Upload,
  X,
  AlertCircle,
  Image as ImageIcon,
  FileImage,
} from "lucide-react";
import { formatFileSize } from "../../lib/utils";

interface LogoUploadProps {
  logoFile: File | null;
  logoPreview: string | null;
  onLogoChange: (file: File | null) => void;
  logoScale: number;
  onLogoScaleChange: (scale: number) => void;
  bgPadding: number;
  onBgPaddingChange: (padding: number) => void;
  bgRadius: number;
  onBgRadiusChange: (radius: number) => void;
  disabled?: boolean;
}

const ACCEPTED_TYPES = {
  "image/png": [".png"],
  "image/jpeg": [".jpg", ".jpeg"],
  "image/svg+xml": [".svg"],
};

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export function LogoUpload({
  logoFile,
  logoPreview,
  onLogoChange,
  logoScale,
  onLogoScaleChange,
  bgPadding,
  onBgPaddingChange,
  bgRadius,
  onBgRadiusChange,
  disabled = false,
}: LogoUploadProps) {
  const [uploadError, setUploadError] = useState<string | null>(null);

  const onDrop = useCallback(
    (acceptedFiles: File[], rejectedFiles: any[]) => {
      setUploadError(null);

      if (rejectedFiles.length > 0) {
        const rejection = rejectedFiles[0];
        if (rejection.errors.some((e: any) => e.code === "file-too-large")) {
          setUploadError(
            `File too large. Maximum size is ${formatFileSize(MAX_FILE_SIZE)}`
          );
        } else if (
          rejection.errors.some((e: any) => e.code === "file-invalid-type")
        ) {
          setUploadError(
            "Invalid file type. Please upload PNG, JPG, or SVG images."
          );
        } else {
          setUploadError("File upload failed. Please try again.");
        }
        return;
      }

      if (acceptedFiles.length > 0) {
        const file = acceptedFiles[0];
        onLogoChange(file);
      }
    },
    [onLogoChange]
  );

  const { getRootProps, getInputProps, isDragActive, isDragReject } =
    useDropzone({
      onDrop,
      accept: ACCEPTED_TYPES,
      maxSize: MAX_FILE_SIZE,
      multiple: false,
      disabled,
    });

  const clearLogo = () => {
    onLogoChange(null);
    setUploadError(null);
  };

  const handleFileInput = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setUploadError(null);

      // Validate file
      if (file.size > MAX_FILE_SIZE) {
        setUploadError(
          `File too large. Maximum size is ${formatFileSize(MAX_FILE_SIZE)}`
        );
        return;
      }

      if (!Object.keys(ACCEPTED_TYPES).includes(file.type)) {
        setUploadError(
          "Invalid file type. Please upload PNG, JPG, or SVG images."
        );
        return;
      }

      onLogoChange(file);
    }
  };

  return (
    <div className="space-y-4">
      <Label className="text-sm font-medium">Logo Upload (Optional)</Label>

      {/* Upload Area */}
      {!logoFile ? (
        <Card
          className={`border-2 border-dashed transition-colors ${
            isDragActive
              ? isDragReject
                ? "border-red-500 bg-red-50"
                : "border-blue-500 bg-blue-50"
              : "border-muted-foreground/25 hover:border-muted-foreground/50"
          } ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
        >
          <CardContent className="p-6">
            <div {...getRootProps()} className="text-center">
              <input {...getInputProps()} />

              <div className="mx-auto w-12 h-12 bg-muted rounded-lg flex items-center justify-center mb-4">
                <Upload className="h-6 w-6 text-muted-foreground" />
              </div>

              <div className="space-y-2">
                <h3 className="font-medium text-sm">
                  {isDragActive ? "Drop your logo here..." : "Upload Logo"}
                </h3>
                <p className="text-xs text-muted-foreground">
                  Drag & drop or click to select
                </p>
                <p className="text-xs text-muted-foreground">
                  PNG, JPG, or SVG • Max {formatFileSize(MAX_FILE_SIZE)}
                </p>
              </div>

              <Button
                type="button"
                variant="outline"
                size="sm"
                className="mt-4"
                disabled={disabled}
              >
                <FileImage className="h-4 w-4 mr-2" />
                Choose File
              </Button>
            </div>

            {/* Manual file input fallback */}
            <input
              type="file"
              accept={Object.keys(ACCEPTED_TYPES).join(",")}
              onChange={handleFileInput}
              className="hidden"
              id="logo-file-input"
              disabled={disabled}
            />
          </CardContent>
        </Card>
      ) : (
        /* Logo Preview */
        <Card>
          <CardContent className="p-4">
            <div className="flex items-start gap-4">
              {/* Preview Image */}
              <div className="flex-shrink-0">
                {logoPreview ? (
                  <img
                    src={logoPreview}
                    alt="Logo preview"
                    className="w-16 h-16 object-contain bg-gray-50 rounded border"
                  />
                ) : (
                  <div className="w-16 h-16 bg-gray-100 rounded border flex items-center justify-center">
                    <ImageIcon className="h-6 w-6 text-gray-400" />
                  </div>
                )}
              </div>

              {/* File Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium truncate">
                      {logoFile.name}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatFileSize(logoFile.size)} • {logoFile.type}
                    </p>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={clearLogo}
                    className="flex-shrink-0"
                    disabled={disabled}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Upload Error */}
      {uploadError && (
        <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 p-3 rounded border border-red-200">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          {uploadError}
        </div>
      )}

      {/* Logo Customization - only show when logo is uploaded */}
      {logoFile && (
        <div className="space-y-4 pt-2 border-t">
          <h4 className="text-sm font-medium">Logo Settings</h4>

          {/* Logo Scale */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="logo-scale" className="text-sm">
                Logo Size
              </Label>
              <span className="text-xs text-muted-foreground">
                {Math.round(logoScale * 100)}%
              </span>
            </div>
            <Slider
              id="logo-scale"
              value={[logoScale]}
              onValueChange={(value) => onLogoScaleChange(value[0])}
              min={0.05}
              max={0.35}
              step={0.01}
              disabled={disabled}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground">
              Adjust the logo size relative to the QR code
            </p>
          </div>

          {/* Background Padding */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="bg-padding" className="text-sm">
                Background Padding
              </Label>
              <span className="text-xs text-muted-foreground">
                {bgPadding}px
              </span>
            </div>
            <Slider
              id="bg-padding"
              value={[bgPadding]}
              onValueChange={(value) => onBgPaddingChange(value[0])}
              min={0}
              max={50}
              step={1}
              disabled={disabled}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground">
              White space around the logo
            </p>
          </div>

          {/* Background Radius */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="bg-radius" className="text-sm">
                Background Roundness
              </Label>
              <span className="text-xs text-muted-foreground">
                {bgRadius}px
              </span>
            </div>
            <Slider
              id="bg-radius"
              value={[bgRadius]}
              onValueChange={(value) => onBgRadiusChange(value[0])}
              min={0}
              max={50}
              step={1}
              disabled={disabled}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground">
              Corner radius of the logo background
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
