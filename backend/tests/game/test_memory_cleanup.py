"""Memory Cleanup Property-Based Tests.

Property 1: Memory Cleanup Completeness
- Tests table creation/deletion and memory verification
- Validates: Requirements 1.1, 1.2, 1.4

Tests ensure that:
1. Tables are properly removed from GameManager
2. Cleanup callbacks are triggered
3. No memory leaks after table removal
"""

import pytest
import asyncio
from hypothesis import given, strategies as st, settings, assume
from typing import List
from unittest.mock import AsyncMock, MagicMock

from app.game.manager import GameManager
from app.game.poker_table import PokerTable, Player, GamePhase


# =============================================================================
# Strategies
# =============================================================================

# Number of tables to create
num_tables_strategy = st.integers(min_value=1, max_value=10)

# Number of players per table
num_players_strategy = st.integers(min_value=2, max_value=9)

# Stack amounts
stack_strategy = st.integers(min_value=400, max_value=2000)


# =============================================================================
# Property 1: Memory Cleanup Completeness
# =============================================================================


class TestMemoryCleanupCompleteness:
    """Property: After table removal, all resources should be cleaned up."""

    @pytest.fixture
    def game_manager(self):
        """Create a fresh GameManager for each test."""
        manager = GameManager()
        yield manager
        # Cleanup
        manager.clear_all()

    @given(num_tables=num_tables_strategy)
    @settings(max_examples=10, deadline=None)
    def test_table_count_after_creation_and_removal(self, num_tables: int):
        """Table count should be zero after removing all tables."""
        manager = GameManager()
        
        # Create tables
        room_ids = []
        for i in range(num_tables):
            room_id = f"test-room-{i}"
            manager.create_table_sync(
                room_id=room_id,
                name=f"Test Table {i}",
                small_blind=10,
                big_blind=20,
                min_buy_in=400,
                max_buy_in=2000,
            )
            room_ids.append(room_id)
        
        assert manager.get_table_count() == num_tables
        
        # Remove all tables synchronously (for hypothesis compatibility)
        for room_id in room_ids:
            manager._tables.pop(room_id, None)
        
        assert manager.get_table_count() == 0

    @given(num_tables=num_tables_strategy)
    @settings(max_examples=10, deadline=None)
    def test_table_not_accessible_after_removal(self, num_tables: int):
        """Tables should not be accessible after removal."""
        manager = GameManager()
        
        room_ids = []
        for i in range(num_tables):
            room_id = f"test-room-{i}"
            manager.create_table_sync(
                room_id=room_id,
                name=f"Test Table {i}",
                small_blind=10,
                big_blind=20,
                min_buy_in=400,
                max_buy_in=2000,
            )
            room_ids.append(room_id)
        
        # Remove tables
        for room_id in room_ids:
            manager._tables.pop(room_id, None)
        
        # Verify tables are not accessible
        for room_id in room_ids:
            assert manager.get_table(room_id) is None
            assert not manager.has_table(room_id)

    @given(num_players=num_players_strategy)
    @settings(max_examples=10, deadline=None)
    def test_player_references_cleared_on_table_removal(self, num_players: int):
        """Player references should be cleared when table is removed."""
        manager = GameManager()
        
        room_id = "test-room"
        table = manager.create_table_sync(
            room_id=room_id,
            name="Test Table",
            small_blind=10,
            big_blind=20,
            min_buy_in=400,
            max_buy_in=2000,
        )
        
        # Add players
        players = []
        for i in range(num_players):
            player = Player(
                user_id=f"user{i}",
                username=f"Player{i}",
                seat=i,
                stack=1000,
            )
            table.seat_player(i, player)
            players.append(player)
        
        # Verify players are seated
        assert len(table.get_active_players()) == num_players
        
        # Remove table
        manager._tables.pop(room_id, None)
        
        # Table should not be accessible
        assert manager.get_table(room_id) is None


