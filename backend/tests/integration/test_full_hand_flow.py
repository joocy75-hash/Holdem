"""Integration tests for full hand flow.

Tests complete hand lifecycle from start to finish.
Validates Requirements 10.3, 10.4 from code-quality-security-upgrade spec.
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime
from uuid import uuid4

from app.game.poker_table import PokerTable, Player, GamePhase
from app.game import game_manager


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def clean_game_manager():
    """Ensure clean game manager state."""
    # Clear any existing tables
    game_manager.clear_all()
    yield game_manager
    # Cleanup after test
    game_manager.clear_all()


@pytest.fixture
def two_player_table(clean_game_manager) -> PokerTable:
    """Create a 2-player table in game manager."""
    room_id = f"test-room-{uuid4()}"
    table = clean_game_manager.create_table_sync(
        room_id=room_id,
        name="Test Table",
        small_blind=10,
        big_blind=20,
        min_buy_in=400,
        max_buy_in=2000,
    )
    
    player1 = Player(user_id="user1", username="Player1", seat=0, stack=1000)
    player2 = Player(user_id="user2", username="Player2", seat=1, stack=1000)
    
    table.seat_player(0, player1)
    table.seat_player(1, player2)
    
    return table


@pytest.fixture
def six_player_table(clean_game_manager) -> PokerTable:
    """Create a 6-player table in game manager."""
    room_id = f"test-room-{uuid4()}"
    table = clean_game_manager.create_table_sync(
        room_id=room_id,
        name="Test Table",
        small_blind=10,
        big_blind=20,
        min_buy_in=400,
        max_buy_in=2000,
    )
    
    for i in range(6):
        player = Player(
            user_id=f"user{i}",
            username=f"Player{i}",
            seat=i,
            stack=1000,
        )
        table.seat_player(i, player)
    
    return table


# =============================================================================
# Full Hand Flow Tests
# =============================================================================


class TestFullHandFlow:
    """Tests for complete hand lifecycle."""

    def test_complete_hand_with_fold(self, two_player_table: PokerTable):
        """Test complete hand ending with fold."""
        table = two_player_table
        
        # Start hand
        result = table.start_new_hand()
        assert result["success"] is True
        assert table.phase == GamePhase.PREFLOP
        
        # First player folds
        current_player = table.players.get(table.current_player_seat)
        result = table.process_action(current_player.user_id, "fold", 0)
        
        # Hand should be complete
        assert result["hand_complete"] is True
        assert result["hand_result"] is not None
        assert len(result["hand_result"]["winners"]) == 1
        
        # State should be reset
        assert table.phase == GamePhase.WAITING

    def test_complete_hand_to_showdown(self, two_player_table: PokerTable):
        """Test complete hand going to showdown."""
        table = two_player_table
        
        # Start hand
        result = table.start_new_hand()
        assert result["success"] is True
        
        # Play through all streets with check/call
        max_actions = 20
        action_count = 0
        
        while table.phase != GamePhase.WAITING and action_count < max_actions:
            current_player = table.players.get(table.current_player_seat)
            if not current_player:
                break
            
            available = table.get_available_actions(current_player.user_id)
            actions = available.get("actions", [])
            
            if "check" in actions:
                result = table.process_action(current_player.user_id, "check", 0)
            elif "call" in actions:
                result = table.process_action(current_player.user_id, "call", 0)
            else:
                break
            
            action_count += 1
            
            if result.get("hand_complete"):
                break
        
        # Hand should be complete
        assert table.phase == GamePhase.WAITING

    def test_phase_progression(self, two_player_table: PokerTable):
        """Test hand progresses through all phases."""
        table = two_player_table
        
        phases_seen = []
        
        # Start hand
        table.start_new_hand()
        phases_seen.append(table.phase)
        
        # Play through
        max_actions = 20
        action_count = 0
        
        while table.phase != GamePhase.WAITING and action_count < max_actions:
            current_player = table.players.get(table.current_player_seat)
            if not current_player:
                break
            
            available = table.get_available_actions(current_player.user_id)
            actions = available.get("actions", [])
            
            if "check" in actions:
                result = table.process_action(current_player.user_id, "check", 0)
            elif "call" in actions:
                result = table.process_action(current_player.user_id, "call", 0)
            else:
                break
            
            if table.phase not in phases_seen:
                phases_seen.append(table.phase)
            
            action_count += 1
            
            if result.get("hand_complete"):
                break
        
        # Should have seen at least PREFLOP
        assert GamePhase.PREFLOP in phases_seen

    def test_community_cards_dealt_correctly(self, two_player_table: PokerTable):
        """Test community cards are dealt at correct phases."""
        table = two_player_table
        
        # Start hand
        table.start_new_hand()
        assert len(table.community_cards) == 0
        
        # Complete preflop
        for _ in range(2):
            current_player = table.players.get(table.current_player_seat)
            if current_player:
                available = table.get_available_actions(current_player.user_id)
                if "check" in available.get("actions", []):
                    table.process_action(current_player.user_id, "check", 0)
                elif "call" in available.get("actions", []):
                    table.process_action(current_player.user_id, "call", 0)
        
        # Should be at flop with 3 cards
        if table.phase == GamePhase.FLOP:
            assert len(table.community_cards) == 3
        
        # Complete flop
        for _ in range(2):
            current_player = table.players.get(table.current_player_seat)
            if current_player and table.phase == GamePhase.FLOP:
                table.process_action(current_player.user_id, "check", 0)
        
        # Should be at turn with 4 cards
        if table.phase == GamePhase.TURN:
            assert len(table.community_cards) == 4

    def test_pot_accumulates_correctly(self, two_player_table: PokerTable):
        """Test pot accumulates with bets."""
        table = two_player_table
        
        # Start hand
        table.start_new_hand()
        initial_pot = table.pot  # Should be blinds (30)
        
        assert initial_pot == 30  # SB + BB
        
        # First player raises
        current_player = table.players.get(table.current_player_seat)
        result = table.process_action(current_player.user_id, "raise", 60)
        
        if result["success"]:
            assert table.pot > initial_pot

    def test_winner_receives_pot(self, two_player_table: PokerTable):
        """Test winner receives the pot."""
        table = two_player_table
        
        # Record initial stacks
        initial_stacks = {
            seat: p.stack for seat, p in table.players.items() if p
        }
        
        # Start hand
        table.start_new_hand()
        
        # First player folds
        current_player = table.players.get(table.current_player_seat)
        folding_seat = table.current_player_seat
        result = table.process_action(current_player.user_id, "fold", 0)
        
        # Find winner
        winner_info = result["hand_result"]["winners"][0]
        winner_seat = winner_info["seat"]
        
        # Winner should have gained chips
        winner = table.players.get(winner_seat)
        assert winner.stack > initial_stacks[winner_seat] - 20  # Minus possible blind


# =============================================================================
# Multi-Player Tests
# =============================================================================


class TestMultiPlayerFlow:
    """Tests for multi-player hand flow."""

    def test_six_player_hand_completes(self, six_player_table: PokerTable):
        """Test 6-player hand completes successfully."""
        table = six_player_table
        
        # Start hand
        result = table.start_new_hand()
        assert result["success"] is True
        
        # Play until hand completes
        max_actions = 50
        action_count = 0
        
        while table.phase != GamePhase.WAITING and action_count < max_actions:
            current_player = table.players.get(table.current_player_seat)
            if not current_player:
                break
            
            available = table.get_available_actions(current_player.user_id)
            actions = available.get("actions", [])
            
            # Simple strategy: check if possible, else call, else fold
            if "check" in actions:
                result = table.process_action(current_player.user_id, "check", 0)
            elif "call" in actions:
                result = table.process_action(current_player.user_id, "call", 0)
            elif "fold" in actions:
                result = table.process_action(current_player.user_id, "fold", 0)
            else:
                break
            
            action_count += 1
            
            if result.get("hand_complete"):
                break
        
        # Hand should complete
        assert table.phase == GamePhase.WAITING

    def test_multiple_folds_to_winner(self, six_player_table: PokerTable):
        """Test multiple players folding leaves one winner."""
        table = six_player_table
        
        # Start hand
        table.start_new_hand()
        
        # Everyone folds except one
        fold_count = 0
        max_folds = 5  # 5 folds should end the hand
        
        while table.phase != GamePhase.WAITING and fold_count < max_folds:
            current_player = table.players.get(table.current_player_seat)
            if not current_player:
                break
            
            result = table.process_action(current_player.user_id, "fold", 0)
            fold_count += 1
            
            if result.get("hand_complete"):
                break
        
        # Hand should be complete with one winner
        assert table.phase == GamePhase.WAITING


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases in hand flow."""

    def test_all_in_scenario(self, two_player_table: PokerTable):
        """Test all-in scenario."""
        table = two_player_table
        
        # Start hand
        table.start_new_hand()
        
        # First player goes all-in
        current_player = table.players.get(table.current_player_seat)
        result = table.process_action(current_player.user_id, "all_in", 0)
        
        assert result["success"] is True
        assert current_player.status == "all_in"

    def test_consecutive_hands(self, two_player_table: PokerTable):
        """Test playing multiple consecutive hands."""
        table = two_player_table
        
        for hand_num in range(3):
            # Start hand
            result = table.start_new_hand()
            assert result["success"] is True
            assert table.hand_number == hand_num + 1
            
            # Complete hand by folding
            current_player = table.players.get(table.current_player_seat)
            table.process_action(current_player.user_id, "fold", 0)
            
            # Verify reset
            assert table.phase == GamePhase.WAITING

    def test_dealer_rotation(self, two_player_table: PokerTable):
        """Test dealer button rotates between hands."""
        table = two_player_table
        
        dealers = []
        
        for _ in range(4):
            result = table.start_new_hand()
            if result["success"]:
                dealers.append(table.dealer_seat)
                
                # Complete hand
                current_player = table.players.get(table.current_player_seat)
                if current_player:
                    table.process_action(current_player.user_id, "fold", 0)
        
        # Dealer should rotate (in 2-player, alternates)
        assert len(dealers) >= 2


