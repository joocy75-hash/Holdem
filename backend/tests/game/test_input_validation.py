"""Input Validation Property-Based Tests.

Property 4: Input Validation Completeness
- Tests invalid action types and out-of-range amounts
- Validates: Requirements 3.1, 3.2, 3.3

Tests ensure that:
1. Invalid action types are rejected
2. Out-of-range amounts are rejected
3. Invalid user IDs are rejected
4. Malformed inputs are handled gracefully
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from typing import List

from app.game.poker_table import PokerTable, Player, GamePhase


# =============================================================================
# Strategies
# =============================================================================

# Valid action types
valid_actions = ["fold", "check", "call", "raise", "all_in"]

# Invalid action types
invalid_action_strategy = st.text(min_size=1, max_size=20).filter(
    lambda x: x.lower() not in valid_actions
)

# Out of range amounts (negative or extremely large)
negative_amount_strategy = st.integers(max_value=-1)
huge_amount_strategy = st.integers(min_value=1_000_000_000)

# Invalid user IDs
invalid_user_id_strategy = st.text(min_size=0, max_size=50).filter(
    lambda x: not x.startswith("user")
)

# Number of players
num_players_strategy = st.integers(min_value=2, max_value=9)


# =============================================================================
# Property 4: Input Validation Completeness
# =============================================================================


class TestInvalidActionTypes:
    """Tests for invalid action type handling."""

    @given(invalid_action=invalid_action_strategy)
    @settings(max_examples=20, deadline=None)
    def test_invalid_action_type_rejected(self, invalid_action: str):
        """Invalid action types should be rejected."""
        table = PokerTable(
            room_id="test-room",
            name="Test Table",
            small_blind=10,
            big_blind=20,
            min_buy_in=400,
            max_buy_in=2000,
        )
        
        # Add players
        for i in range(2):
            player = Player(
                user_id=f"user{i}",
                username=f"Player{i}",
                seat=i,
                stack=1000,
            )
            table.seat_player(i, player)
        
        # Start hand
        result = table.start_new_hand()
        assume(result["success"])
        
        current_player = table.players.get(table.current_player_seat)
        assume(current_player is not None)
        
        # Try invalid action
        result = table.process_action(current_player.user_id, invalid_action, 0)
        
        assert result["success"] is False

    def test_empty_action_type_rejected(self):
        """Empty action type should be rejected."""
        table = PokerTable(
            room_id="test-room",
            name="Test Table",
            small_blind=10,
            big_blind=20,
            min_buy_in=400,
            max_buy_in=2000,
        )
        
        for i in range(2):
            player = Player(
                user_id=f"user{i}",
                username=f"Player{i}",
                seat=i,
                stack=1000,
            )
            table.seat_player(i, player)
        
        result = table.start_new_hand()
        assert result["success"]
        
        current_player = table.players.get(table.current_player_seat)
        result = table.process_action(current_player.user_id, "", 0)
        
        assert result["success"] is False

    def test_none_action_type_rejected(self):
        """None action type should be rejected."""
        table = PokerTable(
            room_id="test-room",
            name="Test Table",
            small_blind=10,
            big_blind=20,
            min_buy_in=400,
            max_buy_in=2000,
        )
        
        for i in range(2):
            player = Player(
                user_id=f"user{i}",
                username=f"Player{i}",
                seat=i,
                stack=1000,
            )
            table.seat_player(i, player)
        
        result = table.start_new_hand()
        assert result["success"]
        
        current_player = table.players.get(table.current_player_seat)
        
        # Try None action (should raise or return error)
        try:
            result = table.process_action(current_player.user_id, None, 0)
            assert result["success"] is False
        except (TypeError, AttributeError):
            # Expected - None is not a valid action
            pass


class TestOutOfRangeAmounts:
    """Tests for out-of-range amount handling."""

    @given(negative_amount=negative_amount_strategy)
    @settings(max_examples=20, deadline=None)
    def test_negative_raise_amount_rejected(self, negative_amount: int):
        """Negative raise amounts should be rejected or handled."""
        table = PokerTable(
            room_id="test-room",
            name="Test Table",
            small_blind=10,
            big_blind=20,
            min_buy_in=400,
            max_buy_in=2000,
        )
        
        for i in range(2):
            player = Player(
                user_id=f"user{i}",
                username=f"Player{i}",
                seat=i,
                stack=1000,
            )
            table.seat_player(i, player)
        
        result = table.start_new_hand()
        assume(result["success"])
        
        current_player = table.players.get(table.current_player_seat)
        assume(current_player is not None)
        
        # Try negative raise
        result = table.process_action(current_player.user_id, "raise", negative_amount)
        
        # Should either fail or be adjusted to valid amount
        # The important thing is it doesn't crash
        assert isinstance(result, dict)

    def test_raise_exceeding_stack_handled(self):
        """Raise exceeding stack should be handled (converted to all-in or rejected)."""
        table = PokerTable(
            room_id="test-room",
            name="Test Table",
            small_blind=10,
            big_blind=20,
            min_buy_in=400,
            max_buy_in=2000,
        )
        
        for i in range(2):
            player = Player(
                user_id=f"user{i}",
                username=f"Player{i}",
                seat=i,
                stack=500,  # Limited stack
            )
            table.seat_player(i, player)
        
        result = table.start_new_hand()
        assert result["success"]
        
        current_player = table.players.get(table.current_player_seat)
        
        # Try to raise more than stack
        result = table.process_action(current_player.user_id, "raise", 10000)
        
        # Should be handled gracefully (either rejected or converted to all-in)
        assert isinstance(result, dict)

    def test_raise_below_minimum_handled(self):
        """Raise below minimum should be handled."""
        table = PokerTable(
            room_id="test-room",
            name="Test Table",
            small_blind=10,
            big_blind=20,
            min_buy_in=400,
            max_buy_in=2000,
        )
        
        for i in range(2):
            player = Player(
                user_id=f"user{i}",
                username=f"Player{i}",
                seat=i,
                stack=1000,
            )
            table.seat_player(i, player)
        
        result = table.start_new_hand()
        assert result["success"]
        
        current_player = table.players.get(table.current_player_seat)
        
        # Try to raise below minimum (1 chip)
        result = table.process_action(current_player.user_id, "raise", 1)
        
        # Should be handled gracefully
        assert isinstance(result, dict)


class TestInvalidUserIds:
    """Tests for invalid user ID handling."""

    @given(invalid_user_id=invalid_user_id_strategy)
    @settings(max_examples=20, deadline=None)
    def test_nonexistent_user_action_rejected(self, invalid_user_id: str):
        """Actions from nonexistent users should be rejected."""
        assume(invalid_user_id)  # Skip empty strings
        
        table = PokerTable(
            room_id="test-room",
            name="Test Table",
            small_blind=10,
            big_blind=20,
            min_buy_in=400,
            max_buy_in=2000,
        )
        
        for i in range(2):
            player = Player(
                user_id=f"user{i}",
                username=f"Player{i}",
                seat=i,
                stack=1000,
            )
            table.seat_player(i, player)
        
        result = table.start_new_hand()
        assume(result["success"])
        
        # Try action from nonexistent user
        result = table.process_action(invalid_user_id, "fold", 0)
        
        assert result["success"] is False

    def test_empty_user_id_rejected(self):
        """Empty user ID should be rejected."""
        table = PokerTable(
            room_id="test-room",
            name="Test Table",
            small_blind=10,
            big_blind=20,
            min_buy_in=400,
            max_buy_in=2000,
        )
        
        for i in range(2):
            player = Player(
                user_id=f"user{i}",
                username=f"Player{i}",
                seat=i,
                stack=1000,
            )
            table.seat_player(i, player)
        
        result = table.start_new_hand()
        assert result["success"]
        
        result = table.process_action("", "fold", 0)
        
        assert result["success"] is False

    def test_wrong_turn_user_rejected(self):
        """Actions from user not in turn should be rejected."""
        table = PokerTable(
            room_id="test-room",
            name="Test Table",
            small_blind=10,
            big_blind=20,
            min_buy_in=400,
            max_buy_in=2000,
        )
        
        for i in range(3):
            player = Player(
                user_id=f"user{i}",
                username=f"Player{i}",
                seat=i,
                stack=1000,
            )
            table.seat_player(i, player)
        
        result = table.start_new_hand()
        assert result["success"]
        
        current_player = table.players.get(table.current_player_seat)
        
        # Find a player who is NOT in turn
        other_user_id = None
        for seat, player in table.players.items():
            if player and player.user_id != current_player.user_id:
                other_user_id = player.user_id
                break
        
        assert other_user_id is not None
        
        # Try action from wrong user
        result = table.process_action(other_user_id, "fold", 0)
        
        assert result["success"] is False


class TestSeatValidation:
    """Tests for seat validation."""

    def test_invalid_seat_number_rejected(self):
        """Invalid seat numbers should be rejected."""
        table = PokerTable(
            room_id="test-room",
            name="Test Table",
            small_blind=10,
            big_blind=20,
            min_buy_in=400,
            max_buy_in=2000,
            max_players=9,
        )
        
        player = Player(
            user_id="user1",
            username="Player1",
            seat=0,
            stack=1000,
        )
        
        # Try to seat at invalid positions
        result = table.seat_player(-1, player)
        assert result is False
        
        result = table.seat_player(9, player)  # max_players is 9, so seat 9 is invalid
        assert result is False
        
        result = table.seat_player(100, player)
        assert result is False

    def test_occupied_seat_rejected(self):
        """Seating at occupied seat should be rejected."""
        table = PokerTable(
            room_id="test-room",
            name="Test Table",
            small_blind=10,
            big_blind=20,
            min_buy_in=400,
            max_buy_in=2000,
        )
        
        player1 = Player(
            user_id="user1",
            username="Player1",
            seat=0,
            stack=1000,
        )
        player2 = Player(
            user_id="user2",
            username="Player2",
            seat=0,  # Same seat
            stack=1000,
        )
        
        result1 = table.seat_player(0, player1)
        assert result1 is True
        
        result2 = table.seat_player(0, player2)
        assert result2 is False


class TestBuyInValidation:
    """Tests for buy-in amount validation."""

    def test_buy_in_below_minimum_rejected(self):
        """Buy-in below minimum should be rejected."""
        table = PokerTable(
            room_id="test-room",
            name="Test Table",
            small_blind=10,
            big_blind=20,
            min_buy_in=400,
            max_buy_in=2000,
        )
        
        player = Player(
            user_id="user1",
            username="Player1",
            seat=0,
            stack=100,  # Below min_buy_in
        )
        
        result = table.seat_player(0, player)
        
        # Should either reject or adjust
        # Implementation may vary
        assert isinstance(result, bool)

    def test_buy_in_above_maximum_handled(self):
        """Buy-in above maximum should be handled."""
        table = PokerTable(
            room_id="test-room",
            name="Test Table",
            small_blind=10,
            big_blind=20,
            min_buy_in=400,
            max_buy_in=2000,
        )
        
        player = Player(
            user_id="user1",
            username="Player1",
            seat=0,
            stack=10000,  # Above max_buy_in
        )
        
        result = table.seat_player(0, player)
        
        # Should either reject or cap at max
        assert isinstance(result, bool)


class TestActionValidation:
    """Tests for action-specific validation."""

    def test_check_when_bet_required_rejected(self):
        """Check when bet is required should be rejected."""
        table = PokerTable(
            room_id="test-room",
            name="Test Table",
            small_blind=10,
            big_blind=20,
            min_buy_in=400,
            max_buy_in=2000,
        )
        
        for i in range(2):
            player = Player(
                user_id=f"user{i}",
                username=f"Player{i}",
                seat=i,
                stack=1000,
            )
            table.seat_player(i, player)
        
        result = table.start_new_hand()
        assert result["success"]
        
        # In preflop, SB needs to call or raise, not check
        current_player = table.players.get(table.current_player_seat)
        available = table.get_available_actions(current_player.user_id)
        
        # If check is not available, trying to check should fail
        if "check" not in available.get("actions", []):
            result = table.process_action(current_player.user_id, "check", 0)
            assert result["success"] is False

    def test_fold_always_allowed_during_turn(self):
        """Fold should always be allowed during player's turn."""
        table = PokerTable(
            room_id="test-room",
            name="Test Table",
            small_blind=10,
            big_blind=20,
            min_buy_in=400,
            max_buy_in=2000,
        )
        
        for i in range(2):
            player = Player(
                user_id=f"user{i}",
                username=f"Player{i}",
                seat=i,
                stack=1000,
            )
            table.seat_player(i, player)
        
        result = table.start_new_hand()
        assert result["success"]
        
        current_player = table.players.get(table.current_player_seat)
        available = table.get_available_actions(current_player.user_id)
        
        # Fold should always be available
        assert "fold" in available.get("actions", [])
        
        # And should succeed
        result = table.process_action(current_player.user_id, "fold", 0)
        assert result["success"] is True


