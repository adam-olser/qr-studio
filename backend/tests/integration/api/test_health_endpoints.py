"""
Integration tests for health API endpoints
"""

from unittest.mock import patch, AsyncMock
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient


class TestHealthEndpoints:
    """Test health check API endpoints."""

    def test_health_check(self, test_client: TestClient):
        """Test basic health check endpoint."""
        response = test_client.get("/api/v1/health")

        assert response.status_code == 200
        health_data = response.json()

        assert "status" in health_data
        assert "timestamp" in health_data
        assert "service" in health_data
        assert "version" in health_data
        assert "environment" in health_data

        assert health_data["status"] == "healthy"
        assert health_data["service"] == "qr-studio-api"

    @patch("app.api.health._check_dependencies")
    async def test_readiness_check_ready(
        self, mock_check_deps, async_client: AsyncClient
    ):
        """Test readiness check when all dependencies are ready."""
        mock_check_deps.return_value = (True, {})

        response = await async_client.get("/api/v1/health/ready")

        assert response.status_code == 200
        readiness_data = response.json()

        assert readiness_data["status"] == "ready"
        assert "timestamp" in readiness_data
        assert "checks" in readiness_data

    @patch("app.api.health._check_dependencies")
    async def test_readiness_check_not_ready(
        self, mock_check_deps, async_client: AsyncClient
    ):
        """Test readiness check when dependencies are not ready."""
        mock_check_deps.return_value = (False, {"redis": "Connection failed"})

        response = await async_client.get("/api/v1/health/ready")

        assert response.status_code == 503
        readiness_data = response.json()

        assert readiness_data["status"] == "not ready"
        assert "checks" in readiness_data
        assert "redis" in readiness_data["checks"]

    def test_liveness_check(self, test_client: TestClient):
        """Test liveness check endpoint."""
        response = test_client.get("/api/v1/health/live")

        assert response.status_code == 200
        liveness_data = response.json()

        assert liveness_data["status"] == "alive"
        assert "timestamp" in liveness_data

    @patch("app.api.health.cache_manager.get_stats")
    async def test_cache_stats_success(self, mock_get_stats, async_client: AsyncClient):
        """Test cache stats endpoint when cache is working."""
        mock_stats = {
            "connected": True,
            "memory_usage": 1024,
            "keyspace_hits": 100,
            "keyspace_misses": 10,
            "hit_rate": 0.91,
        }
        mock_get_stats.return_value = mock_stats

        response = await async_client.get("/api/v1/health/cache")

        assert response.status_code == 200
        cache_data = response.json()

        assert "timestamp" in cache_data
        assert "cache" in cache_data
        assert cache_data["cache"] == mock_stats

    @patch("app.api.health.cache_manager.get_stats")
    async def test_cache_stats_error(self, mock_get_stats, async_client: AsyncClient):
        """Test cache stats endpoint when cache has error."""
        mock_get_stats.side_effect = Exception("Redis connection failed")

        response = await async_client.get("/api/v1/health/cache")

        assert response.status_code == 200  # Still returns 200 but with error info
        cache_data = response.json()

        assert "timestamp" in cache_data
        assert "cache" in cache_data
        assert cache_data["cache"]["connected"] is False
        assert "error" in cache_data["cache"]