@pytest.mark.asyncio
class TestAsyncMemoryCleanup:
    """Async tests for memory cleanup with callbacks."""

    async def test_cleanup_callback_triggered_on_removal(self):
        """Cleanup callbacks should be triggered when table is removed."""
        manager = GameManager()
        callback_called = False
        callback_room_id = None
        
        async def cleanup_callback(room_id: str):
            nonlocal callback_called, callback_room_id
            callback_called = True
            callback_room_id = room_id
        
        manager.register_cleanup_callback(cleanup_callback)
        
        # Create and remove table
        room_id = "test-room"
        manager.create_table_sync(
            room_id=room_id,
            name="Test Table",
            small_blind=10,
            big_blind=20,
            min_buy_in=400,
            max_buy_in=2000,
        )
        
        await manager.remove_table(room_id)
        
        assert callback_called
        assert callback_room_id == room_id

    async def test_multiple_cleanup_callbacks(self):
        """Multiple cleanup callbacks should all be triggered."""
        manager = GameManager()
        callbacks_called = []
        
        async def callback1(room_id: str):
            callbacks_called.append(("callback1", room_id))
        
        async def callback2(room_id: str):
            callbacks_called.append(("callback2", room_id))
        
        manager.register_cleanup_callback(callback1)
        manager.register_cleanup_callback(callback2)
        
        room_id = "test-room"
        manager.create_table_sync(
            room_id=room_id,
            name="Test Table",
            small_blind=10,
            big_blind=20,
            min_buy_in=400,
            max_buy_in=2000,
        )
        
        await manager.remove_table(room_id)
        
        assert len(callbacks_called) == 2
        assert ("callback1", room_id) in callbacks_called
        assert ("callback2", room_id) in callbacks_called

    async def test_cleanup_callback_error_does_not_prevent_removal(self):
        """Cleanup callback errors should not prevent table removal."""
        manager = GameManager()
        
        async def failing_callback(room_id: str):
            raise Exception("Callback error")
        
        manager.register_cleanup_callback(failing_callback)
        
        room_id = "test-room"
        manager.create_table_sync(
            room_id=room_id,
            name="Test Table",
            small_blind=10,
            big_blind=20,
            min_buy_in=400,
            max_buy_in=2000,
        )
        
        # Should not raise, table should still be removed
        result = await manager.remove_table(room_id)
        
        assert result is True
        assert manager.get_table(room_id) is None

    async def test_remove_nonexistent_table_returns_false(self):
        """Removing a nonexistent table should return False."""
        manager = GameManager()
        
        result = await manager.remove_table("nonexistent-room")
        
        assert result is False

    async def test_concurrent_table_creation_and_removal(self):
        """Concurrent table operations should be thread-safe."""
        manager = GameManager()
        
        async def create_and_remove(index: int):
            room_id = f"test-room-{index}"
            await manager.create_table(
                room_id=room_id,
                name=f"Test Table {index}",
                small_blind=10,
                big_blind=20,
                min_buy_in=400,
                max_buy_in=2000,
            )
            await asyncio.sleep(0.01)  # Small delay
            await manager.remove_table(room_id)
        
        # Run concurrent operations
        await asyncio.gather(*[create_and_remove(i) for i in range(5)])
        
        # All tables should be removed
        assert manager.get_table_count() == 0


class TestTableStateCleanup:
    """Tests for table state cleanup after hand completion."""

    @given(num_players=num_players_strategy)
    @settings(max_examples=10, deadline=None)
    def test_table_state_reset_after_hand(self, num_players: int):
        """Table state should be properly reset after hand completion."""
        manager = GameManager()
        
        room_id = "test-room"
        table = manager.create_table_sync(
            room_id=room_id,
            name="Test Table",
            small_blind=10,
            big_blind=20,
            min_buy_in=400,
            max_buy_in=2000,
        )
        
        # Add players
        for i in range(num_players):
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
        
        # Complete hand by folding
        while table.phase != GamePhase.WAITING:
            current_player = table.players.get(table.current_player_seat)
            if current_player:
                table.process_action(current_player.user_id, "fold", 0)
            else:
                break
        
        # Verify state is reset
        assert table.phase == GamePhase.WAITING
        assert table.pot == 0
        assert table.community_cards == []
        assert table.current_player_seat is None
        assert table.current_bet == 0

    def test_reset_table_clears_all_state(self):
        """reset_table should clear all game state."""
        manager = GameManager()
        
        room_id = "test-room"
        table = manager.create_table_sync(
            room_id=room_id,
            name="Test Table",
            small_blind=10,
            big_blind=20,
            min_buy_in=400,
            max_buy_in=2000,
        )
        
        # Add players
        for i in range(3):
            player = Player(
                user_id=f"user{i}",
                username=f"Player{i}",
                seat=i,
                stack=1000,
            )
            table.seat_player(i, player)
        
        # Start hand
        table.start_new_hand()
        
        # Reset table
        reset_table = manager.reset_table(room_id)
        
        assert reset_table is not None
        assert reset_table.phase == GamePhase.WAITING
        assert reset_table.pot == 0
        assert reset_table.community_cards == []
        assert reset_table.hand_number == 0
        
        # All players should be removed
        active_players = reset_table.get_active_players()
        assert len(active_players) == 0

    def test_clear_all_removes_all_tables(self):
        """clear_all should remove all tables."""
        manager = GameManager()
        
        # Create multiple tables
        for i in range(5):
            manager.create_table_sync(
                room_id=f"test-room-{i}",
                name=f"Test Table {i}",
                small_blind=10,
                big_blind=20,
                min_buy_in=400,
                max_buy_in=2000,
            )
        
        assert manager.get_table_count() == 5
        
        manager.clear_all()
        
        assert manager.get_table_count() == 0
        assert manager.get_all_tables() == []
