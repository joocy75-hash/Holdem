"""Tests for login attempt limiter service.

Phase 1.2: Tests for Redis-based login failure counter.

Tests ensure that:
1. Login attempts are tracked correctly
2. Account is locked after 5 failed attempts
3. Lockout lasts for 15 minutes
4. Successful login resets the counter
5. Retry-After header is accurate
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.login_limiter import (
    LoginLimiter,
    LoginAttemptResult,
    get_login_limiter,
    init_login_limiter,
)


# =============================================================================
# Mock Redis Client
# =============================================================================


class MockRedisClient:
    """Mock Redis client for testing."""

    def __init__(self):
        self._data: dict[str, str] = {}
        self._ttls: dict[str, int] = {}

    async def get(self, key: str) -> str | None:
        """Get value by key."""
        return self._data.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> bool:
        """Set value with optional expiry."""
        self._data[key] = value
        if ex:
            self._ttls[key] = ex
        return True

    async def setex(self, key: str, seconds: int, value: str) -> bool:
        """Set value with expiry."""
        self._data[key] = value
        self._ttls[key] = seconds
        return True

    async def incr(self, key: str) -> int:
        """Increment value."""
        current = int(self._data.get(key, "0"))
        new_value = current + 1
        self._data[key] = str(new_value)
        return new_value

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiry on key."""
        self._ttls[key] = seconds
        return True

    async def ttl(self, key: str) -> int:
        """Get TTL for key."""
        if key not in self._data:
            return -2  # Key doesn't exist
        return self._ttls.get(key, -1)  # -1 means no expiry

    async def delete(self, *keys: str) -> int:
        """Delete keys."""
        count = 0
        for key in keys:
            if key in self._data:
                del self._data[key]
                count += 1
            if key in self._ttls:
                del self._ttls[key]
        return count

    def pipeline(self):
        """Return mock pipeline."""
        return MockPipeline(self)


class MockPipeline:
    """Mock Redis pipeline."""

    def __init__(self, client: MockRedisClient):
        self._client = client
        self._commands: list[tuple[str, tuple]] = []

    def incr(self, key: str):
        """Queue incr command."""
        self._commands.append(("incr", (key,)))
        return self

    def expire(self, key: str, seconds: int):
        """Queue expire command."""
        self._commands.append(("expire", (key, seconds)))
        return self

    async def execute(self) -> list:
        """Execute all queued commands."""
        results = []
        for cmd, args in self._commands:
            if cmd == "incr":
                result = await self._client.incr(args[0])
                results.append(result)
            elif cmd == "expire":
                result = await self._client.expire(args[0], args[1])
                results.append(result)
        return results


# =============================================================================
# Unit Tests
# =============================================================================


