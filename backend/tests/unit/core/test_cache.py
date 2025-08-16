"""
Unit tests for cache system
"""

import json
from unittest.mock import AsyncMock, MagicMock
import pytest
from app.core.cache import CacheManager, QRCache


class TestCacheManager:
    """Test CacheManager functionality."""

    @pytest.fixture
    def cache_manager(self, mock_redis) -> CacheManager:
        """Cache manager with mock Redis."""
        cache = CacheManager("redis://fake")
        cache._redis = mock_redis
        cache._connected = True
        return cache

    async def test_connect_success(self, mock_redis):
        """Test successful Redis connection."""
        cache = CacheManager("redis://fake")
        cache._redis = mock_redis
        mock_redis.ping = AsyncMock()

        result = await cache.connect()
        assert result is True
        assert cache._connected is True

    async def test_connect_failure(self):
        """Test Redis connection failure."""
        cache = CacheManager("redis://invalid")
        result = await cache.connect()
        assert result is False
        assert cache._connected is False

    async def test_disconnect(self, cache_manager):
        """Test Redis disconnection."""
        cache_manager._redis.close = AsyncMock()
        await cache_manager.disconnect()
        cache_manager._redis.close.assert_called_once()
        assert cache_manager._connected is False

    def test_generate_key(self, cache_manager):
        """Test cache key generation."""
        # Test with string data
        key1 = cache_manager._generate_key("test", "data")
        assert key1.startswith("qr_studio:test:")
        assert len(key1.split(":")[-1]) == 16  # Hash length

        # Test with dict data
        key2 = cache_manager._generate_key("test", {"key": "value"})
        assert key2.startswith("qr_studio:test:")

        # Same data should generate same key
        key3 = cache_manager._generate_key("test", {"key": "value"})
        assert key2 == key3

    async def test_get_success(self, cache_manager, mock_redis):
        """Test successful cache get."""
        test_data = {"key": "value"}
        mock_redis.get = AsyncMock(return_value=json.dumps(test_data))

        result = await cache_manager.get("test_key")
        assert result == test_data
        mock_redis.get.assert_called_once_with("test_key")

    async def test_get_not_found(self, cache_manager, mock_redis):
        """Test cache get when key not found."""
        mock_redis.get = AsyncMock(return_value=None)

        result = await cache_manager.get("test_key")
        assert result is None

    async def test_get_disconnected(self):
        """Test cache get when disconnected."""
        cache = CacheManager("redis://fake")
        cache._connected = False

        result = await cache.get("test_key")
        assert result is None

    async def test_set_success(self, cache_manager, mock_redis):
        """Test successful cache set."""
        test_data = {"key": "value"}
        mock_redis.set = AsyncMock(return_value=True)

        result = await cache_manager.set("test_key", test_data, ttl=3600)
        assert result is True
        mock_redis.set.assert_called_once()

    async def test_set_with_nx_flag(self, cache_manager, mock_redis):
        """Test cache set with nx flag."""
        test_data = {"key": "value"}
        mock_redis.set = AsyncMock(return_value=True)

        result = await cache_manager.set("test_key", test_data, ttl=3600, nx=True)
        assert result is True

    async def test_delete_success(self, cache_manager, mock_redis):
        """Test successful cache delete."""
        mock_redis.delete = AsyncMock(return_value=1)

        result = await cache_manager.delete("test_key")
        assert result is True
        mock_redis.delete.assert_called_once_with("test_key")

    async def test_exists_true(self, cache_manager, mock_redis):
        """Test cache exists when key exists."""
        mock_redis.exists = AsyncMock(return_value=1)

        result = await cache_manager.exists("test_key")
        assert result is True

    async def test_exists_false(self, cache_manager, mock_redis):
        """Test cache exists when key doesn't exist."""
        mock_redis.exists = AsyncMock(return_value=0)

        result = await cache_manager.exists("test_key")
        assert result is False

    async def test_increment(self, cache_manager, mock_redis):
        """Test cache increment."""
        mock_pipeline = AsyncMock()
        mock_pipeline.incr = AsyncMock()
        mock_pipeline.expire = AsyncMock()
        mock_pipeline.execute = AsyncMock(return_value=[5])
        mock_redis.pipeline = MagicMock(return_value=mock_pipeline)
        mock_pipeline.__aenter__ = AsyncMock(return_value=mock_pipeline)
        mock_pipeline.__aexit__ = AsyncMock(return_value=None)

        result = await cache_manager.increment("test_key", amount=2, ttl=3600)
        assert result == 5

    async def test_get_stats_success(self, cache_manager, mock_redis):
        """Test successful stats retrieval."""
        mock_info = {
            "used_memory": 1024,
            "keyspace_hits": 100,
            "keyspace_misses": 10,
        }
        mock_redis.info = AsyncMock(return_value=mock_info)

        stats = await cache_manager.get_stats()
        assert stats["connected"] is True
        assert stats["memory_usage"] == 1024
        assert stats["keyspace_hits"] == 100
        assert stats["keyspace_misses"] == 10
        assert stats["hit_rate"] == 0.91  # 100 / (100 + 10)

    async def test_get_stats_disconnected(self):
        """Test stats when disconnected."""
        cache = CacheManager("redis://fake")
        cache._connected = False

        stats = await cache.get_stats()
        assert stats == {"connected": False}


