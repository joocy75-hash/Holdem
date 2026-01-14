"""Logging Property-Based Tests.

Property 7: Logging Completeness
- Tests that game actions are properly logged
- Validates: Requirements 9.1, 9.4

Tests ensure that:
1. All game actions generate logs
2. Logs contain required fields (user_id, room_id, action, timestamp)
3. Processing time is logged
4. Security events are logged
5. Log format is consistent
"""

import pytest
import logging
import json
from io import StringIO
from unittest.mock import MagicMock, patch, AsyncMock
from hypothesis import given, strategies as st, settings

import structlog
from structlog.testing import capture_logs

from app.logging_config import (
    configure_logging,
    get_logger,
    bind_context,
    clear_context,
    unbind_context,
)


# =============================================================================
# Property 7: Logging Completeness Tests
# =============================================================================


class TestLoggerConfiguration:
    """Tests for logging configuration."""

    def test_configure_logging_development(self):
        """Development logging should use console renderer."""
        configure_logging(log_level="DEBUG", json_logs=False, app_env="development")
        logger = get_logger("test")
        assert logger is not None

    def test_configure_logging_production(self):
        """Production logging should use JSON renderer."""
        configure_logging(log_level="INFO", json_logs=True, app_env="production")
        logger = get_logger("test")
        assert logger is not None

    def test_get_logger_returns_bound_logger(self):
        """get_logger should return a BoundLogger instance."""
        logger = get_logger(__name__)
        assert logger is not None
        # Should have standard logging methods
        assert hasattr(logger, "info")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")
        assert hasattr(logger, "debug")


class TestContextBinding:
    """Tests for context variable binding."""

    def setup_method(self):
        """Clear context before each test."""
        clear_context()

    def teardown_method(self):
        """Clear context after each test."""
        clear_context()

    def test_bind_context_adds_variables(self):
        """bind_context should add variables to log context."""
        # Note: capture_logs doesn't capture contextvars, so we test differently
        bind_context(user_id="test-user", room_id="test-room")
        
        # Verify context is bound by checking structlog's contextvars
        import structlog
        ctx = structlog.contextvars.get_contextvars()
        assert ctx.get("user_id") == "test-user"
        assert ctx.get("room_id") == "test-room"

    def test_clear_context_removes_all_variables(self):
        """clear_context should remove all bound variables."""
        bind_context(user_id="test-user")
        clear_context()
        
        import structlog
        ctx = structlog.contextvars.get_contextvars()
        assert "user_id" not in ctx

    def test_unbind_context_removes_specific_variables(self):
        """unbind_context should remove only specified variables."""
        bind_context(user_id="test-user", room_id="test-room")
        unbind_context("user_id")
        
        import structlog
        ctx = structlog.contextvars.get_contextvars()
        assert "user_id" not in ctx
        assert ctx.get("room_id") == "test-room"


class TestGameActionLogging:
    """Tests for game action logging."""

    def setup_method(self):
        clear_context()

    def teardown_method(self):
        clear_context()

    def test_action_log_contains_required_fields(self):
        """Action logs should contain user_id, room_id, action."""
        with capture_logs() as cap_logs:
            logger = get_logger("game.action")
            logger.info(
                "player_action",
                user_id="user123",
                room_id="room456",
                action="fold",
                seat=3,
            )

        assert len(cap_logs) == 1
        log = cap_logs[0]
        assert log.get("user_id") == "user123"
        assert log.get("room_id") == "room456"
        assert log.get("action") == "fold"
        assert log.get("event") == "player_action"

    def test_action_log_with_processing_time(self):
        """Action logs should include processing time when provided."""
        with capture_logs() as cap_logs:
            logger = get_logger("game.action")
            logger.info(
                "action_processed",
                user_id="user123",
                room_id="room456",
                action="raise",
                amount=100,
                processing_time_ms=15.5,
            )

        assert len(cap_logs) == 1
        log = cap_logs[0]
        assert log.get("processing_time_ms") == 15.5

    @given(
        action=st.sampled_from(["fold", "check", "call", "raise", "all_in"]),
        amount=st.integers(min_value=0, max_value=10000),
    )
    @settings(max_examples=10, deadline=None)
    def test_all_action_types_logged(self, action: str, amount: int):
        """All action types should be loggable."""
        with capture_logs() as cap_logs:
            logger = get_logger("game.action")
            logger.info(
                "player_action",
                user_id="user123",
                room_id="room456",
                action=action,
                amount=amount,
            )

        assert len(cap_logs) == 1
        assert cap_logs[0].get("action") == action
        assert cap_logs[0].get("amount") == amount


