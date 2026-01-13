"""
GameManager - Memory-based poker table management.

Manages all active poker tables in memory. This is a singleton that
provides thread-safe access to game tables.
"""

from typing import Dict, List, Optional
import asyncio

from app.game.poker_table import PokerTable


class GameManager:
    """Manages all active poker tables in memory."""

    def __init__(self):
        self._tables: Dict[str, PokerTable] = {}
        self._lock = asyncio.Lock()

    def create_table_sync(
        self,
        room_id: str,
        name: str,
        small_blind: int,
        big_blind: int,
        min_buy_in: int,
        max_buy_in: int,
        max_players: int = 9,
    ) -> PokerTable:
        """Create a new table (synchronous)."""
        table = PokerTable(
            room_id=room_id,
            name=name,
            small_blind=small_blind,
            big_blind=big_blind,
            min_buy_in=min_buy_in,
            max_buy_in=max_buy_in,
            max_players=max_players,
        )
        self._tables[room_id] = table
        return table

    async def create_table(
        self,
        room_id: str,
        name: str,
        small_blind: int,
        big_blind: int,
        min_buy_in: int,
        max_buy_in: int,
        max_players: int = 9,
    ) -> PokerTable:
        """Create a new table (async)."""
        async with self._lock:
            return self.create_table_sync(
                room_id, name, small_blind, big_blind,
                min_buy_in, max_buy_in, max_players
            )

    def get_table(self, room_id: str) -> Optional[PokerTable]:
        """Get a table by room ID."""
        return self._tables.get(room_id)

    def get_or_create_table(
        self,
        room_id: str,
        name: str,
        small_blind: int,
        big_blind: int,
        min_buy_in: int,
        max_buy_in: int,
        max_players: int = 9,
    ) -> PokerTable:
        """Get existing table or create new one."""
        if room_id in self._tables:
            return self._tables[room_id]

        return self.create_table_sync(
            room_id, name, small_blind, big_blind,
            min_buy_in, max_buy_in, max_players
        )

    async def remove_table(self, room_id: str) -> bool:
        """Remove a table."""
        async with self._lock:
            if room_id in self._tables:
                del self._tables[room_id]
                return True
            return False

    def get_all_tables(self) -> List[PokerTable]:
        """Get all active tables."""
        return list(self._tables.values())

    def get_table_count(self) -> int:
        """Get number of active tables."""
        return len(self._tables)

    def has_table(self, room_id: str) -> bool:
        """Check if table exists."""
        return room_id in self._tables

    def clear_all(self) -> None:
        """Clear all tables (for testing)."""
        self._tables.clear()

    def reset_table(self, room_id: str) -> Optional[PokerTable]:
        """Reset a table - remove all players/bots and reset game state."""
        table = self._tables.get(room_id)
        if not table:
            return None

        # 모든 플레이어 제거
        for seat in range(table.max_players):
            table.players[seat] = None

        # 게임 상태 초기화
        table.dealer_seat = -1
        table.hand_number = 0
        table.phase = table.phase.__class__.WAITING
        table.pot = 0
        table.community_cards = []
        table.current_player_seat = None
        table.current_bet = 0
        table._state = None
        table._seat_to_index = {}
        table._index_to_seat = {}
        table._hand_actions = []
        table._hand_starting_stacks = {}
        table._hand_start_time = None

        return table

    def remove_bots_from_table(self, room_id: str) -> int:
        """Remove all bots from a table. Returns count of removed bots."""
        table = self._tables.get(room_id)
        if not table:
            return 0

        removed = 0
        for seat in range(table.max_players):
            player = table.players.get(seat)
            if player and player.is_bot:
                table.players[seat] = None
                removed += 1

        return removed


# Singleton instance
game_manager = GameManager()
