"""Merit Platform - FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import get_settings
from app.core.database import close_db
from app.core.redis import close_redis

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # Startup - try to create tables (may fail on first deploy, that's OK)
    try:
        from app.core.database import init_db
        await init_db()
    except Exception as e:
        print(f"Warning: init_db failed (likely first deploy): {e}")
    yield
    # Shutdown
    await close_db()
    await close_redis()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    docs_url=f"{settings.api_v1_prefix}/docs",
    redoc_url=f"{settings.api_v1_prefix}/redoc",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_origin_regex=r"https://.*\\.vercel\\.app|https://.*\\.onrender\\.com|http://localhost:\\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Host Middleware
allowed_hosts = settings.allowed_hosts or ["*"]
if settings.debug:
    middleware_hosts = ["*"]
elif settings.environment.lower() in {"production", "staging", "test"}:
    middleware_hosts = ["*"]
else:
    middleware_hosts = allowed_hosts

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=middleware_hosts,
)


# --- Middleware Slots ---
# Additional middleware (rate limiting, request logging, etc.) will be added here
# as separate middleware classes in app/middleware/


# --- API Router Registration ---
from app.api.v1.router import api_router  # noqa: E402

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.app_version}
