"""Action processing for game engine.

This module provides high-level action processing with validation
and state management, decoupled from the PokerKit wrapper.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from app.engine.core import (
    EngineError,
    InvalidActionError,
    NotYourTurnError,
    PokerKitWrapper,
)
from app.engine.state import (
    ActionRequest,
    ActionType,
    GamePhase,
    HandResult,
    PlayerAction,
    SeatState,
    SeatStatus,
    TableState,
    ValidAction,
)


# =============================================================================
# Result Types
# =============================================================================


@dataclass(frozen=True)
class ValidationResult:
    """Result of action validation."""

    valid: bool
    error_code: str | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class ActionResult:
    """Result of action processing."""

    success: bool
    request_id: str
    new_state: TableState | None = None
    executed_action: PlayerAction | None = None
    error_code: str | None = None
    error_message: str | None = None
    state_version: int | None = None


# =============================================================================
# Event Hook Protocol
# =============================================================================


class EngineEventHook(Protocol):
    """Protocol for engine event hooks.

    Implement this to receive notifications about engine events.
    Used by the Table Orchestrator for broadcasting updates.
    """

    def on_action_processed(
        self,
        action: PlayerAction,
        result: ActionResult,
    ) -> None:
        """Called after action is processed."""
        ...

    def on_hand_completed(
        self,
        hand_result: HandResult,
    ) -> None:
        """Called when hand finishes."""
        ...

    def on_phase_changed(
        self,
        old_phase: GamePhase,
        new_phase: GamePhase,
    ) -> None:
        """Called when game phase changes."""
        ...


# =============================================================================
# Action Processor
# =============================================================================


class ActionProcessor:
    """Processes and validates player actions.

    Responsibilities:
    1. Validate action requests before execution
    2. Apply actions via PokerKitWrapper
    3. Return typed results with error information

    Usage:
        processor = ActionProcessor(wrapper)

        # Validate first (optional but recommended)
        validation = processor.validate_action(state, player_id, action)
        if not validation.valid:
            return error_response(validation)

        # Process action
        result = processor.process_action(state, player_id, action)
        if result.success:
            # Update state, broadcast, etc.
            new_state = result.new_state
    """

    def __init__(self, wrapper: PokerKitWrapper) -> None:
        """Initialize processor with PokerKit wrapper.

        Args:
            wrapper: PokerKitWrapper instance
        """
        self._wrapper = wrapper

    def validate_action(
        self,
        state: TableState,
        player_id: str,
        action: ActionRequest,
    ) -> ValidationResult:
        """Validate action without executing.

        This performs all validation checks and returns a result
        indicating whether the action would succeed.

        Args:
            state: Current table state
            player_id: User ID of the acting player
            action: Requested action

        Returns:
            ValidationResult with valid=True if action is allowed
        """
        # Find player's seat
        seat = self._find_player_seat(state, player_id)
        if seat is None:
            return ValidationResult(
                valid=False,
                error_code="PLAYER_NOT_SEATED",
                error_message="Player is not seated at this table",
            )

        # Check seat status
        if seat.status not in (SeatStatus.ACTIVE, SeatStatus.WAITING):
            return ValidationResult(
                valid=False,
                error_code="INVALID_SEAT_STATUS",
                error_message=f"Cannot act with seat status: {seat.status.value}",
            )

        # Check hand is active
        if state.hand is None:
            return ValidationResult(
                valid=False,
                error_code="NO_ACTIVE_HAND",
                error_message="No hand in progress",
            )

        # Check hand is not finished
        if state.hand.phase == GamePhase.FINISHED:
            return ValidationResult(
                valid=False,
                error_code="HAND_FINISHED",
                error_message="Hand has already finished",
            )

        # Check player's turn
        if state.hand.current_turn != seat.position:
            return ValidationResult(
                valid=False,
                error_code="NOT_YOUR_TURN",
                error_message="It is not your turn to act",
            )

        # Get valid actions from wrapper
        valid_actions = self._wrapper.get_valid_actions(state, seat.position)

        # Check action type is allowed
        allowed_types = {va.action_type for va in valid_actions}
        if action.action_type not in allowed_types:
            return ValidationResult(
                valid=False,
                error_code="INVALID_ACTION_TYPE",
                error_message=f"Cannot {action.action_type.value} in current situation",
            )

        # Validate amount for bet/raise
        if action.action_type in (ActionType.BET, ActionType.RAISE):
            if action.amount is None:
                return ValidationResult(
                    valid=False,
                    error_code="AMOUNT_REQUIRED",
                    error_message="Amount is required for bet/raise actions",
                )

            # Find the valid action constraints
            valid_bet = next(
                (va for va in valid_actions if va.action_type == action.action_type),
                None,
            )

            if valid_bet is None:
                return ValidationResult(
                    valid=False,
                    error_code="INVALID_ACTION_TYPE",
                    error_message=f"Cannot {action.action_type.value} now",
                )

            if valid_bet.min_amount is not None and action.amount < valid_bet.min_amount:
                return ValidationResult(
                    valid=False,
                    error_code="AMOUNT_TOO_LOW",
                    error_message=f"Minimum amount is {valid_bet.min_amount}",
                )

            if valid_bet.max_amount is not None and action.amount > valid_bet.max_amount:
                return ValidationResult(
                    valid=False,
                    error_code="AMOUNT_TOO_HIGH",
                    error_message=f"Maximum amount is {valid_bet.max_amount}",
                )

        return ValidationResult(valid=True)

    def process_action(
        self,
        state: TableState,
        player_id: str,
        action: ActionRequest,
    ) -> ActionResult:
        """Process action and return result.

        This validates and executes the action, returning a new state
        on success or error information on failure.

        Args:
            state: Current table state
            player_id: User ID of the acting player
            action: Requested action

        Returns:
            ActionResult with new state on success, error info on failure
        """
        # Validate first
        validation = self.validate_action(state, player_id, action)
        if not validation.valid:
            return ActionResult(
                success=False,
                request_id=action.request_id,
                error_code=validation.error_code,
                error_message=validation.error_message,
            )

        # Find seat (we know it exists from validation)
        seat = self._find_player_seat(state, player_id)
        if seat is None:  # Should not happen after validation
            return ActionResult(
                success=False,
                request_id=action.request_id,
                error_code="INTERNAL_ERROR",
                error_message="Player seat not found",
            )

        # Execute action via wrapper
        try:
            new_state, executed_action = self._wrapper.apply_action(
                state,
                seat.position,
                action,
            )

            return ActionResult(
                success=True,
                request_id=action.request_id,
                new_state=new_state,
                executed_action=executed_action,
                state_version=new_state.state_version,
            )

        except NotYourTurnError as e:
            return ActionResult(
                success=False,
                request_id=action.request_id,
                error_code="NOT_YOUR_TURN",
                error_message=str(e),
            )

        except InvalidActionError as e:
            return ActionResult(
                success=False,
                request_id=action.request_id,
                error_code="INVALID_ACTION",
                error_message=str(e),
            )

        except EngineError as e:
            return ActionResult(
                success=False,
                request_id=action.request_id,
                error_code="ENGINE_ERROR",
                error_message=str(e),
            )

    def get_available_actions(
        self,
        state: TableState,
        player_id: str,
    ) -> tuple[ValidAction, ...]:
        """Get available actions for a player.

        Args:
            state: Current table state
            player_id: User ID of the player

        Returns:
            Tuple of valid actions (empty if not player's turn)
        """
        seat = self._find_player_seat(state, player_id)
        if seat is None:
            return ()

        if state.hand is None:
            return ()

        if state.hand.current_turn != seat.position:
            return ()

        return self._wrapper.get_valid_actions(state, seat.position)

    def _find_player_seat(
        self,
        state: TableState,
        player_id: str,
    ) -> SeatState | None:
        """Find seat occupied by player."""
        for seat in state.seats:
            if seat.player is not None and seat.player.user_id == player_id:
                return seat
        return None


# =============================================================================
# State Manager (Optional convenience class)
# =============================================================================


class StateManager:
    """Manages table state lifecycle.

    This is a convenience class that combines the PokerKitWrapper
    and ActionProcessor for common operations.
    """

    def __init__(self) -> None:
        """Initialize state manager."""
        self._wrapper = PokerKitWrapper()
        self._processor = ActionProcessor(self._wrapper)

    @property
    def wrapper(self) -> PokerKitWrapper:
        """Get the underlying wrapper."""
        return self._wrapper

    @property
    def processor(self) -> ActionProcessor:
        """Get the action processor."""
        return self._processor

    def start_hand(
        self,
        table_state: TableState,
        hand_id: str | None = None,
    ) -> TableState:
        """Start a new hand.

        Args:
            table_state: Current table state
            hand_id: Optional hand ID (generated if not provided)

        Returns:
            New table state with hand started
        """
        return self._wrapper.create_initial_hand(table_state, hand_id)

    def process_action(
        self,
        state: TableState,
        player_id: str,
        action: ActionRequest,
    ) -> ActionResult:
        """Process a player action.

        Args:
            state: Current table state
            player_id: Acting player's user ID
            action: The action request

        Returns:
            ActionResult with new state or error
        """
        return self._processor.process_action(state, player_id, action)

    def get_hand_result(self, table_state: TableState) -> HandResult | None:
        """Get hand result if hand is finished.

        Args:
            table_state: Current table state

        Returns:
            HandResult if hand finished, None otherwise
        """
        if not self._wrapper.is_hand_finished(table_state):
            return None
        return self._wrapper.evaluate_hand(table_state)

    def is_hand_finished(self, table_state: TableState) -> bool:
        """Check if current hand is finished."""
        return self._wrapper.is_hand_finished(table_state)
