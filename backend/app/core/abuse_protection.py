"""
Advanced Abuse Protection for QR Studio

This module implements comprehensive abuse protection measures to prevent
service abuse, resource exhaustion, and bill racking when deployed publicly.
"""

import time
import hashlib
import logging
import asyncio
from typing import Dict, Set, Optional, Tuple, List
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from fastapi import Request, HTTPException, status
from starlette.responses import JSONResponse

from .config import settings
from .cache import cache_manager

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Threat levels for different types of abuse"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AbuseMetrics:
    """Metrics for tracking abuse patterns"""

    request_count: int = 0
    error_count: int = 0
    large_file_count: int = 0
    suspicious_patterns: int = 0
    last_request_time: float = 0
    first_request_time: float = 0
    blocked_until: Optional[float] = None
    threat_level: ThreatLevel = ThreatLevel.LOW
    violations: List[str] = field(default_factory=list)


class AdvancedRateLimiter:
    """
    Advanced rate limiter with adaptive limits and abuse detection
    """

    def __init__(self):
        self.client_metrics: Dict[str, AbuseMetrics] = {}
        self.global_metrics = AbuseMetrics()
        self.blocked_ips: Set[str] = set()
        self.suspicious_patterns = {
            "rapid_requests": 50,  # More than 50 requests in 60 seconds
            "error_rate": 0.5,  # More than 50% error rate
            "large_files": 10,  # More than 10 large files in 60 seconds
            "burst_requests": 20,  # More than 20 requests in 10 seconds
        }

        # Adaptive limits based on system load
        self.base_limits = {
            "requests_per_minute": 30,
            "qr_generations_per_minute": 10,
            "file_uploads_per_minute": 5,
            "max_file_size": 5 * 1024 * 1024,  # 5MB
            "max_concurrent_requests": 5,
        }

        # Track concurrent requests per IP
        self.concurrent_requests: Dict[str, int] = defaultdict(int)

    async def check_request(
        self, request: Request, client_ip: str
    ) -> Tuple[bool, Optional[str], Dict]:
        """
        Comprehensive request checking with abuse detection

        Returns:
            (is_allowed, block_reason, rate_info)
        """
        now = time.time()
        path = request.url.path
        method = request.method

        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            metrics = self.client_metrics.get(client_ip, AbuseMetrics())
            if metrics.blocked_until and now < metrics.blocked_until:
                return False, "IP temporarily blocked due to abuse", {}
            else:
                # Unblock if time has passed
                self.blocked_ips.discard(client_ip)
                if client_ip in self.client_metrics:
                    self.client_metrics[client_ip].blocked_until = None

        # Get or create client metrics
        if client_ip not in self.client_metrics:
            self.client_metrics[client_ip] = AbuseMetrics(first_request_time=now)

        metrics = self.client_metrics[client_ip]
        metrics.last_request_time = now

        # Check concurrent requests
        if (
            self.concurrent_requests[client_ip]
            >= self.base_limits["max_concurrent_requests"]
        ):
            self._record_violation(client_ip, "too_many_concurrent_requests")
            return False, "Too many concurrent requests", {}

        # Increment concurrent counter
        self.concurrent_requests[client_ip] += 1

        try:
            # Check various abuse patterns
            is_allowed, reason = await self._check_abuse_patterns(
                request, client_ip, metrics, now
            )
            if not is_allowed:
                return False, reason, {}

            # Check endpoint-specific limits
            is_allowed, reason = self._check_endpoint_limits(
                path, method, client_ip, metrics, now
            )
            if not is_allowed:
                return False, reason, {}

            # Update metrics
            metrics.request_count += 1

            # Calculate rate info
            rate_info = self._calculate_rate_info(client_ip, metrics, now)

            return True, None, rate_info

        finally:
            # Always decrement concurrent counter
            self.concurrent_requests[client_ip] = max(
                0, self.concurrent_requests[client_ip] - 1
            )

    async def _check_abuse_patterns(
        self, request: Request, client_ip: str, metrics: AbuseMetrics, now: float
    ) -> Tuple[bool, Optional[str]]:
        """Check for various abuse patterns"""

        # Pattern 1: Rapid requests (burst detection)
        time_window = 10  # 10 seconds
        if now - metrics.last_request_time < 0.5:  # Less than 500ms between requests
            recent_requests = sum(
                1 for t in getattr(metrics, "recent_times", []) if now - t < time_window
            )
            if recent_requests > self.suspicious_patterns["burst_requests"]:
                self._escalate_threat_level(client_ip, "burst_requests")
                return False, "Request rate too high - burst detected"

        # Pattern 2: Suspicious User-Agent
        user_agent = request.headers.get("user-agent", "").lower()
        suspicious_agents = [
            "bot",
            "crawler",
            "spider",
            "scraper",
            "curl",
            "wget",
            "python-requests",
            "postman",
            "insomnia",
            "httpie",
            "test",
            "scanner",
            "exploit",
        ]
        if any(agent in user_agent for agent in suspicious_agents):
            if not self._is_legitimate_tool(user_agent):
                self._record_violation(client_ip, "suspicious_user_agent")
                # Don't block immediately, but increase threat level
                self._escalate_threat_level(client_ip, "suspicious_user_agent")

        # Pattern 3: Missing or suspicious headers
        if not request.headers.get("accept"):
            self._record_violation(client_ip, "missing_accept_header")

        # Pattern 4: Unusual request patterns
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.base_limits["max_file_size"]:
                    metrics.large_file_count += 1
                    if (
                        metrics.large_file_count
                        > self.suspicious_patterns["large_files"]
                    ):
                        self._escalate_threat_level(client_ip, "large_files")
                        return False, "Too many large file uploads"
            except ValueError:
                self._record_violation(client_ip, "invalid_content_length")

        return True, None

    def _check_endpoint_limits(
        self, path: str, method: str, client_ip: str, metrics: AbuseMetrics, now: float
    ) -> Tuple[bool, Optional[str]]:
        """Check endpoint-specific rate limits"""

        # QR generation endpoints - most expensive
        if "/qr/generate" in path and method == "POST":
            limit_key = f"{client_ip}:qr_generation"
            if not self._check_time_window_limit(
                limit_key, self.base_limits["qr_generations_per_minute"], 60
            ):
                return False, "QR generation rate limit exceeded"

        # File upload endpoints
        elif method == "POST" and ("upload" in path or "logo" in path):
            limit_key = f"{client_ip}:file_upload"
            if not self._check_time_window_limit(
                limit_key, self.base_limits["file_uploads_per_minute"], 60
            ):
                return False, "File upload rate limit exceeded"

        # General API endpoints
        else:
            limit_key = f"{client_ip}:general"
            if not self._check_time_window_limit(
                limit_key, self.base_limits["requests_per_minute"], 60
            ):
                return False, "General rate limit exceeded"

        return True, None

    def _check_time_window_limit(
        self, key: str, limit: int, window_seconds: int
    ) -> bool:
        """Check if request is within time window limit"""
        now = time.time()

        # Use a simple in-memory sliding window (in production, use Redis)
        if not hasattr(self, "_time_windows"):
            self._time_windows = defaultdict(deque)

        window = self._time_windows[key]

        # Remove old entries
        while window and window[0] < now - window_seconds:
            window.popleft()

        # Check limit
        if len(window) >= limit:
            return False

        # Add current request
        window.append(now)
        return True

    def _record_violation(self, client_ip: str, violation_type: str):
        """Record a violation for tracking"""
        if client_ip not in self.client_metrics:
            self.client_metrics[client_ip] = AbuseMetrics()

        metrics = self.client_metrics[client_ip]
        metrics.violations.append(f"{time.time()}:{violation_type}")

        # Keep only recent violations (last hour)
        cutoff = time.time() - 3600
        metrics.violations = [
            v for v in metrics.violations if float(v.split(":")[0]) > cutoff
        ]

        logger.warning(f"Violation recorded for {client_ip}: {violation_type}")

    def _escalate_threat_level(self, client_ip: str, reason: str):
        """Escalate threat level and potentially block IP"""
        if client_ip not in self.client_metrics:
            return

        metrics = self.client_metrics[client_ip]

        # Escalate threat level
        if metrics.threat_level == ThreatLevel.LOW:
            metrics.threat_level = ThreatLevel.MEDIUM
        elif metrics.threat_level == ThreatLevel.MEDIUM:
            metrics.threat_level = ThreatLevel.HIGH
        elif metrics.threat_level == ThreatLevel.HIGH:
            metrics.threat_level = ThreatLevel.CRITICAL
            # Block IP for increasing durations
            block_duration = self._calculate_block_duration(len(metrics.violations))
            metrics.blocked_until = time.time() + block_duration
            self.blocked_ips.add(client_ip)
            logger.error(
                f"IP {client_ip} blocked for {block_duration}s due to: {reason}"
            )

    def _calculate_block_duration(self, violation_count: int) -> int:
        """Calculate block duration based on violation count"""
        if violation_count <= 5:
            return 300  # 5 minutes
        elif violation_count <= 10:
            return 900  # 15 minutes
        elif violation_count <= 20:
            return 3600  # 1 hour
        else:
            return 86400  # 24 hours

    def _is_legitimate_tool(self, user_agent: str) -> bool:
        """Check if user agent is from a legitimate tool"""
        legitimate_patterns = [
            "googlebot",
            "bingbot",
            "slackbot",
            "twitterbot",
            "facebookexternalhit",
            "whatsapp",
            "telegram",
            "discord",
            "linkedin",
            "pinterest",
        ]
        return any(pattern in user_agent for pattern in legitimate_patterns)

    def _calculate_rate_info(
        self, client_ip: str, metrics: AbuseMetrics, now: float
    ) -> Dict:
        """Calculate rate limiting information"""
        return {
            "requests_made": metrics.request_count,
            "threat_level": metrics.threat_level.value,
            "violations": len(metrics.violations),
            "blocked_until": metrics.blocked_until,
            "concurrent_requests": self.concurrent_requests[client_ip],
        }

    async def record_error(self, client_ip: str, error_type: str):
        """Record an error for abuse pattern detection"""
        if client_ip not in self.client_metrics:
            self.client_metrics[client_ip] = AbuseMetrics()

        metrics = self.client_metrics[client_ip]
        metrics.error_count += 1

        # Check error rate
        if metrics.request_count > 0:
            error_rate = metrics.error_count / metrics.request_count
            if (
                error_rate > self.suspicious_patterns["error_rate"]
                and metrics.request_count > 10
            ):
                self._escalate_threat_level(client_ip, f"high_error_rate_{error_type}")

    def get_stats(self) -> Dict:
        """Get abuse protection statistics"""
        return {
            "total_clients": len(self.client_metrics),
            "blocked_ips": len(self.blocked_ips),
            "threat_levels": {
                level.value: sum(
                    1 for m in self.client_metrics.values() if m.threat_level == level
                )
                for level in ThreatLevel
            },
            "total_violations": sum(
                len(m.violations) for m in self.client_metrics.values()
            ),
            "concurrent_requests": sum(self.concurrent_requests.values()),
        }


