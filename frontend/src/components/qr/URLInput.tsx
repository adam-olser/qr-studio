/**
 * URL Input Component
 *
 * Handles URL input with validation and real-time feedback
 */

import React, { useState } from "react";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Button } from "../ui/button";
import { AlertCircle, CheckCircle, ExternalLink, Globe } from "lucide-react";
import { URLValidationResponse } from "../../types/qr";

interface URLInputProps {
  value: string;
  onChange: (value: string) => void;
  validation?: URLValidationResponse | null;
  isValidating?: boolean;
  placeholder?: string;
  disabled?: boolean;
}

const URL_EXAMPLES = [
  "https://example.com",
  "https://kiwicom.github.io",
  "mailto:hello@example.com",
  "tel:+1234567890",
  "https://maps.google.com/?q=Prague",
];

export function URLInput({
  value,
  onChange,
  validation,
  isValidating = false,
  placeholder = "Enter URL or text to encode...",
  disabled = false,
}: URLInputProps) {
  const [isFocused, setIsFocused] = useState(false);
  const [showExamples, setShowExamples] = useState(false);

  // Note: Validation is handled by the parent component to avoid duplicate debouncing

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    onChange(newValue);
  };

  const handleExampleClick = (example: string) => {
    onChange(example);
    setShowExamples(false);
  };

  const getValidationIcon = () => {
    if (isValidating) {
      return (
        <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full" />
      );
    }

    if (validation?.valid) {
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    }

    if (validation?.error) {
      return <AlertCircle className="h-4 w-4 text-red-500" />;
    }

    return null;
  };

  const getValidationMessage = () => {
    if (validation?.error) {
      return (
        <div className="flex items-center gap-2 text-sm text-red-600 mt-1">
          <AlertCircle className="h-3 w-3" />
          {validation.error}
        </div>
      );
    }

    if (validation?.warning) {
      return (
        <div className="flex items-center gap-2 text-sm text-yellow-600 mt-1">
          <AlertCircle className="h-3 w-3" />
          {validation.warning}
        </div>
      );
    }

    if (validation?.valid && value.trim()) {
      return (
        <div className="flex items-center gap-2 text-sm text-green-600 mt-1">
          <CheckCircle className="h-3 w-3" />
          URL is valid and ready for QR generation
        </div>
      );
    }

    return null;
  };

  const isWebURL = value.startsWith("http://") || value.startsWith("https://");

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label htmlFor="url-input" className="text-sm font-medium">
          URL or Text to Encode
        </Label>
        {value.trim() && !showExamples && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => setShowExamples(!showExamples)}
            className="text-xs text-muted-foreground hover:text-foreground"
          >
            Show examples
          </Button>
        )}
      </div>

      <div className="relative">
        <div className="flex">
          <div className="relative flex-1">
            <Input
              id="url-input"
              type="text"
              value={value}
              onChange={handleInputChange}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              placeholder={placeholder}
              disabled={disabled}
              className={`pr-10 ${
                validation?.error
                  ? "border-red-500 focus:border-red-500"
                  : validation?.valid
                  ? "border-green-500 focus:border-green-500"
                  : validation?.warning
                  ? "border-yellow-500 focus:border-yellow-500"
                  : ""
              }`}
            />

            {/* Validation icon */}
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
              {getValidationIcon()}
            </div>
          </div>

          {/* Open URL button for web URLs */}
          {isWebURL && value.trim() && (
            <Button
              type="button"
              variant="outline"
              size="icon"
              className="ml-2"
              onClick={() => window.open(value, "_blank")}
              title="Open URL in new tab"
            >
              <ExternalLink className="h-4 w-4" />
            </Button>
          )}
        </div>

        {/* Validation message */}
        {getValidationMessage()}
      </div>

      {/* URL Examples */}
      {(showExamples || (!value.trim() && isFocused)) && (
        <div className="mt-3 p-3 bg-muted/50 rounded-lg border">
          <div className="flex items-center gap-2 mb-2">
            <Globe className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium text-muted-foreground">
              Example URLs:
            </span>
          </div>
          <div className="grid grid-cols-1 gap-1">
            {URL_EXAMPLES.map((example, index) => (
              <button
                key={index}
                type="button"
                onClick={() => handleExampleClick(example)}
                className="text-left text-sm text-blue-600 hover:text-blue-800 hover:underline p-1 rounded transition-colors"
              >
                {example}
              </button>
            ))}
          </div>
          <div className="mt-2 text-xs text-muted-foreground">
            💡 You can encode any text, not just URLs! Try phone numbers, email
            addresses, or plain text.
          </div>
        </div>
      )}

      {/* URL Info */}
      {value.trim() && validation?.valid && (
        <div className="text-xs text-muted-foreground bg-blue-50 p-2 rounded border border-blue-200">
          <div className="flex items-center gap-1">
            <Globe className="h-3 w-3" />
            <span>
              Length: {value.length} characters
              {value.length > 1000 && (
                <span className="text-yellow-600 ml-1">
                  (Large QR codes may be harder to scan)
                </span>
              )}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
