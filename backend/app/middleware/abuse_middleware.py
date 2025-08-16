"""
Abuse Protection Middleware

This middleware integrates comprehensive abuse protection into the FastAPI application.
"""

import time
import logging
import os
from typing import Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from ..core.abuse_protection import check_abuse_protection, advanced_rate_limiter
from ..core.config import settings

logger = logging.getLogger(__name__)


class AbuseProtectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware that applies comprehensive abuse protection to all requests
    """

    def __init__(self, app: Any):
        super().__init__(app)
        self.start_time = time.time()

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """Process request with abuse protection"""
        start_time = time.time()
        client_ip = self._get_client_ip(request)

        try:
            # Skip abuse protection in testing environment
            # Check both settings and environment variables for test mode
            is_test_env = (
                settings.ENV == "test" or 
                os.getenv("ENV") == "test" or 
                os.getenv("PYTEST_CURRENT_TEST") is not None or
                not settings.ENABLE_ABUSE_PROTECTION
            )
            
            if settings.ENABLE_ABUSE_PROTECTION and not is_test_env:
                # Apply abuse protection checks
                is_allowed, error_response = await check_abuse_protection(request)
                if not is_allowed and error_response:
                    # Log the blocked request
                    body_text = "Unknown reason"
                    if hasattr(error_response, 'body') and error_response.body:
                        if isinstance(error_response.body, bytes):
                            body_text = error_response.body.decode()
                        elif isinstance(error_response.body, memoryview):
                            body_text = bytes(error_response.body).decode()
                        else:
                            body_text = str(error_response.body)
                    logger.warning(
                        f"Request blocked from {client_ip} to {request.url.path}: {body_text}"
                    )
                    return error_response

            # Process the request
            response = await call_next(request)

            # Record successful request metrics
            processing_time = time.time() - start_time
            await self._record_request_metrics(
                request, response, client_ip, processing_time
            )

            # Add abuse protection headers
            self._add_protection_headers(response, client_ip)

            return response  # type: ignore

        except Exception as e:
            # Record error and let it propagate
            logger.error(f"Error in abuse protection middleware: {e}")
            await advanced_rate_limiter.record_error(client_ip, "middleware_error")

            # Still try to process the request
            try:
                response = await call_next(request)
                return response  # type: ignore
            except Exception as inner_e:
                logger.error(
                    f"Error processing request after middleware error: {inner_e}"
                )
                return JSONResponse(
                    status_code=500,
                    content={
                        "message": "Internal server error",
                        "error_code": "INTERNAL_ERROR",
                    },
                )

    def _get_client_ip(self, request: Request) -> str:
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

    async def _record_request_metrics(
        self,
        request: Request,
        response: Response,
        client_ip: str,
        processing_time: float,
    ) -> None:
        """Record request metrics for monitoring"""
        # Record errors for abuse detection
        if response.status_code >= 400:
            error_type = (
                "client_error" if response.status_code < 500 else "server_error"
            )
            await advanced_rate_limiter.record_error(client_ip, error_type)

        # Log slow requests
        if processing_time > 5.0:  # More than 5 seconds
            logger.warning(
                f"Slow request from {client_ip}: {request.method} {request.url.path} "
                f"took {processing_time:.2f}s"
            )

        # Log large responses (potential data exfiltration)
        content_length = response.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > 10 * 1024 * 1024:  # 10MB
                    logger.warning(
                        f"Large response to {client_ip}: {size} bytes for {request.url.path}"
                    )
            except ValueError:
                pass

    def _add_protection_headers(self, response: Response, client_ip: str) -> None:
        """Add abuse protection related headers"""
        # Add rate limit headers
        if (
            hasattr(advanced_rate_limiter, "client_metrics")
            and client_ip in advanced_rate_limiter.client_metrics
        ):
            metrics = advanced_rate_limiter.client_metrics[client_ip]
            response.headers["X-RateLimit-Remaining"] = str(
                max(0, 30 - metrics.request_count)
            )
            response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))
            response.headers["X-Threat-Level"] = metrics.threat_level.value

        # Add server identification (helps with debugging)
        response.headers["X-Protected-By"] = "QR-Studio-Abuse-Protection"

        # Add cache control for expensive endpoints
        if "/qr/generate" in response.headers.get("X-Request-Path", ""):
            response.headers["Cache-Control"] = "private, max-age=300"  # 5 minutes
