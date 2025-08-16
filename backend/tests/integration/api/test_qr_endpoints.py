"""
Integration tests for QR API endpoints
"""

import io
from unittest.mock import patch, AsyncMock
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from PIL import Image

from app.main import app


class TestQRGenerationEndpoints:
    """Test QR generation API endpoints."""

    def test_generate_qr_json_endpoint(self, test_client: TestClient):
        """Test QR generation with JSON payload."""
        payload = {
            "url": "https://example.com",
            "size": 512,
            "style": "rounded",
            "dark_color": "#000000",
            "light_color": "#FFFFFF",
        }

        response = test_client.post("/api/v1/qr/generate", json=payload)

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert len(response.content) > 0

        # Verify it's a valid PNG
        img = Image.open(io.BytesIO(response.content))
        assert img.format == "PNG"
        assert img.size == (512, 512)

    def test_generate_qr_form_endpoint(self, test_client: TestClient):
        """Test QR generation with form data."""
        form_data = {
            "url": "https://example.com",
            "size": "1024",
            "style": "square",
            "dark_color": "#FF0000",
            "light_color": "#FFFFFF",
        }

        response = test_client.post("/api/v1/qr/generate-form", data=form_data)

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert len(response.content) > 0

        # Verify it's a valid PNG with correct size
        img = Image.open(io.BytesIO(response.content))
        assert img.format == "PNG"
        assert img.size == (1024, 1024)

    def test_generate_qr_with_logo_upload(
        self, test_client: TestClient, sample_logo_bytes: bytes
    ):
        """Test QR generation with logo file upload."""
        form_data = {
            "url": "https://example.com",
            "size": "512",
            "style": "rounded",
        }

        files = {"logo": ("test_logo.png", io.BytesIO(sample_logo_bytes), "image/png")}

        response = test_client.post(
            "/api/v1/qr/generate-form", data=form_data, files=files
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert len(response.content) > 0

    def test_generate_qr_invalid_url(self, test_client: TestClient):
        """Test QR generation with invalid URL."""
        payload = {
            "url": "",  # Empty URL
            "size": 512,
        }

        response = test_client.post("/api/v1/qr/generate", json=payload)

        assert response.status_code == 422  # Validation error
        error_data = response.json()
        assert "detail" in error_data

    def test_generate_qr_invalid_size(self, test_client: TestClient):
        """Test QR generation with invalid size."""
        payload = {
            "url": "https://example.com",
            "size": 50,  # Too small
        }

        response = test_client.post("/api/v1/qr/generate", json=payload)

        assert response.status_code == 422  # Validation error

    def test_generate_qr_invalid_color(self, test_client: TestClient):
        """Test QR generation with invalid color."""
        payload = {
            "url": "https://example.com",
            "size": 512,
            "dark_color": "invalid-color",
        }

        response = test_client.post("/api/v1/qr/generate", json=payload)

        assert response.status_code == 422  # Validation error

    def test_generate_qr_invalid_logo_file(
        self, test_client: TestClient, invalid_image_bytes: bytes
    ):
        """Test QR generation with invalid logo file."""
        form_data = {
            "url": "https://example.com",
            "size": "512",
        }

        files = {"logo": ("invalid.txt", io.BytesIO(invalid_image_bytes), "text/plain")}

        response = test_client.post(
            "/api/v1/qr/generate-form", data=form_data, files=files
        )

        assert response.status_code == 400  # Bad request
        error_data = response.json()
        assert "error_code" in error_data

    def test_generate_qr_large_logo_file(
        self, test_client: TestClient, large_image_bytes: bytes
    ):
        """Test QR generation with oversized logo file."""
        form_data = {
            "url": "https://example.com",
            "size": "512",
        }

        files = {"logo": ("large.png", io.BytesIO(large_image_bytes), "image/png")}

        response = test_client.post(
            "/api/v1/qr/generate-form", data=form_data, files=files
        )

        assert response.status_code == 400  # Bad request
        error_data = response.json()
        assert "too large" in error_data["message"].lower()


class TestQRPresetsEndpoint:
    """Test QR presets API endpoint."""

    def test_get_presets(self, test_client: TestClient):
        """Test getting QR presets."""
        response = test_client.get("/api/v1/qr/presets")

        assert response.status_code == 200
        presets = response.json()

        assert isinstance(presets, dict)
        assert len(presets) > 0

        # Check preset structure
        for name, config in presets.items():
            assert isinstance(name, str)
            assert "style" in config
            assert "dark_color" in config
            assert "light_color" in config

    @patch("app.api.qr.qr_cache.get_presets")
    async def test_get_presets_from_cache(
        self, mock_get_presets, async_client: AsyncClient
    ):
        """Test getting presets from cache."""
        cached_presets = {
            "presets": {"test": {"style": "square"}},
            "cached_at": "2023-01-01T00:00:00",
        }
        mock_get_presets.return_value = cached_presets

        response = await async_client.get("/api/v1/qr/presets")

        assert response.status_code == 200
        presets = response.json()
        assert presets == cached_presets["presets"]


class TestQRStylesEndpoint:
    """Test QR styles API endpoint."""

    def test_get_styles(self, test_client: TestClient):
        """Test getting available QR styles."""
        response = test_client.get("/api/v1/qr/styles")

        assert response.status_code == 200
        styles_data = response.json()

        assert "styles" in styles_data
        assert "eye_shapes" in styles_data
        assert "eye_styles" in styles_data
        assert "error_correction_levels" in styles_data

        # Check styles list
        styles = styles_data["styles"]
        expected_styles = [
            "square",
            "rounded",
            "dots",
            "gapped",
            "bars-vertical",
            "bars-horizontal",
        ]
        for style in expected_styles:
            assert style in styles


class TestURLValidationEndpoint:
    """Test URL validation API endpoint."""

    @pytest.mark.parametrize(
        "url",
        [
            "https://example.com",
            "http://localhost:3000",
            "mailto:test@example.com",
        ],
    )
    def test_validate_valid_urls(self, test_client: TestClient, url: str):
        """Test URL validation with valid URLs."""
        response = test_client.get(f"/api/v1/qr/validate-url?url={url}")

        assert response.status_code == 200
        validation = response.json()

        assert validation["valid"] is True
        assert validation["error"] is None

    @pytest.mark.parametrize(
        "url",
        [
            "",
            "not-a-url",
            "javascript:alert('xss')",
        ],
    )
    def test_validate_invalid_urls(self, test_client: TestClient, url: str):
        """Test URL validation with invalid URLs."""
        response = test_client.get(f"/api/v1/qr/validate-url?url={url}")

        assert response.status_code == 200
        validation = response.json()

        assert validation["valid"] is False
        assert validation["error"] is not None

    def test_validate_url_with_warning(self, test_client: TestClient):
        """Test URL validation that returns a warning."""
        url = "example.com"  # Missing protocol
        response = test_client.get(f"/api/v1/qr/validate-url?url={url}")

        assert response.status_code == 200
        validation = response.json()

        assert validation["valid"] is True
        assert validation["warning"] is not None
        assert "protocol" in validation["warning"].lower()

    def test_validate_url_with_suggestions(self, test_client: TestClient):
        """Test URL validation that provides suggestions."""
        url = "example.com"
        response = test_client.get(f"/api/v1/qr/validate-url?url={url}")

        assert response.status_code == 200
        validation = response.json()

        if "suggestions" in validation:
            assert isinstance(validation["suggestions"], list)
            assert len(validation["suggestions"]) > 0

    @patch("app.api.qr.qr_cache.get_url_validation")
    async def test_validate_url_from_cache(
        self, mock_get_validation, async_client: AsyncClient
    ):
        """Test URL validation from cache."""
        cached_validation = {
            "valid": True,
            "error": None,
            "warning": None,
            "cached_at": "2023-01-01T00:00:00",
        }
        mock_get_validation.return_value = cached_validation

        response = await async_client.get(
            "/api/v1/qr/validate-url?url=https://example.com"
        )

        assert response.status_code == 200
        validation = response.json()

        # Should not include cached_at in response
        expected = {k: v for k, v in cached_validation.items() if k != "cached_at"}
        assert validation == expected


class TestQREndpointsErrorHandling:
    """Test error handling in QR endpoints."""

    def test_generate_qr_missing_url(self, test_client: TestClient):
        """Test QR generation without URL."""
        payload = {
            "size": 512,
        }

        response = test_client.post("/api/v1/qr/generate", json=payload)

        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data

    def test_generate_qr_malformed_json(self, test_client: TestClient):
        """Test QR generation with malformed JSON."""
        response = test_client.post(
            "/api/v1/qr/generate",
            data="invalid-json",
            headers={"content-type": "application/json"},
        )

        assert response.status_code == 422

    @patch("app.api.qr.qr_service.generate_qr_with_logo")
    async def test_generate_qr_service_error(
        self, mock_generate, async_client: AsyncClient
    ):
        """Test QR generation when service raises error."""
        mock_generate.side_effect = Exception("Service error")

        payload = {
            "url": "https://example.com",
            "size": 512,
        }

        response = await async_client.post("/api/v1/qr/generate", json=payload)

        assert response.status_code == 500
        error_data = response.json()
        assert "error_code" in error_data

    def test_validate_url_missing_parameter(self, test_client: TestClient):
        """Test URL validation without URL parameter."""
        response = test_client.get("/api/v1/qr/validate-url")

        assert response.status_code == 422  # Missing required parameter
