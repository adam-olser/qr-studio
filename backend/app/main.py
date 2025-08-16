import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .api import qr, health, admin
from .core.config import settings
from .core.error_handlers import setup_error_handlers
from .core.security import SecurityMiddleware, RateLimiter
from .core.cache import init_cache, close_cache
from .middleware.abuse_middleware import AbuseProtectionMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.ENV == "production" else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="QR Studio API",
    description="High-performance QR code generation service with advanced styling",
    version="1.0.0",
    docs_url="/api/docs" if settings.ENV != "production" else None,
    redoc_url="/api/redoc" if settings.ENV != "production" else None,
)

# Store settings in app state for access in error handlers
app.state.settings = settings

# Setup error handlers
setup_error_handlers(app)

# Abuse protection middleware (should be first)
app.add_middleware(AbuseProtectionMiddleware)

# Security middleware (should be added before CORS)
app.add_middleware(SecurityMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
)

# API routes
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(qr.router, prefix="/api/v1/qr", tags=["QR Generation"])

# Admin routes (only in development or with proper authentication)
if settings.ENV != "production" or hasattr(settings, "ADMIN_TOKEN"):
    app.include_router(admin.router, prefix="/admin", tags=["Admin"])

# Static files (for generated QR codes if needed)
# app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize services on startup"""
    logger.info("Starting QR Studio API...")
    await init_cache()
    logger.info("QR Studio API started successfully")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Cleanup on shutdown"""
    logger.info("Shutting down QR Studio API...")
    await close_cache()
    logger.info("QR Studio API shutdown complete")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "QR Studio API", "version": "1.0.0", "docs": "/api/docs"}
