"""Hand state caching service.

Phase 4.3.2: HandCacheService implementation.

Design Goals:
- Keep active hand state in Redis only (no DB writes during hand)
- Batch save to DB on hand completion
- Efficient action history tracking with Redis List

Redis Hash Structure (hand:{hand_id}:state):
- hand_id, table_id, hand_number: identifiers
- phase: GamePhase value
- community_cards: JSON list of card strings
- pot_main, pot_side: pot amounts
- current_turn, min_raise: current action state
- dealer_position: button position
- started_at: ISO timestamp
- player_states: JSON dict by position

Redis List Structure (hand:{hand_id}:actions):
- Each action pushed as JSON string
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from redis.asyncio import Redis

from app.cache.keys import CacheKeys

logger = logging.getLogger(__name__)


class HandCacheService:
    """Hand state Redis caching service.

    Stores in-progress hand data exclusively in Redis for performance.
    On hand completion, data is retrieved and saved to PostgreSQL.
    """

    def __init__(self, redis: Redis) -> None:
        """Initialize with Redis connection.

        Args:
            redis: Async Redis client instance
        """
        self._redis = redis

    # =========================================================================
    # Hand Lifecycle
    # =========================================================================

    async def create_hand(
        self,
        hand_id: str,
        table_id: str,
        hand_number: int,
        player_positions: list[int],
        dealer_position: int,
        small_blind: int,
        big_blind: int,
    ) -> None:
        """Initialize cache for new hand.

        Args:
            hand_id: Unique hand identifier
            table_id: Parent table ID
            hand_number: Sequential hand number
            player_positions: List of active player positions
            dealer_position: Dealer button position
            small_blind: Small blind amount
            big_blind: Big blind amount
        """
        key = CacheKeys.hand_state(hand_id)

        # Initial player states
        player_states = {
            str(pos): {
                "holeCards": None,
                "betAmount": 0,
                "totalBet": 0,
                "status": "active",
                "lastAction": None,
            }
            for pos in player_positions
        }

        hash_data = {
            "hand_id": hand_id,
            "table_id": table_id,
            "hand_number": str(hand_number),
            "phase": "preflop",
            "community_cards": "[]",
            "pot_main": "0",
            "pot_side": "[]",
            "current_turn": "",
            "min_raise": str(big_blind),
            "dealer_position": str(dealer_position),
            "small_blind": str(small_blind),
            "big_blind": str(big_blind),
            "started_at": datetime.utcnow().isoformat(),
            "player_states": json.dumps(player_states),
        }

        pipe = self._redis.pipeline()
        pipe.hset(key, mapping=hash_data)
        pipe.expire(key, CacheKeys.HAND_STATE_TTL.seconds)
        await pipe.execute()

        logger.info(f"Created hand cache: {hand_id} with {len(player_positions)} players")

    async def complete_hand(self, hand_id: str) -> dict[str, Any] | None:
        """Mark hand as complete and return final state for DB storage.

        This retrieves all hand data and deletes the cache entries.

        Args:
            hand_id: Hand ID to complete

        Returns:
            Complete hand data including action history, or None if not found
        """
        state = await self.get_hand_state(hand_id)
        actions = await self.get_action_history(hand_id)

        if state is None:
            logger.warning(f"Hand {hand_id} not found in cache for completion")
            return None

        state["actions"] = actions
        state["completedAt"] = datetime.utcnow().isoformat()

        # Delete cache entries
        await self.delete_hand(hand_id)

        logger.info(f"Completed hand {hand_id} with {len(actions)} actions")
        return state

    async def delete_hand(self, hand_id: str) -> None:
        """Remove hand from cache.

        Args:
            hand_id: Hand ID to delete
        """
        state_key = CacheKeys.hand_state(hand_id)
        actions_key = CacheKeys.hand_actions(hand_id)
        await self._redis.delete(state_key, actions_key)
        logger.debug(f"Deleted hand cache: {hand_id}")

    # =========================================================================
    # State Queries
    # =========================================================================

    async def get_hand_state(self, hand_id: str) -> dict[str, Any] | None:
        """Get current hand state.

        Args:
            hand_id: Hand ID to look up

        Returns:
            Hand state dict, or None if not found
        """
        key = CacheKeys.hand_state(hand_id)
        data = await self._redis.hgetall(key)

        if not data:
            return None

        return self._deserialize_hand_hash(data)

    async def get_hand_field(self, hand_id: str, field: str) -> str | None:
        """Get specific field from hand state.

        Args:
            hand_id: Hand ID
            field: Field name

        Returns:
            Field value, or None if not found
        """
        key = CacheKeys.hand_state(hand_id)
        value = await self._redis.hget(key, field)
        return value.decode() if isinstance(value, bytes) else value

    async def exists(self, hand_id: str) -> bool:
        """Check if hand is in cache.

        Args:
            hand_id: Hand ID to check

        Returns:
            True if cached
        """
        key = CacheKeys.hand_state(hand_id)
        return await self._redis.exists(key) > 0

    # =========================================================================
    # Phase Updates
    # =========================================================================

    async def update_phase(
        self,
        hand_id: str,
        phase: str,
        community_cards: list[str] | None = None,
    ) -> bool:
        """Update game phase and optionally community cards.

        Args:
            hand_id: Hand ID
            phase: New phase (preflop, flop, turn, river, showdown, finished)
            community_cards: Updated community cards (optional)

        Returns:
            True if updated, False if hand not found
        """
        key = CacheKeys.hand_state(hand_id)

        if not await self._redis.exists(key):
            return False

        updates: dict[str, str] = {"phase": phase}
        if community_cards is not None:
            updates["community_cards"] = json.dumps(community_cards)

        await self._redis.hset(key, mapping=updates)
        logger.debug(f"Hand {hand_id} phase updated to {phase}")
        return True

    # =========================================================================
    # Pot Updates
    # =========================================================================

    async def update_pot(
        self,
        hand_id: str,
        main_pot: int,
        side_pots: list[dict[str, Any]] | None = None,
    ) -> bool:
        """Update pot amounts.

        Args:
            hand_id: Hand ID
            main_pot: Main pot amount
            side_pots: List of side pot dicts (optional)

        Returns:
            True if updated
        """
        key = CacheKeys.hand_state(hand_id)

        if not await self._redis.exists(key):
            return False

        updates = {"pot_main": str(main_pot)}
        if side_pots is not None:
            updates["pot_side"] = json.dumps(side_pots)

        await self._redis.hset(key, mapping=updates)
        return True

    async def add_to_pot(self, hand_id: str, amount: int) -> int:
        """Add amount to main pot atomically.

        Args:
            hand_id: Hand ID
            amount: Amount to add

        Returns:
            New pot total
        """
        key = CacheKeys.hand_state(hand_id)
        new_total = await self._redis.hincrby(key, "pot_main", amount)
        return new_total

    # =========================================================================
    # Turn Management
    # =========================================================================

    async def update_current_turn(
        self,
        hand_id: str,
        position: int | None,
        min_raise: int | None = None,
    ) -> bool:
        """Update whose turn it is.

        Args:
            hand_id: Hand ID
            position: Seat position of active player, or None if betting complete
            min_raise: Minimum raise amount (optional)

        Returns:
            True if updated
        """
        key = CacheKeys.hand_state(hand_id)

        if not await self._redis.exists(key):
            return False

        updates: dict[str, str] = {
            "current_turn": str(position) if position is not None else ""
        }
        if min_raise is not None:
            updates["min_raise"] = str(min_raise)

        await self._redis.hset(key, mapping=updates)
        return True

    # =========================================================================
    # Player State Updates
    # =========================================================================

    async def set_hole_cards(
        self,
        hand_id: str,
        position: int,
        cards: list[str],
    ) -> bool:
        """Set player's hole cards.

        Args:
            hand_id: Hand ID
            position: Player's seat position
            cards: List of card strings (e.g., ["Ah", "Kd"])

        Returns:
            True if updated
        """
        return await self._update_player_field(
            hand_id, position, "holeCards", cards
        )

    async def update_player_bet(
        self,
        hand_id: str,
        position: int,
        bet_amount: int,
        total_bet: int,
    ) -> bool:
        """Update player's bet amounts.

        Args:
            hand_id: Hand ID
            position: Player's seat position
            bet_amount: Current round bet
            total_bet: Total bet this hand

        Returns:
            True if updated
        """
        key = CacheKeys.hand_state(hand_id)

        current = await self._redis.hget(key, "player_states")
        if not current:
            return False

        current_str = current.decode() if isinstance(current, bytes) else current
        player_states = json.loads(current_str)

        pos_key = str(position)
        if pos_key not in player_states:
            return False

        player_states[pos_key]["betAmount"] = bet_amount
        player_states[pos_key]["totalBet"] = total_bet

        await self._redis.hset(key, "player_states", json.dumps(player_states))
        return True

    async def update_player_status(
        self,
        hand_id: str,
        position: int,
        status: str,
        last_action: dict[str, Any] | None = None,
    ) -> bool:
        """Update player's status (active, folded, all_in).

        Args:
            hand_id: Hand ID
            position: Player's seat position
            status: New status
            last_action: Last action dict (optional)

        Returns:
            True if updated
        """
        key = CacheKeys.hand_state(hand_id)

        current = await self._redis.hget(key, "player_states")
        if not current:
            return False

        current_str = current.decode() if isinstance(current, bytes) else current
        player_states = json.loads(current_str)

        pos_key = str(position)
        if pos_key not in player_states:
            return False

        player_states[pos_key]["status"] = status
        if last_action is not None:
            player_states[pos_key]["lastAction"] = last_action

        await self._redis.hset(key, "player_states", json.dumps(player_states))
        return True

    async def _update_player_field(
        self,
        hand_id: str,
        position: int,
        field: str,
        value: Any,
    ) -> bool:
        """Update single field in player state.

        Args:
            hand_id: Hand ID
            position: Player position
            field: Field name
            value: New value

        Returns:
            True if updated
        """
        key = CacheKeys.hand_state(hand_id)

        current = await self._redis.hget(key, "player_states")
        if not current:
            return False

        current_str = current.decode() if isinstance(current, bytes) else current
        player_states = json.loads(current_str)

        pos_key = str(position)
        if pos_key not in player_states:
            player_states[pos_key] = {}

        player_states[pos_key][field] = value

        await self._redis.hset(key, "player_states", json.dumps(player_states))
        return True

    # =========================================================================
    # Action History
    # =========================================================================

    async def record_action(
        self,
        hand_id: str,
        position: int,
        action_type: str,
        amount: int,
        timestamp: datetime | None = None,
    ) -> int:
        """Record player action to history.

        Args:
            hand_id: Hand ID
            position: Acting player's position
            action_type: Action type (fold, check, call, bet, raise, all_in)
            amount: Action amount
            timestamp: Action timestamp (defaults to now)

        Returns:
            Number of actions in history after this one
        """
        key = CacheKeys.hand_actions(hand_id)

        action = {
            "position": position,
            "actionType": action_type,
            "amount": amount,
            "timestamp": (timestamp or datetime.utcnow()).isoformat(),
        }

        pipe = self._redis.pipeline()
        pipe.rpush(key, json.dumps(action))
        pipe.expire(key, CacheKeys.HAND_ACTIONS_TTL.seconds)
        results = await pipe.execute()

        return results[0]  # Length after RPUSH

    async def get_action_history(self, hand_id: str) -> list[dict[str, Any]]:
        """Get all actions for hand.

        Args:
            hand_id: Hand ID

        Returns:
            List of action dicts in order
        """
        key = CacheKeys.hand_actions(hand_id)
        actions = await self._redis.lrange(key, 0, -1)

        return [
            json.loads(a.decode() if isinstance(a, bytes) else a)
            for a in actions
        ]

    async def get_last_action(self, hand_id: str) -> dict[str, Any] | None:
        """Get most recent action.

        Args:
            hand_id: Hand ID

        Returns:
            Last action dict, or None if no actions
        """
        key = CacheKeys.hand_actions(hand_id)
        result = await self._redis.lindex(key, -1)

        if result is None:
            return None

        result_str = result.decode() if isinstance(result, bytes) else result
        return json.loads(result_str)

    async def get_action_count(self, hand_id: str) -> int:
        """Get number of actions recorded.

        Args:
            hand_id: Hand ID

        Returns:
            Action count
        """
        key = CacheKeys.hand_actions(hand_id)
        return await self._redis.llen(key)

    # =========================================================================
    # Serialization Helpers
    # =========================================================================

    def _deserialize_hand_hash(
        self, data: dict[bytes | str, bytes | str]
    ) -> dict[str, Any]:
        """Convert Redis Hash to frontend-compatible dict.

        Args:
            data: Raw Redis HGETALL result

        Returns:
            Deserialized hand state dict
        """
        # Decode bytes
        decoded = {}
        for k, v in data.items():
            key = k.decode() if isinstance(k, bytes) else k
            val = v.decode() if isinstance(v, bytes) else v
            decoded[key] = val

        current_turn = decoded.get("current_turn", "")

        return {
            "handId": decoded.get("hand_id", ""),
            "tableId": decoded.get("table_id", ""),
            "handNumber": int(decoded.get("hand_number", "0")),
            "phase": decoded.get("phase", "preflop"),
            "communityCards": json.loads(decoded.get("community_cards", "[]")),
            "pot": {
                "mainPot": int(decoded.get("pot_main", "0")),
                "sidePots": json.loads(decoded.get("pot_side", "[]")),
            },
            "currentTurn": int(current_turn) if current_turn else None,
            "minRaise": int(decoded.get("min_raise", "0")),
            "dealerPosition": int(decoded.get("dealer_position", "0")),
            "smallBlind": int(decoded.get("small_blind", "0")),
            "bigBlind": int(decoded.get("big_blind", "0")),
            "startedAt": decoded.get("started_at", ""),
            "playerStates": json.loads(decoded.get("player_states", "{}")),
        }
