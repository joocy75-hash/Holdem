"""Login attempt limiter service.

Phase 1.2: Redis-based login failure counter to prevent brute-force attacks.

Features:
- 5 failed attempts → 15 minute lockout
- Email-based tracking (per account protection)
- Automatic counter reset on successful login
- Accurate retry-after calculation
"""

import time
from typing import NamedTuple

from redis.asyncio import Redis

from app.logging_config import get_logger

logger = get_logger(__name__)


class LoginAttemptResult(NamedTuple):
    """Result of login attempt check."""
    is_locked: bool
    attempts_remaining: int
    retry_after_seconds: int
    total_attempts: int


class LoginLimiter:
    """Redis-based login attempt limiter.
    
    Tracks failed login attempts per email and enforces lockout
    after exceeding the maximum allowed failures.
    """
    
    # Configuration
    MAX_ATTEMPTS = 5  # Maximum failed attempts before lockout
    LOCKOUT_SECONDS = 900  # 15 minutes lockout
    ATTEMPT_WINDOW_SECONDS = 900  # Track attempts within 15 minute window
    
    # Redis key prefixes
    KEY_PREFIX_ATTEMPTS = "login_attempts"
    KEY_PREFIX_LOCKOUT = "login_lockout"
    
    def __init__(self, redis_client: Redis):
        """Initialize login limiter.
        
        Args:
            redis_client: Redis client instance
        """
        self._redis = redis_client
    
    def _get_attempts_key(self, email: str) -> str:
        """Get Redis key for tracking login attempts."""
        # Normalize email to lowercase for consistent tracking
        return f"{self.KEY_PREFIX_ATTEMPTS}:{email.lower()}"
    
    def _get_lockout_key(self, email: str) -> str:
        """Get Redis key for lockout status."""
        return f"{self.KEY_PREFIX_LOCKOUT}:{email.lower()}"
    
    async def check_login_allowed(self, email: str) -> LoginAttemptResult:
        """Check if login attempt is allowed for the given email.
        
        Args:
            email: User email address
            
        Returns:
            LoginAttemptResult with lockout status and remaining attempts
        """
        lockout_key = self._get_lockout_key(email)
        attempts_key = self._get_attempts_key(email)
        
        # Check if account is locked
        lockout_ttl = await self._redis.ttl(lockout_key)
        
        if lockout_ttl > 0:
            # Account is locked
            logger.warning(
                "login_attempt_blocked",
                email=email,
                retry_after=lockout_ttl,
                reason="account_locked",
            )
            return LoginAttemptResult(
                is_locked=True,
                attempts_remaining=0,
                retry_after_seconds=lockout_ttl,
                total_attempts=self.MAX_ATTEMPTS,
            )
        
        # Get current attempt count
        current_attempts = await self._redis.get(attempts_key)
        attempt_count = int(current_attempts) if current_attempts else 0
        
        attempts_remaining = max(0, self.MAX_ATTEMPTS - attempt_count)
        
        return LoginAttemptResult(
            is_locked=False,
            attempts_remaining=attempts_remaining,
            retry_after_seconds=0,
            total_attempts=attempt_count,
        )
    
    async def record_failed_attempt(self, email: str, ip_address: str | None = None) -> LoginAttemptResult:
        """Record a failed login attempt.
        
        Args:
            email: User email address
            ip_address: Client IP address (for logging)
            
        Returns:
            LoginAttemptResult with updated status
        """
        attempts_key = self._get_attempts_key(email)
        lockout_key = self._get_lockout_key(email)
        
        # Increment attempt counter
        pipe = self._redis.pipeline()
        pipe.incr(attempts_key)
        pipe.expire(attempts_key, self.ATTEMPT_WINDOW_SECONDS)
        results = await pipe.execute()
        
        new_count = results[0]
        
        logger.warning(
            "login_failed_attempt",
            email=email,
            ip_address=ip_address,
            attempt_number=new_count,
            max_attempts=self.MAX_ATTEMPTS,
        )
        
        # Check if we should lock the account
        if new_count >= self.MAX_ATTEMPTS:
            # Set lockout
            await self._redis.setex(
                lockout_key,
                self.LOCKOUT_SECONDS,
                str(int(time.time())),
            )
            
            logger.warning(
                "account_locked",
                email=email,
                ip_address=ip_address,
                lockout_seconds=self.LOCKOUT_SECONDS,
                failed_attempts=new_count,
            )
            
            return LoginAttemptResult(
                is_locked=True,
                attempts_remaining=0,
                retry_after_seconds=self.LOCKOUT_SECONDS,
                total_attempts=new_count,
            )
        
        return LoginAttemptResult(
            is_locked=False,
            attempts_remaining=self.MAX_ATTEMPTS - new_count,
            retry_after_seconds=0,
            total_attempts=new_count,
        )
    
    async def reset_attempts(self, email: str) -> None:
        """Reset login attempts after successful login.
        
        Args:
            email: User email address
        """
        attempts_key = self._get_attempts_key(email)
        lockout_key = self._get_lockout_key(email)
        
        # Delete both keys
        await self._redis.delete(attempts_key, lockout_key)
        
        logger.info(
            "login_attempts_reset",
            email=email,
        )
    
    async def get_lockout_status(self, email: str) -> dict:
        """Get detailed lockout status for an email.
        
        Args:
            email: User email address
            
        Returns:
            Dict with lockout details
        """
        lockout_key = self._get_lockout_key(email)
        attempts_key = self._get_attempts_key(email)
        
        lockout_ttl = await self._redis.ttl(lockout_key)
        current_attempts = await self._redis.get(attempts_key)
        
        return {
            "email": email,
            "is_locked": lockout_ttl > 0,
            "retry_after_seconds": max(0, lockout_ttl),
            "failed_attempts": int(current_attempts) if current_attempts else 0,
            "max_attempts": self.MAX_ATTEMPTS,
            "lockout_duration_seconds": self.LOCKOUT_SECONDS,
        }


# Singleton instance getter
_login_limiter: LoginLimiter | None = None


def get_login_limiter() -> LoginLimiter | None:
    """Get the login limiter instance.
    
    Returns:
        LoginLimiter instance or None if Redis not available
    """
    global _login_limiter
    
    if _login_limiter is None:
        from app.utils.redis_client import get_redis
        current_redis = get_redis()
        if current_redis:
            _login_limiter = LoginLimiter(current_redis)
    
    return _login_limiter


async def init_login_limiter(redis_client: Redis) -> LoginLimiter:
    """Initialize login limiter with Redis client.
    
    Args:
        redis_client: Redis client instance
        
    Returns:
        LoginLimiter instance
    """
    global _login_limiter
    _login_limiter = LoginLimiter(redis_client)
    return _login_limiter
