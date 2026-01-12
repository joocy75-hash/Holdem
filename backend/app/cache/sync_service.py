"""Cache-to-DB synchronization service (Write-Behind pattern).

Phase 4.4.1: CacheSyncService implementation.

Synchronization Strategy:
1. Periodic sync: Every SYNC_INTERVAL seconds, sync dirty tables to DB
2. Event-based sync:
   - On hand completion: Immediately save hand history
   - On player leave: Sync player balance
3. Shutdown sync: Flush all dirty data before shutdown

This reduces DB write load by batching updates while ensuring
data durability through periodic persistence.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import TYPE_CHECKING

from redis.asyncio import Redis

from app.cache.keys import CacheKeys
from app.cache.table_cache import TableCacheService
from app.cache.hand_cache import HandCacheService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = logging.getLogger(__name__)


class CacheSyncService:
    """Write-Behind pattern cache synchronization service.

    Runs a background task that periodically syncs dirty cache entries
    to the database, reducing DB write pressure during gameplay.
    """

    SYNC_INTERVAL: int = 5  # Seconds between sync cycles
    BATCH_SIZE: int = 10    # Max tables to sync per cycle

    def __init__(
        self,
        redis: Redis,
        session_factory: "async_sessionmaker[AsyncSession]",
    ) -> None:
        """Initialize sync service.

        Args:
            redis: Redis client
            session_factory: SQLAlchemy async session factory
        """
        self._redis = redis
        self._session_factory = session_factory
        self._table_cache = TableCacheService(redis)
        self._hand_cache = HandCacheService(redis)
        self._running = False
        self._sync_task: asyncio.Task[None] | None = None
        self._sync_count = 0
        self._error_count = 0

    # =========================================================================
    # Lifecycle Management
    # =========================================================================

    async def start(self) -> None:
        """Start the background sync loop."""
        if self._running:
            logger.warning("CacheSyncService already running")
            return

        self._running = True
        self._sync_task = asyncio.create_task(
            self._sync_loop(),
            name="cache-sync-loop"
        )
        logger.info("CacheSyncService started (interval=%ds)", self.SYNC_INTERVAL)

    async def stop(self) -> None:
        """Stop sync service with final flush.

        Performs one last sync of all dirty data before stopping.
        """
        self._running = False

        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
            self._sync_task = None

        # Final sync - flush everything
        logger.info("Performing final cache sync before shutdown...")
        await self._sync_all_dirty_tables()
        logger.info(
            "CacheSyncService stopped (total syncs=%d, errors=%d)",
            self._sync_count,
            self._error_count
        )

    @property
    def is_running(self) -> bool:
        """Check if sync service is running."""
        return self._running

    @property
    def stats(self) -> dict[str, int]:
        """Get sync statistics."""
        return {
            "total_syncs": self._sync_count,
            "errors": self._error_count,
        }

    # =========================================================================
    # Background Sync Loop
    # =========================================================================

    async def _sync_loop(self) -> None:
        """Main sync loop running in background."""
        while self._running:
            try:
                await asyncio.sleep(self.SYNC_INTERVAL)
                await self._sync_dirty_tables()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._error_count += 1
                logger.error(f"Sync loop error: {e}", exc_info=True)

    async def _sync_dirty_tables(self) -> None:
        """Sync tables marked as dirty (batch)."""
        dirty_tables = await self._table_cache.get_dirty_tables()

        if not dirty_tables:
            return

        # Process in batches to avoid overloading DB
        batch = list(dirty_tables)[: self.BATCH_SIZE]
        logger.debug(f"Syncing {len(batch)} dirty tables")

        for table_id in batch:
            try:
                await self._sync_table_to_db(table_id)
                self._sync_count += 1
            except Exception as e:
                self._error_count += 1
                logger.error(f"Failed to sync table {table_id}: {e}")

    async def _sync_all_dirty_tables(self) -> None:
        """Sync ALL dirty tables (used during shutdown)."""
        dirty_tables = await self._table_cache.get_dirty_tables()

        for table_id in dirty_tables:
            try:
                await self._sync_table_to_db(table_id)
                self._sync_count += 1
            except Exception as e:
                self._error_count += 1
                logger.error(f"Final sync failed for table {table_id}: {e}")

    # =========================================================================
    # Table Synchronization
    # =========================================================================

    async def _sync_table_to_db(self, table_id: str) -> None:
        """Sync single table state to database.

        Args:
            table_id: Table ID to sync
        """
        state = await self._table_cache.get_table_state(table_id)

        if not state:
            # Not in cache, remove from dirty set
            await self._redis.srem(CacheKeys.DIRTY_TABLES, table_id)
            return

        if not state.get("isDirty"):
            # Not actually dirty
            await self._redis.srem(CacheKeys.DIRTY_TABLES, table_id)
            return

        async with self._session_factory() as session:
            from app.models.table import Table

            table = await session.get(Table, table_id)
            if not table:
                logger.warning(f"Table {table_id} not found in DB, invalidating cache")
                await self._table_cache.invalidate(table_id)
                return

            # Update DB from cache
            table.seats = self._convert_seats_to_db_format(state.get("seats", []))
            table.dealer_position = state.get("dealerPosition", 0)
            table.state_version = state.get("stateVersion", 0)
            table.updated_at = datetime.utcnow()

            await session.commit()

        # Mark as clean after successful DB write
        await self._table_cache.mark_clean(table_id)
        logger.debug(f"Synced table {table_id} to DB")

    def _convert_seats_to_db_format(
        self, seats: list[dict]
    ) -> dict[str, dict]:
        """Convert cache seats format to DB JSONB format.

        Cache format uses camelCase, DB uses snake_case.

        Args:
            seats: List of seat dicts from cache

        Returns:
            Dict with position keys and seat data values
        """
        db_seats: dict[str, dict] = {}

        for seat in seats:
            position = seat.get("position")
            player = seat.get("player")

            if player:
                db_seats[str(position)] = {
                    "user_id": player.get("userId", ""),
                    "nickname": player.get("nickname", ""),
                    "avatar_url": player.get("avatarUrl"),
                    "stack": seat.get("stack", 0),
                    "status": seat.get("status", "active"),
                    "bet_amount": seat.get("betAmount", 0),
                }

        return db_seats

    # =========================================================================
    # Event-Based Sync (Immediate)
    # =========================================================================

    async def sync_on_hand_complete(
        self,
        hand_id: str,
        table_id: str,
        winners: list[dict] | None = None,
    ) -> dict | None:
        """Sync immediately when hand completes.

        This is critical for data integrity - hand history must be
        persisted before cache expires.

        Args:
            hand_id: Completed hand ID
            table_id: Parent table ID
            winners: Optional winner info

        Returns:
            Complete hand data that was saved, or None if not found
        """
        # Get final hand state and actions from cache
        hand_data = await self._hand_cache.complete_hand(hand_id)

        if not hand_data:
            logger.warning(f"Hand {hand_id} not found in cache for completion")
            return None

        # Add winner info if provided
        if winners:
            hand_data["winners"] = winners

        async with self._session_factory() as session:
            from app.models.hand import Hand, HandEvent, EventType

            # Create Hand record
            hand = Hand(
                id=hand_id,
                table_id=table_id,
                hand_number=hand_data.get("handNumber", 0),
                started_at=datetime.fromisoformat(hand_data["startedAt"]),
                ended_at=datetime.utcnow(),
                initial_state={
                    "dealerPosition": hand_data.get("dealerPosition"),
                    "blinds": {
                        "small": hand_data.get("smallBlind"),
                        "big": hand_data.get("bigBlind"),
                    },
                },
                result={
                    "winners": winners or [],
                    "finalPot": hand_data["pot"]["mainPot"],
                    "communityCards": hand_data.get("communityCards", []),
                },
            )
            session.add(hand)

            # Create HandEvent records for action history
            for seq, action in enumerate(hand_data.get("actions", [])):
                event_type = self._map_action_to_event_type(action.get("actionType", ""))
                if event_type:
                    event = HandEvent(
                        hand_id=hand_id,
                        seq_no=seq,
                        event_type=event_type,
                        payload={
                            "position": action.get("position"),
                            "amount": action.get("amount", 0),
                        },
                    )
                    session.add(event)

            await session.commit()

        # Also sync the table state
        await self._sync_table_to_db(table_id)

        logger.info(
            f"Synced completed hand {hand_id} to DB "
            f"({len(hand_data.get('actions', []))} actions)"
        )
        return hand_data

    def _map_action_to_event_type(self, action_type: str) -> str | None:
        """Map action type string to EventType value.

        Args:
            action_type: Action type from cache

        Returns:
            EventType value or None if unknown
        """
        mapping = {
            "fold": "FOLD",
            "check": "CHECK",
            "call": "CALL",
            "bet": "BET",
            "raise": "RAISE",
            "all_in": "ALL_IN",
        }
        return mapping.get(action_type.lower())

    async def sync_player_balance(
        self,
        user_id: str,
        table_id: str,
        final_stack: int,
    ) -> None:
        """Sync player balance when leaving table.

        This ensures player's chips are credited back to their account.

        Args:
            user_id: Player's user ID
            table_id: Table they're leaving
            final_stack: Their final chip stack
        """
        async with self._session_factory() as session:
            from app.models.user import User

            user = await session.get(User, user_id)
            if user:
                # Add stack back to balance
                user.balance = (user.balance or 0) + final_stack
                await session.commit()
                logger.info(
                    f"Player {user_id} balance updated: +{final_stack} chips"
                )

    # =========================================================================
    # Manual Sync Trigger
    # =========================================================================

    async def force_sync(self, table_id: str) -> bool:
        """Force immediate sync for a specific table.

        Args:
            table_id: Table ID to sync

        Returns:
            True if sync successful, False otherwise
        """
        try:
            await self._sync_table_to_db(table_id)
            self._sync_count += 1
            return True
        except Exception as e:
            self._error_count += 1
            logger.error(f"Force sync failed for table {table_id}: {e}")
            return False
