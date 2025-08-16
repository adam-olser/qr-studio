"""
Security utilities and middleware for QR Studio
"""

import time
import hashlib
import logging
from typing import Dict, Optional, Tuple, Any
from collections import defaultdict, deque
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .config import settings
from .exceptions import BadRequestException

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter with sliding window
    """

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, deque] = defaultdict(deque)

    def is_allowed(self, identifier: str) -> Tuple[bool, Dict[str, int]]:
        """
        Check if request is allowed for the given identifier

        Args:
            identifier: Client identifier (IP, user ID, etc.)

        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        now = time.time()
        window_start = now - self.window_seconds

        # Clean old requests
        client_requests = self.requests[identifier]
        while client_requests and client_requests[0] < window_start:
            client_requests.popleft()

        # Check if under limit
        current_requests = len(client_requests)
        is_allowed = current_requests < self.max_requests

        if is_allowed:
            client_requests.append(now)

        # Calculate reset time
        reset_time = (
            int(window_start + self.window_seconds) if client_requests else int(now)
        )

        return is_allowed, {
            "limit": self.max_requests,
            "remaining": max(
                0, self.max_requests - current_requests - (1 if is_allowed else 0)
            ),
            "reset": reset_time,
            "retry_after": max(1, int(client_requests[0] + self.window_seconds - now))
            if not is_allowed and client_requests
            else 0,
        }


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Security middleware for headers and basic protections
    """

    def __init__(self, app: Any, rate_limiter: Optional[RateLimiter] = None):
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter(
            max_requests=100,  # 100 requests per minute by default
            window_seconds=60,
        )

        # Rate limiting for specific endpoints
        self.endpoint_limits = {
            "/api/v1/qr/generate": RateLimiter(
                max_requests=20, window_seconds=60
            ),  # 20 QR generations per minute
            "/api/v1/qr/generate-form": RateLimiter(max_requests=20, window_seconds=60),
            "/api/v1/qr/validate-url": RateLimiter(
                max_requests=50, window_seconds=60
            ),  # 50 validations per minute
        }

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """Process request with security checks"""

        # Get client identifier
        client_ip = self._get_client_ip(request)

        # Apply rate limiting
        if not await self._check_rate_limit(request, client_ip):
            return Response(
                content='{"message": "Rate limit exceeded", "error_code": "RATE_LIMIT_EXCEEDED"}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={"Content-Type": "application/json"},
            )

        # Security headers check
        if not self._validate_request_headers(request):
            return Response(
                content='{"message": "Invalid request headers", "error_code": "INVALID_HEADERS"}',
                status_code=status.HTTP_400_BAD_REQUEST,
                headers={"Content-Type": "application/json"},
            )

        # Process request
        response = await call_next(request)

        # Add security headers
        self._add_security_headers(response)

        return response  # type: ignore

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

    async def _check_rate_limit(self, request: Request, client_ip: str) -> bool:
        """Check rate limits for the request"""
        path = request.url.path

        # Check endpoint-specific limits first
        endpoint_limiter = None
        for endpoint_path, limiter in self.endpoint_limits.items():
            if path.startswith(endpoint_path):
                endpoint_limiter = limiter
                break

        # Apply endpoint-specific rate limiting
        if endpoint_limiter:
            is_allowed, rate_info = endpoint_limiter.is_allowed(f"{client_ip}:{path}")
            if not is_allowed:
                logger.warning(f"Rate limit exceeded for {client_ip} on {path}")
                return False

        # Apply global rate limiting
        is_allowed, rate_info = self.rate_limiter.is_allowed(client_ip)
        if not is_allowed:
            logger.warning(f"Global rate limit exceeded for {client_ip}")
            return False

        return True

    def _validate_request_headers(self, request: Request) -> bool:
        """Validate request headers for security"""
        # Check Content-Length for potential attacks
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length = int(content_length)
                if length > 50 * 1024 * 1024:  # 50MB max
                    logger.warning(
                        f"Request too large: {length} bytes from {self._get_client_ip(request)}"
                    )
                    return False
            except ValueError:
                logger.warning(
                    f"Invalid Content-Length header from {self._get_client_ip(request)}"
                )
                return False

        # Check for suspicious User-Agent patterns
        user_agent = request.headers.get("user-agent", "").lower()
        suspicious_patterns = ["sqlmap", "nikto", "nmap", "masscan", "zap"]
        if any(pattern in user_agent for pattern in suspicious_patterns):
            logger.warning(
                f"Suspicious User-Agent: {user_agent} from {self._get_client_ip(request)}"
            )
            return False

        return True

    def _add_security_headers(self, response: Response) -> None:
        """Add security headers to response"""
        security_headers = {
            # Prevent clickjacking
            "X-Frame-Options": "DENY",
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            # XSS protection
            "X-XSS-Protection": "1; mode=block",
            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            # Content Security Policy (basic)
            "Content-Security-Policy": "default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'",
            # Permissions policy
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            # Server header
            "Server": "QR-Studio/1.0",
        }

        # Add HSTS in production
        if settings.ENV == "production":
            security_headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        for header, value in security_headers.items():
            response.headers[header] = value


def sanitize_input(text: str, max_length: int = 2000, allow_html: bool = False) -> str:
    """
    Sanitize user input

    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        allow_html: Whether to allow HTML tags

    Returns:
        Sanitized text

    Raises:
        BadRequestException: If input is invalid
    """
    if not isinstance(text, str):
        raise BadRequestException("Input must be a string")

    # Length check
    if len(text) > max_length:
        raise BadRequestException(f"Input too long (max {max_length} characters)")

    # Remove null bytes
    text = text.replace("\x00", "")

    # HTML sanitization if not allowed
    if not allow_html:
        # Basic HTML entity encoding for safety
        text = (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
        )

    # Remove control characters except common whitespace
    allowed_chars = set(range(32, 127))  # Printable ASCII
    allowed_chars.update([9, 10, 13])  # Tab, LF, CR
    text = "".join(
        char for char in text if ord(char) in allowed_chars or ord(char) > 127
    )

    return text.strip()


def generate_csrf_token(session_id: str) -> str:
    """
    Generate CSRF token for session

    Args:
        session_id: Session identifier

    Returns:
        CSRF token
    """
    timestamp = str(int(time.time()))
    data = f"{session_id}:{timestamp}:{settings.SECRET_KEY}"
    return hashlib.sha256(data.encode()).hexdigest()


def validate_csrf_token(token: str, session_id: str, max_age: int = 3600) -> bool:
    """
    Validate CSRF token

    Args:
        token: CSRF token to validate
        session_id: Session identifier
        max_age: Maximum token age in seconds

    Returns:
        True if token is valid
    """
    try:
        # Generate expected token for current time window
        current_time = int(time.time())

        # Check tokens for current and previous time windows (to handle clock skew)
        for time_offset in range(0, max_age, 60):  # Check every minute
            timestamp = current_time - time_offset
            data = f"{session_id}:{timestamp}:{settings.SECRET_KEY}"
            expected_token = hashlib.sha256(data.encode()).hexdigest()

            if token == expected_token:
                return True

        return False
    except Exception:
        return False


class FileUploadSecurity:
    """Security utilities for file uploads"""

    ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg"}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    @staticmethod
    def validate_filename(filename: str) -> str:
        """
        Validate and sanitize filename

        Args:
            filename: Original filename

        Returns:
            Sanitized filename

        Raises:
            BadRequestException: If filename is invalid
        """
        if not filename:
            raise BadRequestException("Filename is required")

        # Remove path components
        filename = filename.split("/")[-1].split("\\")[-1]

        # Check for dangerous patterns
        dangerous_patterns = ["../", "..\\", "..", "~", "$"]
        if any(pattern in filename for pattern in dangerous_patterns):
            raise BadRequestException("Invalid filename")

        # Sanitize filename
        allowed_chars = set(
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_"
        )
        sanitized = "".join(c if c in allowed_chars else "_" for c in filename)

        # Ensure it has an extension
        if "." not in sanitized:
            raise BadRequestException("File must have an extension")

        # Check extension
        extension = "." + sanitized.split(".")[-1].lower()
        if extension not in FileUploadSecurity.ALLOWED_EXTENSIONS:
            raise BadRequestException(
                f"File type not allowed. Allowed: {', '.join(FileUploadSecurity.ALLOWED_EXTENSIONS)}"
            )

        return sanitized

    @staticmethod
    def scan_file_content(content: bytes, filename: str) -> bool:
        """
        Basic file content scanning

        Args:
            content: File content
            filename: Filename

        Returns:
            True if file appears safe
        """
        # Check for executable signatures
        executable_signatures = [
            b"\x4d\x5a",  # PE executable
            b"\x7f\x45\x4c\x46",  # ELF executable
            b"\xca\xfe\xba\xbe",  # Mach-O executable
            b"#!/bin/",  # Shell script
            b"#!/usr/bin/",  # Shell script
        ]

        for sig in executable_signatures:
            if content.startswith(sig):
                logger.warning(f"Executable file detected: {filename}")
                return False

        # Check for script content in image files
        if filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
            suspicious_content = [b"<script", b"javascript:", b"vbscript:", b"<?php"]
            content_lower = content.lower()

            for sus in suspicious_content:
                if sus in content_lower:
                    logger.warning(f"Suspicious content in image file: {filename}")
                    return False

        return True
