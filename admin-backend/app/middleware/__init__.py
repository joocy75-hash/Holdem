"""Middleware package for admin-backend."""

from app.middleware.csrf import CSRFMiddleware

__all__ = ["CSRFMiddleware"]
