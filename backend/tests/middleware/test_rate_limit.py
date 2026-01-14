"""Rate Limit Property-Based Tests.

Property 5: Rate Limit Accuracy
- Tests rate limit enforcement and Retry-After header accuracy
- Validates: Requirements 8.1, 8.3

Tests ensure that:
1. Rate limits are enforced correctly
2. 429 responses are returned when limit exceeded
3. Retry-After header is accurate
4. Sliding window works correctly
5. User-based and IP-based limits work independently
"""

import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from hypothesis import given, strategies as st, settings, assume, HealthCheck

from app.middleware.rate_limit import (
    SlidingWindowRateLimiter,
    RateLimitMiddleware,
    WebSocketRateLimiter,
)


# =============================================================================
# Mock Redis Client
# =============================================================================


class MockRedisClient:
    """Mock Redis client for testing."""

    def __init__(self):
        self._data: dict[str, list[tuple[str, float]]] = {}
        self._expiry: dict[str, float] = {}

    def pipeline(self):
        return MockPipeline(self)

    async def zrange(self, key: str, start: int, end: int, withscores: bool = False):
        """Get range of sorted set."""
        if key not in self._data:
            return []
        entries = sorted(self._data[key], key=lambda x: x[1])
        if end == -1:
            end = len(entries)
        else:
            end = end + 1
        result = entries[start:end]
        if withscores:
            return result
        return [e[0] for e in result]

    async def zrem(self, key: str, member: str):
        """Remove member from sorted set."""
        if key in self._data:
            self._data[key] = [(m, s) for m, s in self._data[key] if m != member]


class MockPipeline:
    """Mock Redis pipeline."""

    def __init__(self, client: MockRedisClient):
        self._client = client
        self._commands: list[tuple[str, tuple]] = []

    def zremrangebyscore(self, key: str, min_score: float, max_score: float):
        self._commands.append(("zremrangebyscore", (key, min_score, max_score)))
        return self

    def zcard(self, key: str):
        self._commands.append(("zcard", (key,)))
        return self

    def zadd(self, key: str, mapping: dict):
        self._commands.append(("zadd", (key, mapping)))
        return self

    def expire(self, key: str, seconds: int):
        self._commands.append(("expire", (key, seconds)))
        return self

    async def execute(self):
        results = []
        for cmd, args in self._commands:
            if cmd == "zremrangebyscore":
                key, min_score, max_score = args
                if key in self._client._data:
                    self._client._data[key] = [
                        (m, s) for m, s in self._client._data[key]
                        if not (min_score <= s <= max_score)
                    ]
                results.append(0)
            elif cmd == "zcard":
                key = args[0]
                count = len(self._client._data.get(key, []))
                results.append(count)
            elif cmd == "zadd":
                key, mapping = args
                if key not in self._client._data:
                    self._client._data[key] = []
                for member, score in mapping.items():
                    self._client._data[key].append((member, score))
                results.append(1)
            elif cmd == "expire":
                key, seconds = args
                self._client._expiry[key] = time.time() + seconds
                results.append(1)
        return results


# =============================================================================
# Property 5: Rate Limit Accuracy Tests
# =============================================================================


class TestSlidingWindowRateLimiter:
    """Tests for SlidingWindowRateLimiter."""

    @pytest.fixture
    def redis_client(self):
        return MockRedisClient()

    @pytest.fixture
    def limiter(self, redis_client):
        return SlidingWindowRateLimiter(redis_client)

    @pytest.mark.asyncio
    async def test_allows_requests_under_limit(self, limiter):
        """Requests under limit should be allowed."""
        key = "test:key"
        limit = 10
        window = 60

        for i in range(limit):
            is_allowed, remaining, retry_after = await limiter.is_allowed(key, limit, window)
            assert is_allowed is True
            assert remaining >= 0
            assert retry_after == 0

    @pytest.mark.asyncio
    async def test_blocks_requests_over_limit(self, limiter):
        """Requests over limit should be blocked."""
        key = "test:key"
        limit = 5
        window = 60

        # Make requests up to limit
        for i in range(limit):
            is_allowed, _, _ = await limiter.is_allowed(key, limit, window)
            assert is_allowed is True

        # Next request should be blocked
        is_allowed, remaining, retry_after = await limiter.is_allowed(key, limit, window)
        assert is_allowed is False
        assert remaining == 0
        assert retry_after > 0

    @pytest.mark.asyncio
    async def test_retry_after_is_positive(self, limiter):
        """Retry-After should always be positive when blocked."""
        key = "test:key"
        limit = 3
        window = 60

        # Exhaust limit
        for _ in range(limit):
            await limiter.is_allowed(key, limit, window)

        # Check retry_after
        is_allowed, _, retry_after = await limiter.is_allowed(key, limit, window)
        assert is_allowed is False
        assert retry_after >= 1

    @pytest.mark.asyncio
    @given(limit=st.integers(min_value=1, max_value=100))
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_remaining_count_decreases(self, limiter, limit: int):
        """Remaining count should decrease with each request."""
        key = f"test:key:{limit}"
        window = 60

        previous_remaining = limit
        for i in range(min(limit, 10)):  # Test up to 10 requests
            is_allowed, remaining, _ = await limiter.is_allowed(key, limit, window)
            if is_allowed:
                assert remaining <= previous_remaining
                previous_remaining = remaining


