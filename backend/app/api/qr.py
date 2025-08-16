"""
QR Code Generation API Endpoints
"""

import io
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator

from ..services.qr_generator import QRConfig, qr_service
from ..core.config import settings
from ..core.exceptions import (
    BadRequestException,
    ValidationException,
    FileUploadException,
    QRGenerationException,
)
from ..core.validators import (
    validate_url,
    validate_color,
    validate_file_upload,
    validate_qr_size,
    validate_border,
    validate_float_range,
    validate_enum_choice,
)
from ..core.security import sanitize_input, FileUploadSecurity
from ..core.cache import qr_cache


router = APIRouter(tags=["qr"])
logger = logging.getLogger(__name__)


class QRGenerationRequest(BaseModel):
    """Request model for QR generation with comprehensive validation"""

    url: str = Field(
        ..., description="URL or text to encode in QR code", max_length=2000
    )
    size: int = Field(
        1024,
        description="QR code size in pixels",
        ge=settings.MIN_QR_SIZE,
        le=settings.MAX_QR_SIZE,
    )
    border: int = Field(4, description="Border size in modules", ge=0, le=20)
    style: str = Field("rounded", description="QR module style")
    dark_color: str = Field("#000000", description="Foreground color (hex format)")
    light_color: str = Field("#FFFFFF", description="Background color (hex format)")
    ec_level: str = Field("Q", description="Error correction level")
    eye_radius: float = Field(0.9, description="Eye corner radius", ge=0.0, le=1.0)
    eye_scale_x: float = Field(1.0, description="Eye horizontal scale", ge=0.5, le=2.0)
    eye_scale_y: float = Field(1.0, description="Eye vertical scale", ge=0.5, le=2.0)
    eye_shape: str = Field("rect", description="Eye shape")
    eye_style: str = Field("standard", description="Eye style")
    logo_scale: float = Field(0.22, description="Logo scale factor", ge=0.1, le=0.5)
    bg_padding: int = Field(20, description="Background padding", ge=0, le=100)
    bg_radius: int = Field(28, description="Background corner radius", ge=0, le=100)
    qr_radius: int = Field(0, description="QR module corner radius", ge=0, le=20)
    compress_level: int = Field(9, description="PNG compression level", ge=0, le=9)
    quantize_colors: int = Field(64, description="Color quantization", ge=2, le=256)

    @validator("url")
    def validate_url_field(cls, v: str) -> str:
        # Sanitize input first
        sanitized_url = sanitize_input(v, max_length=2000, allow_html=False)

        # Then validate
        is_valid, error, warning = validate_url(sanitized_url)
        if not is_valid:
            raise ValueError(error)
        return sanitized_url

    @validator("style")
    def validate_style_field(cls, v: str) -> str:
        valid_styles = [
            "square",
            "gapped",
            "dots",
            "rounded",
            "bars-vertical",
            "bars-horizontal",
        ]
        return validate_enum_choice(v, "style", valid_styles)

    @validator("ec_level")
    def validate_ec_level_field(cls, v: str) -> str:
        return validate_enum_choice(v, "ec_level", ["L", "M", "Q", "H"])

    @validator("eye_shape")
    def validate_eye_shape_field(cls, v: str) -> str:
        return validate_enum_choice(v, "eye_shape", ["rect", "rounded", "circle"])

    @validator("eye_style")
    def validate_eye_style_field(cls, v: str) -> str:
        return validate_enum_choice(v, "eye_style", ["standard", "circle-ring"])

    @validator("dark_color")
    def validate_dark_color(cls, v: str) -> str:
        return validate_color(v, "dark_color")

    @validator("light_color")
    def validate_light_color(cls, v: str) -> str:
        return validate_color(v, "light_color")


class QRGenerationResponse(BaseModel):
    """Response model for QR generation"""

    message: str
    size: int
    format: str = "PNG"


