"""
Admin endpoints for monitoring and management
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..core.config import settings
from ..core.abuse_protection import (
    get_abuse_stats,
    advanced_rate_limiter,
    cost_protection,
)

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


def verify_admin_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> bool:
    """
    Verify admin token for accessing admin endpoints
    In production, use proper authentication
    """
    # Simple token check - in production, use proper JWT validation
    expected_token = getattr(settings, "ADMIN_TOKEN", "admin-secret-token")
    if credentials.credentials != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True


@router.get("/stats")
async def get_protection_stats(
    admin: bool = Depends(verify_admin_token),
) -> Dict[str, Any]:
    """
    Get comprehensive abuse protection statistics

    Requires admin authentication
    """
    try:
        stats = await get_abuse_stats()
        return {
            "status": "success",
            "data": stats,
            "message": "Abuse protection statistics retrieved successfully",
        }
    except Exception as e:
        logger.error(f"Error getting abuse stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics",
        )


@router.get("/blocked-ips")
async def get_blocked_ips(admin: bool = Depends(verify_admin_token)) -> Dict[str, Any]:
    """
    Get list of currently blocked IPs

    Requires admin authentication
    """
    try:
        blocked_ips = list(advanced_rate_limiter.blocked_ips)
        client_metrics = {}

        for ip in blocked_ips:
            if ip in advanced_rate_limiter.client_metrics:
                metrics = advanced_rate_limiter.client_metrics[ip]
                client_metrics[ip] = {
                    "threat_level": metrics.threat_level.value,
                    "violations": len(metrics.violations),
                    "blocked_until": metrics.blocked_until,
                    "request_count": metrics.request_count,
                    "error_count": metrics.error_count,
                }

        return {
            "status": "success",
            "data": {
                "blocked_ips": blocked_ips,
                "count": len(blocked_ips),
                "details": client_metrics,
            },
            "message": f"Found {len(blocked_ips)} blocked IPs",
        }
    except Exception as e:
        logger.error(f"Error getting blocked IPs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve blocked IPs",
        )


@router.post("/unblock-ip/{ip_address}")
async def unblock_ip(
    ip_address: str, admin: bool = Depends(verify_admin_token)
) -> Dict[str, Any]:
    """
    Manually unblock an IP address

    Requires admin authentication
    """
    try:
        if ip_address in advanced_rate_limiter.blocked_ips:
            advanced_rate_limiter.blocked_ips.remove(ip_address)

            # Reset metrics for this IP
            if ip_address in advanced_rate_limiter.client_metrics:
                metrics = advanced_rate_limiter.client_metrics[ip_address]
                metrics.blocked_until = None
                metrics.threat_level = metrics.threat_level.__class__.LOW

            logger.info(f"IP {ip_address} manually unblocked by admin")

            return {
                "status": "success",
                "message": f"IP {ip_address} has been unblocked",
            }
        else:
            return {"status": "info", "message": f"IP {ip_address} was not blocked"}
    except Exception as e:
        logger.error(f"Error unblocking IP {ip_address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unblock IP",
        )


@router.get("/usage-stats")
async def get_usage_stats(admin: bool = Depends(verify_admin_token)) -> Dict[str, Any]:
    """
    Get current usage statistics for cost protection

    Requires admin authentication
    """
    try:
        usage_stats = cost_protection.get_usage_stats()
        return {
            "status": "success",
            "data": usage_stats,
            "message": "Usage statistics retrieved successfully",
        }
    except Exception as e:
        logger.error(f"Error getting usage stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage statistics",
        )


@router.post("/reset-limits")
async def reset_limits(admin: bool = Depends(verify_admin_token)) -> Dict[str, Any]:
    """
    Reset all rate limits and usage counters (emergency use only)

    Requires admin authentication
    """
    try:
        # Reset rate limiter
        advanced_rate_limiter.client_metrics.clear()
        advanced_rate_limiter.blocked_ips.clear()
        advanced_rate_limiter.concurrent_requests.clear()

        # Reset cost protection counters
        cost_protection.daily_usage.clear()
        cost_protection.hourly_usage.clear()

        logger.warning("All rate limits and usage counters reset by admin")

        return {
            "status": "success",
            "message": "All limits and counters have been reset",
        }
    except Exception as e:
        logger.error(f"Error resetting limits: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset limits",
        )


@router.get("/health-detailed")
async def get_detailed_health(
    admin: bool = Depends(verify_admin_token),
) -> Dict[str, Any]:
    """
    Get detailed health information including abuse protection status

    Requires admin authentication
    """
    try:
        stats = await get_abuse_stats()

        # Calculate health score based on various metrics
        health_score = 100
        warnings = []

        # Check blocked IPs
        blocked_count = stats["rate_limiter"]["blocked_ips"]
        if blocked_count > 10:
            health_score -= 20
            warnings.append(f"High number of blocked IPs: {blocked_count}")

        # Check threat levels
        threat_levels = stats["rate_limiter"]["threat_levels"]
        high_threat_count = threat_levels.get("high", 0) + threat_levels.get(
            "critical", 0
        )
        if high_threat_count > 5:
            health_score -= 15
            warnings.append(f"High threat level clients: {high_threat_count}")

        # Check concurrent requests
        concurrent = stats["rate_limiter"]["concurrent_requests"]
        if concurrent > 50:
            health_score -= 10
            warnings.append(f"High concurrent requests: {concurrent}")

        # Determine status
        if health_score >= 90:
            status_text = "excellent"
        elif health_score >= 70:
            status_text = "good"
        elif health_score >= 50:
            status_text = "warning"
        else:
            status_text = "critical"

        return {
            "status": "success",
            "data": {
                "health_score": health_score,
                "status": status_text,
                "warnings": warnings,
                "detailed_stats": stats,
                "timestamp": stats["timestamp"],
            },
            "message": f"System health: {status_text} ({health_score}/100)",
        }
    except Exception as e:
        logger.error(f"Error getting detailed health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve detailed health information",
        )
