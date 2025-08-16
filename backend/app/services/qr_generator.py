"""
QR Code Generation Service

Converts the CLI-based QR generation script into a service class
for use in the FastAPI application.
"""

import io
from typing import Tuple, Optional, Any
from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageColor
import qrcode
from qrcode.constants import (
    ERROR_CORRECT_L,
    ERROR_CORRECT_M,
    ERROR_CORRECT_Q,
    ERROR_CORRECT_H,
)
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import SolidFillColorMask
from qrcode.image.styles.moduledrawers import (
    SquareModuleDrawer,
    GappedSquareModuleDrawer,
    CircleModuleDrawer,
    RoundedModuleDrawer,
    VerticalBarsDrawer,
    HorizontalBarsDrawer,
)


@dataclass
class QRConfig:
    """Configuration for QR code generation"""

    # Basic settings
    url: str
    size: int = 1024
    border: int = 4

    # Style settings
    style: str = (
        "rounded"  # square, gapped, dots, rounded, bars-vertical, bars-horizontal
    )
    dark_color: str = "#000000"
    light_color: str = "#FFFFFF"
    ec_level: str = "Q"  # L, M, Q, H

    # Eye customization
    eye_radius: float = 0.9
    eye_scale_x: float = 1.0
    eye_scale_y: float = 1.0
    eye_shape: str = "rect"  # rect, rounded, circle
    eye_style: str = "standard"  # standard, circle-ring

    # Logo settings
    logo_scale: float = 0.22
    bg_padding: int = 20
    bg_radius: int = 28

    # Output settings
    qr_radius: int = 0
    compress_level: int = 9
    quantize_colors: int = 64


