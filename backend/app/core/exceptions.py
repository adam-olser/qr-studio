"""
Custom exceptions for the QR Studio application
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class QRStudioException(Exception):
    """Base exception class for QR Studio"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(QRStudioException):
    """Raised when input validation fails"""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.field = field
        super().__init__(message, details)


class QRGenerationError(QRStudioException):
    """Raised when QR code generation fails"""

    def __init__(self, message: str, config: Optional[Dict[str, Any]] = None):
        details = {"config": config} if config else None
        super().__init__(message, details)


class FileProcessingError(QRStudioException):
    """Raised when file processing fails"""

    def __init__(
        self,
        message: str,
        filename: Optional[str] = None,
        file_size: Optional[int] = None,
    ):
        details = {}
        if filename:
            details["filename"] = filename
        if file_size:
            details["file_size"] = str(file_size)
        super().__init__(message, details)


class ConfigurationError(QRStudioException):
    """Raised when configuration is invalid"""

    pass


# HTTP Exception classes for FastAPI
class QRStudioHTTPException(HTTPException):
    """Base HTTP exception with enhanced error details"""

    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        detail = {
            "message": message,
            "error_code": error_code or "GENERIC_ERROR",
            "details": details or {},
        }
        super().__init__(status_code=status_code, detail=detail)


class BadRequestException(QRStudioHTTPException):
    """400 Bad Request"""

    def __init__(
        self,
        message: str,
        error_code: str = "BAD_REQUEST",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status.HTTP_400_BAD_REQUEST, message, error_code, details)


class ValidationException(QRStudioHTTPException):
    """422 Validation Error"""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        if field:
            error_details["field"] = field
        super().__init__(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            message,
            "VALIDATION_ERROR",
            error_details,
        )


class FileUploadException(QRStudioHTTPException):
    """413 or 400 File Upload Error"""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error_code: str = "FILE_UPLOAD_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code, message, error_code, details)


class QRGenerationException(QRStudioHTTPException):
    """500 QR Generation Error"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            message,
            "QR_GENERATION_ERROR",
            details,
        )


class ServiceUnavailableException(QRStudioHTTPException):
    """503 Service Unavailable"""

    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status.HTTP_503_SERVICE_UNAVAILABLE, message, "SERVICE_UNAVAILABLE", details
        )