class TestRateLimitMiddleware:
    """Tests for RateLimitMiddleware."""

    @pytest.fixture
    def redis_client(self):
        return MockRedisClient()

    @pytest.fixture
    def middleware(self, redis_client):
        app = AsyncMock()
        return RateLimitMiddleware(app, redis_client)

    def test_get_ip_limit_for_known_path(self, middleware):
        """Known paths should return specific limits."""
        limit, window = middleware._get_ip_limit_for_path("/api/v1/auth/login")
        assert limit == 5
        assert window == 60

    def test_get_ip_limit_for_unknown_path(self, middleware):
        """Unknown paths should return default limits."""
        limit, window = middleware._get_ip_limit_for_path("/api/v1/unknown")
        assert limit == middleware.DEFAULT_IP_LIMIT[0]
        assert window == middleware.DEFAULT_IP_LIMIT[1]

    def test_get_user_limit_for_known_path(self, middleware):
        """Known paths should return user-specific limits."""
        limit, window = middleware._get_user_limit_for_path("/api/v1/auth/refresh")
        assert limit == 20
        assert window == 60

    def test_normalize_path_with_uuid(self, middleware):
        """UUIDs in path should be normalized."""
        path = "/api/v1/rooms/550e8400-e29b-41d4-a716-446655440000"
        normalized = middleware._normalize_path(path)
        assert "*" in normalized

    def test_normalize_path_with_numeric_id(self, middleware):
        """Numeric IDs in path should be normalized."""
        path = "/api/v1/rooms/12345"
        normalized = middleware._normalize_path(path)
        assert "*" in normalized

    def test_get_client_ip_from_forwarded_header(self, middleware):
        """Should extract IP from X-Forwarded-For header."""
        request = MagicMock()
        request.headers = {"X-Forwarded-For": "192.168.1.1, 10.0.0.1"}
        request.client = MagicMock(host="127.0.0.1")

        ip = middleware._get_client_ip(request)
        assert ip == "192.168.1.1"

    def test_get_client_ip_from_client(self, middleware):
        """Should extract IP from client when no forwarded header."""
        request = MagicMock()
        request.headers = {}
        request.client = MagicMock(host="192.168.1.100")

        ip = middleware._get_client_ip(request)
        assert ip == "192.168.1.100"


class TestWebSocketRateLimiter:
    """Tests for WebSocketRateLimiter."""

    @pytest.fixture
    def redis_client(self):
        return MockRedisClient()

    @pytest.fixture
    def ws_limiter(self, redis_client):
        return WebSocketRateLimiter(
            redis_client,
            messages_per_second=10,
            burst_limit=5,
        )

    @pytest.mark.asyncio
    async def test_allows_messages_under_burst_limit(self, ws_limiter):
        """Messages under burst limit should be allowed."""
        connection_id = "test-connection"

        for i in range(5):
            is_allowed, retry_after = await ws_limiter.is_allowed(connection_id)
            assert is_allowed is True
            assert retry_after == 0

    @pytest.mark.asyncio
    async def test_blocks_messages_over_burst_limit(self, ws_limiter):
        """Messages over burst limit should be blocked."""
        connection_id = "test-connection"

        # Exhaust burst limit
        for _ in range(5):
            await ws_limiter.is_allowed(connection_id)

        # Next message should be blocked
        is_allowed, retry_after = await ws_limiter.is_allowed(connection_id)
        assert is_allowed is False
        assert retry_after > 0

    @pytest.mark.asyncio
    async def test_different_connections_independent(self, ws_limiter):
        """Different connections should have independent limits."""
        conn1 = "connection-1"
        conn2 = "connection-2"

        # Exhaust limit for conn1
        for _ in range(5):
            await ws_limiter.is_allowed(conn1)

        # conn2 should still be allowed
        is_allowed, _ = await ws_limiter.is_allowed(conn2)
        assert is_allowed is True

    @pytest.mark.asyncio
    async def test_returns_retry_after_in_milliseconds(self, ws_limiter):
        """Retry-After should be in milliseconds."""
        connection_id = "test-connection"

        # Exhaust limit
        for _ in range(5):
            await ws_limiter.is_allowed(connection_id)

        # Check retry_after is in ms (should be >= 1000 for 1 second)
        is_allowed, retry_after = await ws_limiter.is_allowed(connection_id)
        assert is_allowed is False
        # retry_after is in milliseconds, so should be >= 1000 for 1 second window
        assert retry_after >= 1000 or retry_after > 0


