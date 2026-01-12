"""Redis cache key definitions and TTL policies.

Phase 4.2: Cache key design for game state caching.

Key Naming Convention:
- Hierarchical structure: {domain}:{entity}:{id}:{field}
- Examples: table:123:state, hand:456:actions
- All keys use lowercase with colons as separators

TTL Strategy:
- Active game data: 1 hour (refreshed on access)
- Hand data: 30 minutes (hands typically finish in 5-10 min)
- Room list: 10 seconds (frequently changing)
- Static config: 24 hours (rarely changes)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class CacheTTL:
    """TTL configuration for cache entries."""

    seconds: int
    description: str


class CacheKeys:
    """Redis cache key patterns and TTLs.

    All key-generating methods are classmethods for easy access.
    """

    # =========================================================================
    # Table State Cache (Redis Hash)
    # =========================================================================

    # Table full state: hash with config, seats, hand_id, etc.
    # TTL: 1 hour (active tables refresh continuously)
    TABLE_STATE_TTL: ClassVar[CacheTTL] = CacheTTL(3600, "Table state hash TTL - 1 hour")

    # Table configuration only (rarely changes)
    TABLE_CONFIG_TTL: ClassVar[CacheTTL] = CacheTTL(86400, "Table config TTL - 24 hours")

    @classmethod
    def table_state(cls, table_id: str) -> str:
        """Get cache key for table state hash."""
        return f"table:{table_id}:state"

    @classmethod
    def table_config(cls, table_id: str) -> str:
        """Get cache key for table configuration."""
        return f"table:{table_id}:config"

    # =========================================================================
    # Hand State Cache (Redis Hash + List)
    # =========================================================================

    # Hand state: hash with phase, pot, community cards, etc.
    # TTL: 30 minutes (hands typically complete in 5-10 min)
    HAND_STATE_TTL: ClassVar[CacheTTL] = CacheTTL(1800, "Active hand state TTL - 30 min")

    # Hand action history: list of actions
    HAND_ACTIONS_TTL: ClassVar[CacheTTL] = CacheTTL(1800, "Hand actions TTL - 30 min")

    @classmethod
    def hand_state(cls, hand_id: str) -> str:
        """Get cache key for hand state hash."""
        return f"hand:{hand_id}:state"

    @classmethod
    def hand_actions(cls, hand_id: str) -> str:
        """Get cache key for hand action history list."""
        return f"hand:{hand_id}:actions"

    # =========================================================================
    # Room/Lobby Cache
    # =========================================================================

    # Room list cache: short TTL since it changes frequently
    ROOM_LIST_TTL: ClassVar[CacheTTL] = CacheTTL(10, "Room list cache TTL - 10 seconds")

    # Individual room detail
    ROOM_DETAIL_TTL: ClassVar[CacheTTL] = CacheTTL(60, "Room detail TTL - 1 minute")

    @classmethod
    def room_list(cls, page: int = 1, page_size: int = 20) -> str:
        """Get cache key for room list."""
        return f"rooms:list:{page}:{page_size}"

    @classmethod
    def room_detail(cls, room_id: str) -> str:
        """Get cache key for room detail."""
        return f"room:{room_id}:detail"

    # =========================================================================
    # Player Mapping Cache
    # =========================================================================

    # Player's current table mapping
    PLAYER_TABLE_TTL: ClassVar[CacheTTL] = CacheTTL(3600, "Player table mapping TTL - 1 hour")

    @classmethod
    def player_table(cls, user_id: str) -> str:
        """Get cache key for player's current table."""
        return f"player:{user_id}:table"

    @classmethod
    def player_position(cls, table_id: str, user_id: str) -> str:
        """Get cache key for player's position at table."""
        return f"table:{table_id}:player:{user_id}:position"

    # =========================================================================
    # Sync Tracking (Write-Behind Pattern)
    # =========================================================================

    # Dirty tables set: tables needing DB sync
    DIRTY_TABLES: ClassVar[str] = "sync:dirty_tables"

    # Last sync timestamp per table
    @classmethod
    def sync_last_time(cls, table_id: str) -> str:
        """Get cache key for last sync timestamp."""
        return f"sync:last:{table_id}"

    # =========================================================================
    # Lock Keys (for distributed locking)
    # =========================================================================

    LOCK_TTL: ClassVar[CacheTTL] = CacheTTL(30, "Distributed lock TTL - 30 seconds")

    @classmethod
    def table_lock(cls, table_id: str) -> str:
        """Get lock key for table operations."""
        return f"lock:table:{table_id}"

    @classmethod
    def hand_lock(cls, hand_id: str) -> str:
        """Get lock key for hand operations."""
        return f"lock:hand:{hand_id}"

    @classmethod
    def user_balance_lock(cls, user_id: str) -> str:
        """Get lock key for user balance operations."""
        return f"lock:balance:{user_id}"


class CachePatterns:
    """Cache key patterns for bulk operations (SCAN, DEL)."""

    # All keys for a specific table
    TABLE_ALL: ClassVar[str] = "table:{table_id}:*"

    # All keys for a specific hand
    HAND_ALL: ClassVar[str] = "hand:{hand_id}:*"

    # All room-related keys
    ROOMS_ALL: ClassVar[str] = "rooms:*"

    @classmethod
    def table_all(cls, table_id: str) -> str:
        """Get pattern for all table keys."""
        return cls.TABLE_ALL.format(table_id=table_id)

    @classmethod
    def hand_all(cls, hand_id: str) -> str:
        """Get pattern for all hand keys."""
        return cls.HAND_ALL.format(hand_id=hand_id)


class CacheInvalidation:
    """Cache invalidation patterns for various events."""

    @staticmethod
    def on_table_update(table_id: str) -> list[str]:
        """Keys to invalidate when table state changes."""
        return [
            CacheKeys.table_state(table_id),
            # Room list might change (player count, status)
            # We use pattern, actual invalidation should use SCAN
        ]

    @staticmethod
    def on_hand_complete(hand_id: str, table_id: str) -> list[str]:
        """Keys to invalidate when hand completes."""
        return [
            CacheKeys.hand_state(hand_id),
            CacheKeys.hand_actions(hand_id),
            CacheKeys.table_state(table_id),
        ]

    @staticmethod
    def on_player_leave(table_id: str, user_id: str) -> list[str]:
        """Keys to invalidate when player leaves table."""
        return [
            CacheKeys.player_table(user_id),
            CacheKeys.player_position(table_id, user_id),
            CacheKeys.table_state(table_id),
        ]
