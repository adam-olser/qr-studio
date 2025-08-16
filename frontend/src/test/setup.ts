import "@testing-library/jest-dom";

// Mock URL.createObjectURL and URL.revokeObjectURL
global.URL.createObjectURL = vi.fn(() => "mock-blob-url");
global.URL.revokeObjectURL = vi.fn();

// Mock fetch for API calls
global.fetch = vi.fn();

// Mock file reader
Object.defineProperty(global, "FileReader", {
  writable: true,
  value: vi.fn().mockImplementation(() => ({
    readAsDataURL: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  })),
});
