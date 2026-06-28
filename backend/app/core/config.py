"""Application configuration using Pydantic settings."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Merit Platform"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"

    # API
    api_v1_prefix: str = "/api/v1"
    allowed_origins: list[str] = ["http://localhost:3000"]

    # Database
    database_url: str = "postgresql+asyncpg://merit:merit@localhost:5432/merit"
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_session_db: int = 1
    redis_cache_db: int = 2
    redis_cache_ttl: int = 300

    # Celery / ARQ
    celery_broker_url: str = "redis://localhost:6379/3"
    celery_result_backend: str = "redis://localhost:6379/4"
    arq_redis_url: str = "redis://localhost:6379/5"

    # JWT
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # File Storage
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 10

    # Rate Limiting
    rate_limit_authenticated: int = 100
    rate_limit_unauthenticated: int = 20

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": False}


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
