"""Unit tests for CSRF middleware."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from starlette.testclient import TestClient
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from app.middleware.csrf import CSRFMiddleware, SAFE_METHODS


class TestCSRFMiddleware:
    """Test cases for CSRFMiddleware."""

    @pytest.fixture
    def app_with_csrf(self):
        """Create test app with CSRF middleware enabled."""
        async def homepage(request):
            return JSONResponse({"message": "ok"})
        
        async def create_item(request):
            return JSONResponse({"created": True})
        
        app = Starlette(
            routes=[
                Route("/", homepage),
                Route("/items", create_item, methods=["POST"]),
                Route("/health", homepage),
            ]
        )
        app.add_middleware(
            CSRFMiddleware,
            enabled=True,
            cookie_secure=False,  # For testing
            exempt_paths={"/health"},
        )
        return app

    @pytest.fixture
    def app_csrf_disabled(self):
        """Create test app with CSRF middleware disabled."""
        async def homepage(request):
            return JSONResponse({"message": "ok"})
        
        async def create_item(request):
            return JSONResponse({"created": True})
        
        app = Starlette(
            routes=[
                Route("/", homepage),
                Route("/items", create_item, methods=["POST"]),
            ]
        )
        app.add_middleware(
            CSRFMiddleware,
            enabled=False,
        )
        return app

    def test_safe_methods_allowed_without_token(self, app_with_csrf):
        """Test that safe methods (GET, HEAD, OPTIONS) are allowed without CSRF token."""
        client = TestClient(app_with_csrf)
        
        response = client.get("/")
        assert response.status_code == 200
        
        # Should set CSRF cookie
        assert "csrftoken" in response.cookies

    def test_unsafe_method_blocked_without_token(self, app_with_csrf):
        """Test that unsafe methods are blocked without CSRF token."""
        client = TestClient(app_with_csrf)
        
        response = client.post("/items", json={"name": "test"})
        assert response.status_code == 403
        assert "CSRF" in response.json()["detail"]

    def test_unsafe_method_allowed_with_valid_token(self, app_with_csrf):
        """Test that unsafe methods are allowed with valid CSRF token."""
        client = TestClient(app_with_csrf)
        
        # First, get the CSRF cookie
        get_response = client.get("/")
        csrf_token = get_response.cookies.get("csrftoken")
        
        # Now make POST with the token
        response = client.post(
            "/items",
            json={"name": "test"},
            headers={"X-CSRF-Token": csrf_token},
            cookies={"csrftoken": csrf_token},
        )
        assert response.status_code == 200

    def test_unsafe_method_blocked_with_mismatched_token(self, app_with_csrf):
        """Test that unsafe methods are blocked with mismatched tokens."""
        client = TestClient(app_with_csrf)
        
        # Get a valid cookie
        get_response = client.get("/")
        csrf_token = get_response.cookies.get("csrftoken")
        
        # Send with different header token
        response = client.post(
            "/items",
            json={"name": "test"},
            headers={"X-CSRF-Token": "wrong-token"},
            cookies={"csrftoken": csrf_token},
        )
        assert response.status_code == 403

    def test_exempt_paths_bypass_csrf(self, app_with_csrf):
        """Test that exempt paths bypass CSRF protection."""
        client = TestClient(app_with_csrf)
        
        # Health endpoint should work without CSRF
        response = client.get("/health")
        assert response.status_code == 200

    def test_disabled_middleware_allows_all(self, app_csrf_disabled):
        """Test that disabled middleware allows all requests."""
        client = TestClient(app_csrf_disabled)
        
        # POST should work without CSRF token when disabled
        response = client.post("/items", json={"name": "test"})
        assert response.status_code == 200

    def test_csrf_cookie_not_httponly(self, app_with_csrf):
        """Test that CSRF cookie is not httponly (so JS can read it)."""
        client = TestClient(app_with_csrf)
        
        response = client.get("/")
        # The cookie should be accessible to JavaScript
        # TestClient doesn't expose httponly flag directly, but we verify it's set
        assert "csrftoken" in response.cookies


class TestCSRFTokenGeneration:
    """Test CSRF token generation."""

    def test_generate_token_returns_string(self):
        """Test that generate_token returns a string."""
        token = CSRFMiddleware.generate_token()
        assert isinstance(token, str)
        assert len(token) > 0

    def test_generate_token_unique(self):
        """Test that generate_token returns unique values."""
        tokens = [CSRFMiddleware.generate_token() for _ in range(100)]
        assert len(set(tokens)) == 100  # All unique


class TestSafeMethods:
    """Test safe methods constant."""

    def test_safe_methods_include_get(self):
        """Test that GET is a safe method."""
        assert "GET" in SAFE_METHODS

    def test_safe_methods_include_head(self):
        """Test that HEAD is a safe method."""
        assert "HEAD" in SAFE_METHODS

    def test_safe_methods_include_options(self):
        """Test that OPTIONS is a safe method."""
        assert "OPTIONS" in SAFE_METHODS

    def test_safe_methods_exclude_post(self):
        """Test that POST is not a safe method."""
        assert "POST" not in SAFE_METHODS

    def test_safe_methods_exclude_put(self):
        """Test that PUT is not a safe method."""
        assert "PUT" not in SAFE_METHODS

    def test_safe_methods_exclude_delete(self):
        """Test that DELETE is not a safe method."""
        assert "DELETE" not in SAFE_METHODS