class ResourceMonitor:
    """Monitor system resources and adjust limits dynamically"""

    def __init__(self):
        self.cpu_threshold = 80.0  # CPU usage percentage
        self.memory_threshold = 80.0  # Memory usage percentage
        self.disk_threshold = 90.0  # Disk usage percentage
        self.last_check = 0
        self.check_interval = 30  # Check every 30 seconds

    async def check_resources(self) -> Dict[str, float]:
        """Check system resources (simplified version)"""
        now = time.time()
        if now - self.last_check < self.check_interval:
            return {}

        self.last_check = now

        # In a real implementation, you would check actual system resources
        # For now, return dummy values
        return {
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "disk_usage": 0.0,
            "active_connections": 0,
        }

    def should_throttle(self, resources: Dict[str, float]) -> bool:
        """Determine if we should throttle requests based on resources"""
        return (
            resources.get("cpu_usage", 0) > self.cpu_threshold
            or resources.get("memory_usage", 0) > self.memory_threshold
            or resources.get("disk_usage", 0) > self.disk_threshold
        )


class CostProtection:
    """Protect against cost-related abuse"""

    def __init__(self):
        self.daily_limits = {
            "qr_generations": 10000,  # Max QR codes per day
            "file_uploads": 1000,  # Max file uploads per day
            "api_calls": 100000,  # Max API calls per day
            "bandwidth_mb": 10000,  # Max bandwidth per day (MB)
        }

        self.hourly_limits = {
            "qr_generations": 1000,
            "file_uploads": 100,
            "api_calls": 10000,
            "bandwidth_mb": 1000,
        }

        # Track usage (in production, use persistent storage)
        self.daily_usage = defaultdict(int)
        self.hourly_usage = defaultdict(int)
        self.last_reset = {"daily": 0, "hourly": 0}

    def check_limits(self, operation: str, cost: int = 1) -> Tuple[bool, str]:
        """Check if operation is within cost limits"""
        self._reset_counters()

        # Check daily limits
        daily_key = f"daily_{operation}"
        if self.daily_usage[daily_key] + cost > self.daily_limits.get(
            operation, float("inf")
        ):
            return False, f"Daily limit exceeded for {operation}"

        # Check hourly limits
        hourly_key = f"hourly_{operation}"
        if self.hourly_usage[hourly_key] + cost > self.hourly_limits.get(
            operation, float("inf")
        ):
            return False, f"Hourly limit exceeded for {operation}"

        # Update usage
        self.daily_usage[daily_key] += cost
        self.hourly_usage[hourly_key] += cost

        return True, ""

    def _reset_counters(self):
        """Reset usage counters when time periods expire"""
        now = time.time()

        # Reset daily counters
        if now - self.last_reset["daily"] > 86400:  # 24 hours
            self.daily_usage.clear()
            self.last_reset["daily"] = now

        # Reset hourly counters
        if now - self.last_reset["hourly"] > 3600:  # 1 hour
            self.hourly_usage.clear()
            self.last_reset["hourly"] = now

    def get_usage_stats(self) -> Dict:
        """Get current usage statistics"""
        self._reset_counters()
        return {
            "daily": dict(self.daily_usage),
            "hourly": dict(self.hourly_usage),
            "limits": {"daily": self.daily_limits, "hourly": self.hourly_limits},
        }


