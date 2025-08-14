from pydantic import BaseModel, HttpUrl, Field, validator
from typing import Optional, Literal
from enum import Enum

class QRStyle(str, Enum):
    SQUARE = "square"
    ROUNDED = "rounded"
    DOTS = "dots"
    GAPPED = "gapped"
    BARS_VERTICAL = "bars-vertical"
    BARS_HORIZONTAL = "bars-horizontal"

class EyeShape(str, Enum):
    RECT = "rect"
    ROUNDED = "rounded"
    CIRCLE = "circle"

class EyeStyle(str, Enum):
    STANDARD = "standard"
    CIRCLE_RING = "circle-ring"

class ErrorCorrectionLevel(str, Enum):
    L = "L"
    M = "M"
    Q = "Q"
    H = "H"

class QRGenerationRequest(BaseModel):
    url: HttpUrl
    size: int = Field(default=1024, ge=200, le=2048)
    style: QRStyle = QRStyle.SQUARE
    eye_shape: EyeShape = EyeShape.RECT
    eye_style: EyeStyle = EyeStyle.STANDARD
    eye_radius: float = Field(default=1.0, ge=0.0, le=5.0)
    eye_scale_x: float = Field(default=1.0, ge=0.5, le=2.0)
    eye_scale_y: float = Field(default=1.0, ge=0.5, le=2.0)
    error_correction: ErrorCorrectionLevel = ErrorCorrectionLevel.M
    logo_scale: float = Field(default=0.2, ge=0.05, le=0.4)
    bg_padding: int = Field(default=20, ge=0, le=50)
    bg_radius: int = Field(default=30, ge=0, le=100)
    qr_radius: int = Field(default=0, ge=0, le=50)
    dark_color: str = Field(default="#000000")
    light_color: str = Field(default="#FFFFFF")
    compress_level: int = Field(default=6, ge=0, le=9)
    quantize_colors: int = Field(default=96, ge=0, le=256)

    @validator('dark_color', 'light_color')
    def validate_hex_color(cls, v):
        if not v.startswith('#') or len(v) != 7:
            raise ValueError('Color must be a valid hex color (e.g., #000000)')
        try:
            int(v[1:], 16)
        except ValueError:
            raise ValueError('Color must be a valid hex color')
        return v

class QRPreset(BaseModel):
    name: str
    description: str
    style: QRStyle
    eye_shape: EyeShape
    error_correction: ErrorCorrectionLevel
    logo_scale: float = 0.2
    eye_radius: float = 1.0

class QRPresetsResponse(BaseModel):
    presets: dict[str, QRPreset] = {
        "mobile_app": QRPreset(
            name="Mobile App",
            description="Optimized for mobile app downloads",
            style=QRStyle.ROUNDED,
            eye_shape=EyeShape.ROUNDED,
            error_correction=ErrorCorrectionLevel.M,
            logo_scale=0.2,
            eye_radius=2.0
        ),
        "print_media": QRPreset(
            name="Print Media",
            description="High error correction for printed materials",
            style=QRStyle.SQUARE,
            eye_shape=EyeShape.RECT,
            error_correction=ErrorCorrectionLevel.H,
            logo_scale=0.15,
            eye_radius=0.0
        ),
        "social_media": QRPreset(
            name="Social Media",
            description="Stylish design for social platforms",
            style=QRStyle.DOTS,
            eye_shape=EyeShape.CIRCLE,
            error_correction=ErrorCorrectionLevel.L,
            logo_scale=0.25,
            eye_radius=1.5
        ),
        "website": QRPreset(
            name="Website",
            description="Clean design for websites",
            style=QRStyle.GAPPED,
            eye_shape=EyeShape.ROUNDED,
            error_correction=ErrorCorrectionLevel.M,
            logo_scale=0.2,
            eye_radius=1.8
        )
    }
