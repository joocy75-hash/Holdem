"""Cache module for Redis-based game state caching.

Phase 4: Redis High Availability + Game State Caching

This module provides:
- TableCacheService: Table state caching with Cache-Aside pattern
- HandCacheService: In-progress hand caching
- CacheSyncService: Write-Behind pattern DB synchronization
- CacheWarmupService: Server startup cache population
- CacheManager: Unified interface for all cache operations

Expected Performance Improvement:
- DB query reduction: 70-90%
- Table state read latency: 15-30ms (DB) -> 1-3ms (Redis)
- Write operations batched every 5 seconds
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from redis.asyncio import Redis

from app.cache.keys import CacheKeys, CacheTTL, CachePatterns, CacheInvalidation
from app.cache.table_cache import TableCacheService
from app.cache.hand_cache import HandCacheService
from app.cache.sync_service import CacheSyncService
from app.cache.warmup import CacheWarmupService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

__all__ = [
    # Key definitions
    "CacheKeys",
    "CacheTTL",
    "CachePatterns",
    "CacheInvalidation",
    # Services
    "TableCacheService",
    "HandCacheService",
    "CacheSyncService",
    "CacheWarmupService",
    # Manager
    "CacheManager",
    # Functions
    "init_cache_manager",
    "get_cache_manager",
    "shutdown_cache_manager",
]


class CacheManager:
    """Unified cache manager providing access to all cache services.

    This is the main entry point for cache operations. It manages
    the lifecycle of all cache services and provides convenient
    access to each service.

    Usage:
        cache = await get_cache_manager()

        # Access table cache
        state = await cache.table_cache.get_table_state(table_id)

        # Access hand cache
        await cache.hand_cache.record_action(hand_id, ...)

        # Manual sync if needed
        await cache.sync_service.force_sync(table_id)
    """

    def __init__(
        self,
        redis: Redis,
        session_factory: "async_sessionmaker[AsyncSession]",
    ) -> None:
        """Initialize cache manager with all services.

        Args:
            redis: Redis client instance
            session_factory: SQLAlchemy async session factory for DB sync
        """
        self._redis = redis
        self._session_factory = session_factory

        # Initialize services
        self.table_cache = TableCacheService(redis)
        self.hand_cache = HandCacheService(redis)
        self.sync_service = CacheSyncService(redis, session_factory)
        self.warmup_service = CacheWarmupService(redis)

        self._started = False

    @property
    def redis(self) -> Redis:
        """Get underlying Redis client."""
        return self._redis

    @property
    def is_running(self) -> bool:
        """Check if cache manager is running."""
        return self._started

    async def start(self) -> None:
        """Start cache services (sync loop)."""
        if self._started:
            return

        await self.sync_service.start()
        self._started = True

    async def stop(self) -> None:
        """Stop cache services gracefully."""
        if not self._started:
            return

        await self.sync_service.stop()
        self._started = False

    async def warmup(self, session: "AsyncSession") -> dict[str, int]:
        """Perform cache warmup.

        Should be called during server startup after DB is ready.

        Args:
            session: Database session

        Returns:
            Warmup statistics
        """
        return await self.warmup_service.full_warmup(session)

    def get_stats(self) -> dict[str, any]:
        """Get cache operation statistics.

        Returns:
            Dict with sync stats
        """
        return {
            "sync": self.sync_service.stats,
            "running": self._started,
        }


# Global cache manager instance
_cache_manager: CacheManager | None = None


async def init_cache_manager(
    redis: Redis,
    session_factory: "async_sessionmaker[AsyncSession]",
) -> CacheManager:
    """Initialize global cache manager.

    This should be called once during application startup,
    after Redis and database are initialized.

    Args:
        redis: Redis client
        session_factory: SQLAlchemy session factory

    Returns:
        Initialized CacheManager instance
    """
    global _cache_manager

    if _cache_manager is not None:
        raise RuntimeError("CacheManager already initialized")

    _cache_manager = CacheManager(redis, session_factory)
    await _cache_manager.start()

    return _cache_manager


def get_cache_manager() -> CacheManager:
    """Get global cache manager instance.

    Returns:
        CacheManager instance

    Raises:
        RuntimeError: If cache manager not initialized
    """
    if _cache_manager is None:
        raise RuntimeError(
            "CacheManager not initialized. "
            "Call init_cache_manager() during startup."
        )
    return _cache_manager


async def shutdown_cache_manager() -> None:
    """Shutdown global cache manager.

    Performs final sync and cleans up resources.
    Should be called during application shutdown.
    """
    global _cache_manager

    if _cache_manager is not None:
        await _cache_manager.stop()
        _cache_manager = None


# Dependency injection helper for FastAPI
async def get_cache_manager_dep() -> CacheManager:
    """FastAPI dependency for cache manager.

    Usage:
        @router.get("/tables/{table_id}")
        async def get_table(
            table_id: str,
            cache: CacheManager = Depends(get_cache_manager_dep)
        ):
            state = await cache.table_cache.get_table_state(table_id)
            ...
    """
    return get_cache_manager()