class TestQRCache:
    """Test QRCache functionality."""

    @pytest.fixture
    def qr_cache_instance(self, cache_manager) -> QRCache:
        """QR cache instance."""
        return QRCache(cache_manager)

    async def test_get_qr_code_hit(self, qr_cache_instance, sample_qr_config):
        """Test QR code cache hit."""
        # Mock cache hit
        cached_data = {
            "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
            "created_at": "2023-01-01T00:00:00",
            "config": sample_qr_config.model_dump()
            if hasattr(sample_qr_config, "model_dump")
            else sample_qr_config.__dict__,
        }
        qr_cache_instance.cache.get = AsyncMock(return_value=cached_data)

        config_dict = (
            sample_qr_config.model_dump()
            if hasattr(sample_qr_config, "model_dump")
            else sample_qr_config.__dict__
        )
        result = await qr_cache_instance.get_qr_code(config_dict)

        assert result is not None
        assert isinstance(result, bytes)

    async def test_get_qr_code_miss(self, qr_cache_instance, sample_qr_config):
        """Test QR code cache miss."""
        qr_cache_instance.cache.get = AsyncMock(return_value=None)

        config_dict = (
            sample_qr_config.model_dump()
            if hasattr(sample_qr_config, "model_dump")
            else sample_qr_config.__dict__
        )
        result = await qr_cache_instance.get_qr_code(config_dict)

        assert result is None

    async def test_set_qr_code(self, qr_cache_instance, sample_qr_config):
        """Test QR code cache set."""
        qr_cache_instance.cache.set = AsyncMock(return_value=True)
        test_qr_bytes = b"fake-qr-image-data"

        config_dict = (
            sample_qr_config.model_dump()
            if hasattr(sample_qr_config, "model_dump")
            else sample_qr_config.__dict__
        )
        result = await qr_cache_instance.set_qr_code(config_dict, test_qr_bytes)

        assert result is True
        qr_cache_instance.cache.set.assert_called_once()

    async def test_get_url_validation_hit(self, qr_cache_instance):
        """Test URL validation cache hit."""
        cached_validation = {
            "valid": True,
            "error": None,
            "warning": None,
            "cached_at": "2023-01-01T00:00:00",
        }
        qr_cache_instance.cache.get = AsyncMock(return_value=cached_validation)

        result = await qr_cache_instance.get_url_validation("https://example.com")

        assert result == cached_validation

    async def test_set_url_validation(self, qr_cache_instance):
        """Test URL validation cache set."""
        qr_cache_instance.cache.set = AsyncMock(return_value=True)
        validation_result = {
            "valid": True,
            "error": None,
            "warning": None,
        }

        result = await qr_cache_instance.set_url_validation(
            "https://example.com", validation_result
        )

        assert result is True
        qr_cache_instance.cache.set.assert_called_once()

    async def test_get_presets_hit(self, qr_cache_instance):
        """Test presets cache hit."""
        cached_presets = {
            "presets": {"minimal": {"style": "square"}},
            "cached_at": "2023-01-01T00:00:00",
        }
        qr_cache_instance.cache.get = AsyncMock(return_value=cached_presets)

        result = await qr_cache_instance.get_presets()

        assert result == cached_presets

    async def test_set_presets(self, qr_cache_instance):
        """Test presets cache set."""
        qr_cache_instance.cache.set = AsyncMock(return_value=True)
        presets = {"minimal": {"style": "square"}}

        result = await qr_cache_instance.set_presets(presets)

        assert result is True
        qr_cache_instance.cache.set.assert_called_once()

    def test_generate_logo_hash(self, qr_cache_instance):
        """Test logo hash generation."""
        logo_data = b"fake-logo-data"

        hash1 = qr_cache_instance.generate_logo_hash(logo_data)
        hash2 = qr_cache_instance.generate_logo_hash(logo_data)

        assert hash1 == hash2  # Same data should generate same hash
        assert len(hash1) == 64  # SHA256 hex length

        # Different data should generate different hash
        different_data = b"different-logo-data"
        hash3 = qr_cache_instance.generate_logo_hash(different_data)
        assert hash1 != hash3
