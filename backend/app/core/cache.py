"""
Caching utilities for QR Studio
"""

import json
import hashlib
import logging
from typing import Optional, Any, Dict, Union
from datetime import datetime, timedelta
import redis.asyncio as redis

from .config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Redis-based cache manager for QR Studio
    """

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self._redis: Optional[redis.Redis] = None
        self._connected = False

    async def connect(self) -> bool:
        """
        Connect to Redis

        Returns:
            True if connection successful
        """
        try:
            self._redis = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )

            # Test connection
            await self._redis.ping()
            self._connected = True
            logger.info("Connected to Redis cache")
            return True

        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {str(e)}")
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        if self._redis:
            await self._redis.close()
            self._connected = False
            logger.info("Disconnected from Redis cache")

    def _generate_key(self, prefix: str, data: Union[str, Dict[str, Any]]) -> str:
        """
        Generate cache key from data

        Args:
            prefix: Key prefix
            data: Data to hash

        Returns:
            Cache key
        """
        if isinstance(data, dict):
            # Sort keys for consistent hashing
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)

        # Create hash
        hash_obj = hashlib.sha256(data_str.encode())
        hash_hex = hash_obj.hexdigest()[:16]  # Use first 16 chars

        return f"qr_studio:{prefix}:{hash_hex}"

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if not self._connected or not self._redis:
            return None

        try:
            value = await self._redis.get(key)
            if value:
                return json.loads(value)
            return None

        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {str(e)}")
            return None

    async def set(
        self, key: str, value: Any, ttl: int = 3600, nx: bool = False
    ) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            nx: Only set if key doesn't exist

        Returns:
            True if set successfully
        """
        if not self._connected or not self._redis:
            return False

        try:
            serialized = json.dumps(value, default=str)
            result = await self._redis.set(key, serialized, ex=ttl, nx=nx)
            return bool(result)

        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete key from cache

        Args:
            key: Cache key

        Returns:
            True if deleted
        """
        if not self._connected or not self._redis:
            return False

        try:
            result = await self._redis.delete(key)
            return bool(result)

        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        if not self._connected or not self._redis:
            return False

        try:
            result = await self._redis.exists(key)
            return bool(result)

        except Exception as e:
            logger.warning(f"Cache exists error for key {key}: {str(e)}")
            return False

    async def increment(
        self, key: str, amount: int = 1, ttl: int = 3600
    ) -> Optional[int]:
        """
        Increment counter in cache

        Args:
            key: Cache key
            amount: Amount to increment
            ttl: TTL for new keys

        Returns:
            New value or None
        """
        if not self._connected or not self._redis:
            return None

        try:
            # Use pipeline for atomic operations
            async with self._redis.pipeline() as pipe:
                await pipe.incr(key, amount)
                await pipe.expire(key, ttl)
                results = await pipe.execute()
                return int(results[0])

        except Exception as e:
            logger.warning(f"Cache increment error for key {key}: {str(e)}")
            return None

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Cache statistics
        """
        if not self._connected or not self._redis:
            return {"connected": False}

        try:
            info = await self._redis.info()
            return {
                "connected": True,
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0), info.get("keyspace_misses", 0)
                ),
            }

        except Exception as e:
            logger.warning(f"Cache stats error: {str(e)}")
            return {"connected": False, "error": str(e)}

    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate"""
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0.0


class QRCache:
    """
    QR code specific caching operations
    """

    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.qr_ttl = 3600 * 24  # 24 hours for QR codes
        self.preset_ttl = 3600 * 24 * 7  # 7 days for presets
        self.validation_ttl = 3600  # 1 hour for URL validation

    async def get_qr_code(
        self, config: Dict[str, Any], logo_hash: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Get cached QR code

        Args:
            config: QR configuration
            logo_hash: Hash of logo file

        Returns:
            Cached QR code bytes or None
        """
        cache_data = config.copy()
        if logo_hash:
            cache_data["logo_hash"] = logo_hash

        key = self.cache._generate_key("qr", cache_data)

        try:
            cached = await self.cache.get(key)
            if cached and "data" in cached:
                # Decode base64 data
                import base64

                return base64.b64decode(cached["data"])
            return None

        except Exception as e:
            logger.warning(f"QR cache get error: {str(e)}")
            return None

    async def set_qr_code(
        self, config: Dict[str, Any], qr_bytes: bytes, logo_hash: Optional[str] = None
    ) -> bool:
        """
        Cache QR code

        Args:
            config: QR configuration
            qr_bytes: QR code bytes
            logo_hash: Hash of logo file

        Returns:
            True if cached successfully
        """
        cache_data = config.copy()
        if logo_hash:
            cache_data["logo_hash"] = logo_hash

        key = self.cache._generate_key("qr", cache_data)

        try:
            # Encode bytes as base64 for JSON serialization
            import base64

            cached_data = {
                "data": base64.b64encode(qr_bytes).decode("utf-8"),
                "size": len(qr_bytes),
                "created_at": datetime.utcnow().isoformat(),
                "config": config,
            }

            return await self.cache.set(key, cached_data, ttl=self.qr_ttl)

        except Exception as e:
            logger.warning(f"QR cache set error: {str(e)}")
            return False

    async def get_url_validation(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get cached URL validation result

        Args:
            url: URL to validate

        Returns:
            Cached validation result or None
        """
        key = self.cache._generate_key("url_validation", url)
        return await self.cache.get(key)

    async def set_url_validation(
        self, url: str, validation_result: Dict[str, Any]
    ) -> bool:
        """
        Cache URL validation result

        Args:
            url: URL that was validated
            validation_result: Validation result

        Returns:
            True if cached successfully
        """
        key = self.cache._generate_key("url_validation", url)

        cached_data = {
            **validation_result,
            "cached_at": datetime.utcnow().isoformat(),
        }

        return await self.cache.set(key, cached_data, ttl=self.validation_ttl)

    async def get_presets(self) -> Optional[Dict[str, Any]]:
        """
        Get cached presets

        Returns:
            Cached presets or None
        """
        key = "qr_studio:presets:all"
        return await self.cache.get(key)

    async def set_presets(self, presets: Dict[str, Any]) -> bool:
        """
        Cache presets

        Args:
            presets: Presets to cache

        Returns:
            True if cached successfully
        """
        key = "qr_studio:presets:all"

        cached_data = {
            "presets": presets,
            "cached_at": datetime.utcnow().isoformat(),
        }

        return await self.cache.set(key, cached_data, ttl=self.preset_ttl)

    def generate_logo_hash(self, logo_data: bytes) -> str:
        """
        Generate hash for logo data

        Args:
            logo_data: Logo file bytes

        Returns:
            SHA256 hash of logo data
        """
        return hashlib.sha256(logo_data).hexdigest()[:16]


# Global cache instances
cache_manager = CacheManager()
qr_cache = QRCache(cache_manager)


async def init_cache() -> None:
    """Initialize cache connection"""
    await cache_manager.connect()


async def close_cache() -> None:
    """Close cache connection"""
    await cache_manager.disconnect()
