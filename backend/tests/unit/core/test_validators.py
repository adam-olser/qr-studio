"""
Unit tests for core validators
"""

import pytest
from app.core.validators import (
    validate_url,
    validate_color,
    validate_file_upload,
    validate_qr_size,
    validate_border,
    validate_float_range,
    validate_enum_choice,
)
from app.core.exceptions import ValidationError, FileProcessingError
from tests.conftest import (
    VALID_URLS,
    INVALID_URLS,
    VALID_HEX_COLORS,
    INVALID_HEX_COLORS,
)


class TestValidateUrl:
    """Test URL validation."""

    @pytest.mark.parametrize("url", VALID_URLS)
    def test_valid_urls(self, url: str):
        """Test that valid URLs pass validation."""
        is_valid, error, warning = validate_url(url)
        assert is_valid is True
        assert error is None

    @pytest.mark.parametrize("url", INVALID_URLS)
    def test_invalid_urls(self, url: str):
        """Test that invalid URLs fail validation."""
        is_valid, error, warning = validate_url(url)
        assert is_valid is False
        assert error is not None
        assert isinstance(error, str)

    def test_url_without_protocol_warning(self):
        """Test that URLs without protocol get a warning."""
        is_valid, error, warning = validate_url("example.com")
        assert is_valid is True
        assert error is None
        assert warning is not None
        assert "protocol" in warning.lower()

    def test_plain_text_warning(self):
        """Test that plain text gets a warning."""
        is_valid, error, warning = validate_url("Hello World")
        assert is_valid is True
        assert error is None
        assert warning is not None
        assert "plain text" in warning.lower()

    def test_empty_url(self):
        """Test empty URL validation."""
        is_valid, error, warning = validate_url("")
        assert is_valid is False
        assert "required" in error.lower()

    def test_non_string_url(self):
        """Test non-string URL validation."""
        is_valid, error, warning = validate_url(123)  # type: ignore
        assert is_valid is False
        assert "string" in error.lower()


class TestValidateColor:
    """Test color validation."""

    @pytest.mark.parametrize("color", VALID_HEX_COLORS)
    def test_valid_colors(self, color: str):
        """Test that valid hex colors pass validation."""
        result = validate_color(color, "test_color")
        assert result == color.upper()

    @pytest.mark.parametrize("color", INVALID_HEX_COLORS)
    def test_invalid_colors(self, color: str):
        """Test that invalid hex colors raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_color(color, "test_color")
        assert "test_color" in str(exc_info.value)

    def test_color_without_hash(self):
        """Test that colors without # get it added."""
        result = validate_color("FF0000", "test_color")
        assert result == "#FF0000"

    def test_lowercase_color(self):
        """Test that lowercase colors get uppercased."""
        result = validate_color("#ff0000", "test_color")
        assert result == "#FF0000"

    def test_empty_color(self):
        """Test empty color validation."""
        with pytest.raises(ValidationError) as exc_info:
            validate_color("", "test_color")
        assert "required" in str(exc_info.value)

    def test_non_string_color(self):
        """Test non-string color validation."""
        with pytest.raises(ValidationError):
            validate_color(123, "test_color")  # type: ignore


class TestValidateFileUpload:
    """Test file upload validation."""

    def test_valid_image_file(self, sample_logo_bytes: bytes):
        """Test valid image file validation."""
        # Should not raise any exception
        validate_file_upload(sample_logo_bytes, "test.png", "image/png")

    def test_invalid_file_content(self, invalid_image_bytes: bytes):
        """Test invalid file content validation."""
        with pytest.raises(FileProcessingError) as exc_info:
            validate_file_upload(invalid_image_bytes, "test.png", "image/png")
        assert "Invalid image file" in str(exc_info.value)

    def test_file_too_large(self, large_image_bytes: bytes):
        """Test file size limit validation."""
        with pytest.raises(FileProcessingError) as exc_info:
            validate_file_upload(large_image_bytes, "large.png", "image/png")
        assert "too large" in str(exc_info.value).lower()

    def test_invalid_content_type(self, sample_logo_bytes: bytes):
        """Test invalid content type validation."""
        with pytest.raises(FileProcessingError) as exc_info:
            validate_file_upload(sample_logo_bytes, "test.txt", "text/plain")
        assert "Invalid file type" in str(exc_info.value)

    def test_empty_file(self):
        """Test empty file validation."""
        with pytest.raises(FileProcessingError) as exc_info:
            validate_file_upload(b"", "test.png", "image/png")
        assert "too large" in str(exc_info.value).lower()


