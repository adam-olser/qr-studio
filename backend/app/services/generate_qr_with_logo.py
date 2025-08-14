#!/usr/bin/env python3

import argparse
import io
import os
from typing import Tuple

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a QR code with a centered logo overlay."
    )
    parser.add_argument(
        "--url", required=True, help="Deep link URL to encode in the QR code"
    )
    parser.add_argument(
        "--logo",
        required=True,
        help="Path to the logo image (PNG/SVG/JPG). PNG with transparency recommended",
    )
    parser.add_argument("--out", required=True, help="Output PNG file path")
    parser.add_argument(
        "--size",
        type=int,
        default=1024,
        help="Output image size in pixels (square). Default: 1024",
    )
    parser.add_argument(
        "--logo-scale",
        type=float,
        default=0.22,
        dest="logo_scale",
        help="Logo width relative to QR size (0-1). Default: 0.22",
    )
    parser.add_argument(
        "--border", type=int, default=4, help="QR border (modules). Default: 4"
    )
    parser.add_argument(
        "--bg-radius",
        type=int,
        default=28,
        dest="bg_radius",
        help="Rounded background corner radius in pixels. Default: 28",
    )
    parser.add_argument(
        "--bg-padding",
        type=int,
        default=20,
        dest="bg_padding",
        help="Padding around logo inside rounded background, in pixels. Default: 20",
    )
    parser.add_argument(
        "--style",
        choices=[
            "square",
            "gapped",
            "dots",
            "rounded",
            "bars-vertical",
            "bars-horizontal",
        ],
        default="rounded",
        help="QR module style. Default: rounded",
    )
    parser.add_argument(
        "--ec-level",
        choices=["L", "M", "Q", "H"],
        default="Q",
        help="Error correction level (higher = denser). Default: Q",
    )
    parser.add_argument(
        "--eye-radius",
        type=float,
        default=0.9,
        help="Rounded eye corner radius in module units. Default: 0.9",
    )
    parser.add_argument(
        "--eye-shape",
        choices=["rect", "rounded", "circle"],
        default="rect",
        help="Finder eye shape: rect (classic square), rounded (rounded-rect), circle (concentric). Default: rect",
    )
    parser.add_argument(
        "--eye-style",
        choices=["standard", "circle-ring"],
        default="standard",
        help="Finder eye style: standard (solid shapes), circle-ring (circular rings like iOS). Default: standard",
    )
    parser.add_argument(
        "--eye-scale-x",
        type=float,
        default=1.0,
        help="Scale factor for eye width relative to the standard 7 modules (0.7–1.3). Default: 1.0",
    )
    parser.add_argument(
        "--eye-scale-y",
        type=float,
        default=1.0,
        help="Scale factor for eye height relative to the standard 7 modules (0.7–1.3). Default: 1.0",
    )
    parser.add_argument(
        "--dark",
        default="#000000",
        help="Dark/module color (hex). Default: #000000",
    )
    parser.add_argument(
        "--light",
        default="#FFFFFF",
        help="Light/background color (hex). Default: #FFFFFF",
    )
    parser.add_argument(
        "--compress-level",
        type=int,
        default=9,
        dest="compress_level",
        help="PNG compress level (0-9). Default: 9 (smallest files)",
    )
    parser.add_argument(
        "--no-optimize",
        action="store_true",
        help="Disable Pillow PNG optimizer (enabled by default)",
    )
    parser.add_argument(
        "--quantize-colors",
        type=int,
        default=64,
        dest="quantize_colors",
        help="Reduce colors to this palette size (2-256) to shrink PNG. Set 0 to disable. Default: 64",
    )
    parser.add_argument(
        "--qr-radius",
        type=int,
        default=0,
        help="Round the outer corners of the QR image by this many pixels. Default: 0 (square)",
    )
    return parser.parse_args()