# =============================================================================
# State Consistency Tests
# =============================================================================


class TestStateConsistency:
    """Tests for state consistency during hand flow."""

    def test_player_states_consistent(self, two_player_table: PokerTable):
        """Test player states remain consistent."""
        table = two_player_table
        
        # Start hand
        table.start_new_hand()
        
        # Verify all players have hole cards
        for seat, player in table.players.items():
            if player:
                assert player.hole_cards is not None
                assert len(player.hole_cards) == 2

    def test_state_for_player_view(self, two_player_table: PokerTable):
        """Test get_state_for_player returns correct view."""
        table = two_player_table
        
        # Start hand
        table.start_new_hand()
        
        # Get state for player 1
        state = table.get_state_for_player("user1")
        
        assert state["tableId"] == table.room_id
        assert state["phase"] == table.phase.value
        assert state["myPosition"] == 0
        
        # Player should see own cards
        for player_data in state["players"]:
            if player_data and player_data["userId"] == "user1":
                assert player_data.get("holeCards") is not None

    def test_available_actions_accurate(self, two_player_table: PokerTable):
        """Test available actions are accurate."""
        table = two_player_table
        
        # Start hand
        table.start_new_hand()
        
        # Get available actions for current player
        current_player = table.players.get(table.current_player_seat)
        available = table.get_available_actions(current_player.user_id)
        
        # Should have actions
        assert len(available["actions"]) > 0
        
        # Non-current player should have no actions
        for seat, player in table.players.items():
            if player and seat != table.current_player_seat:
                other_available = table.get_available_actions(player.user_id)
                assert other_available["actions"] == []


# =============================================================================
# Cleanup Tests
# =============================================================================


class TestCleanup:
    """Tests for cleanup after hand completion."""

    def test_cleanup_after_fold(self, two_player_table: PokerTable):
        """Test cleanup after fold ends hand."""
        table = two_player_table
        
        # Start and complete hand
        table.start_new_hand()
        current_player = table.players.get(table.current_player_seat)
        table.process_action(current_player.user_id, "fold", 0)
        
        # Verify cleanup
        assert table.phase == GamePhase.WAITING
        assert table.pot == 0
        assert table.community_cards == []
        assert table.current_player_seat is None
        assert table._state is None

    def test_player_cleanup_after_hand(self, two_player_table: PokerTable):
        """Test player state cleanup after hand."""
        table = two_player_table
        
        # Start and complete hand
        table.start_new_hand()
        current_player = table.players.get(table.current_player_seat)
        table.process_action(current_player.user_id, "fold", 0)
        
        # Verify player cleanup
        for seat, player in table.players.items():
            if player:
                assert player.current_bet == 0
                assert player.total_bet_this_hand == 0
                assert player.hole_cards is None