class TestValidateQrSize:
    """Test QR size validation."""

    def test_valid_sizes(self):
        """Test valid QR sizes."""
        valid_sizes = [256, 512, 1024, 2048]
        for size in valid_sizes:
            result = validate_qr_size(size)
            assert result == size

    def test_size_as_string(self):
        """Test QR size validation with string input."""
        result = validate_qr_size("512")
        assert result == 512

    def test_size_too_small(self):
        """Test QR size too small."""
        with pytest.raises(ValidationError) as exc_info:
            validate_qr_size(50)
        assert "between" in str(exc_info.value)

    def test_size_too_large(self):
        """Test QR size too large."""
        with pytest.raises(ValidationError) as exc_info:
            validate_qr_size(5000)
        assert "between" in str(exc_info.value)

    def test_invalid_size_type(self):
        """Test invalid size type."""
        with pytest.raises(ValidationError) as exc_info:
            validate_qr_size("not-a-number")
        assert "integer" in str(exc_info.value)


class TestValidateBorder:
    """Test border validation."""

    def test_valid_borders(self):
        """Test valid border sizes."""
        valid_borders = [0, 4, 10, 20]
        for border in valid_borders:
            result = validate_border(border)
            assert result == border

    def test_border_as_string(self):
        """Test border validation with string input."""
        result = validate_border("4")
        assert result == 4

    def test_border_too_large(self):
        """Test border too large."""
        with pytest.raises(ValidationError) as exc_info:
            validate_border(25)
        assert "between 0 and 20" in str(exc_info.value)

    def test_negative_border(self):
        """Test negative border."""
        with pytest.raises(ValidationError) as exc_info:
            validate_border(-1)
        assert "between 0 and 20" in str(exc_info.value)


class TestValidateFloatRange:
    """Test float range validation."""

    def test_valid_float_values(self):
        """Test valid float values."""
        result = validate_float_range(0.5, "test_field", 0.0, 1.0)
        assert result == 0.5

    def test_float_as_string(self):
        """Test float validation with string input."""
        result = validate_float_range("0.75", "test_field", 0.0, 1.0)
        assert result == 0.75

    def test_float_out_of_range_low(self):
        """Test float value too low."""
        with pytest.raises(ValidationError) as exc_info:
            validate_float_range(-0.5, "test_field", 0.0, 1.0)
        assert "between 0.0 and 1.0" in str(exc_info.value)

    def test_float_out_of_range_high(self):
        """Test float value too high."""
        with pytest.raises(ValidationError) as exc_info:
            validate_float_range(1.5, "test_field", 0.0, 1.0)
        assert "between 0.0 and 1.0" in str(exc_info.value)

    def test_invalid_float_type(self):
        """Test invalid float type."""
        with pytest.raises(ValidationError) as exc_info:
            validate_float_range("not-a-number", "test_field", 0.0, 1.0)
        assert "number" in str(exc_info.value)


class TestValidateEnumChoice:
    """Test enum choice validation."""

    def test_valid_enum_choices(self):
        """Test valid enum choices."""
        choices = ["option1", "option2", "option3"]
        for choice in choices:
            result = validate_enum_choice(choice, "test_field", choices)
            assert result == choice

    def test_invalid_enum_choice(self):
        """Test invalid enum choice."""
        choices = ["option1", "option2", "option3"]
        with pytest.raises(ValidationError) as exc_info:
            validate_enum_choice("invalid", "test_field", choices)
        assert "must be one of" in str(exc_info.value)
        assert "option1, option2, option3" in str(exc_info.value)

    def test_non_string_enum_choice(self):
        """Test non-string enum choice."""
        choices = ["option1", "option2", "option3"]
        with pytest.raises(ValidationError) as exc_info:
            validate_enum_choice(123, "test_field", choices)  # type: ignore
        assert "string" in str(exc_info.value)