class QRGeneratorService:
    """Service for generating QR codes with logos and custom styling"""

    def __init__(self) -> None:
        self._module_drawers = {
            "square": SquareModuleDrawer(),
            "gapped": GappedSquareModuleDrawer(),
            "dots": CircleModuleDrawer(),
            "rounded": RoundedModuleDrawer(),
            "bars-vertical": VerticalBarsDrawer(),
            "bars-horizontal": HorizontalBarsDrawer(),
        }

        self._error_correction_levels = {
            "L": ERROR_CORRECT_L,
            "M": ERROR_CORRECT_M,
            "Q": ERROR_CORRECT_Q,
            "H": ERROR_CORRECT_H,
        }

    async def generate_qr_with_logo(
        self, config: QRConfig, logo_data: Optional[bytes] = None
    ) -> bytes:
        """
        Generate a QR code with optional logo overlay

        Args:
            config: QR generation configuration
            logo_data: Optional logo image bytes

        Returns:
            PNG image data as bytes
        """
        try:
            # Generate the base QR code
            qr_img = self._make_qr(config)

            # If logo provided, compose with logo
            if logo_data:
                logo_img = self._load_logo_from_bytes(logo_data)
                final_img = self._compose_with_logo(qr_img, logo_img, config)
            else:
                final_img = qr_img

            # Convert to RGB and optimize
            final_img = self._optimize_image(final_img, config)

            # Return as bytes
            return self._image_to_bytes(final_img, config)

        except Exception as e:
            raise ValueError(f"QR generation failed: {str(e)}")

    def _make_qr(self, config: QRConfig) -> Image.Image:
        """Create the base QR code with custom styling"""
        qr = qrcode.QRCode(
            version=None,
            error_correction=self._error_correction_levels[config.ec_level],
            box_size=10,
            border=config.border,
        )
        qr.add_data(config.url)
        qr.make(fit=True)

        # Convert colors to RGB
        dark_rgb = ImageColor.getcolor(config.dark_color, "RGB")
        light_rgb = ImageColor.getcolor(config.light_color, "RGB")

        # Create styled QR image
        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=self._module_drawers.get(config.style, SquareModuleDrawer()),
            color_mask=SolidFillColorMask(back_color=light_rgb, front_color=dark_rgb),
        ).convert("RGBA")

        # Add custom finder eyes
        self._draw_custom_eyes(img, qr, dark_rgb, light_rgb, config)

        # Resize to target size
        resized_img: Image.Image = img.resize(
            (config.size, config.size), resample=Image.NEAREST
        )
        return resized_img

    def _draw_custom_eyes(
        self,
        img: Image.Image,
        qr: qrcode.QRCode,
        dark_rgb: Any,
        light_rgb: Any,
        config: QRConfig,
    ) -> None:
        """Draw custom finder pattern eyes"""
        draw = ImageDraw.Draw(img)
        modules = qr.modules_count
        box_size = qr.box_size
        border = qr.border

        outer = 7 * box_size
        inner_w = 5 * box_size
        core_w = 3 * box_size

        positions = [
            (border * box_size, border * box_size),  # top-left
            (
                border * box_size + (modules - 7) * box_size,
                border * box_size,
            ),  # top-right
            (
                border * box_size,
                border * box_size + (modules - 7) * box_size,
            ),  # bottom-left
        ]

        sx = max(0.7, min(1.3, config.eye_scale_x))
        sy = max(0.7, min(1.3, config.eye_scale_y))
        r_px = int(max(0, config.eye_radius) * box_size)

        for x, y in positions:
            ow = int(outer * sx)
            oh = int(outer * sy)
            ox = x + (outer - ow) // 2
            oy = y + (outer - oh) // 2

            iw = int(inner_w * sx)
            ih = int(inner_w * sy)
            ix = x + box_size + (inner_w - iw) // 2
            iy = y + box_size + (inner_w - ih) // 2

            cw = int(core_w * sx)
            ch = int(core_w * sy)
            cx = x + 2 * box_size + (core_w - cw) // 2
            cy = y + 2 * box_size + (core_w - ch) // 2

            if config.eye_style == "circle-ring":
                # iOS-style circular rings
                ring_width = box_size
                draw.ellipse([ox, oy, ox + ow, oy + oh], fill=dark_rgb)
                draw.ellipse(
                    [
                        ox + ring_width,
                        oy + ring_width,
                        ox + ow - ring_width,
                        oy + oh - ring_width,
                    ],
                    fill=light_rgb,
                )

                core_margin = int(1.5 * box_size)
                draw.ellipse(
                    [
                        ox + core_margin,
                        oy + core_margin,
                        ox + ow - core_margin,
                        oy + oh - core_margin,
                    ],
                    fill=dark_rgb,
                )

            elif config.eye_shape == "circle":
                draw.ellipse([ox, oy, ox + ow, oy + oh], fill=dark_rgb)
                draw.ellipse([ix, iy, ix + iw, iy + ih], fill=light_rgb)
                draw.ellipse([cx, cy, cx + cw, cy + ch], fill=dark_rgb)

            elif config.eye_shape == "rounded":
                r_outer = min(r_px, min(ow, oh) // 2)
                r_inner = min(r_px, min(iw, ih) // 2)
                r_core = min(r_px, min(cw, ch) // 2)

                draw.rounded_rectangle(
                    (ox, oy, ox + ow, oy + oh), radius=r_outer, fill=dark_rgb
                )
                draw.rounded_rectangle(
                    (ix, iy, ix + iw, iy + ih), radius=r_inner, fill=light_rgb
                )
                draw.rounded_rectangle(
                    (cx, cy, cx + cw, cy + ch), radius=r_core, fill=dark_rgb
                )

            else:  # rect
                draw.rectangle((ox, oy, ox + ow, oy + oh), fill=dark_rgb)
                draw.rectangle((ix, iy, ix + iw, iy + ih), fill=light_rgb)
                draw.rectangle((cx, cy, cx + cw, cy + ch), fill=dark_rgb)

    def _load_logo_from_bytes(self, logo_data: bytes) -> Image.Image:
        """Load logo from bytes data"""
        logo_stream = io.BytesIO(logo_data)
        return Image.open(logo_stream).convert("RGBA")

    def _compose_with_logo(
        self, qr_img: Image.Image, logo_img: Image.Image, config: QRConfig
    ) -> Image.Image:
        """Compose QR code with logo overlay"""
        qr_w, qr_h = qr_img.size

        # Calculate logo size
        target_logo_w = int(qr_w * max(0.05, min(config.logo_scale, 0.35)))
        logo_aspect = logo_img.width / logo_img.height
        target_logo_h = int(target_logo_w / logo_aspect)
        logo_resized = logo_img.resize(
            (target_logo_w, target_logo_h), resample=Image.LANCZOS
        )

        # Create rounded background for logo
        bg_w = target_logo_w + config.bg_padding * 2
        bg_h = target_logo_h + config.bg_padding * 2
        bg = self._draw_rounded_rect(
            (bg_w, bg_h), config.bg_radius, (255, 255, 255, 255)
        )

        composed = qr_img.copy()

        # Optional outer rounding of entire QR code
        if config.qr_radius > 0:
            mask = self._draw_rounded_rect(
                (qr_w, qr_h), config.qr_radius, (255, 255, 255, 255)
            )
            rounded = Image.new("RGBA", (qr_w, qr_h), (255, 255, 255, 0))
            rounded.alpha_composite(composed)
            rounded = Image.composite(
                rounded,
                Image.new("RGBA", (qr_w, qr_h), (255, 255, 255, 255)),
                mask.split()[3],
            )
            composed = rounded

        # Center and composite logo
        center_x = (qr_w - bg_w) // 2
        center_y = (qr_h - bg_h) // 2

        composed.alpha_composite(bg, (center_x, center_y))
        composed.alpha_composite(
            logo_resized, (center_x + config.bg_padding, center_y + config.bg_padding)
        )

        return composed

    def _draw_rounded_rect(
        self,
        size: Tuple[int, int],
        radius: int,
        color: Tuple[int, int, int, int] = (255, 255, 255, 255),
    ) -> Image.Image:
        """Draw a rounded rectangle"""
        width, height = size
        bg = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(bg)
        draw.rounded_rectangle((0, 0, width, height), radius=radius, fill=color)
        return bg

    def _optimize_image(self, img: Image.Image, config: QRConfig) -> Image.Image:
        """Optimize image for file size"""
        # Convert to RGB
        image_to_save = img.convert("RGB")

        # Optional palette quantization
        if config.quantize_colors > 0:
            colors = max(2, min(256, config.quantize_colors))
            image_to_save = image_to_save.quantize(
                colors=colors, method=Image.MEDIANCUT, dither=0
            )

        return image_to_save

    def _image_to_bytes(self, img: Image.Image, config: QRConfig) -> bytes:
        """Convert PIL Image to bytes"""
        output_buffer = io.BytesIO()
        img.save(
            output_buffer,
            format="PNG",
            optimize=True,
            compress_level=max(0, min(9, config.compress_level)),
        )
        return output_buffer.getvalue()

    def get_preset_configs(self) -> dict:
        """Get predefined QR styling presets"""
        return {
            "classic": QRConfig(
                url="",
                style="square",
                dark_color="#000000",
                light_color="#FFFFFF",
                eye_shape="rect",
                eye_style="standard",
            ),
            "modern": QRConfig(
                url="",
                style="rounded",
                dark_color="#1a1a1a",
                light_color="#FFFFFF",
                eye_shape="rect",
                eye_style="standard",
                bg_radius=32,
            ),
            "dots": QRConfig(
                url="",
                style="dots",
                dark_color="#2563eb",
                light_color="#FFFFFF",
                eye_shape="rect",
                eye_style="standard",
            ),
            "retro": QRConfig(
                url="",
                style="square",
                dark_color="#8b4513",
                light_color="#f5deb3",
                eye_shape="rect",
                eye_style="standard",
                bg_radius=8,
                border=3,
            ),
            "dark": QRConfig(
                url="",
                style="rounded",
                dark_color="#ffffff",
                light_color="#04070b",
                eye_shape="rect",
                eye_style="standard",
                bg_radius=16,
                border=4,
            ),
            "neon": QRConfig(
                url="",
                style="rounded",
                dark_color="#00ff88",
                light_color="#1a1a1a",
                eye_shape="rect",
                eye_style="standard",
                bg_radius=20,
                border=4,
            ),
        }


# Global service instance
qr_service = QRGeneratorService()