# Global instances
advanced_rate_limiter = AdvancedRateLimiter()
resource_monitor = ResourceMonitor()
cost_protection = CostProtection()


async def check_abuse_protection(
    request: Request,
) -> Tuple[bool, Optional[JSONResponse]]:
    """
    Main abuse protection check function

    Returns:
        (is_allowed, error_response)
    """
    client_ip = _get_client_ip(request)

    try:
        # Check rate limiting and abuse patterns
        is_allowed, reason, rate_info = await advanced_rate_limiter.check_request(
            request, client_ip
        )
        if not is_allowed:
            await advanced_rate_limiter.record_error(client_ip, "rate_limit")
            return False, JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "message": reason or "Rate limit exceeded",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "details": rate_info,
                },
            )

        # Check system resources
        resources = await resource_monitor.check_resources()
        if resource_monitor.should_throttle(resources):
            return False, JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "message": "Service temporarily unavailable due to high load",
                    "error_code": "SERVICE_OVERLOADED",
                    "retry_after": 60,
                },
            )

        # Check cost limits for expensive operations
        path = request.url.path
        if "/qr/generate" in path:
            allowed, reason = cost_protection.check_limits("qr_generations")
            if not allowed:
                return False, JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"message": reason, "error_code": "COST_LIMIT_EXCEEDED"},
                )

        return True, None

    except Exception as e:
        logger.error(f"Error in abuse protection: {e}")
        # Fail open but log the error
        return True, None


def _get_client_ip(request: Request) -> str:
    """Get client IP address with proxy support"""
    # Check for forwarded headers (be careful with these in production)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fallback to direct connection IP
    return request.client.host if request.client else "unknown"


async def get_abuse_stats() -> Dict:
    """Get comprehensive abuse protection statistics"""
    return {
        "rate_limiter": advanced_rate_limiter.get_stats(),
        "cost_protection": cost_protection.get_usage_stats(),
        "resources": await resource_monitor.check_resources(),
        "timestamp": time.time(),
    }
