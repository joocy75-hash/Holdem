"""Tests for WebSocket token validation."""

import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.ws.gateway import (
    TokenValidator,
    TOKEN_VALIDATION_INTERVAL_SECONDS,
    create_reauth_required_message,
)
from app.utils.security import create_access_token, TokenError


class TestCreateReauthRequiredMessage:
    """Tests for REAUTH_REQUIRED message creation."""

    def test_message_has_correct_type(self):
        """Message should have REAUTH_REQUIRED type."""
        msg = create_reauth_required_message()
        assert msg["type"] == "REAUTH_REQUIRED"

    def test_message_has_payload(self):
        """Message should have payload with reason and message."""
        msg = create_reauth_required_message()
        assert "payload" in msg
        assert msg["payload"]["reason"] == "token_expired"
        assert "message" in msg["payload"]

    def test_message_has_timestamp(self):
        """Message should have timestamp."""
        msg = create_reauth_required_message()
        assert "timestamp" in msg


class TestTokenValidator:
    """Tests for TokenValidator class."""

    @pytest.fixture
    def mock_connection(self):
        """Create mock WebSocket connection."""
        conn = MagicMock()
        conn.user_id = "user-123"
        conn.connection_id = "conn-456"
        conn.send = AsyncMock()
        conn.websocket = MagicMock()
        conn.websocket.close = AsyncMock()
        return conn

    @pytest.fixture
    def valid_token(self):
        """Create a valid token."""
        return create_access_token("user-123")

    @pytest.fixture
    def expired_token(self):
        """Create an expired token."""
        return create_access_token(
            "user-123",
            expires_delta=timedelta(seconds=-1)
        )

    def test_init_stores_token_and_connection(self, mock_connection, valid_token):
        """TokenValidator should store token and connection."""
        validator = TokenValidator(valid_token, mock_connection)
        assert validator.token == valid_token
        assert validator.connection == mock_connection
        assert validator._running is False
        assert validator._task is None

    @pytest.mark.asyncio
    async def test_start_sets_running_flag(self, mock_connection, valid_token):
        """Start should set running flag and create task."""
        validator = TokenValidator(valid_token, mock_connection)
        
        # Start and immediately stop to avoid long wait
        await validator.start()
        assert validator._running is True
        assert validator._task is not None
        
        await validator.stop()

    @pytest.mark.asyncio
    async def test_stop_cancels_task(self, mock_connection, valid_token):
        """Stop should cancel the validation task."""
        validator = TokenValidator(valid_token, mock_connection)
        
        await validator.start()
        await validator.stop()
        
        assert validator._running is False
        assert validator._task is None

    @pytest.mark.asyncio
    async def test_validate_token_returns_true_for_valid(self, mock_connection, valid_token):
        """_validate_token should return True for valid token."""
        validator = TokenValidator(valid_token, mock_connection)
        
        result = await validator._validate_token()
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_token_returns_false_for_expired(self, mock_connection, expired_token):
        """_validate_token should return False for expired token."""
        validator = TokenValidator(expired_token, mock_connection)
        
        result = await validator._validate_token()
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_token_returns_false_for_invalid(self, mock_connection):
        """_validate_token should return False for invalid token."""
        validator = TokenValidator("invalid-token", mock_connection)
        
        result = await validator._validate_token()
        assert result is False

    @pytest.mark.asyncio
    async def test_validation_loop_sends_reauth_on_expiry(self, mock_connection, expired_token):
        """Validation loop should send REAUTH_REQUIRED when token expires."""
        validator = TokenValidator(expired_token, mock_connection)
        
        # Patch sleep to return immediately
        with patch('asyncio.sleep', new_callable=AsyncMock):
            validator._running = True
            
            # Run one iteration of the loop
            await validator._validation_loop()
        
        # Should have sent reauth message
        mock_connection.send.assert_called_once()
        call_args = mock_connection.send.call_args[0][0]
        assert call_args["type"] == "REAUTH_REQUIRED"
        
        # Should have closed connection
        mock_connection.websocket.close.assert_called_once()
        close_args = mock_connection.websocket.close.call_args
        assert close_args[0][0] == 4002  # Close code

    @pytest.mark.asyncio
    async def test_validation_loop_continues_on_valid_token(self, mock_connection, valid_token):
        """Validation loop should continue when token is valid."""
        validator = TokenValidator(valid_token, mock_connection)
        
        call_count = 0
        
        async def mock_sleep(seconds):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                validator._running = False
            return None
        
        with patch('asyncio.sleep', side_effect=mock_sleep):
            validator._running = True
            await validator._validation_loop()
        
        # Should not have sent reauth message
        mock_connection.send.assert_not_called()
        
        # Should not have closed connection
        mock_connection.websocket.close.assert_not_called()

    @pytest.mark.asyncio
    async def test_stop_while_running(self, mock_connection, valid_token):
        """Stop should properly cancel running validation."""
        validator = TokenValidator(valid_token, mock_connection)
        
        await validator.start()
        
        # Give task time to start
        await asyncio.sleep(0.01)
        
        await validator.stop()
        
        assert validator._running is False


class TestTokenValidationInterval:
    """Tests for token validation interval configuration."""

    def test_interval_is_5_minutes(self):
        """Token validation interval should be 5 minutes (300 seconds)."""
        assert TOKEN_VALIDATION_INTERVAL_SECONDS == 300.0

    def test_interval_is_reasonable(self):
        """Interval should be between 1 and 10 minutes."""
        assert 60 <= TOKEN_VALIDATION_INTERVAL_SECONDS <= 600


class TestTokenValidatorErrorHandling:
    """Tests for error handling in TokenValidator."""

    @pytest.fixture
    def mock_connection(self):
        """Create mock WebSocket connection."""
        conn = MagicMock()
        conn.user_id = "user-123"
        conn.connection_id = "conn-456"
        conn.send = AsyncMock()
        conn.websocket = MagicMock()
        conn.websocket.close = AsyncMock()
        return conn

    @pytest.mark.asyncio
    async def test_handles_send_error_gracefully(self, mock_connection):
        """Should handle send errors gracefully."""
        expired_token = create_access_token(
            "user-123",
            expires_delta=timedelta(seconds=-1)
        )
        validator = TokenValidator(expired_token, mock_connection)
        
        # Make send raise an exception
        mock_connection.send.side_effect = Exception("Send failed")
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            validator._running = True
            # Should not raise
            await validator._validation_loop()
        
        # Should still try to close connection
        mock_connection.websocket.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_close_error_gracefully(self, mock_connection):
        """Should handle close errors gracefully."""
        expired_token = create_access_token(
            "user-123",
            expires_delta=timedelta(seconds=-1)
        )
        validator = TokenValidator(expired_token, mock_connection)
        
        # Make close raise an exception
        mock_connection.websocket.close.side_effect = Exception("Close failed")
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            validator._running = True
            # Should not raise
            await validator._validation_loop()
        
        # Should have stopped running
        assert validator._running is False

    @pytest.mark.asyncio
    async def test_handles_validation_exception(self, mock_connection):
        """Should handle unexpected validation exceptions."""
        validator = TokenValidator("some-token", mock_connection)
        
        call_count = 0
        
        async def mock_sleep(seconds):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                validator._running = False
        
        with patch('asyncio.sleep', side_effect=mock_sleep):
            with patch.object(
                validator, '_validate_token',
                side_effect=Exception("Unexpected error")
            ):
                validator._running = True
                # Should not raise, should continue loop
                await validator._validation_loop()
        
        # Should have continued after error
        assert call_count >= 1
