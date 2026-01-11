"""Game engine module - PokerKit wrapper.

This module provides a complete game engine layer for Texas Hold'em poker,
wrapping the PokerKit library with immutable state semantics.

Main Components:
- state: Immutable data models (Card, TableState, HandState, etc.)
- core: PokerKitWrapper for game logic
- actions: ActionProcessor for action validation and processing
- snapshot: SnapshotSerializer for JSON serialization and view generation

Usage Example:
    from app.engine import (
        PokerKitWrapper,
        ActionProcessor,
        SnapshotSerializer,
        TableState,
        TableConfig,
        SeatState,
        Player,
        ActionRequest,
        ActionType,
    )

    # Create wrapper and processor
    wrapper = PokerKitWrapper()
    processor = ActionProcessor(wrapper)
    serializer = SnapshotSerializer()

    # Start a hand
    table_state = wrapper.create_initial_hand(table_state)

    # Process an action
    action = ActionRequest(request_id="123", action_type=ActionType.CALL)
    result = processor.process_action(table_state, player_id, action)

    # Serialize for client
    snapshot = serializer.create_player_snapshot(result.new_state, player_id)
"""

# State models
from app.engine.state import (
    ActionRequest,
    ActionType,
    Card,
    GamePhase,
    HandRank,
    HandResult,
    HandState,
    Player,
    PlayerAction,
    PlayerHandState,
    PlayerHandStatus,
    PlayerViewState,
    PotState,
    Rank,
    SeatState,
    SeatStatus,
    ShowdownHand,
    SidePot,
    SpectatorViewState,
    StateTransition,
    Suit,
    TableConfig,
    TableState,
    ValidAction,
    WinnerInfo,
)

# Core wrapper
from app.engine.core import (
    EngineError,
    GameStateError,
    InsufficientStackError,
    InvalidActionError,
    NotYourTurnError,
    PokerKitWrapper,
    card_to_pk_string,
    pk_card_to_card,
)

# Action processing
from app.engine.actions import (
    ActionProcessor,
    ActionResult,
    EngineEventHook,
    StateManager,
    ValidationResult,
)

# Serialization
from app.engine.snapshot import (
    SnapshotSerializer,
    ViewType,
    create_player_view,
    create_spectator_view,
    deserialize_state,
    serialize_state,
)

__all__ = [
    # State models
    "ActionRequest",
    "ActionType",
    "Card",
    "GamePhase",
    "HandRank",
    "HandResult",
    "HandState",
    "Player",
    "PlayerAction",
    "PlayerHandState",
    "PlayerHandStatus",
    "PlayerViewState",
    "PotState",
    "Rank",
    "SeatState",
    "SeatStatus",
    "ShowdownHand",
    "SidePot",
    "SpectatorViewState",
    "StateTransition",
    "Suit",
    "TableConfig",
    "TableState",
    "ValidAction",
    "WinnerInfo",
    # Exceptions
    "EngineError",
    "GameStateError",
    "InsufficientStackError",
    "InvalidActionError",
    "NotYourTurnError",
    # Core
    "PokerKitWrapper",
    "card_to_pk_string",
    "pk_card_to_card",
    # Actions
    "ActionProcessor",
    "ActionResult",
    "EngineEventHook",
    "StateManager",
    "ValidationResult",
    # Serialization
    "SnapshotSerializer",
    "ViewType",
    "create_player_view",
    "create_spectator_view",
    "deserialize_state",
    "serialize_state",
]
