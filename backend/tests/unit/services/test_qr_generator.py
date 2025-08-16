"""
Unit tests for QR generator service
"""

import io
from unittest.mock import patch, MagicMock
import pytest
from PIL import Image

from app.services.qr_generator import QRGeneratorService
from app.models.qr_request import QRGenerationRequest


class TestQRGeneratorService:
    """Test QR generator service functionality."""

    @pytest.fixture
    def qr_service(self) -> QRGeneratorService:
        """QR generator service instance."""
        return QRGeneratorService()

    def test_service_initialization(self, qr_service):
        """Test service initializes correctly."""
        assert qr_service is not None
        assert hasattr(qr_service, "_module_drawers")
        assert len(qr_service._module_drawers) > 0

    async def test_generate_qr_without_logo(self, qr_service, sample_qr_config):
        """Test QR generation without logo."""
        result = await qr_service.generate_qr_with_logo(sample_qr_config, None)

        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0

        # Verify it's a valid PNG
        img = Image.open(io.BytesIO(result))
        assert img.format == "PNG"
        assert img.size == (sample_qr_config.size, sample_qr_config.size)

    async def test_generate_qr_with_logo(
        self, qr_service, sample_qr_config, sample_logo_bytes
    ):
        """Test QR generation with logo."""
        result = await qr_service.generate_qr_with_logo(
            sample_qr_config, sample_logo_bytes
        )

        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0

        # Verify it's a valid PNG
        img = Image.open(io.BytesIO(result))
        assert img.format == "PNG"
        assert img.size == (sample_qr_config.size, sample_qr_config.size)

    async def test_generate_qr_different_styles(self, qr_service, sample_qr_config):
        """Test QR generation with different styles."""
        styles = [
            "square",
            "rounded",
            "dots",
            "gapped",
            "bars-vertical",
            "bars-horizontal",
        ]

        for style in styles:
            config = QRGenerationRequest(
                **{**sample_qr_config.__dict__, "style": style}
            )
            result = await qr_service.generate_qr_with_logo(config, None)

            assert result is not None
            assert isinstance(result, bytes)
            assert len(result) > 0

    async def test_generate_qr_different_sizes(self, qr_service, sample_qr_config):
        """Test QR generation with different sizes."""
        sizes = [256, 512, 1024, 2048]

        for size in sizes:
            config = QRGenerationRequest(**{**sample_qr_config.__dict__, "size": size})
            result = await qr_service.generate_qr_with_logo(config, None)

            assert result is not None
            img = Image.open(io.BytesIO(result))
            assert img.size == (size, size)

    async def test_generate_qr_different_error_correction(
        self, qr_service, sample_qr_config
    ):
        """Test QR generation with different error correction levels."""
        ec_levels = ["L", "M", "Q", "H"]

        for ec_level in ec_levels:
            config = QRGenerationRequest(
                **{**sample_qr_config.__dict__, "ec_level": ec_level}
            )
            result = await qr_service.generate_qr_with_logo(config, None)

            assert result is not None
            assert isinstance(result, bytes)

    async def test_generate_qr_different_eye_shapes(self, qr_service, sample_qr_config):
        """Test QR generation with different eye shapes."""
        eye_shapes = ["rect", "rounded", "circle"]

        for eye_shape in eye_shapes:
            config = QRGenerationRequest(
                **{**sample_qr_config.__dict__, "eye_shape": eye_shape}
            )
            result = await qr_service.generate_qr_with_logo(config, None)

            assert result is not None
            assert isinstance(result, bytes)

    async def test_generate_qr_with_custom_colors(self, qr_service, sample_qr_config):
        """Test QR generation with custom colors."""
        color_combinations = [
            ("#FF0000", "#FFFFFF"),  # Red on white
            ("#000000", "#FFFF00"),  # Black on yellow
            ("#0000FF", "#FFFFFF"),  # Blue on white
        ]

        for dark_color, light_color in color_combinations:
            config = QRGenerationRequest(
                **{
                    **sample_qr_config.__dict__,
                    "dark_color": dark_color,
                    "light_color": light_color,
                }
            )
            result = await qr_service.generate_qr_with_logo(config, None)

            assert result is not None
            assert isinstance(result, bytes)

    def test_get_preset_configs(self, qr_service):
        """Test getting preset configurations."""
        presets = qr_service.get_preset_configs()

        assert isinstance(presets, dict)
        assert len(presets) > 0

        # Check that all presets have required fields
        for name, config in presets.items():
            assert isinstance(name, str)
            assert hasattr(config, "style")
            assert hasattr(config, "dark_color")
            assert hasattr(config, "light_color")

    def test_load_logo_from_bytes(self, qr_service, sample_logo_bytes):
        """Test loading logo from bytes."""
        logo_img = qr_service._load_logo_from_bytes(sample_logo_bytes)

        assert isinstance(logo_img, Image.Image)
        assert logo_img.mode == "RGBA"
        assert logo_img.size == (100, 100)  # From our sample logo

    def test_load_invalid_logo_bytes(self, qr_service, invalid_image_bytes):
        """Test loading invalid logo bytes."""
        with pytest.raises(Exception):  # Should raise PIL exception
            qr_service._load_logo_from_bytes(invalid_image_bytes)

    async def test_generate_qr_with_compression(self, qr_service, sample_qr_config):
        """Test QR generation with different compression levels."""
        compression_levels = [0, 3, 6, 9]

        results = []
        for level in compression_levels:
            config = QRGenerationRequest(
                **{**sample_qr_config.__dict__, "compress_level": level}
            )
            result = await qr_service.generate_qr_with_logo(config, None)
            results.append((level, len(result)))

        # Higher compression should generally result in smaller files
        # (though this isn't guaranteed for all images)
        assert all(isinstance(result[1], int) and result[1] > 0 for result in results)

    async def test_generate_qr_with_quantization(self, qr_service, sample_qr_config):
        """Test QR generation with color quantization."""
        quantize_values = [2, 16, 64, 256]

        for quantize in quantize_values:
            config = QRGenerationRequest(
                **{**sample_qr_config.__dict__, "quantize_colors": quantize}
            )
            result = await qr_service.generate_qr_with_logo(config, None)

            assert result is not None
            assert isinstance(result, bytes)

    def test_create_rounded_background(self, qr_service):
        """Test creating rounded background."""
        size = (200, 200)
        radius = 20
        color = (255, 255, 255, 255)

        bg_img = qr_service._draw_rounded_rect(size, radius, color)

        assert isinstance(bg_img, Image.Image)
        assert bg_img.size == size
        assert bg_img.mode == "RGBA"

    async def test_generate_qr_long_url(self, qr_service):
        """Test QR generation with very long URL."""
        long_url = "https://example.com/" + "a" * 1000
        config = QRGenerationRequest(
            url=long_url,
            size=512,
            style="square",
            dark_color="#000000",
            light_color="#FFFFFF",
        )

        result = await qr_service.generate_qr_with_logo(config, None)

        assert result is not None
        assert isinstance(result, bytes)

    async def test_generate_qr_special_characters(self, qr_service):
        """Test QR generation with special characters in URL."""
        special_urls = [
            "https://example.com/path?query=value&other=测试",
            "https://example.com/émoji/🚀",
            "https://example.com/spaces and symbols!@#$%",
        ]

        for url in special_urls:
            config = QRGenerationRequest(
                url=url,
                size=512,
                style="square",
                dark_color="#000000",
                light_color="#FFFFFF",
            )

            result = await qr_service.generate_qr_with_logo(config, None)

            assert result is not None
            assert isinstance(result, bytes)

    def test_optimize_image(self, qr_service, sample_qr_config):
        """Test image optimization."""
        # Create a test image
        test_img = Image.new("RGBA", (512, 512), (255, 0, 0, 255))

        optimized = qr_service._optimize_image(test_img, sample_qr_config)

        assert isinstance(optimized, Image.Image)
        # When quantize_colors > 0, image is converted to palette mode ("P")
        # When quantize_colors = 0, image stays in RGB mode
        assert optimized.mode in ["RGB", "P"]
