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

    # Abuse protection settings
    ENABLE_ABUSE_PROTECTION: bool = True
    MAX_CONCURRENT_REQUESTS: int = 5  # per IP
    DAILY_QR_LIMIT: int = 1000  # QR codes per day per IP
    HOURLY_QR_LIMIT: int = 100  # QR codes per hour per IP
    DAILY_API_LIMIT: int = 10000  # API calls per day per IP
    HOURLY_API_LIMIT: int = 1000  # API calls per hour per IP

    # Threat escalation thresholds
    BURST_REQUEST_THRESHOLD: int = 20  # requests in 10 seconds
    ERROR_RATE_THRESHOLD: float = 0.5  # 50% error rate
    LARGE_FILE_THRESHOLD: int = 10  # large files per minute

    # Block durations (in seconds)
    FIRST_BLOCK_DURATION: int = 300  # 5 minutes
    SECOND_BLOCK_DURATION: int = 900  # 15 minutes
    THIRD_BLOCK_DURATION: int = 3600  # 1 hour
    MAX_BLOCK_DURATION: int = 86400  # 24 hours

    # Admin access
    ADMIN_TOKEN: str = "change-this-admin-token-in-production"

    # Storage (for future use)
    AWS_BUCKET: str = ""
    AWS_REGION: str = "us-east-1"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
