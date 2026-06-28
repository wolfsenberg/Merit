"""ARQ async task queue configuration."""

from arq.connections import RedisSettings

from app.core.config import get_settings

settings = get_settings()


def get_arq_redis_settings() -> RedisSettings:
    """Get ARQ Redis connection settings."""
    # Parse the redis URL to extract components
    url = settings.arq_redis_url
    # Default: redis://localhost:6379/5
    parts = url.replace("redis://", "").split("/")
    host_port = parts[0].split(":")
    host = host_port[0] if host_port[0] else "localhost"
    port = int(host_port[1]) if len(host_port) > 1 else 6379
    database = int(parts[1]) if len(parts) > 1 else 0

    return RedisSettings(
        host=host,
        port=port,
        database=database,
    )


class WorkerSettings:
    """ARQ worker settings for background task processing."""

    redis_settings = get_arq_redis_settings()
    max_jobs = 10
    job_timeout = 600  # 10 minutes
    max_tries = 5
    health_check_interval = 30

    # Functions will be registered by individual task modules
    functions: list = []