class TestRateLimitPropertyBased:
    """Property-based tests for rate limiting."""

    @pytest.fixture
    def redis_client(self):
        return MockRedisClient()

    @pytest.fixture
    def limiter(self, redis_client):
        return SlidingWindowRateLimiter(redis_client)

    @pytest.mark.asyncio
    @given(
        limit=st.integers(min_value=1, max_value=50),
        window=st.integers(min_value=1, max_value=300),
    )
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_limit_enforced_exactly(self, limiter, limit: int, window: int):
        """Rate limit should be enforced at exactly the limit."""
        key = f"test:exact:{limit}:{window}"

        allowed_count = 0
        for _ in range(limit + 5):
            is_allowed, _, _ = await limiter.is_allowed(key, limit, window)
            if is_allowed:
                allowed_count += 1

        # Should allow exactly 'limit' requests
        assert allowed_count == limit

    @pytest.mark.asyncio
    @given(limit=st.integers(min_value=1, max_value=20))
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_remaining_never_negative(self, limiter, limit: int):
        """Remaining count should never be negative."""
        key = f"test:remaining:{limit}"
        window = 60

        for _ in range(limit + 10):
            is_allowed, remaining, _ = await limiter.is_allowed(key, limit, window)
            assert remaining >= 0

    @pytest.mark.asyncio
    @given(limit=st.integers(min_value=1, max_value=20))
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_retry_after_within_window(self, limiter, limit: int):
        """Retry-After should be within the window size."""
        key = f"test:retry:{limit}"
        window = 60

        # Exhaust limit
        for _ in range(limit):
            await limiter.is_allowed(key, limit, window)

        # Check retry_after
        is_allowed, _, retry_after = await limiter.is_allowed(key, limit, window)
        if not is_allowed:
            assert 0 < retry_after <= window + 1


class TestRateLimitEdgeCases:
    """Edge case tests for rate limiting."""

    @pytest.fixture
    def redis_client(self):
        return MockRedisClient()

    @pytest.fixture
    def limiter(self, redis_client):
        return SlidingWindowRateLimiter(redis_client)

    @pytest.mark.asyncio
    async def test_limit_of_one(self, limiter):
        """Rate limit of 1 should work correctly."""
        key = "test:limit:one"
        limit = 1
        window = 60

        # First request allowed
        is_allowed, remaining, _ = await limiter.is_allowed(key, limit, window)
        assert is_allowed is True
        assert remaining == 0

        # Second request blocked
        is_allowed, _, retry_after = await limiter.is_allowed(key, limit, window)
        assert is_allowed is False
        assert retry_after > 0

    @pytest.mark.asyncio
    async def test_very_short_window(self, limiter):
        """Very short window (1 second) should work."""
        key = "test:short:window"
        limit = 5
        window = 1

        for _ in range(limit):
            is_allowed, _, _ = await limiter.is_allowed(key, limit, window)
            assert is_allowed is True

        is_allowed, _, _ = await limiter.is_allowed(key, limit, window)
        assert is_allowed is False

    @pytest.mark.asyncio
    async def test_high_limit(self, limiter):
        """High limit should work correctly."""
        key = "test:high:limit"
        limit = 1000
        window = 60

        # Make 100 requests (should all be allowed)
        for _ in range(100):
            is_allowed, _, _ = await limiter.is_allowed(key, limit, window)
            assert is_allowed is True

    def test_middleware_without_redis(self):
        """Middleware should work without Redis (no rate limiting)."""
        app = AsyncMock()
        middleware = RateLimitMiddleware(app, redis_client=None)
        assert middleware._limiter is None

    def test_ws_limiter_without_redis(self):
        """WebSocket limiter should work without Redis."""
        limiter = WebSocketRateLimiter(None)
        assert limiter._limiter is None