class TestLoginLimiter:
    """Tests for LoginLimiter class."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        return MockRedisClient()

    @pytest.fixture
    def limiter(self, mock_redis):
        """Create LoginLimiter with mock Redis."""
        return LoginLimiter(mock_redis)

    @pytest.mark.asyncio
    async def test_check_login_allowed_no_attempts(self, limiter):
        """Test that login is allowed when no previous attempts."""
        result = await limiter.check_login_allowed("test@example.com")
        
        assert result.is_locked is False
        assert result.attempts_remaining == 5
        assert result.retry_after_seconds == 0
        assert result.total_attempts == 0

    @pytest.mark.asyncio
    async def test_record_failed_attempt_increments_counter(self, limiter, mock_redis):
        """Test that failed attempt increments the counter."""
        email = "test@example.com"
        
        result = await limiter.record_failed_attempt(email)
        
        assert result.is_locked is False
        assert result.attempts_remaining == 4
        assert result.total_attempts == 1

    @pytest.mark.asyncio
    async def test_account_locked_after_5_failures(self, limiter):
        """Test that account is locked after 5 failed attempts."""
        email = "test@example.com"
        
        # Record 5 failed attempts
        for i in range(5):
            result = await limiter.record_failed_attempt(email)
        
        # Should be locked after 5th attempt
        assert result.is_locked is True
        assert result.attempts_remaining == 0
        assert result.retry_after_seconds == 900  # 15 minutes

    @pytest.mark.asyncio
    async def test_locked_account_blocks_login(self, limiter):
        """Test that locked account blocks further login attempts."""
        email = "test@example.com"
        
        # Lock the account
        for _ in range(5):
            await limiter.record_failed_attempt(email)
        
        # Check if login is allowed
        result = await limiter.check_login_allowed(email)
        
        assert result.is_locked is True
        assert result.attempts_remaining == 0
        assert result.retry_after_seconds > 0

    @pytest.mark.asyncio
    async def test_reset_attempts_clears_counter(self, limiter, mock_redis):
        """Test that reset_attempts clears the counter and lockout."""
        email = "test@example.com"
        
        # Record some failed attempts
        for _ in range(3):
            await limiter.record_failed_attempt(email)
        
        # Reset attempts
        await limiter.reset_attempts(email)
        
        # Check that counter is cleared
        result = await limiter.check_login_allowed(email)
        
        assert result.is_locked is False
        assert result.attempts_remaining == 5
        assert result.total_attempts == 0

    @pytest.mark.asyncio
    async def test_reset_attempts_clears_lockout(self, limiter):
        """Test that reset_attempts clears lockout status."""
        email = "test@example.com"
        
        # Lock the account
        for _ in range(5):
            await limiter.record_failed_attempt(email)
        
        # Verify locked
        result = await limiter.check_login_allowed(email)
        assert result.is_locked is True
        
        # Reset attempts
        await limiter.reset_attempts(email)
        
        # Verify unlocked
        result = await limiter.check_login_allowed(email)
        assert result.is_locked is False

    @pytest.mark.asyncio
    async def test_email_normalization(self, limiter):
        """Test that email is normalized to lowercase."""
        # Record attempt with uppercase email
        await limiter.record_failed_attempt("TEST@EXAMPLE.COM")
        
        # Check with lowercase email
        result = await limiter.check_login_allowed("test@example.com")
        
        assert result.total_attempts == 1

    @pytest.mark.asyncio
    async def test_get_lockout_status(self, limiter):
        """Test get_lockout_status returns correct information."""
        email = "test@example.com"
        
        # Record some failed attempts
        for _ in range(3):
            await limiter.record_failed_attempt(email)
        
        status = await limiter.get_lockout_status(email)
        
        assert status["email"] == email
        assert status["is_locked"] is False
        assert status["failed_attempts"] == 3
        assert status["max_attempts"] == 5
        assert status["lockout_duration_seconds"] == 900

    @pytest.mark.asyncio
    async def test_get_lockout_status_when_locked(self, limiter):
        """Test get_lockout_status when account is locked."""
        email = "test@example.com"
        
        # Lock the account
        for _ in range(5):
            await limiter.record_failed_attempt(email)
        
        status = await limiter.get_lockout_status(email)
        
        assert status["is_locked"] is True
        assert status["retry_after_seconds"] > 0
        assert status["failed_attempts"] == 5

    @pytest.mark.asyncio
    async def test_different_emails_tracked_separately(self, limiter):
        """Test that different emails are tracked separately."""
        email1 = "user1@example.com"
        email2 = "user2@example.com"
        
        # Record attempts for email1
        for _ in range(3):
            await limiter.record_failed_attempt(email1)
        
        # Record attempts for email2
        await limiter.record_failed_attempt(email2)
        
        # Check email1
        result1 = await limiter.check_login_allowed(email1)
        assert result1.total_attempts == 3
        
        # Check email2
        result2 = await limiter.check_login_allowed(email2)
        assert result2.total_attempts == 1


# =============================================================================
# Integration Tests (with real Redis mock behavior)
# =============================================================================


class TestLoginLimiterIntegration:
    """Integration tests for login limiter."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        return MockRedisClient()

    @pytest.fixture
    def limiter(self, mock_redis):
        """Create LoginLimiter with mock Redis."""
        return LoginLimiter(mock_redis)

    @pytest.mark.asyncio
    async def test_full_lockout_flow(self, limiter):
        """Test complete lockout flow: attempts → lock → reset."""
        email = "test@example.com"
        
        # 1. Initial state - no attempts
        result = await limiter.check_login_allowed(email)
        assert result.is_locked is False
        assert result.attempts_remaining == 5
        
        # 2. Record 4 failed attempts
        for i in range(4):
            result = await limiter.record_failed_attempt(email)
            assert result.is_locked is False
            assert result.attempts_remaining == 4 - i
        
        # 3. 5th attempt locks the account
        result = await limiter.record_failed_attempt(email)
        assert result.is_locked is True
        assert result.retry_after_seconds == 900
        
        # 4. Further login attempts are blocked
        result = await limiter.check_login_allowed(email)
        assert result.is_locked is True
        
        # 5. Reset clears everything
        await limiter.reset_attempts(email)
        result = await limiter.check_login_allowed(email)
        assert result.is_locked is False
        assert result.attempts_remaining == 5

    @pytest.mark.asyncio
    async def test_successful_login_resets_counter(self, limiter):
        """Test that successful login (reset) clears failed attempts."""
        email = "test@example.com"
        
        # Record 4 failed attempts (one away from lockout)
        for _ in range(4):
            await limiter.record_failed_attempt(email)
        
        # Simulate successful login by resetting
        await limiter.reset_attempts(email)
        
        # Counter should be reset
        result = await limiter.check_login_allowed(email)
        assert result.attempts_remaining == 5
        assert result.total_attempts == 0


# =============================================================================
# Factory Function Tests
# =============================================================================


class TestLoginLimiterFactory:
    """Tests for factory functions."""

    @pytest.mark.asyncio
    async def test_init_login_limiter(self):
        """Test init_login_limiter creates instance."""
        mock_redis = MockRedisClient()
        
        limiter = await init_login_limiter(mock_redis)
        
        assert limiter is not None
        assert isinstance(limiter, LoginLimiter)

    def test_get_login_limiter_returns_none_without_redis(self):
        """Test get_login_limiter returns None when Redis not available."""
        # Reset the singleton
        import app.services.login_limiter as module
        module._login_limiter = None
        
        with patch("app.utils.redis_client.redis_client", None):
            result = get_login_limiter()
            
            # Should return None when Redis is not available
            assert result is None
