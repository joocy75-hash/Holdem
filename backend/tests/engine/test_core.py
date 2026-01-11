"""Tests for PokerKit wrapper (core.py)."""

import pytest
from datetime import datetime

from app.engine.core import (
    PokerKitWrapper,
    InvalidActionError,
    NotYourTurnError,
    pk_card_to_card,
    card_to_pk_string,
)
from app.engine.state import (
    Card,
    Rank,
    Suit,
    Player,
    SeatState,
    SeatStatus,
    TableConfig,
    TableState,
    ActionRequest,
    ActionType,
    GamePhase,
)


@pytest.fixture
def table_config() -> TableConfig:
    """Create a test table configuration."""
    return TableConfig(
        max_seats=6,
        small_blind=10,
        big_blind=20,
        min_buy_in=400,
        max_buy_in=2000,
    )


@pytest.fixture
def two_player_table(table_config: TableConfig) -> TableState:
    """Create a table with 2 active players."""
    player1 = Player(user_id="user1", nickname="Player1")
    player2 = Player(user_id="user2", nickname="Player2")

    seats = (
        SeatState(position=0, player=player1, stack=1000, status=SeatStatus.ACTIVE),
        SeatState(position=1, player=player2, stack=1000, status=SeatStatus.ACTIVE),
        SeatState(position=2, player=None, stack=0, status=SeatStatus.EMPTY),
        SeatState(position=3, player=None, stack=0, status=SeatStatus.EMPTY),
        SeatState(position=4, player=None, stack=0, status=SeatStatus.EMPTY),
        SeatState(position=5, player=None, stack=0, status=SeatStatus.EMPTY),
    )

    return TableState(
        table_id="table-1",
        config=table_config,
        seats=seats,
        hand=None,
        dealer_position=0,
        state_version=0,
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def three_player_table(table_config: TableConfig) -> TableState:
    """Create a table with 3 active players."""
    player1 = Player(user_id="user1", nickname="Player1")
    player2 = Player(user_id="user2", nickname="Player2")
    player3 = Player(user_id="user3", nickname="Player3")

    seats = (
        SeatState(position=0, player=player1, stack=1000, status=SeatStatus.ACTIVE),
        SeatState(position=1, player=player2, stack=1000, status=SeatStatus.ACTIVE),
        SeatState(position=2, player=player3, stack=1000, status=SeatStatus.ACTIVE),
        SeatState(position=3, player=None, stack=0, status=SeatStatus.EMPTY),
        SeatState(position=4, player=None, stack=0, status=SeatStatus.EMPTY),
        SeatState(position=5, player=None, stack=0, status=SeatStatus.EMPTY),
    )

    return TableState(
        table_id="table-1",
        config=table_config,
        seats=seats,
        hand=None,
        dealer_position=0,
        state_version=0,
        updated_at=datetime.utcnow(),
    )


class TestCardMapping:
    """Tests for card conversion functions."""

    def test_card_to_pk_string(self):
        """Test converting our Card to PokerKit string."""
        card = Card(rank=Rank.ACE, suit=Suit.HEARTS)
        assert card_to_pk_string(card) == "Ah"

        card2 = Card(rank=Rank.TEN, suit=Suit.CLUBS)
        assert card_to_pk_string(card2) == "Tc"


class TestPokerKitWrapper:
    """Tests for PokerKitWrapper."""

    def test_create_initial_hand(self, two_player_table: TableState):
        """Test creating a new hand."""
        wrapper = PokerKitWrapper()

        state = wrapper.create_initial_hand(two_player_table, hand_id="hand-1")

        assert state.hand is not None
        assert state.hand.hand_id == "hand-1"
        assert state.hand.hand_number == 1
        assert state.hand.phase == GamePhase.PREFLOP
        assert state.state_version == 1
        assert len(state.hand.player_states) == 2

        # Both players should have hole cards
        for ps in state.hand.player_states:
            assert ps.hole_cards is not None
            assert len(ps.hole_cards) == 2

    def test_create_hand_requires_two_players(self, table_config: TableConfig):
        """Test that creating a hand requires at least 2 players."""
        player1 = Player(user_id="user1", nickname="Player1")

        seats = (
            SeatState(position=0, player=player1, stack=1000, status=SeatStatus.ACTIVE),
            SeatState(position=1, player=None, stack=0, status=SeatStatus.EMPTY),
        )

        state = TableState(
            table_id="table-1",
            config=table_config,
            seats=seats,
            hand=None,
            dealer_position=0,
            state_version=0,
            updated_at=datetime.utcnow(),
        )

        wrapper = PokerKitWrapper()
        with pytest.raises(ValueError, match="at least 2 active players"):
            wrapper.create_initial_hand(state)

    def test_get_valid_actions_preflop(self, two_player_table: TableState):
        """Test getting valid actions in preflop."""
        wrapper = PokerKitWrapper()
        state = wrapper.create_initial_hand(two_player_table, hand_id="hand-1")

        # Current turn should be one of the players
        assert state.hand.current_turn is not None

        # Get valid actions for current player
        valid = wrapper.get_valid_actions(state, state.hand.current_turn)
        assert len(valid) > 0

        # Should be able to fold
        action_types = {va.action_type for va in valid}
        assert ActionType.FOLD in action_types

    def test_apply_fold_action(self, two_player_table: TableState):
        """Test applying a fold action."""
        wrapper = PokerKitWrapper()
        state = wrapper.create_initial_hand(two_player_table, hand_id="hand-1")

        current_turn = state.hand.current_turn
        assert current_turn is not None

        action = ActionRequest(
            request_id="req-1",
            action_type=ActionType.FOLD,
        )

        new_state, player_action = wrapper.apply_action(state, current_turn, action)

        assert new_state.state_version == state.state_version + 1
        assert player_action.action_type == ActionType.FOLD
        assert player_action.position == current_turn

    def test_apply_call_action(self, two_player_table: TableState):
        """Test applying a call action."""
        wrapper = PokerKitWrapper()
        state = wrapper.create_initial_hand(two_player_table, hand_id="hand-1")

        current_turn = state.hand.current_turn
        assert current_turn is not None

        # Check if call is available
        valid = wrapper.get_valid_actions(state, current_turn)
        call_action = next(
            (va for va in valid if va.action_type == ActionType.CALL), None
        )

        if call_action:
            action = ActionRequest(
                request_id="req-1",
                action_type=ActionType.CALL,
            )

            new_state, player_action = wrapper.apply_action(state, current_turn, action)
            assert player_action.action_type == ActionType.CALL

    def test_apply_action_not_your_turn(self, two_player_table: TableState):
        """Test applying action when it's not your turn."""
        wrapper = PokerKitWrapper()
        state = wrapper.create_initial_hand(two_player_table, hand_id="hand-1")

        current_turn = state.hand.current_turn
        other_position = 1 if current_turn == 0 else 0

        action = ActionRequest(
            request_id="req-1",
            action_type=ActionType.FOLD,
        )

        with pytest.raises(NotYourTurnError):
            wrapper.apply_action(state, other_position, action)

    def test_hand_finishes_after_fold(self, two_player_table: TableState):
        """Test that hand finishes when one player folds heads up."""
        wrapper = PokerKitWrapper()
        state = wrapper.create_initial_hand(two_player_table, hand_id="hand-1")

        current_turn = state.hand.current_turn
        action = ActionRequest(
            request_id="req-1",
            action_type=ActionType.FOLD,
        )

        new_state, _ = wrapper.apply_action(state, current_turn, action)

        # In heads up, folding should end the hand
        assert wrapper.is_hand_finished(new_state)

    def test_three_player_hand(self, three_player_table: TableState):
        """Test a hand with 3 players."""
        wrapper = PokerKitWrapper()
        state = wrapper.create_initial_hand(three_player_table, hand_id="hand-1")

        assert state.hand is not None
        assert len(state.hand.player_states) == 3

        # All three should have hole cards
        for ps in state.hand.player_states:
            assert ps.hole_cards is not None

    def test_evaluate_finished_hand(self, two_player_table: TableState):
        """Test evaluating a finished hand."""
        wrapper = PokerKitWrapper()
        state = wrapper.create_initial_hand(two_player_table, hand_id="hand-1")

        # Fold to end the hand
        current_turn = state.hand.current_turn
        action = ActionRequest(
            request_id="req-1",
            action_type=ActionType.FOLD,
        )

        new_state, _ = wrapper.apply_action(state, current_turn, action)

        # Should be able to evaluate
        result = wrapper.evaluate_hand(new_state)
        assert result.hand_id == "hand-1"
        assert len(result.winners) > 0

    def test_apply_action_no_hand(self, two_player_table: TableState):
        """Test applying action when no hand is active."""
        wrapper = PokerKitWrapper()

        action = ActionRequest(
            request_id="req-1",
            action_type=ActionType.FOLD,
        )

        with pytest.raises(InvalidActionError, match="No active hand"):
            wrapper.apply_action(two_player_table, 0, action)


class TestFullHandSimulation:
    """Integration tests for complete hand simulation."""

    def test_simple_hand_call_check_to_showdown(self, three_player_table: TableState):
        """Test a hand where players check/call to showdown."""
        wrapper = PokerKitWrapper()
        state = wrapper.create_initial_hand(three_player_table, hand_id="hand-1")

        # Play through the hand with calls/checks
        action_count = 0
        max_actions = 50  # Safety limit

        while not wrapper.is_hand_finished(state) and action_count < max_actions:
            current_turn = state.hand.current_turn
            if current_turn is None:
                break

            valid = wrapper.get_valid_actions(state, current_turn)
            if not valid:
                break

            # Prefer check, then call, then fold
            action_type = ActionType.FOLD
            for va in valid:
                if va.action_type == ActionType.CHECK:
                    action_type = ActionType.CHECK
                    break
                elif va.action_type == ActionType.CALL:
                    action_type = ActionType.CALL
                    break

            action = ActionRequest(
                request_id=f"req-{action_count}",
                action_type=action_type,
            )

            state, _ = wrapper.apply_action(state, current_turn, action)
            action_count += 1

        # Should be finished
        assert wrapper.is_hand_finished(state)

        # Should be able to evaluate
        result = wrapper.evaluate_hand(state)
        assert len(result.winners) > 0

    def test_hand_with_raise(self, two_player_table: TableState):
        """Test a hand with a raise action."""
        wrapper = PokerKitWrapper()
        state = wrapper.create_initial_hand(two_player_table, hand_id="hand-1")

        current_turn = state.hand.current_turn
        valid = wrapper.get_valid_actions(state, current_turn)

        # Find raise action
        raise_action = next(
            (
                va
                for va in valid
                if va.action_type in (ActionType.RAISE, ActionType.BET)
            ),
            None,
        )

        if raise_action and raise_action.min_amount:
            action = ActionRequest(
                request_id="req-1",
                action_type=raise_action.action_type,
                amount=raise_action.min_amount,
            )

            new_state, player_action = wrapper.apply_action(state, current_turn, action)
            assert player_action.amount == raise_action.min_amount