class TestHealthDependencyChecks:
    """Test health dependency check functions."""

    @patch("app.api.health._check_redis")
    @patch("app.api.health._check_filesystem")
    @patch("app.api.health._check_qr_service")
    async def test_check_dependencies_all_pass(
        self, mock_qr, mock_fs, mock_redis, async_client: AsyncClient
    ):
        """Test dependency checks when all pass."""
        mock_redis.return_value = (True, None)
        mock_fs.return_value = (True, None)
        mock_qr.return_value = (True, None)

        # Import the function to test it directly
        from app.api.health import _check_dependencies

        is_ready, failed_checks = await _check_dependencies()

        assert is_ready is True
        assert failed_checks == {}

    @patch("app.api.health._check_redis")
    @patch("app.api.health._check_filesystem")
    @patch("app.api.health._check_qr_service")
    async def test_check_dependencies_redis_fails(
        self, mock_qr, mock_fs, mock_redis, async_client: AsyncClient
    ):
        """Test dependency checks when Redis fails."""
        mock_redis.return_value = (False, "Connection timeout")
        mock_fs.return_value = (True, None)
        mock_qr.return_value = (True, None)

        from app.api.health import _check_dependencies

        is_ready, failed_checks = await _check_dependencies()

        assert is_ready is False
        assert "redis" in failed_checks
        assert failed_checks["redis"] == "Connection timeout"

    @patch("app.api.health.cache_manager")
    async def test_check_redis_success(self, mock_cache_manager):
        """Test Redis check when connection is successful."""
        mock_cache_manager._connected = True
        mock_cache_manager._redis.ping = AsyncMock()

        from app.api.health import _check_redis

        is_healthy, error = await _check_redis()

        assert is_healthy is True
        assert error is None

    @patch("app.api.health.cache_manager")
    async def test_check_redis_disconnected(self, mock_cache_manager):
        """Test Redis check when not connected."""
        mock_cache_manager._connected = False

        from app.api.health import _check_redis

        is_healthy, error = await _check_redis()

        assert is_healthy is False
        assert "not connected" in error.lower()

    @patch("app.api.health.cache_manager")
    async def test_check_redis_ping_fails(self, mock_cache_manager):
        """Test Redis check when ping fails."""
        mock_cache_manager._connected = True
        mock_cache_manager._redis.ping = AsyncMock(
            side_effect=Exception("Connection lost")
        )

        from app.api.health import _check_redis

        is_healthy, error = await _check_redis()

        assert is_healthy is False
        assert "Connection lost" in error

    @patch("os.path.exists")
    @patch("os.access")
    async def test_check_filesystem_success(self, mock_access, mock_exists):
        """Test filesystem check when all is well."""
        mock_exists.return_value = True
        mock_access.return_value = True

        from app.api.health import _check_filesystem

        is_healthy, error = await _check_filesystem()

        assert is_healthy is True
        assert error is None

    @patch("os.path.exists")
    async def test_check_filesystem_missing_directory(self, mock_exists):
        """Test filesystem check when directory is missing."""
        mock_exists.return_value = False

        from app.api.health import _check_filesystem

        is_healthy, error = await _check_filesystem()

        assert is_healthy is False
        assert "does not exist" in error

    @patch("app.api.health.qr_service")
    async def test_check_qr_service_success(self, mock_qr_service):
        """Test QR service check when service is working."""
        mock_qr_service.get_preset_configs.return_value = {"test": {}}

        from app.api.health import _check_qr_service

        is_healthy, error = await _check_qr_service()

        assert is_healthy is True
        assert error is None

    @patch("app.api.health.qr_service")
    async def test_check_qr_service_failure(self, mock_qr_service):
        """Test QR service check when service fails."""
        mock_qr_service.get_preset_configs.side_effect = Exception("Service error")

        from app.api.health import _check_qr_service

        is_healthy, error = await _check_qr_service()

        assert is_healthy is False
        assert "Service error" in error


class TestHealthEndpointsIntegration:
    """Integration tests for health endpoints with real dependencies."""

    def test_health_endpoints_accessible(self, test_client: TestClient):
        """Test that all health endpoints are accessible."""
        endpoints = [
            "/api/v1/health",
            "/api/v1/health/ready",
            "/api/v1/health/live",
            "/api/v1/health/cache",
        ]

        for endpoint in endpoints:
            response = test_client.get(endpoint)
            # Should not return 404 (endpoint exists)
            assert response.status_code != 404
            # Should return JSON
            assert response.headers.get("content-type") == "application/json"

    def test_health_response_structure(self, test_client: TestClient):
        """Test that health responses have consistent structure."""
        response = test_client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()

        # Required fields
        required_fields = ["status", "timestamp", "service", "version", "environment"]
        for field in required_fields:
            assert field in data
            assert data[field] is not None

    def test_readiness_response_structure(self, test_client: TestClient):
        """Test that readiness responses have consistent structure."""
        response = test_client.get("/api/v1/health/ready")

        # Should be either 200 (ready) or 503 (not ready)
        assert response.status_code in [200, 503]
        data = response.json()

        # Required fields
        required_fields = ["status", "timestamp", "checks"]
        for field in required_fields:
            assert field in data

        # Status should be either "ready" or "not ready"
        assert data["status"] in ["ready", "not ready"]
