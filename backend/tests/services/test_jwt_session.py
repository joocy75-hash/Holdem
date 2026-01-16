"""Tests for JWT token validation and session management."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from jose import jwt

from app.config import get_settings
from app.services.auth import AuthService, MAX_SESSIONS_PER_USER
from app.utils.security import (
    TokenError,
    create_access_token,
    verify_access_token,
)

settings = get_settings()


class TestJWTTokenExpiration:
    """Tests for JWT token expiration validation."""

    def test_valid_token_returns_payload(self):
        """Valid token should return payload."""
        token = create_access_token("user-123")
        payload = verify_access_token(token)
        
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"

    def test_expired_token_raises_token_error(self):
        """Expired token should raise TokenError with TOKEN_EXPIRED code."""
        # Create token that expired 1 hour ago
        token = create_access_token(
            "user-123",
            expires_delta=timedelta(hours=-1)
        )
        
        with pytest.raises(TokenError) as exc_info:
            verify_access_token(token)
        
        assert exc_info.value.code == "TOKEN_EXPIRED"
        assert "expired" in exc_info.value.message.lower()

    def test_token_without_exp_returns_none(self):
        """Token without exp claim should return None."""
        # Create token manually without exp
        payload = {
            "sub": "user-123",
            "type": "access",
            "iat": datetime.now(timezone.utc),
        }
        token = jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        
        # Should return None (not raise) because jwt.decode will fail
        result = verify_access_token(token)
        assert result is None

    def test_token_with_wrong_type_returns_none(self):
        """Token with wrong type should return None."""
        # Create a refresh token
        payload = {
            "sub": "user-123",
            "type": "refresh",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        
        result = verify_access_token(token)
        assert result is None

    def test_invalid_signature_returns_none(self):
        """Token with invalid signature should return None."""
        payload = {
            "sub": "user-123",
            "type": "access",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(
            payload,
            "wrong-secret-key",
            algorithm=settings.jwt_algorithm,
        )
        
        result = verify_access_token(token)
        assert result is None

    def test_malformed_token_returns_none(self):
        """Malformed token should return None."""
        result = verify_access_token("not-a-valid-token")
        assert result is None

    def test_token_expiring_soon_still_valid(self):
        """Token expiring in 1 second should still be valid."""
        token = create_access_token(
            "user-123",
            expires_delta=timedelta(seconds=10)
        )
        
        payload = verify_access_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"


class TestSessionLimit:
    """Tests for concurrent session limit enforcement."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        return db

    @pytest.fixture
    def auth_service(self, mock_db):
        """Create AuthService with mock db."""
        return AuthService(mock_db)

    @pytest.mark.asyncio
    async def test_enforce_session_limit_removes_oldest(self, auth_service, mock_db):
        """Should remove oldest sessions when at limit."""
        # Create mock sessions (oldest first)
        sessions = []
        for i in range(MAX_SESSIONS_PER_USER):
            session = MagicMock()
            session.created_at = datetime.now(timezone.utc) - timedelta(hours=MAX_SESSIONS_PER_USER - i)
            sessions.append(session)
        
        # Mock the query result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = sessions
        mock_db.execute.return_value = mock_result
        
        # Call enforce session limit
        await auth_service._enforce_session_limit("user-123")
        
        # Should delete the oldest session (first one)
        mock_db.delete.assert_called_once_with(sessions[0])

    @pytest.mark.asyncio
    async def test_enforce_session_limit_no_removal_under_limit(self, auth_service, mock_db):
        """Should not remove sessions when under limit."""
        # Create fewer sessions than limit
        sessions = []
        for i in range(MAX_SESSIONS_PER_USER - 1):
            session = MagicMock()
            session.created_at = datetime.now(timezone.utc) - timedelta(hours=i)
            sessions.append(session)
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = sessions
        mock_db.execute.return_value = mock_result
        
        await auth_service._enforce_session_limit("user-123")
        
        # Should not delete any sessions
        mock_db.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_enforce_session_limit_removes_multiple_if_over(self, auth_service, mock_db):
        """Should remove multiple sessions if way over limit."""
        # Create more sessions than limit + 1
        sessions = []
        for i in range(MAX_SESSIONS_PER_USER + 2):
            session = MagicMock()
            session.created_at = datetime.now(timezone.utc) - timedelta(hours=MAX_SESSIONS_PER_USER + 2 - i)
            sessions.append(session)
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = sessions
        mock_db.execute.return_value = mock_result
        
        await auth_service._enforce_session_limit("user-123")
        
        # Should delete 3 oldest sessions (to make room for 1 new)
        assert mock_db.delete.call_count == 3

    @pytest.mark.asyncio
    async def test_enforce_session_limit_empty_sessions(self, auth_service, mock_db):
        """Should handle empty sessions list."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result
        
        await auth_service._enforce_session_limit("user-123")
        
        mock_db.delete.assert_not_called()


class TestMaxSessionsConstant:
    """Tests for MAX_SESSIONS_PER_USER constant."""

    def test_max_sessions_is_three(self):
        """MAX_SESSIONS_PER_USER should be 3."""
        assert MAX_SESSIONS_PER_USER == 3