def _resolve_module_drawer(style: str):
    if style == "square":
        return SquareModuleDrawer()
    if style == "gapped":
        return GappedSquareModuleDrawer()
    if style == "dots":
        return CircleModuleDrawer()
    if style == "rounded":
        return RoundedModuleDrawer()
    if style == "bars-vertical":
        return VerticalBarsDrawer()
    if style == "bars-horizontal":
        return HorizontalBarsDrawer()
    return SquareModuleDrawer()


def _ec_from_str(level: str):
    return {
        "L": ERROR_CORRECT_L,
        "M": ERROR_CORRECT_M,
        "Q": ERROR_CORRECT_Q,
        "H": ERROR_CORRECT_H,
    }[level]


def _draw_rounded_eyes(
    base_img: Image.Image,
    modules: int,
    box_size: int,
    border: int,
    dark_rgb,
    light_rgb,
    radius_modules: float,
    eye_scale_x: float = 1.0,
    eye_scale_y: float = 1.0,
    eye_shape: str = "rect",
    eye_style: str = "standard",
) -> None:
    draw = ImageDraw.Draw(base_img)
    outer = 7 * box_size
    inner_w = 5 * box_size
    core_w = 3 * box_size

    positions = [
        (border * box_size, border * box_size),  # top-left
        (border * box_size + (modules - 7) * box_size, border * box_size),  # top-right
        (
            border * box_size,
            border * box_size + (modules - 7) * box_size,
        ),  # bottom-left
    ]

    sx = max(0.7, min(1.3, float(eye_scale_x)))
    sy = max(0.7, min(1.3, float(eye_scale_y)))
    r_px = int(max(0, radius_modules) * box_size)

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

        if eye_style == "circle-ring":
            # Draw iOS-style circular rings with proper spacing
            # Outer ring (thick black circle)
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
            # Inner solid circle (black dot)
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
        elif eye_shape == "circle":
            draw.ellipse([ox, oy, ox + ow, oy + oh], fill=dark_rgb)
            draw.ellipse([ix, iy, ix + iw, iy + ih], fill=light_rgb)
            draw.ellipse([cx, cy, cx + cw, cy + ch], fill=dark_rgb)
        elif eye_shape == "rounded":
            r_outer = min(r_px, min(ow, oh) // 2)
            r_inner = min(r_px, min(iw, ih) // 2)
            r_core = min(r_px, min(cw, ch) // 2)
            draw.rounded_rectangle(
                [ox, oy, ox + ow, oy + oh], radius=r_outer, fill=dark_rgb
            )
            draw.rounded_rectangle(
                [ix, iy, ix + iw, iy + ih], radius=r_inner, fill=light_rgb
            )
            draw.rounded_rectangle(
                [cx, cy, cx + cw, cy + ch], radius=r_core, fill=dark_rgb
            )
        else:  # rect
            draw.rectangle([ox, oy, ox + ow, oy + oh], fill=dark_rgb)
            draw.rectangle([ix, iy, ix + iw, iy + ih], fill=light_rgb)
            draw.rectangle([cx, cy, cx + cw, cy + ch], fill=dark_rgb)


def make_qr(
    url: str,
    size_px: int,
    border: int,
    style: str,
    dark: str,
    light: str,
    ec_level: str,
    eye_radius: float,
    eye_scale_x: float,
    eye_scale_y: float,
    eye_shape: str,
    eye_style: str,
) -> Image.Image:
    qr = qrcode.QRCode(
        version=None,
        error_correction=_ec_from_str(ec_level),
        box_size=10,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)
    # Use RGB (not RGBA) for the styled image colors; RGBA can cause white-on-white output
    dark_rgb = ImageColor.getcolor(dark, "RGB")
    light_rgb = ImageColor.getcolor(light, "RGB")

    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=_resolve_module_drawer(style),
        color_mask=SolidFillColorMask(back_color=light_rgb, front_color=dark_rgb),
    ).convert("RGBA")
    # Add custom finder eyes on top of styled modules
    _draw_rounded_eyes(
        img,
        modules=qr.modules_count,
        box_size=qr.box_size,
        border=qr.border,
        dark_rgb=dark_rgb,
        light_rgb=light_rgb,
        radius_modules=eye_radius,
        eye_scale_x=eye_scale_x,
        eye_scale_y=eye_scale_y,
        eye_shape=eye_shape,
        eye_style=eye_style,
    )
    return img.resize((size_px, size_px), resample=Image.NEAREST)


def load_logo(path: str) -> Image.Image:
    logo = Image.open(path).convert("RGBA")
    return logo


def draw_rounded_rect(
    size: Tuple[int, int], radius: int, color=(255, 255, 255, 255)
) -> Image.Image:
    width, height = size
    bg = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(bg)
    draw.rounded_rectangle([(0, 0), (width, height)], radius=radius, fill=color)
    return bg


def compose(
    qr_img: Image.Image,
    logo_img: Image.Image,
    logo_scale: float,
    bg_padding: int,
    bg_radius: int,
    qr_radius: int = 0,
) -> Image.Image:
    qr_w, qr_h = qr_img.size
    target_logo_w = int(qr_w * max(0.05, min(logo_scale, 0.35)))
    logo_aspect = logo_img.width / logo_img.height
    target_logo_h = int(target_logo_w / logo_aspect)
    logo_resized = logo_img.resize(
        (target_logo_w, target_logo_h), resample=Image.LANCZOS
    )

    bg_w = target_logo_w + bg_padding * 2
    bg_h = target_logo_h + bg_padding * 2
    bg = draw_rounded_rect((bg_w, bg_h), radius=bg_radius, color=(255, 255, 255, 255))

    composed = qr_img.copy()

    # Optional outer rounding of the entire QR code canvas
    if int(qr_radius) > 0:
        mask = draw_rounded_rect(
            (qr_w, qr_h), radius=int(qr_radius), color=(255, 255, 255, 255)
        )
        # Apply mask by blending white outside corners
        rounded = Image.new("RGBA", (qr_w, qr_h), (255, 255, 255, 0))
        rounded.alpha_composite(composed)
        rounded = Image.composite(
            rounded,
            Image.new("RGBA", (qr_w, qr_h), (255, 255, 255, 255)),
            mask.split()[3],
        )
        composed = rounded

    center_x = (qr_w - bg_w) // 2
    center_y = (qr_h - bg_h) // 2

    composed.alpha_composite(bg, (center_x, center_y))
    composed.alpha_composite(
        logo_resized, (center_x + bg_padding, center_y + bg_padding)
    )

    return composed


def main() -> None:
    args = parse_args()

    if not os.path.isfile(args.logo):
        raise FileNotFoundError(f"Logo file not found: {args.logo}")

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    qr_img = make_qr(
        args.url,
        args.size,
        args.border,
        style=args.style,
        dark=args.dark,
        light=args.light,
        ec_level=args.ec_level,
        eye_radius=args.eye_radius,
        eye_scale_x=args.eye_scale_x,
        eye_scale_y=args.eye_scale_y,
        eye_shape=args.eye_shape,
        eye_style=args.eye_style,
    )
    logo_img = load_logo(args.logo)
    final = compose(
        qr_img,
        logo_img,
        args.logo_scale,
        args.bg_padding,
        args.bg_radius,
        qr_radius=args.qr_radius,
    )
    # Ensure 3-channel RGB to avoid alpha rendering issues in certain viewers
    image_to_save = final.convert("RGB")
    # Optional palette quantization to significantly reduce file size
    if int(args.quantize_colors) > 0:
        colors = max(2, min(256, int(args.quantize_colors)))
        image_to_save = image_to_save.quantize(
            colors=colors, method=Image.MEDIANCUT, dither=0
        )

    image_to_save.save(
        args.out,
        format="PNG",
        optimize=not args.no_optimize,
        compress_level=max(0, min(9, int(args.compress_level))),
    )
    print(f"Saved QR with logo to: {args.out}")


if __name__ == "__main__":
    main()
