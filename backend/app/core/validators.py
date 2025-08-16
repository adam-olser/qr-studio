"""
Validation utilities for QR Studio
"""

import re
import mimetypes
from typing import Optional, Tuple, List
from urllib.parse import urlparse
from PIL import Image
import io

from .exceptions import ValidationError, FileProcessingError
from .config import settings


def validate_url(url: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate URL for QR code generation

    Returns:
        Tuple of (is_valid, error_message, warning_message)
    """
    if not url:
        return False, "URL is required", None

    if not isinstance(url, str):
        return False, "URL must be a string", None

    # Check length
    if len(url) > 2000:
        return False, "URL too long (maximum 2000 characters)", None

    if len(url.strip()) == 0:
        return False, "URL cannot be empty", None

    url = url.strip()

    # Check for common protocols
    valid_protocols = [
        "http://",
        "https://",
        "mailto:",
        "tel:",
        "sms:",
        "ftp://",
        "smb://",
        "file://",
        "app://",
        "intent://",
        "market://",
        "whatsapp://",
        "telegram://",
        "skype:",
        "zoom://",
    ]

    has_protocol = any(url.lower().startswith(protocol) for protocol in valid_protocols)

    if not has_protocol:
        # Check if it looks like a domain/URL without protocol
        if re.match(r"^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?\.[a-zA-Z]{2,}", url):
            return (
                True,
                None,
                "URL may not be clickable without a protocol (http://, https://, etc.)",
            )

        # Allow plain text for QR codes (common use case)
        return True, None, "Plain text will be encoded as-is in the QR code"

    # Validate URLs with protocols
    if url.startswith(("http://", "https://")):
        try:
            parsed = urlparse(url)
            if not parsed.netloc:
                return False, "Invalid URL format", None

            # Check for suspicious characters
            if any(char in url for char in ['"', "'", "<", ">", "`"]):
                return False, "URL contains potentially unsafe characters", None

        except Exception:
            return False, "Invalid URL format", None

    return True, None, None


def validate_color(color: str, field_name: str = "color") -> str:
    """
    Validate hex color format

    Args:
        color: Color string to validate
        field_name: Name of the field for error messages

    Returns:
        Normalized color string

    Raises:
        ValidationError: If color format is invalid
    """
    if not color:
        raise ValidationError(f"{field_name} is required", field_name)

    if not isinstance(color, str):
        raise ValidationError(f"{field_name} must be a string", field_name)

    color = color.strip()

    # Add # if missing
    if not color.startswith("#"):
        color = f"#{color}"

    # Validate hex format
    if not re.match(r"^#[0-9A-Fa-f]{6}$", color):
        raise ValidationError(
            f"{field_name} must be a valid hex color (e.g., #FF0000 or #ff0000)",
            field_name,
        )

    return color.upper()


def validate_file_upload(file_content: bytes, filename: str, content_type: str) -> None:
    """
    Validate uploaded file

    Args:
        file_content: File content bytes
        filename: Original filename
        content_type: MIME content type

    Raises:
        FileProcessingError: If file validation fails
    """
    # Check file size
    if len(file_content) > settings.MAX_FILE_SIZE:
        raise FileProcessingError(
            f"File too large. Maximum size: {settings.MAX_FILE_SIZE / (1024 * 1024):.1f}MB",
            filename,
            len(file_content),
        )

    # Check content type
    if content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise FileProcessingError(
            f"Invalid file type '{content_type}'. Allowed types: {', '.join(settings.ALLOWED_IMAGE_TYPES)}",
            filename,
        )

    # Verify file is actually an image by trying to open it
    try:
        with Image.open(io.BytesIO(file_content)) as img:
            # Check image dimensions
            width, height = img.size
            if width > 2048 or height > 2048:
                raise FileProcessingError(
                    "Image dimensions too large. Maximum: 2048x2048 pixels", filename
                )

            if width < 32 or height < 32:
                raise FileProcessingError(
                    "Image dimensions too small. Minimum: 32x32 pixels", filename
                )

            # Check for potential issues
            if img.mode not in ["RGB", "RGBA", "L", "P"]:
                raise FileProcessingError(
                    f"Unsupported image mode '{img.mode}'. Supported: RGB, RGBA, L, P",
                    filename,
                )

    except Exception as e:
        if isinstance(e, FileProcessingError):
            raise
        raise FileProcessingError(f"Invalid image file: {str(e)}", filename)


def validate_qr_size(size: int) -> int:
    """
    Validate QR code size

    Args:
        size: QR code size in pixels

    Returns:
        Validated size

    Raises:
        ValidationError: If size is invalid
    """
    if not isinstance(size, int):
        try:
            size = int(size)
        except (ValueError, TypeError):
            raise ValidationError("Size must be an integer", "size")

    if not (settings.MIN_QR_SIZE <= size <= settings.MAX_QR_SIZE):
        raise ValidationError(
            f"Size must be between {settings.MIN_QR_SIZE} and {settings.MAX_QR_SIZE} pixels",
            "size",
        )

    return size


def validate_border(border: int) -> int:
    """
    Validate QR code border size

    Args:
        border: Border size in modules

    Returns:
        Validated border size

    Raises:
        ValidationError: If border is invalid
    """
    if not isinstance(border, int):
        try:
            border = int(border)
        except (ValueError, TypeError):
            raise ValidationError("Border must be an integer", "border")

    if not (0 <= border <= 20):
        raise ValidationError("Border must be between 0 and 20 modules", "border")

    return border


def validate_float_range(
    value: float, field_name: str, min_val: float, max_val: float
) -> float:
    """
    Validate float value within range

    Args:
        value: Value to validate
        field_name: Field name for error messages
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        Validated float value

    Raises:
        ValidationError: If value is invalid
    """
    if not isinstance(value, (int, float)):
        try:
            value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be a number", field_name)

    if not (min_val <= value <= max_val):
        raise ValidationError(
            f"{field_name} must be between {min_val} and {max_val}", field_name
        )

    return float(value)


def validate_enum_choice(value: str, field_name: str, choices: List[str]) -> str:
    """
    Validate enum choice

    Args:
        value: Value to validate
        field_name: Field name for error messages
        choices: List of valid choices

    Returns:
        Validated choice

    Raises:
        ValidationError: If choice is invalid
    """
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string", field_name)

    if value not in choices:
        raise ValidationError(
            f"{field_name} must be one of: {', '.join(choices)}", field_name
        )

    return value