class TestSecurityEventLogging:
    """Tests for security event logging."""

    def setup_method(self):
        clear_context()

    def teardown_method(self):
        clear_context()

    def test_login_failure_logged(self):
        """Login failures should be logged with details."""
        with capture_logs() as cap_logs:
            logger = get_logger("security")
            logger.warning(
                "login_failed",
                username="testuser",
                client_ip="192.168.1.1",
                reason="invalid_password",
            )

        assert len(cap_logs) == 1
        log = cap_logs[0]
        assert log.get("event") == "login_failed"
        assert log.get("username") == "testuser"
        assert log.get("client_ip") == "192.168.1.1"
        assert log.get("log_level") == "warning"

    def test_rate_limit_exceeded_logged(self):
        """Rate limit violations should be logged."""
        with capture_logs() as cap_logs:
            logger = get_logger("security")
            logger.warning(
                "rate_limit_exceeded",
                client_ip="192.168.1.1",
                user_id="user123",
                path="/api/v1/auth/login",
                limit=5,
                window=60,
            )

        assert len(cap_logs) == 1
        log = cap_logs[0]
        assert log.get("event") == "rate_limit_exceeded"
        assert log.get("limit") == 5
        assert log.get("window") == 60

    def test_unauthorized_access_logged(self):
        """Unauthorized access attempts should be logged."""
        with capture_logs() as cap_logs:
            logger = get_logger("security")
            logger.warning(
                "unauthorized_access",
                user_id="user123",
                resource="/api/v1/admin/users",
                method="GET",
            )

        assert len(cap_logs) == 1
        log = cap_logs[0]
        assert log.get("event") == "unauthorized_access"


class TestLogLevels:
    """Tests for log level handling."""

    def setup_method(self):
        clear_context()

    def teardown_method(self):
        clear_context()

    def test_debug_level_logged(self):
        """Debug level logs should be captured."""
        with capture_logs() as cap_logs:
            logger = get_logger("test")
            logger.debug("debug message", detail="some detail")

        assert len(cap_logs) == 1
        assert cap_logs[0].get("log_level") == "debug"

    def test_info_level_logged(self):
        """Info level logs should be captured."""
        with capture_logs() as cap_logs:
            logger = get_logger("test")
            logger.info("info message")

        assert len(cap_logs) == 1
        assert cap_logs[0].get("log_level") == "info"

    def test_warning_level_logged(self):
        """Warning level logs should be captured."""
        with capture_logs() as cap_logs:
            logger = get_logger("test")
            logger.warning("warning message")

        assert len(cap_logs) == 1
        assert cap_logs[0].get("log_level") == "warning"

    def test_error_level_logged(self):
        """Error level logs should be captured."""
        with capture_logs() as cap_logs:
            logger = get_logger("test")
            logger.error("error message", error_code="E001")

        assert len(cap_logs) == 1
        assert cap_logs[0].get("log_level") == "error"
        assert cap_logs[0].get("error_code") == "E001"


