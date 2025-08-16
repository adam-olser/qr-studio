import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Environment
    ENV: str = "development"
    DEBUG: bool = True

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:8080",
    ]

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # File upload limits
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_TYPES: List[str] = [
        "image/png",
        "image/jpeg",
        "image/jpg",
        "image/svg+xml",
    ]

    # QR generation limits
    MIN_QR_SIZE: int = 200
    MAX_QR_SIZE: int = 2048

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100  # requests per minute
    RATE_LIMIT_WINDOW: int = 60  # seconds

    # QR generation rate limits
    QR_GENERATION_LIMIT: int = 20  # QR generations per minute
    URL_VALIDATION_LIMIT: int = 50  # URL validations per minute

    # Storage (for future use)
    AWS_BUCKET: str = ""
    AWS_REGION: str = "us-east-1"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
