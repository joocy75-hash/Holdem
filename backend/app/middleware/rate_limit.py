"""Rate limiting middleware.

Provides Redis-based rate limiting for API endpoints.

Phase 4 Enhancement:
- Sliding window rate limiting using Redis sorted sets
- User-based rate limiting for authenticated requests
- WebSocket message rate limiting
- More accurate Retry-After header calculation
"""

import time
from typing import Callable, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.logging_config import get_logger

logger = get_logger(__name__)


class SlidingWindowRateLimiter:
    """Sliding window rate limiter using Redis sorted sets.

    More accurate than fixed window counters as it considers
    the actual time distribution of requests.
    """

    def __init__(self, redis_client):
        """Initialize rate limiter.

        Args:
            redis_client: Redis client instance
        """
        self._redis = redis_client

    async def is_allowed(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> tuple[bool, int, int]:
        """Check if request is allowed using sliding window.

        Args:
            key: Rate limit key (e.g., "ratelimit:ip:path")
            limit: Maximum requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            Tuple of (is_allowed, remaining, retry_after_seconds)
        """
        now = time.time()
        window_start = now - window_seconds

        # Use pipeline for atomic operations
        pipe = self._redis.pipeline()

        # Remove entries outside the window
        pipe.zremrangebyscore(key, 0, window_start)

        # Count current entries in window
        pipe.zcard(key)

        # Add current request with timestamp as score
        request_id = f"{now}:{id(self)}"
        pipe.zadd(key, {request_id: now})

        # Set key expiry to window size (cleanup)
        pipe.expire(key, window_seconds + 1)

        results = await pipe.execute()
        current_count = results[1]  # zcard result

        if current_count >= limit:
            # Over limit - calculate accurate retry_after
            # Get the oldest entry to know when it will expire
            oldest_entries = await self._redis.zrange(key, 0, 0, withscores=True)
            if oldest_entries:
                oldest_time = oldest_entries[0][1]
                retry_after = int(oldest_time + window_seconds - now) + 1
                retry_after = max(1, retry_after)  # At least 1 second
            else:
                retry_after = window_seconds

            # Remove the request we just added since it's rejected
            await self._redis.zrem(key, request_id)

            return False, 0, retry_after

        remaining = max(0, limit - current_count - 1)
        return True, remaining, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis-based rate limiting middleware with sliding window.

    Features:
    - Sliding window for accurate rate limiting
    - IP-based limits for unauthenticated requests
    - User-based limits for authenticated requests
    - Endpoint-specific rate limits
    """

    # IP-based rate limits (unauthenticated requests)
    IP_RATE_LIMITS: dict[str, tuple[int, int]] = {
        "/api/v1/auth/login": (5, 60),       # 5 requests per 60 seconds
        "/api/v1/auth/register": (3, 60),    # 3 requests per 60 seconds
        "/api/v1/auth/refresh": (10, 60),    # 10 requests per 60 seconds
    }

    # User-based rate limits (authenticated requests - more generous)
    USER_RATE_LIMITS: dict[str, tuple[int, int]] = {
        "/api/v1/auth/refresh": (20, 60),    # 20 requests per 60 seconds
        "/api/v1/rooms": (60, 60),           # 60 requests per 60 seconds
        # Wallet endpoints - stricter limits for financial security
        "/api/v1/wallet/withdraw": (5, 3600),  # 5 requests per hour
        "/api/v1/wallet/deposit-address": (10, 60),  # 10 requests per minute
        "/api/v1/wallet/balance": (60, 60),   # 60 requests per minute
        "/api/v1/wallet/transactions": (30, 60),  # 30 requests per minute
        "/api/v1/wallet/rates": (120, 60),    # 120 requests per minute (cached)
    }

    # Default rate limits
    DEFAULT_IP_LIMIT: tuple[int, int] = (100, 60)    # 100 requests per 60 seconds
    DEFAULT_USER_LIMIT: tuple[int, int] = (200, 60)  # 200 requests per 60 seconds

    def __init__(self, app: Callable, redis_client=None):
        """Initialize rate limiter.

        Args:
            app: ASGI application
            redis_client: Redis client instance (optional, disables rate limiting if None)
        """
        super().__init__(app)
        self._redis = redis_client
        self._limiter: Optional[SlidingWindowRateLimiter] = None
        if redis_client:
            self._limiter = SlidingWindowRateLimiter(redis_client)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limit before processing request."""
        # Skip WebSocket upgrade requests - BaseHTTPMiddleware doesn't handle them properly
        if request.headers.get("upgrade", "").lower() == "websocket":
            return await call_next(request)

        # Skip rate limiting if Redis not available
        if self._limiter is None:
            return await call_next(request)

        # Skip rate limiting for WebSocket, health checks, and docs
        path = request.url.path
        if path.startswith(("/ws", "/health", "/docs", "/redoc", "/openapi.json", "/metrics")):
            return await call_next(request)

        # Get client identifiers
        client_ip = self._get_client_ip(request)
        user_id = self._get_user_id(request)

        # Determine rate limit key and limits
        if user_id:
            # Authenticated user - use user-based limits
            key = f"ratelimit:user:{user_id}:{self._normalize_path(path)}"
            limit, window = self._get_user_limit_for_path(path)
        else:
            # Unauthenticated - use IP-based limits
            key = f"ratelimit:ip:{client_ip}:{self._normalize_path(path)}"
            limit, window = self._get_ip_limit_for_path(path)

        try:
            is_allowed, remaining, retry_after = await self._limiter.is_allowed(
                key, limit, window
            )

            if not is_allowed:
                # Log rate limit violation
                logger.warning(
                    "rate_limit_exceeded",
                    client_ip=client_ip,
                    user_id=user_id,
                    path=path,
                    limit=limit,
                    window=window,
                    retry_after=retry_after,
                )
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": "Too many requests. Please try again later.",
                            "details": {
                                "limit": limit,
                                "window": window,
                                "retry_after": retry_after,
                            },
                        }
                    },
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(retry_after),
                    },
                )

            # Add rate limit headers to response
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(window)
            return response

        except Exception as e:
            # If Redis fails, allow request but log error
            logger.error("rate_limit_check_failed", error=str(e), path=path)
            return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request.

        Handles X-Forwarded-For header for reverse proxy setups.
        """
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take first IP in chain (original client)
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request if authenticated.

        Checks for user_id in request state (set by auth middleware).
        """
        if hasattr(request.state, "user_id"):
            return request.state.user_id
        return None

    def _normalize_path(self, path: str) -> str:
        """Normalize path for rate limit key.

        Removes path parameters to group similar endpoints.
        e.g., /api/v1/rooms/123 -> /api/v1/rooms/*
        """
        parts = path.split("/")
        normalized = []
        for part in parts:
            # Replace UUIDs and numeric IDs with wildcard
            if part and (
                len(part) == 36 and "-" in part  # UUID
                or part.isdigit()  # Numeric ID
            ):
                normalized.append("*")
            else:
                normalized.append(part)
        return "/".join(normalized)

    def _get_ip_limit_for_path(self, path: str) -> tuple[int, int]:
        """Get IP-based rate limit for the given path."""
        # Check exact match first
        if path in self.IP_RATE_LIMITS:
            return self.IP_RATE_LIMITS[path]

        # Check prefix match for parameterized routes
        for pattern, limit in self.IP_RATE_LIMITS.items():
            if path.startswith(pattern):
                return limit

        return self.DEFAULT_IP_LIMIT

    def _get_user_limit_for_path(self, path: str) -> tuple[int, int]:
        """Get user-based rate limit for the given path."""
        # Check exact match first
        if path in self.USER_RATE_LIMITS:
            return self.USER_RATE_LIMITS[path]

        # Check prefix match for parameterized routes
        for pattern, limit in self.USER_RATE_LIMITS.items():
            if path.startswith(pattern):
                return limit

        return self.DEFAULT_USER_LIMIT