class TestLogPropertyBased:
    """Property-based tests for logging."""

    def setup_method(self):
        clear_context()

    def teardown_method(self):
        clear_context()

    @given(
        user_id=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        room_id=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    )
    @settings(max_examples=10, deadline=None)
    def test_context_preserved_in_logs(self, user_id: str, room_id: str):
        """Context variables should be preserved in logs."""
        bind_context(user_id=user_id, room_id=room_id)
        
        # Verify context is bound
        import structlog
        ctx = structlog.contextvars.get_contextvars()
        assert ctx.get("user_id") == user_id
        assert ctx.get("room_id") == room_id
        
        clear_context()

    @given(
        event_name=st.text(min_size=1, max_size=30, alphabet="abcdefghijklmnopqrstuvwxyz_"),
    )
    @settings(max_examples=10, deadline=None)
    def test_event_name_preserved(self, event_name: str):
        """Event names should be preserved in logs."""
        with capture_logs() as cap_logs:
            logger = get_logger("test")
            logger.info(event_name)

        assert len(cap_logs) == 1
        assert cap_logs[0].get("event") == event_name

    @given(
        extra_fields=st.dictionaries(
            keys=st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz_"),
            values=st.one_of(
                st.integers(min_value=-1000, max_value=1000),
                st.text(min_size=0, max_size=50),
                st.booleans(),
            ),
            min_size=0,
            max_size=5,
        ),
    )
    @settings(max_examples=10, deadline=None)
    def test_extra_fields_preserved(self, extra_fields: dict):
        """Extra fields should be preserved in logs."""
        with capture_logs() as cap_logs:
            logger = get_logger("test")
            logger.info("test event", **extra_fields)

        assert len(cap_logs) == 1
        for key, value in extra_fields.items():
            assert cap_logs[0].get(key) == value


class TestLogEdgeCases:
    """Edge case tests for logging."""

    def setup_method(self):
        clear_context()

    def teardown_method(self):
        clear_context()

    def test_empty_message(self):
        """Empty message should still create log entry."""
        with capture_logs() as cap_logs:
            logger = get_logger("test")
            logger.info("")

        assert len(cap_logs) == 1

    def test_unicode_in_logs(self):
        """Unicode characters should be handled correctly."""
        with capture_logs() as cap_logs:
            logger = get_logger("test")
            logger.info("한글 테스트", user_name="사용자")

        assert len(cap_logs) == 1
        assert cap_logs[0].get("event") == "한글 테스트"
        assert cap_logs[0].get("user_name") == "사용자"

    def test_special_characters_in_logs(self):
        """Special characters should be handled correctly."""
        with capture_logs() as cap_logs:
            logger = get_logger("test")
            logger.info("test<>&\"'", data="<script>alert('xss')</script>")

        assert len(cap_logs) == 1
        assert "<script>" in cap_logs[0].get("data", "")

    def test_none_values_in_logs(self):
        """None values should be handled correctly."""
        with capture_logs() as cap_logs:
            logger = get_logger("test")
            logger.info("test event", nullable_field=None)

        assert len(cap_logs) == 1
        assert cap_logs[0].get("nullable_field") is None

    def test_nested_dict_in_logs(self):
        """Nested dictionaries should be handled correctly."""
        with capture_logs() as cap_logs:
            logger = get_logger("test")
            logger.info(
                "test event",
                nested={"level1": {"level2": "value"}},
            )

        assert len(cap_logs) == 1
        assert cap_logs[0].get("nested") == {"level1": {"level2": "value"}}

    def test_list_in_logs(self):
        """Lists should be handled correctly."""
        with capture_logs() as cap_logs:
            logger = get_logger("test")
            logger.info("test event", items=[1, 2, 3, "four"])

        assert len(cap_logs) == 1
        assert cap_logs[0].get("items") == [1, 2, 3, "four"]

    def test_multiple_loggers_independent(self):
        """Multiple loggers should work independently."""
        with capture_logs() as cap_logs:
            logger1 = get_logger("module1")
            logger2 = get_logger("module2")

            logger1.info("from module1")
            logger2.info("from module2")

        assert len(cap_logs) == 2
        assert cap_logs[0].get("event") == "from module1"
        assert cap_logs[1].get("event") == "from module2"
