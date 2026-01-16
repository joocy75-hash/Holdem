"""CSRF Protection Middleware.

Implements Double Submit Cookie pattern for CSRF protection.
This is primarily for defense-in-depth since the API uses JWT tokens
in Authorization headers rather than session cookies.
"""

import secrets
import logging
from typing import Optional, Set

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

logger = logging.getLogger(__name__)

# Safe HTTP methods that don't require CSRF protection
SAFE_METHODS: Set[str] = {"GET", "HEAD", "OPTIONS", "TRACE"}

# Default cookie and header names
DEFAULT_COOKIE_NAME = "csrftoken"
DEFAULT_HEADER_NAME = "X-CSRF-Token"


class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF protection middleware using Double Submit Cookie pattern.
    
    For unsafe methods (POST, PUT, DELETE, PATCH), the middleware:
    1. Checks for a CSRF token in the cookie
    2. Checks for the same token in the request header
    3. Compares them - if they match, the request is allowed
    
    For safe methods (GET, HEAD, OPTIONS, TRACE):
    - Sets a CSRF cookie if not present
    - Allows the request to proceed
    
    Note: This middleware is optional for APIs using JWT tokens in
    Authorization headers, as those are not vulnerable to CSRF attacks.
    It's included for defense-in-depth.
    """
    
    def __init__(
        self,
        app,
        cookie_name: str = DEFAULT_COOKIE_NAME,
        header_name: str = DEFAULT_HEADER_NAME,
        cookie_secure: bool = True,
        cookie_httponly: bool = False,  # Must be False for JS to read
        cookie_samesite: str = "lax",
        exempt_paths: Optional[Set[str]] = None,
        enabled: bool = True,
    ):
        """Initialize CSRF middleware.
        
        Args:
            app: ASGI application
            cookie_name: Name of the CSRF cookie
            header_name: Name of the CSRF header
            cookie_secure: Whether cookie requires HTTPS
            cookie_httponly: Whether cookie is HTTP-only (must be False for JS access)
            cookie_samesite: SameSite cookie attribute
            exempt_paths: Paths exempt from CSRF protection
            enabled: Whether CSRF protection is enabled
        """
        super().__init__(app)
        self.cookie_name = cookie_name
        self.header_name = header_name
        self.cookie_secure = cookie_secure
        self.cookie_httponly = cookie_httponly
        self.cookie_samesite = cookie_samesite
        self.exempt_paths = exempt_paths or {"/health", "/docs", "/redoc", "/openapi.json"}
        self.enabled = enabled
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and apply CSRF protection."""
        # Skip if disabled
        if not self.enabled:
            return await call_next(request)
        
        # Skip exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)
        
        # Skip safe methods but ensure cookie is set
        if request.method in SAFE_METHODS:
            response = await call_next(request)
            return self._ensure_csrf_cookie(request, response)
        
        # For unsafe methods, validate CSRF token
        if not self._validate_csrf_token(request):
            logger.warning(
                f"CSRF validation failed for {request.method} {request.url.path} "
                f"from {request.client.host if request.client else 'unknown'}"
            )
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token missing or invalid"},
            )
        
        response = await call_next(request)
        return self._ensure_csrf_cookie(request, response)
    
    def _validate_csrf_token(self, request: Request) -> bool:
        """Validate CSRF token from cookie and header.
        
        Args:
            request: The incoming request
            
        Returns:
            True if valid, False otherwise
        """
        # Get token from cookie
        cookie_token = request.cookies.get(self.cookie_name)
        if not cookie_token:
            logger.debug("CSRF cookie not found")
            return False
        
        # Get token from header
        header_token = request.headers.get(self.header_name)
        if not header_token:
            logger.debug("CSRF header not found")
            return False
        
        # Compare tokens (constant-time comparison)
        return secrets.compare_digest(cookie_token, header_token)
    
    def _ensure_csrf_cookie(self, request: Request, response: Response) -> Response:
        """Ensure CSRF cookie is set on response.
        
        Args:
            request: The incoming request
            response: The outgoing response
            
        Returns:
            Response with CSRF cookie set
        """
        # Check if cookie already exists
        if self.cookie_name in request.cookies:
            return response
        
        # Generate new token
        token = secrets.token_urlsafe(32)
        
        # Set cookie
        response.set_cookie(
            key=self.cookie_name,
            value=token,
            secure=self.cookie_secure,
            httponly=self.cookie_httponly,
            samesite=self.cookie_samesite,
            max_age=86400,  # 24 hours
        )
        
        return response
    
    @staticmethod
    def generate_token() -> str:
        """Generate a new CSRF token.
        
        Returns:
            URL-safe random token
        """
        return secrets.token_urlsafe(32)