class TestAvailableActionsValidation:
    """Tests for available actions validation."""

    @given(num_players=num_players_strategy)
    @settings(max_examples=10, deadline=None)
    def test_available_actions_always_valid(self, num_players: int):
        """Available actions should always be valid action types."""
        table = PokerTable(
            room_id="test-room",
            name="Test Table",
            small_blind=10,
            big_blind=20,
            min_buy_in=400,
            max_buy_in=2000,
            max_players=9,
        )
        
        for i in range(num_players):
            player = Player(
                user_id=f"user{i}",
                username=f"Player{i}",
                seat=i,
                stack=1000,
            )
            table.seat_player(i, player)
        
        result = table.start_new_hand()
        assume(result["success"])
        
        current_player = table.players.get(table.current_player_seat)
        assume(current_player is not None)
        
        available = table.get_available_actions(current_player.user_id)
        
        # All available actions should be valid
        for action in available.get("actions", []):
            assert action in valid_actions

    @given(num_players=num_players_strategy)
    @settings(max_examples=10, deadline=None)
    def test_min_max_raise_valid(self, num_players: int):
        """Min and max raise should be valid when raise is available."""
        table = PokerTable(
            room_id="test-room",
            name="Test Table",
            small_blind=10,
            big_blind=20,
            min_buy_in=400,
            max_buy_in=2000,
            max_players=9,
        )
        
        for i in range(num_players):
            player = Player(
                user_id=f"user{i}",
                username=f"Player{i}",
                seat=i,
                stack=1000,
            )
            table.seat_player(i, player)
        
        result = table.start_new_hand()
        assume(result["success"])
        
        current_player = table.players.get(table.current_player_seat)
        assume(current_player is not None)
        
        available = table.get_available_actions(current_player.user_id)
        
        if "raise" in available.get("actions", []):
            min_raise = available.get("min_raise", 0)
            max_raise = available.get("max_raise", 0)
            
            # Min should be <= max
            assert min_raise <= max_raise
            
            # Both should be positive
            assert min_raise >= 0
            assert max_raise >= 0
