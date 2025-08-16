import { render, screen, fireEvent } from "@testing-library/react";
import { URLInput } from "../URLInput";

describe("URLInput", () => {
  const mockProps = {
    value: "",
    onChange: vi.fn(),
    isValid: false,
    isValidating: false,
    validation: null,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders input field", () => {
    render(<URLInput {...mockProps} />);

    const input = screen.getByPlaceholderText(/enter url or text/i);
    expect(input).toBeInTheDocument();
  });

  it("calls onChange when input value changes", () => {
    render(<URLInput {...mockProps} />);

    const input = screen.getByPlaceholderText(/enter url or text/i);

    fireEvent.change(input, { target: { value: "https://example.com" } });

    expect(mockProps.onChange).toHaveBeenCalledWith("https://example.com");
  });

  it("shows input value", () => {
    render(<URLInput {...mockProps} value="https://example.com" />);

    const input = screen.getByDisplayValue("https://example.com");
    expect(input).toBeInTheDocument();
  });

  it("shows validation error when provided", () => {
    render(
      <URLInput
        {...mockProps}
        value="invalid-url"
        validation={{
          valid: false,
          error: "Invalid URL format",
        }}
      />
    );

    expect(screen.getByText(/invalid url format/i)).toBeInTheDocument();
  });
});
