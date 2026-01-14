"""Security headers middleware.

Adds security-related HTTP headers to all responses.

Phase 4 Enhancement:
- Content-Security-Policy (CSP) for production
- Strict-Transport-Security (HSTS) for production
- Enhanced cache control
"""

from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses.

    Headers added:
    - X-Content-Type-Options: Prevents MIME type sniffing
    - X-Frame-Options: Prevents clickjacking
    - X-XSS-Protection: Enables XSS filter (legacy browsers)
    - Referrer-Policy: Controls referrer information
    - Permissions-Policy: Restricts browser features
    - Content-Security-Policy: Controls resource loading (production only)
    - Strict-Transport-Security: Enforces HTTPS (production only)
    """

    def __init__(self, app: Callable, app_env: str = "development"):
        """Initialize middleware with environment setting.

        Args:
            app: ASGI application
            app_env: Application environment (development/production)
        """
        super().__init__(app)
        self.app_env = app_env
        self._is_production = app_env == "production"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        # Skip WebSocket upgrade requests - BaseHTTPMiddleware doesn't handle them properly
        if request.headers.get("upgrade", "").lower() == "websocket":
            return await call_next(request)

        response = await call_next(request)

        # === Basic Security Headers (all environments) ===

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # XSS protection for legacy browsers
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Restrict browser features (minimal permissions)
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )

        # === Production-Only Security Headers ===

        if self._is_production:
            # Content Security Policy (CSP)
            # Restricts resource loading to prevent XSS and data injection
            csp_directives = [
                "default-src 'self'",
                "script-src 'self'",
                "style-src 'self' 'unsafe-inline'",  # Allow inline styles for UI frameworks
                "img-src 'self' data: https:",
                "font-src 'self' data:",
                "connect-src 'self' wss: https:",  # Allow WebSocket and HTTPS connections
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'",
                "upgrade-insecure-requests",
            ]
            response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

            # HTTP Strict Transport Security (HSTS)
            # Forces HTTPS for 1 year, includes subdomains, allows preload list
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # === Cache Control ===

        # API responses should not be cached
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response
