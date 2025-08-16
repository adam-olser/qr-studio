"""
Middleware package for QR Studio
"""

from .abuse_middleware import AbuseProtectionMiddleware

__all__ = ["AbuseProtectionMiddleware"]
