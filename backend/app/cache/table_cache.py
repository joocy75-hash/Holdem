"""Table state caching service using Redis Hash.

Phase 4.3.1: TableCacheService implementation.

Design Goals:
- DB query reduction: 70-90% for table state reads
- Cache-Aside pattern: Check cache first, fallback to DB
- Write-Behind pattern: Update cache immediately, sync to DB periodically

Redis Hash Structure (table:{table_id}:state):
- table_id: str
- config: JSON serialized TableConfig
- seats: JSON serialized list of SeatState
- hand_id: current hand ID (empty string if none)
- dealer_position: int as string
- state_version: int as string
- updated_at: ISO timestamp
- is_dirty: "1" or "0" (needs DB sync)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from redis.asyncio import Redis

from app.cache.keys import CacheKeys
from app.engine.snapshot import SnapshotSerializer

if TYPE_CHECKING:
    from app.engine.state import TableState

logger = logging.getLogger(__name__)


class TableCacheService:
    """Table state Redis caching service.

    Provides Cache-Aside pattern for table state with efficient
    partial updates using Redis Hash operations.
    """

    def __init__(self, redis: Redis) -> None:
        """Initialize with Redis connection.

        Args:
            redis: Async Redis client instance
        """
        self._redis = redis
        self._serializer = SnapshotSerializer()

    # =========================================================================
    # Read Operations (Cache-Aside Pattern)
    # =========================================================================

    async def get_table_state(self, table_id: str) -> dict[str, Any] | None:
        """Get table state from cache.

        Args:
            table_id: Table ID to look up

        Returns:
            Cached table state dict, or None if not in cache (cache miss)
        """
        key = CacheKeys.table_state(table_id)
        data = await self._redis.hgetall(key)

        if not data:
            logger.debug(f"Cache miss for table {table_id}")
            return None

        logger.debug(f"Cache hit for table {table_id}")
        return self._deserialize_table_hash(data)

    async def get_table_field(self, table_id: str, field: str) -> str | None:
        """Get specific field from table state cache.

        More efficient when only one field is needed.

        Args:
            table_id: Table ID
            field: Field name (e.g., "seats", "dealer_position")

        Returns:
            Field value as string, or None if not found
        """
        key = CacheKeys.table_state(table_id)
        value = await self._redis.hget(key, field)
        return value.decode() if isinstance(value, bytes) else value

    async def get_multiple_tables(
        self, table_ids: list[str]
    ) -> dict[str, dict[str, Any] | None]:
        """Get multiple table states in one operation using pipeline.

        Args:
            table_ids: List of table IDs to look up

        Returns:
            Dict mapping table_id to state dict (or None if not cached)
        """
        if not table_ids:
            return {}

        pipe = self._redis.pipeline()
        for table_id in table_ids:
            key = CacheKeys.table_state(table_id)
            pipe.hgetall(key)

        results = await pipe.execute()

        return {
            table_id: self._deserialize_table_hash(data) if data else None
            for table_id, data in zip(table_ids, results)
        }

    async def exists(self, table_id: str) -> bool:
        """Check if table is in cache.

        Args:
            table_id: Table ID to check

        Returns:
            True if cached, False otherwise
        """
        key = CacheKeys.table_state(table_id)
        return await self._redis.exists(key) > 0

    # =========================================================================
    # Write Operations
    # =========================================================================

    async def set_table_state(
        self,
        table_id: str,
        state: "TableState",
        mark_dirty: bool = True,
    ) -> None:
        """Store table state in cache.

        Args:
            table_id: Table ID
            state: Full TableState object
            mark_dirty: Whether to mark for DB sync (default True)
        """
        key = CacheKeys.table_state(table_id)
        hash_data = self._serialize_table_to_hash(state, mark_dirty)

        pipe = self._redis.pipeline()
        pipe.hset(key, mapping=hash_data)
        pipe.expire(key, CacheKeys.TABLE_STATE_TTL.seconds)

        if mark_dirty:
            # Add to dirty set for sync service
            pipe.sadd(CacheKeys.DIRTY_TABLES, table_id)

        await pipe.execute()
        logger.debug(f"Cached table state for {table_id} (dirty={mark_dirty})")

    async def set_table_state_from_dict(
        self,
        table_id: str,
        state_dict: dict[str, Any],
        mark_dirty: bool = True,
    ) -> None:
        """Store table state from pre-serialized dict.

        Useful when state is already serialized (e.g., from DB).

        Args:
            table_id: Table ID
            state_dict: Serialized state dict (camelCase keys)
            mark_dirty: Whether to mark for DB sync
        """
        key = CacheKeys.table_state(table_id)

        hash_data = {
            "table_id": table_id,
            "config": json.dumps(state_dict.get("config", {})),
            "seats": json.dumps(state_dict.get("seats", [])),
            "hand_id": state_dict.get("hand", {}).get("handId", "") if state_dict.get("hand") else "",
            "dealer_position": str(state_dict.get("dealerPosition", 0)),
            "state_version": str(state_dict.get("stateVersion", 0)),
            "updated_at": state_dict.get("updatedAt", datetime.utcnow().isoformat()),
            "is_dirty": "1" if mark_dirty else "0",
        }

        pipe = self._redis.pipeline()
        pipe.hset(key, mapping=hash_data)
        pipe.expire(key, CacheKeys.TABLE_STATE_TTL.seconds)

        if mark_dirty:
            pipe.sadd(CacheKeys.DIRTY_TABLES, table_id)

        await pipe.execute()

    async def update_seat(
        self,
        table_id: str,
        position: int,
        stack: int | None = None,
        status: str | None = None,
        player: dict[str, Any] | None = None,
    ) -> bool:
        """Update specific seat without rewriting entire state.

        More efficient for frequent stack/status updates.

        Args:
            table_id: Table ID
            position: Seat position (0-based)
            stack: New stack value (optional)
            status: New status (optional)
            player: New player info dict (optional)

        Returns:
            True if updated, False if table not in cache
        """
        key = CacheKeys.table_state(table_id)

        # Get current seats
        seats_json = await self._redis.hget(key, "seats")
        if not seats_json:
            logger.warning(f"Cannot update seat: table {table_id} not in cache")
            return False

        seats_str = seats_json.decode() if isinstance(seats_json, bytes) else seats_json
        seats = json.loads(seats_str)

        # Find and update seat
        updated = False
        for seat in seats:
            if seat.get("position") == position:
                if stack is not None:
                    seat["stack"] = stack
                if status is not None:
                    seat["status"] = status
                if player is not None:
                    seat["player"] = player
                updated = True
                break

        if not updated:
            logger.warning(f"Seat {position} not found in table {table_id}")
            return False

        # Update cache with new seats
        pipe = self._redis.pipeline()
        pipe.hset(key, "seats", json.dumps(seats))
        pipe.hset(key, "updated_at", datetime.utcnow().isoformat())
        pipe.hset(key, "is_dirty", "1")
        pipe.hincrby(key, "state_version", 1)
        pipe.sadd(CacheKeys.DIRTY_TABLES, table_id)
        await pipe.execute()

        return True

    async def update_player_stack(
        self,
        table_id: str,
        position: int,
        new_stack: int,
    ) -> bool:
        """Quick stack update for a player.

        Args:
            table_id: Table ID
            position: Seat position
            new_stack: New stack value

        Returns:
            True if updated, False otherwise
        """
        return await self.update_seat(table_id, position, stack=new_stack)

    async def update_dealer_position(
        self,
        table_id: str,
        new_position: int,
    ) -> bool:
        """Update dealer button position.

        Args:
            table_id: Table ID
            new_position: New dealer position

        Returns:
            True if updated, False if table not in cache
        """
        key = CacheKeys.table_state(table_id)

        if not await self._redis.exists(key):
            return False

        pipe = self._redis.pipeline()
        pipe.hset(key, "dealer_position", str(new_position))
        pipe.hset(key, "updated_at", datetime.utcnow().isoformat())
        pipe.hset(key, "is_dirty", "1")
        pipe.hincrby(key, "state_version", 1)
        pipe.sadd(CacheKeys.DIRTY_TABLES, table_id)
        await pipe.execute()

        return True

    async def set_current_hand(
        self,
        table_id: str,
        hand_id: str | None,
    ) -> bool:
        """Update current hand ID for table.

        Args:
            table_id: Table ID
            hand_id: New hand ID, or None to clear

        Returns:
            True if updated, False if table not in cache
        """
        key = CacheKeys.table_state(table_id)

        if not await self._redis.exists(key):
            return False

        pipe = self._redis.pipeline()
        pipe.hset(key, "hand_id", hand_id or "")
        pipe.hset(key, "updated_at", datetime.utcnow().isoformat())
        pipe.hset(key, "is_dirty", "1")
        pipe.hincrby(key, "state_version", 1)
        pipe.sadd(CacheKeys.DIRTY_TABLES, table_id)
        await pipe.execute()

        return True

    # =========================================================================
    # Cache Management
    # =========================================================================

    async def invalidate(self, table_id: str) -> None:
        """Remove table from cache.

        Args:
            table_id: Table ID to invalidate
        """
        key = CacheKeys.table_state(table_id)
        await self._redis.delete(key)
        logger.debug(f"Invalidated cache for table {table_id}")

    async def mark_clean(self, table_id: str) -> None:
        """Mark table as synced (remove dirty flag).

        Called by sync service after DB write.

        Args:
            table_id: Table ID that was synced
        """
        key = CacheKeys.table_state(table_id)
        pipe = self._redis.pipeline()
        pipe.hset(key, "is_dirty", "0")
        pipe.srem(CacheKeys.DIRTY_TABLES, table_id)
        await pipe.execute()

    async def get_dirty_tables(self) -> set[str]:
        """Get set of tables needing DB sync.

        Returns:
            Set of table IDs marked as dirty
        """
        result = await self._redis.smembers(CacheKeys.DIRTY_TABLES)
        return {
            item.decode() if isinstance(item, bytes) else item
            for item in result
        }

    async def refresh_ttl(self, table_id: str) -> bool:
        """Refresh cache TTL for active table.

        Args:
            table_id: Table ID

        Returns:
            True if TTL was refreshed, False if key doesn't exist
        """
        key = CacheKeys.table_state(table_id)
        return await self._redis.expire(key, CacheKeys.TABLE_STATE_TTL.seconds)

    # =========================================================================
    # Serialization Helpers
    # =========================================================================

    def _serialize_table_to_hash(
        self,
        state: "TableState",
        is_dirty: bool,
    ) -> dict[str, str]:
        """Convert TableState to Redis Hash mapping.

        Args:
            state: TableState object
            is_dirty: Whether table needs DB sync

        Returns:
            Dict with string keys and string values for Redis HSET
        """
        serialized = self._serializer.serialize(state)

        return {
            "table_id": state.table_id,
            "config": json.dumps(serialized.get("config", {})),
            "seats": json.dumps(serialized.get("seats", [])),
            "hand_id": state.hand.hand_id if state.hand else "",
            "dealer_position": str(state.dealer_position),
            "state_version": str(state.state_version),
            "updated_at": state.updated_at.isoformat(),
            "is_dirty": "1" if is_dirty else "0",
        }

    def _deserialize_table_hash(
        self, data: dict[bytes | str, bytes | str]
    ) -> dict[str, Any]:
        """Convert Redis Hash data to frontend-compatible dict.

        Args:
            data: Raw data from Redis HGETALL

        Returns:
            Dict with camelCase keys for frontend
        """
        # Decode bytes if needed
        decoded = {}
        for k, v in data.items():
            key = k.decode() if isinstance(k, bytes) else k
            val = v.decode() if isinstance(v, bytes) else v
            decoded[key] = val

        return {
            "tableId": decoded.get("table_id", ""),
            "config": json.loads(decoded.get("config", "{}")),
            "seats": json.loads(decoded.get("seats", "[]")),
            "handId": decoded.get("hand_id") or None,
            "dealerPosition": int(decoded.get("dealer_position", "0")),
            "stateVersion": int(decoded.get("state_version", "0")),
            "updatedAt": decoded.get("updated_at", ""),
            "isDirty": decoded.get("is_dirty") == "1",
        }