class WebSocketRateLimiter:
    """Rate limiter for WebSocket messages.

    Limits the number of messages a client can send per time window.
    """

    def __init__(
        self,
        redis_client,
        messages_per_second: int = 10,
        burst_limit: int = 20,
    ):
        """Initialize WebSocket rate limiter.

        Args:
            redis_client: Redis client instance
            messages_per_second: Sustained message rate limit
            burst_limit: Maximum burst of messages allowed
        """
        self._redis = redis_client
        self._messages_per_second = messages_per_second
        self._burst_limit = burst_limit
        self._limiter = SlidingWindowRateLimiter(redis_client) if redis_client else None

    async def is_allowed(self, connection_id: str) -> tuple[bool, int]:
        """Check if WebSocket message is allowed.

        Args:
            connection_id: Unique connection identifier

        Returns:
            Tuple of (is_allowed, retry_after_ms)
        """
        if self._limiter is None:
            return True, 0

        key = f"ws_ratelimit:{connection_id}"

        try:
            is_allowed, remaining, retry_after = await self._limiter.is_allowed(
                key, self._burst_limit, 1  # 1 second window
            )

            if not is_allowed:
                logger.warning(
                    "ws_rate_limit_exceeded",
                    connection_id=connection_id,
                    burst_limit=self._burst_limit,
                )
                return False, retry_after * 1000  # Convert to milliseconds

            return True, 0

        except Exception as e:
            logger.error("ws_rate_limit_check_failed", error=str(e))
            return True, 0  # Allow on error
