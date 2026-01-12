"""State serialization and view generation.

This module handles:
1. Serializing TableState to JSON-compatible dicts
2. Deserializing dicts back to TableState
3. Generating player-specific views (with hole card masking)
4. Generating spectator views (all hole cards hidden)
"""

from datetime import datetime
from enum import Enum
from typing import Any

from app.engine.state import (
    ActionType,
    Card,
    GamePhase,
    HandState,
    Player,
    PlayerAction,
    PlayerHandState,
    PlayerHandStatus,
    PotState,
    SeatState,
    SeatStatus,
    SidePot,
    TableConfig,
    TableState,
    ValidAction,
)


# =============================================================================
# View Types
# =============================================================================


class ViewType(Enum):
    """Snapshot view type for access control."""

    PLAYER = "player"  # Show player's own hole cards
    SPECTATOR = "spectator"  # Hide all hole cards
    ADMIN = "admin"  # Show all hole cards (for debugging)


# =============================================================================
# Snapshot Serializer
# =============================================================================


class SnapshotSerializer:
    """Handles state serialization and view generation.

    Responsibilities:
    1. Serialize TableState to JSON-compatible dict
    2. Deserialize dict to TableState
    3. Generate player-specific views (hole card masking)
    4. Generate spectator views

    JSON keys use camelCase for frontend compatibility.
    """

    def serialize(self, state: TableState) -> dict[str, Any]:
        """Serialize full state to dict.

        Note: This includes all hole cards. Use create_player_snapshot
        or create_spectator_snapshot for client-safe views.

        Args:
            state: TableState to serialize

        Returns:
            JSON-serializable dict
        """
        return {
            "tableId": state.table_id,
            "config": self._serialize_config(state.config),
            "seats": [self._serialize_seat(s) for s in state.seats],
            "hand": self._serialize_hand(state.hand) if state.hand else None,
            "dealerPosition": state.dealer_position,
            "stateVersion": state.state_version,
            "updatedAt": state.updated_at.isoformat(),
        }

    def deserialize(self, data: dict[str, Any]) -> TableState:
        """Deserialize dict to TableState.

        Note: Does not restore _pk_snapshot. The PokerKit state
        must be reconstructed separately if needed.

        Args:
            data: Dict from serialize()

        Returns:
            TableState instance
        """
        return TableState(
            table_id=data["tableId"],
            config=self._deserialize_config(data["config"]),
            seats=tuple(self._deserialize_seat(s) for s in data["seats"]),
            hand=self._deserialize_hand(data["hand"]) if data.get("hand") else None,
            dealer_position=data["dealerPosition"],
            state_version=data["stateVersion"],
            updated_at=datetime.fromisoformat(data["updatedAt"]),
            _pk_snapshot=None,  # Must be restored separately
        )

    def create_player_snapshot(
        self,
        state: TableState,
        player_id: str,
        allowed_actions: tuple[ValidAction, ...] = (),
        turn_deadline_at: datetime | None = None,
    ) -> dict[str, Any]:
        """Create player view with their hole cards visible.

        Other players' hole cards are masked (set to null).

        Args:
            state: Full table state
            player_id: User ID of the viewing player
            allowed_actions: Actions available to this player
            turn_deadline_at: Deadline for current turn

        Returns:
            Snapshot dict safe to send to the player
        """
        base = self.serialize(state)

        # Find player's position
        player_position = None
        for seat in state.seats:
            if seat.player and seat.player.user_id == player_id:
                player_position = seat.position
                break

        if player_position is None:
            # Not seated, return spectator view
            return self.create_spectator_snapshot(state)

        # Mask other players' hole cards
        if base["hand"] and "playerStates" in base["hand"]:
            for ps in base["hand"]["playerStates"]:
                if ps["position"] != player_position:
                    ps["holeCards"] = None  # Mask

        # Extract player's hole cards
        my_hole_cards = None
        if state.hand:
            for ps in state.hand.player_states:
                if ps.position == player_position and ps.hole_cards:
                    my_hole_cards = [str(c) for c in ps.hole_cards]

        # Add player-specific fields
        base["myPosition"] = player_position
        base["myHoleCards"] = my_hole_cards
        base["allowedActions"] = [
            self._serialize_valid_action(va) for va in allowed_actions
        ]
        base["turnDeadlineAt"] = (
            turn_deadline_at.isoformat() if turn_deadline_at else None
        )
        base["viewType"] = ViewType.PLAYER.value

        return base

    def create_spectator_snapshot(self, state: TableState) -> dict[str, Any]:
        """Create spectator view with all hole cards masked.

        Args:
            state: Full table state

        Returns:
            Snapshot dict safe to send to spectators
        """
        base = self.serialize(state)

        # Mask all hole cards
        if base["hand"] and "playerStates" in base["hand"]:
            for ps in base["hand"]["playerStates"]:
                ps["holeCards"] = None

        # Add spectator-specific fields
        base["myPosition"] = None
        base["myHoleCards"] = None
        base["allowedActions"] = []
        base["turnDeadlineAt"] = None
        base["viewType"] = ViewType.SPECTATOR.value

        return base

    def create_admin_snapshot(self, state: TableState) -> dict[str, Any]:
        """Create admin view with all hole cards visible.

        For debugging and administrative purposes only.

        Args:
            state: Full table state

        Returns:
            Full snapshot with all information
        """
        base = self.serialize(state)
        base["myPosition"] = None
        base["myHoleCards"] = None
        base["allowedActions"] = []
        base["turnDeadlineAt"] = None
        base["viewType"] = ViewType.ADMIN.value
        return base

    # =========================================================================
    # Config Serialization
    # =========================================================================

    def _serialize_config(self, config: TableConfig) -> dict[str, Any]:
        """Serialize table configuration."""
        return {
            "maxSeats": config.max_seats,
            "smallBlind": config.small_blind,
            "bigBlind": config.big_blind,
            "minBuyIn": config.min_buy_in,
            "maxBuyIn": config.max_buy_in,
            "turnTimeoutSeconds": config.turn_timeout_seconds,
            "ante": config.ante,
        }

    def _deserialize_config(self, data: dict[str, Any]) -> TableConfig:
        """Deserialize table configuration."""
        return TableConfig(
            max_seats=data["maxSeats"],
            small_blind=data["smallBlind"],
            big_blind=data["bigBlind"],
            min_buy_in=data["minBuyIn"],
            max_buy_in=data["maxBuyIn"],
            turn_timeout_seconds=data.get("turnTimeoutSeconds", 30),
            ante=data.get("ante", 0),
        )

    # =========================================================================
    # Seat Serialization
    # =========================================================================

    def _serialize_seat(self, seat: SeatState) -> dict[str, Any]:
        """Serialize seat state."""
        return {
            "position": seat.position,
            "player": self._serialize_player(seat.player) if seat.player else None,
            "stack": seat.stack,
            "status": seat.status.value,
        }

    def _deserialize_seat(self, data: dict[str, Any]) -> SeatState:
        """Deserialize seat state."""
        return SeatState(
            position=data["position"],
            player=(
                self._deserialize_player(data["player"]) if data.get("player") else None
            ),
            stack=data["stack"],
            status=SeatStatus(data["status"]),
        )

    def _serialize_player(self, player: Player) -> dict[str, Any]:
        """Serialize player identity."""
        return {
            "userId": player.user_id,
            "nickname": player.nickname,
            "avatarUrl": player.avatar_url,
        }

    def _deserialize_player(self, data: dict[str, Any]) -> Player:
        """Deserialize player identity."""
        return Player(
            user_id=data["userId"],
            nickname=data["nickname"],
            avatar_url=data.get("avatarUrl"),
        )

    # =========================================================================
    # Hand Serialization
    # =========================================================================

    def _serialize_hand(self, hand: HandState) -> dict[str, Any]:
        """Serialize hand state."""
        return {
            "handId": hand.hand_id,
            "handNumber": hand.hand_number,
            "phase": hand.phase.value,
            "communityCards": [str(c) for c in hand.community_cards],
            "pot": self._serialize_pot(hand.pot),
            "playerStates": [
                self._serialize_player_hand_state(ps) for ps in hand.player_states
            ],
            "currentTurn": hand.current_turn,
            "lastAggressor": hand.last_aggressor,
            "minRaise": hand.min_raise,
            "startedAt": hand.started_at.isoformat(),
        }

    def _deserialize_hand(self, data: dict[str, Any]) -> HandState:
        """Deserialize hand state."""
        return HandState(
            hand_id=data["handId"],
            hand_number=data["handNumber"],
            phase=GamePhase(data["phase"]),
            community_cards=tuple(
                Card.from_string(s) for s in data.get("communityCards", [])
            ),
            pot=self._deserialize_pot(data["pot"]),
            player_states=tuple(
                self._deserialize_player_hand_state(ps)
                for ps in data.get("playerStates", [])
            ),
            current_turn=data.get("currentTurn"),
            last_aggressor=data.get("lastAggressor"),
            min_raise=data.get("minRaise", 0),
            started_at=datetime.fromisoformat(data["startedAt"]),
        )

    # =========================================================================
    # Pot Serialization
    # =========================================================================

    def _serialize_pot(self, pot: PotState) -> dict[str, Any]:
        """Serialize pot state."""
        return {
            "mainPot": pot.main_pot,
            "sidePots": [
                {
                    "amount": sp.amount,
                    "eligiblePositions": list(sp.eligible_positions),
                }
                for sp in pot.side_pots
            ],
            "total": pot.total,
        }

    def _deserialize_pot(self, data: dict[str, Any]) -> PotState:
        """Deserialize pot state."""
        return PotState(
            main_pot=data["mainPot"],
            side_pots=tuple(
                SidePot(
                    amount=sp["amount"],
                    eligible_positions=tuple(sp.get("eligiblePositions", [])),
                )
                for sp in data.get("sidePots", [])
            ),
        )

    # =========================================================================
    # Player Hand State Serialization
    # =========================================================================

    def _serialize_player_hand_state(
        self, ps: PlayerHandState
    ) -> dict[str, Any]:
        """Serialize player's hand state."""
        return {
            "position": ps.position,
            "holeCards": [str(c) for c in ps.hole_cards] if ps.hole_cards else None,
            "betAmount": ps.bet_amount,
            "totalBet": ps.total_bet,
            "status": ps.status.value,
            "lastAction": (
                self._serialize_action(ps.last_action) if ps.last_action else None
            ),
        }

    def _deserialize_player_hand_state(
        self, data: dict[str, Any]
    ) -> PlayerHandState:
        """Deserialize player's hand state."""
        hole_cards = None
        if data.get("holeCards"):
            hole_cards = tuple(Card.from_string(s) for s in data["holeCards"])

        return PlayerHandState(
            position=data["position"],
            hole_cards=hole_cards,
            bet_amount=data.get("betAmount", 0),
            total_bet=data.get("totalBet", 0),
            status=PlayerHandStatus(data["status"]),
            last_action=(
                self._deserialize_action(data["lastAction"])
                if data.get("lastAction")
                else None
            ),
        )

    # =========================================================================
    # Action Serialization
    # =========================================================================

    def _serialize_action(self, action: PlayerAction) -> dict[str, Any]:
        """Serialize player action."""
        return {
            "position": action.position,
            "actionType": action.action_type.value,
            "amount": action.amount,
            "timestamp": action.timestamp.isoformat(),
        }

    def _deserialize_action(self, data: dict[str, Any]) -> PlayerAction:
        """Deserialize player action."""
        return PlayerAction(
            position=data["position"],
            action_type=ActionType(data["actionType"]),
            amount=data["amount"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )

    def _serialize_valid_action(self, va: ValidAction) -> dict[str, Any]:
        """Serialize valid action option."""
        return {
            "type": va.action_type.value,  # FE expects "type" not "actionType"
            "minAmount": va.min_amount,
            "maxAmount": va.max_amount,
        }


# =============================================================================
# Convenience Functions
# =============================================================================


def serialize_state(state: TableState) -> dict[str, Any]:
    """Serialize table state to dict.

    Convenience function for quick serialization.
    """
    return SnapshotSerializer().serialize(state)


def deserialize_state(data: dict[str, Any]) -> TableState:
    """Deserialize dict to table state.

    Convenience function for quick deserialization.
    """
    return SnapshotSerializer().deserialize(data)


def create_player_view(
    state: TableState,
    player_id: str,
    allowed_actions: tuple[ValidAction, ...] = (),
) -> dict[str, Any]:
    """Create player-safe view of table state.

    Convenience function for creating player snapshots.
    """
    return SnapshotSerializer().create_player_snapshot(
        state, player_id, allowed_actions
    )


def create_spectator_view(state: TableState) -> dict[str, Any]:
    """Create spectator-safe view of table state.

    Convenience function for creating spectator snapshots.
    """
    return SnapshotSerializer().create_spectator_snapshot(state)
