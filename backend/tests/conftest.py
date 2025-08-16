"""
Pytest configuration and shared fixtures
"""

import asyncio
import io
import os
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import fakeredis.aioredis
from fastapi.testclient import TestClient
from httpx import AsyncClient
from PIL import Image

from app.main import app
from app.core.config import Settings
from app.core.cache import CacheManager, QRCache
from app.services.qr_generator import QRGeneratorService
from app.models.qr_request import QRGenerationRequest


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    """Test settings with overrides."""
    return Settings(
        ENV="test",
        REDIS_URL="redis://localhost:6379/1",
        SECRET_KEY="test-secret-key-for-testing-only",
        CORS_ORIGINS=["http://localhost:3000", "http://localhost:5174"],
        RATE_LIMIT_REQUESTS=1000,  # Higher limits for testing
        RATE_LIMIT_WINDOW=60,
        QR_GENERATION_LIMIT=100,
        URL_VALIDATION_LIMIT=200,
        ENABLE_ABUSE_PROTECTION=False,  # Disable for tests
    )


@pytest.fixture
def mock_redis():
    """Mock Redis instance using fakeredis."""
    return fakeredis.aioredis.FakeRedis()


@pytest.fixture
async def cache_manager(mock_redis) -> AsyncGenerator[CacheManager, None]:
    """Cache manager with fake Redis."""
    cache = CacheManager("redis://fake")
    cache._redis = mock_redis
    cache._connected = True
    yield cache
    await cache.disconnect()


@pytest.fixture
async def qr_cache(cache_manager) -> QRCache:
    """QR cache instance with fake Redis."""
    return QRCache(cache_manager)


@pytest.fixture
def qr_service() -> QRGeneratorService:
    """QR generator service instance."""
    return QRGeneratorService()


@pytest.fixture
def test_client() -> TestClient:
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
async def async_client(test_settings) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for testing."""
    # Override the settings dependency
    from app.core.config import get_settings
    app.dependency_overrides[get_settings] = lambda: test_settings
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def sample_qr_config() -> QRGenerationRequest:
    """Sample QR configuration for testing."""
    return QRGenerationRequest(
        url="https://example.com",
        size=512,
        border=4,
        style="rounded",
        dark_color="#000000",
        light_color="#FFFFFF",
        ec_level="M",
        eye_radius=0.9,
        eye_scale_x=1.0,
        eye_scale_y=1.0,
        eye_shape="rect",
        eye_style="standard",
        logo_scale=0.22,
        bg_padding=20,
        bg_radius=28,
        qr_radius=0,
        compress_level=6,
        quantize_colors=64,
    )


@pytest.fixture
def sample_logo_bytes() -> bytes:
    """Sample logo image as bytes."""
    # Create a simple test image
    img = Image.new("RGBA", (100, 100), (255, 0, 0, 255))  # Red square
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    return img_bytes.getvalue()


@pytest.fixture
def invalid_image_bytes() -> bytes:
    """Invalid image data for testing error cases."""
    return b"not-an-image-file"


@pytest.fixture
def large_image_bytes() -> bytes:
    """Large image for testing size limits."""
    # Create a large image (3000x3000)
    img = Image.new("RGB", (3000, 3000), (0, 255, 0))  # Green square
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    return img_bytes.getvalue()


@pytest.fixture
def mock_cache_manager() -> MagicMock:
    """Mock cache manager for testing without Redis."""
    mock = MagicMock(spec=CacheManager)
    mock.connect = AsyncMock(return_value=True)
    mock.disconnect = AsyncMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=True)
    mock.exists = AsyncMock(return_value=False)
    mock.get_stats = AsyncMock(
        return_value={
            "connected": True,
            "memory_usage": 1024,
            "keyspace_hits": 100,
            "keyspace_misses": 10,
            "hit_rate": 0.91,
        }
    )
    return mock


# Test data
VALID_URLS = [
    "https://example.com",
    "http://localhost:3000",
    "mailto:test@example.com",
    "tel:+1234567890",
    "https://subdomain.example.com/path?query=value",
]

INVALID_URLS = [
    "",  # Empty string
    "x" * 2001,  # Too long
]

VALID_HEX_COLORS = [
    "#000000",
    "#FFFFFF",
    "#FF0000",
    "#00FF00",
    "#0000FF",
    "#123456",
]

INVALID_HEX_COLORS = [
    "",
    "#GGG",  # Invalid hex
    "#12345",  # Wrong length
    "#1234567",  # Too long
    "red",  # Named color
]
