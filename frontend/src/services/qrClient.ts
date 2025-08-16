/**
 * QR Studio API Client
 *
 * Handles all communication with the backend QR generation service
 */

import axios, { AxiosInstance, AxiosResponse } from "axios";
import {
  QRGenerationRequest,
  QRPresets,
  QRStylesResponse,
  URLValidationResponse,
} from "../types/qr";

class QRApiClient {
  private client: AxiosInstance;
  private baseURL: string;

  constructor(baseURL: string = "http://localhost:8000") {
    this.baseURL = baseURL;
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000, // 30 second timeout for QR generation
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Request interceptor for debugging in development
    if (process.env.NODE_ENV === "development") {
      this.client.interceptors.request.use(
        (config) => {
          console.log(`[QR API] ${config.method?.toUpperCase()} ${config.url}`);
          return config;
        },
        (error) => {
          console.error("[QR API] Request error:", error);
          return Promise.reject(error);
        }
      );
    }

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => {
        if (process.env.NODE_ENV === "development") {
          console.log(
            `[QR API] Response: ${response.status} ${response.config.url}`
          );
        }
        return response;
      },
      (error) => {
        console.error(
          "[QR API] Response error:",
          error.response?.data || error.message
        );

        // Transform API errors into user-friendly messages
        if (error.response?.status === 413) {
          throw new Error("File too large. Please use a smaller logo image.");
        } else if (error.response?.status === 400) {
          throw new Error(
            error.response.data?.error || "Invalid request parameters."
          );
        } else if (error.response?.status === 422) {
          const details = error.response.data?.details;
          if (details && Array.isArray(details)) {
            const firstError = details[0];
            throw new Error(
              `Validation error: ${firstError.msg || "Invalid input"}`
            );
          }
          throw new Error("Validation failed. Please check your inputs.");
        } else if (error.response?.status >= 500) {
          throw new Error("Server error. Please try again later.");
        } else if (error.code === "ECONNABORTED") {
          throw new Error("Request timeout. The QR generation took too long.");
        } else if (!error.response) {
          if (error.code === "ERR_NETWORK") {
            throw new Error(
              "Cannot connect to server. Please check if the backend is running."
            );
          }
          throw new Error("Network error. Please check your connection.");
        }

        throw new Error(
          error.response?.data?.error || "An unexpected error occurred."
        );
      }
    );
  }

  /**
   * Generate QR code with optional logo
   */
  async generateQR(
    request: QRGenerationRequest,
    logoFile?: File
  ): Promise<Blob> {
    try {
      const formData = new FormData();

      // Add all configuration parameters to form data
      Object.entries(request).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          formData.append(key, value.toString());
        }
      });

      // Add logo file if provided
      if (logoFile) {
        formData.append("logo", logoFile);
      }

      const response = await this.client.post(
        "/api/v1/qr/generate-form",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
          responseType: "blob",
        }
      );

      return response.data;
    } catch (error) {
      console.error("QR generation failed:", error);
      throw error;
    }
  }

  /**
   * Get available QR styling presets
   */
  async getPresets(): Promise<QRPresets> {
    try {
      const response: AxiosResponse<QRPresets> = await this.client.get(
        "/api/v1/qr/presets"
      );
      return response.data;
    } catch (error) {
      console.error("Failed to fetch presets:", error);
      throw new Error("Failed to load QR styling presets.");
    }
  }

  /**
   * Get available styles and configuration options
   */
  async getStyles(): Promise<QRStylesResponse> {
    try {
      const response: AxiosResponse<QRStylesResponse> = await this.client.get(
        "/api/v1/qr/styles"
      );
      return response.data;
    } catch (error) {
      console.error("Failed to fetch styles:", error);
      throw new Error("Failed to load QR styling options.");
    }
  }

  /**
   * Validate a URL for QR code generation
   */
  async validateURL(url: string): Promise<URLValidationResponse> {
    try {
      const response: AxiosResponse<URLValidationResponse> =
        await this.client.get("/api/v1/qr/validate-url", {
          params: { url },
        });
      return response.data;
    } catch (error) {
      console.error("URL validation failed:", error);
      // Return a basic validation response if the API fails
      return {
        valid: url.length > 0 && url.length <= 2000,
        error:
          url.length === 0
            ? "URL is required"
            : url.length > 2000
            ? "URL too long"
            : undefined,
        url,
      };
    }
  }

  /**
   * Check API health
   */
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    try {
      const response = await this.client.get("/health");
      return response.data;
    } catch (error) {
      console.error("Health check failed:", error);
      throw new Error("API is not available.");
    }
  }

  /**
   * Download QR code as file
   */
  async downloadQR(
    request: QRGenerationRequest,
    logoFile?: File,
    filename?: string
  ): Promise<void> {
    try {
      const blob = await this.generateQR(request, logoFile);

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download =
        filename ||
        `qr_code_${request.size || 1024}x${request.size || 1024}.png`;

      // Trigger download
      document.body.appendChild(link);
      link.click();

      // Cleanup
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("QR download failed:", error);
      throw error;
    }
  }

  /**
   * Create preview URL from blob
   */
  createPreviewURL(blob: Blob): string {
    return window.URL.createObjectURL(blob);
  }

  /**
   * Cleanup preview URL
   */
  revokePreviewURL(url: string): void {
    window.URL.revokeObjectURL(url);
  }
}

// Create and export singleton instance
export const qrClient = new QRApiClient();

// Export class for testing
export default QRApiClient;
