"""Cache warmup service.

Phase 4.4.2: CacheWarmupService implementation.

On server startup, loads active tables into Redis cache to ensure
fast response times from the first request. This prevents the
"cold start" problem where initial requests hit the database.

Warmup Strategy:
1. Query DB for tables in active rooms (WAITING, PLAYING status)
2. Convert to cache format and store in Redis
3. Mark as clean (since data matches DB)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.cache.table_cache import TableCacheService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class CacheWarmupService:
    """Cache warmup service for server startup."""

    def __init__(self, redis: Redis) -> None:
        """Initialize warmup service.

        Args:
            redis: Redis client
        """
        self._redis = redis
        self._table_cache = TableCacheService(redis)

    async def warmup_active_tables(
        self, session: "AsyncSession"
    ) -> int:
        """Load all active tables into cache.

        Args:
            session: Database session

        Returns:
            Number of tables warmed up
        """
        from app.models.table import Table
        from app.models.room import Room, RoomStatus

        # Query tables in active rooms
        query = (
            select(Table)
            .join(Room)
            .where(
                Room.status.in_([
                    RoomStatus.WAITING.value,
                    RoomStatus.PLAYING.value,
                ])
            )
            .options(selectinload(Table.room))
        )

        result = await session.execute(query)
        tables = result.scalars().all()

        warmed = 0
        for table in tables:
            try:
                await self._warmup_table(table)
                warmed += 1
            except Exception as e:
                logger.error(f"Failed to warmup table {table.id}: {e}")

        logger.info(f"Cache warmup complete: {warmed}/{len(tables)} tables loaded")
        return warmed

    async def _warmup_table(self, table) -> None:
        """Load single table into cache.

        Args:
            table: SQLAlchemy Table model instance
        """
        room = table.room
        config = room.config if room else {}

        # Build cache-format state dict
        max_seats = config.get("max_seats", 6)
        seats = self._build_seats_from_db(table.seats, max_seats)

        state_dict = {
            "tableId": table.id,
            "config": {
                "maxSeats": max_seats,
                "smallBlind": config.get("small_blind", 10),
                "bigBlind": config.get("big_blind", 20),
                "minBuyIn": config.get("buy_in_min", 400),
                "maxBuyIn": config.get("buy_in_max", 2000),
                "turnTimeoutSeconds": config.get("turn_timeout", 30),
                "ante": config.get("ante", 0),
            },
            "seats": seats,
            "hand": None,  # Hand state loaded separately if needed
            "dealerPosition": table.dealer_position or 0,
            "stateVersion": table.state_version or 0,
            "updatedAt": (
                table.updated_at.isoformat()
                if table.updated_at
                else datetime.utcnow().isoformat()
            ),
        }

        # Store in cache (mark_dirty=False since data matches DB)
        await self._table_cache.set_table_state_from_dict(
            table.id,
            state_dict,
            mark_dirty=False,
        )

        logger.debug(f"Warmed up table {table.id}")

    def _build_seats_from_db(
        self,
        db_seats: dict | None,
        max_seats: int,
    ) -> list[dict]:
        """Convert DB seats format to cache format.

        Args:
            db_seats: JSONB seats from database
            max_seats: Maximum seats at table

        Returns:
            List of seat dicts in cache format
        """
        seats = []

        for i in range(max_seats):
            seat_data = db_seats.get(str(i)) if db_seats else None

            if seat_data:
                player = {
                    "userId": seat_data.get("user_id", ""),
                    "nickname": seat_data.get("nickname", f"Player{i + 1}"),
                    "avatarUrl": seat_data.get("avatar_url"),
                }
                seats.append({
                    "position": i,
                    "player": player,
                    "stack": seat_data.get("stack", 0),
                    "status": seat_data.get("status", "active"),
                    "betAmount": seat_data.get("bet_amount", 0),
                })
            else:
                seats.append({
                    "position": i,
                    "player": None,
                    "stack": 0,
                    "status": "empty",
                    "betAmount": 0,
                })

        return seats

    async def warmup_room_list(self, session: "AsyncSession") -> int:
        """Pre-cache room list for lobby.

        Args:
            session: Database session

        Returns:
            Number of rooms cached
        """
        from app.cache.keys import CacheKeys
        from app.models.room import Room, RoomStatus
        import json

        # Get active rooms
        query = (
            select(Room)
            .where(
                Room.status.in_([
                    RoomStatus.WAITING.value,
                    RoomStatus.PLAYING.value,
                ])
            )
            .order_by(Room.created_at.desc())
            .limit(100)
        )

        result = await session.execute(query)
        rooms = result.scalars().all()

        # Build room list
        room_list = [
            {
                "id": room.id,
                "name": room.name,
                "status": room.status.value if hasattr(room.status, 'value') else room.status,
                "currentPlayers": room.current_players or 0,
                "maxPlayers": room.config.get("max_seats", 6) if room.config else 6,
                "smallBlind": room.config.get("small_blind", 10) if room.config else 10,
                "bigBlind": room.config.get("big_blind", 20) if room.config else 20,
            }
            for room in rooms
        ]

        # Cache first page
        cache_key = CacheKeys.room_list(page=1, page_size=20)
        await self._redis.setex(
            cache_key,
            CacheKeys.ROOM_LIST_TTL.seconds,
            json.dumps(room_list[:20]),
        )

        logger.info(f"Warmed up room list: {len(rooms)} rooms")
        return len(rooms)

    async def clear_stale_cache(self) -> int:
        """Clear potentially stale cache entries on startup.

        This is useful when server restarts after crash where
        cache might be out of sync with DB.

        Returns:
            Number of keys cleared
        """
        # Clear dirty tables set (will be rebuilt as changes occur)
        await self._redis.delete("sync:dirty_tables")

        # Clear any orphaned locks
        lock_pattern = "lock:*"
        cursor = 0
        cleared = 0

        while True:
            cursor, keys = await self._redis.scan(
                cursor=cursor,
                match=lock_pattern,
                count=100,
            )
            if keys:
                await self._redis.delete(*keys)
                cleared += len(keys)
            if cursor == 0:
                break

        if cleared > 0:
            logger.info(f"Cleared {cleared} stale lock keys")

        return cleared

    async def full_warmup(self, session: "AsyncSession") -> dict[str, int]:
        """Perform full cache warmup.

        Args:
            session: Database session

        Returns:
            Dict with warmup statistics
        """
        logger.info("Starting full cache warmup...")

        # Clear stale data first
        stale_cleared = await self.clear_stale_cache()

        # Warm up tables
        tables_warmed = await self.warmup_active_tables(session)

        # Warm up room list
        rooms_cached = await self.warmup_room_list(session)

        stats = {
            "stale_cleared": stale_cleared,
            "tables_warmed": tables_warmed,
            "rooms_cached": rooms_cached,
        }

        logger.info(f"Cache warmup complete: {stats}")
        return stats
