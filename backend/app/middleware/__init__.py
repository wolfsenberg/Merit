"""Middleware package - rate limiting, logging, and security middleware."""

from app.middleware.rate_limit import rate_limit_dependency

__all__ = ["rate_limit_dependency"]