@router.post("/generate", response_class=StreamingResponse)
async def generate_qr(
    request: QRGenerationRequest, logo: Optional[UploadFile] = File(None)
) -> StreamingResponse:
    """
    Generate a QR code with optional logo overlay

    Returns the QR code as a PNG image stream.

    Raises:
        BadRequestException: Invalid request parameters
        FileUploadException: Logo file validation failed
        QRGenerationException: QR code generation failed
    """
    logger.info(
        f"QR generation request: {request.url[:50]}{'...' if len(request.url) > 50 else ''}"
    )

    try:
        # Validate and process logo file if provided
        logo_data = None
        if logo:
            if not logo.filename:
                raise FileUploadException("Logo file must have a filename")

            if not logo.content_type:
                raise FileUploadException("Logo file content type is required")

            # Sanitize filename
            safe_filename = FileUploadSecurity.validate_filename(logo.filename)
            logger.debug(f"Processing logo file: {safe_filename} ({logo.content_type})")

            # Read file content
            logo_content = await logo.read()

            # Security scan
            if not FileUploadSecurity.scan_file_content(logo_content, safe_filename):
                raise FileUploadException(
                    "File failed security scan", details={"filename": safe_filename}
                )

            # Validate file
            validate_file_upload(logo_content, safe_filename, logo.content_type)
            logo_data = logo_content

        # Create QR configuration
        config = QRConfig(
            url=request.url,
            size=request.size,
            border=request.border,
            style=request.style,
            dark_color=request.dark_color,
            light_color=request.light_color,
            ec_level=request.ec_level,
            eye_radius=request.eye_radius,
            eye_scale_x=request.eye_scale_x,
            eye_scale_y=request.eye_scale_y,
            eye_shape=request.eye_shape,
            eye_style=request.eye_style,
            logo_scale=request.logo_scale,
            bg_padding=request.bg_padding,
            bg_radius=request.bg_radius,
            qr_radius=request.qr_radius,
            compress_level=request.compress_level,
            quantize_colors=request.quantize_colors,
        )

        # Check cache first
        logo_hash = None
        if logo_data:
            logo_hash = qr_cache.generate_logo_hash(logo_data)

        config_dict = {
            "url": config.url,
            "size": config.size,
            "border": config.border,
            "style": config.style,
            "dark_color": config.dark_color,
            "light_color": config.light_color,
            "ec_level": config.ec_level,
            "eye_radius": config.eye_radius,
            "eye_scale_x": config.eye_scale_x,
            "eye_scale_y": config.eye_scale_y,
            "eye_shape": config.eye_shape,
            "eye_style": config.eye_style,
            "logo_scale": config.logo_scale,
            "bg_padding": config.bg_padding,
            "bg_radius": config.bg_radius,
            "qr_radius": config.qr_radius,
            "compress_level": config.compress_level,
            "quantize_colors": config.quantize_colors,
        }
        cached_qr = await qr_cache.get_qr_code(config_dict, logo_hash)

        if cached_qr:
            logger.info(f"QR code served from cache, size: {len(cached_qr)} bytes")
            qr_bytes = cached_qr
        else:
            # Generate QR code
            logger.debug("Starting QR code generation")
            qr_bytes = await qr_service.generate_qr_with_logo(config, logo_data)

            if not qr_bytes:
                raise QRGenerationException("QR code generation returned empty result")

            # Cache the result
            await qr_cache.set_qr_code(config_dict, qr_bytes, logo_hash)
            logger.info(f"QR code generated and cached, size: {len(qr_bytes)} bytes")

        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(qr_bytes),
            media_type="image/png",
            headers={
                "Content-Disposition": f"attachment; filename=qr_code_{request.size}x{request.size}.png",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )

    except (BadRequestException, FileUploadException, QRGenerationException):
        # Re-raise custom exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in QR generation: {str(e)}", exc_info=True)
        raise QRGenerationException(f"Failed to generate QR code: {str(e)}")


@router.post("/generate-form", response_class=StreamingResponse)
async def generate_qr_form(
    url: str = Form(...),
    size: int = Form(1024),
    border: int = Form(4),
    style: str = Form("rounded"),
    dark_color: str = Form("#000000"),
    light_color: str = Form("#FFFFFF"),
    ec_level: str = Form("Q"),
    eye_radius: float = Form(0.9),
    eye_scale_x: float = Form(1.0),
    eye_scale_y: float = Form(1.0),
    eye_shape: str = Form("rect"),
    eye_style: str = Form("standard"),
    logo_scale: float = Form(0.22),
    bg_padding: int = Form(20),
    bg_radius: int = Form(28),
    qr_radius: int = Form(0),
    compress_level: int = Form(9),
    quantize_colors: int = Form(64),
    logo: Optional[UploadFile] = File(None),
) -> StreamingResponse:
    """
    Generate a QR code using form data (alternative endpoint for form submissions)
    """
    # Create request object from form data
    request = QRGenerationRequest(
        url=url,
        size=size,
        border=border,
        style=style,
        dark_color=dark_color,
        light_color=light_color,
        ec_level=ec_level,
        eye_radius=eye_radius,
        eye_scale_x=eye_scale_x,
        eye_scale_y=eye_scale_y,
        eye_shape=eye_shape,
        eye_style=eye_style,
        logo_scale=logo_scale,
        bg_padding=bg_padding,
        bg_radius=bg_radius,
        qr_radius=qr_radius,
        compress_level=compress_level,
        quantize_colors=quantize_colors,
    )

    # Use the main generation function
    return await generate_qr(request, logo)


