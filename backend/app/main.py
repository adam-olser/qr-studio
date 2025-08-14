from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api import qr, health
from app.core.config import settings

app = FastAPI(
    title="QR Studio API",
    description="High-performance QR code generation service with advanced styling",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(qr.router, prefix="/api/v1/qr", tags=["QR Generation"])

# Static files (for generated QR codes if needed)
# app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return {
        "message": "QR Studio API",
        "version": "1.0.0",
        "docs": "/api/docs"
    }
