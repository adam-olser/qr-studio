import logging
import asyncio
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, HTTPException

from ..core.config import settings
from ..core.exceptions import ServiceUnavailableException
from ..core.cache import cache_manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint

    Returns service status and basic information
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "qr-studio-api",
        "version": "1.0.0",
        "environment": settings.ENV,
    }


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint with dependency validation

    Checks if the service is ready to handle requests by validating:
    - Basic service health
    - Dependencies (Redis, file system, etc.)

    Returns:
        Service readiness status

    Raises:
        ServiceUnavailableException: If service is not ready
    """
    logger.debug("Performing readiness check")

    checks = {
        "service": False,
        "dependencies": False,
    }

    try:
        # Basic service check
        checks["service"] = True

        # Check dependencies
        dependency_checks = await _check_dependencies()
        checks.update(dependency_checks)
        checks["dependencies"] = all(dependency_checks.values())

        # Overall status
        is_ready = all(checks.values())

        result = {
            "status": "ready" if is_ready else "not_ready",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks,
        }

        if not is_ready:
            logger.warning(f"Readiness check failed: {checks}")
            raise ServiceUnavailableException("Service not ready", {"checks": checks})

        logger.debug("Readiness check passed")
        return result

    except ServiceUnavailableException:
        raise
    except Exception as e:
        logger.error(f"Readiness check error: {str(e)}", exc_info=True)
        raise ServiceUnavailableException(f"Readiness check failed: {str(e)}")


@router.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check endpoint

    Simple check to verify the service is alive and responding
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/cache")
async def cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics and health

    Returns:
        Cache statistics and performance metrics
    """
    try:
        stats = await cache_manager.get_stats()
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "cache": stats,
        }
    except Exception as e:
        logger.error(f"Cache stats error: {str(e)}", exc_info=True)
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "cache": {"connected": False, "error": str(e)},
        }


async def _check_dependencies() -> Dict[str, bool]:
    """
    Check external dependencies

    Returns:
        Dictionary of dependency check results
    """
    checks = {}

    # Check Redis connection (if configured)
    if settings.REDIS_URL:
        checks["redis"] = await _check_redis()

    # Check file system write permissions
    checks["filesystem"] = await _check_filesystem()

    # Check QR generation service
    checks["qr_service"] = await _check_qr_service()

    return checks


async def _check_redis() -> bool:
    """Check Redis connectivity"""
    try:
        # Import here to avoid dependency issues if Redis is not available
        import redis.asyncio as redis

        client = redis.from_url(settings.REDIS_URL)
        await client.ping()
        await client.close()
        return True
    except Exception as e:
        logger.warning(f"Redis check failed: {str(e)}")
        return False


async def _check_filesystem() -> bool:
    """Check filesystem write permissions"""
    try:
        import tempfile
        import os

        # Try to create and write to a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"health_check")
            tmp_path = tmp.name

        # Clean up
        os.unlink(tmp_path)
        return True
    except Exception as e:
        logger.warning(f"Filesystem check failed: {str(e)}")
        return False


async def _check_qr_service() -> bool:
    """Check QR generation service"""
    try:
        from ..services.qr_generator import qr_service

        # Try to get presets (lightweight operation)
        presets = qr_service.get_preset_configs()
        return len(presets) > 0
    except Exception as e:
        logger.warning(f"QR service check failed: {str(e)}")
        return False