@router.get("/presets")
async def get_presets() -> dict[str, dict[str, Any]]:
    """
    Get available QR styling presets
    """
    try:
        # Check cache first
        cached_presets = await qr_cache.get_presets()
        if cached_presets:
            logger.debug("Presets served from cache")
            return cached_presets["presets"]  # type: ignore

        # Generate presets
        presets = qr_service.get_preset_configs()

        # Convert to serializable format
        preset_data = {}
        for name, config in presets.items():
            preset_data[name] = {
                "name": name.title(),
                "description": f"{name.title()} QR code style",
                "config": {
                    "style": config.style,
                    "dark_color": config.dark_color,
                    "light_color": config.light_color,
                    "eye_shape": config.eye_shape,
                    "eye_style": config.eye_style,
                    "bg_radius": config.bg_radius,
                    "border": config.border,
                },
            }

        # Cache the result
        await qr_cache.set_presets(preset_data)
        logger.debug("Presets generated and cached")

        return preset_data

    except Exception as e:
        logger.error(f"Failed to get presets: {str(e)}", exc_info=True)
        raise QRGenerationException(f"Failed to get presets: {str(e)}")


@router.get("/styles")
async def get_available_styles() -> dict[str, Any]:
    """
    Get available QR styles and options
    """
    return {
        "styles": [
            "square",
            "gapped",
            "dots",
            "rounded",
            "bars-vertical",
            "bars-horizontal",
        ],
        "eye_shapes": ["rect", "rounded", "circle"],
        "eye_styles": ["standard", "circle-ring"],
        "error_correction_levels": ["L", "M", "Q", "H"],
        "size_limits": {"min": settings.MIN_QR_SIZE, "max": settings.MAX_QR_SIZE},
        "file_limits": {
            "max_size_mb": settings.MAX_FILE_SIZE / (1024 * 1024),
            "allowed_types": settings.ALLOWED_IMAGE_TYPES,
        },
    }


@router.get("/validate-url")
async def validate_url_endpoint(url: str) -> dict[str, Any]:
    """
    Validate a URL for QR code generation

    Args:
        url: URL to validate

    Returns:
        Validation result with status, warnings, and suggestions
    """
    logger.debug(f"Validating URL: {url[:100]}{'...' if len(url) > 100 else ''}")

    try:
        # Check cache first
        cached_validation = await qr_cache.get_url_validation(url)
        if cached_validation:
            logger.debug("URL validation served from cache")
            return {k: v for k, v in cached_validation.items() if k != "cached_at"}

        # Perform validation
        is_valid, error_message, warning_message = validate_url(url)

        result = {
            "valid": is_valid,
            "url": url.strip() if url else "",
            "length": len(url) if url else 0,
            "max_length": 2000,
        }

        if error_message:
            result["error"] = error_message

        if warning_message:
            result["warning"] = warning_message

        # Add suggestions for common issues
        if not is_valid and url:
            suggestions = []

            # Suggest adding protocol
            if not any(
                url.lower().startswith(p)
                for p in ["http://", "https://", "mailto:", "tel:"]
            ):
                if "." in url and not url.startswith("www."):
                    suggestions.append(f"https://{url}")
                elif url.startswith("www."):
                    suggestions.append(f"https://{url}")

            if suggestions:
                result["suggestions"] = suggestions

        # Cache the result
        await qr_cache.set_url_validation(url, result)

        logger.debug(f"URL validation result: {result['valid']}")
        return result

    except Exception as e:
        logger.error(f"Error validating URL: {str(e)}", exc_info=True)
        return {
            "valid": False,
            "error": "Failed to validate URL",
            "url": url if url else "",
        }
