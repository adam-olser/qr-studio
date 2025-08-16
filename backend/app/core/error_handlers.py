"""
Global error handlers for the FastAPI application
"""

import logging
import traceback
from typing import Any, Dict
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError

from .exceptions import QRStudioException, QRStudioHTTPException

logger = logging.getLogger(__name__)


async def qr_studio_exception_handler(
    request: Request, exc: QRStudioException
) -> JSONResponse:
    """Handle custom QR Studio exceptions"""
    logger.error(f"QR Studio Exception: {exc.message}", extra={"details": exc.details})

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": exc.message,
            "error_code": "INTERNAL_ERROR",
            "details": exc.details,
        },
    )


async def qr_studio_http_exception_handler(
    request: Request, exc: QRStudioHTTPException
) -> JSONResponse:
    """Handle custom HTTP exceptions with enhanced error details"""
    logger.warning(f"HTTP Exception: {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail,
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle standard FastAPI HTTP exceptions"""
    logger.warning(f"HTTP Exception: {exc.detail}")

    # Ensure consistent error format
    if isinstance(exc.detail, dict):
        content = exc.detail
    else:
        content = {
            "message": str(exc.detail),
            "error_code": "HTTP_ERROR",
            "details": {},
        }

    return JSONResponse(status_code=exc.status_code, content=content)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors"""
    errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        errors.append(
            {
                "field": field_path,
                "message": error["msg"],
                "type": error["type"],
                "input": error.get("input"),
            }
        )

    logger.warning(f"Validation Error: {errors}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "message": "Validation failed",
            "error_code": "VALIDATION_ERROR",
            "details": {"errors": errors},
        },
    )


async def pydantic_validation_exception_handler(
    request: Request, exc: PydanticValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors from models"""
    errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        errors.append(
            {
                "field": field_path,
                "message": error["msg"],
                "type": error["type"],
            }
        )

    logger.warning(f"Pydantic Validation Error: {errors}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "message": "Model validation failed",
            "error_code": "MODEL_VALIDATION_ERROR",
            "details": {"errors": errors},
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    error_id = id(exc)  # Simple error ID for tracking

    logger.error(
        f"Unexpected error (ID: {error_id}): {str(exc)}",
        extra={
            "error_id": error_id,
            "traceback": traceback.format_exc(),
            "request_url": str(request.url),
            "request_method": request.method,
        },
    )

    # Don't expose internal error details in production
    if request.app.state.settings.ENV == "production":
        message = "An internal error occurred"
        details: Dict[str, Any] = {"error_id": str(error_id)}
    else:
        message = f"Internal server error: {str(exc)}"
        details = {
            "error_id": str(error_id),
            "type": type(exc).__name__,
            "traceback": traceback.format_exc().split("\n"),
        }

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": message,
            "error_code": "INTERNAL_SERVER_ERROR",
            "details": details,
        },
    )


def setup_error_handlers(app: Any) -> None:
    """Setup all error handlers for the FastAPI app"""
    app.add_exception_handler(QRStudioException, qr_studio_exception_handler)
    app.add_exception_handler(QRStudioHTTPException, qr_studio_http_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(
        PydanticValidationError, pydantic_validation_exception_handler
    )
    app.add_exception_handler(Exception, generic_exception_handler)
