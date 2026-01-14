"""
GameManager - Memory-based poker table management.

Manages all active poker tables in memory. This is a singleton that
provides thread-safe access to game tables.
"""

from typing import Awaitable, Callable, Dict, List, Optional
import asyncio
import logging

from app.game.poker_table import PokerTable

logger = logging.getLogger(__name__)


class GameManager:
    """Manages all active poker tables in memory."""

    def __init__(self):
        self._tables: Dict[str, PokerTable] = {}
        self._lock = asyncio.Lock()
        self._cleanup_callbacks: List[Callable[[str], Awaitable[None]]] = []

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

    def register_cleanup_callback(
        self,
        callback: Callable[[str], Awaitable[None]]
    ) -> None:
        """Register a callback to be called when a table is removed.
        
        Args:
            callback: Async function that takes room_id as parameter.
                     Will be called before the table is deleted.
        """
        self._cleanup_callbacks.append(callback)
        logger.debug(f"Registered cleanup callback: {callback.__name__ if hasattr(callback, '__name__') else callback}")

    async def remove_table(self, room_id: str) -> bool:
        """Remove a table and trigger cleanup callbacks."""
        async with self._lock:
            if room_id not in self._tables:
                return False
            
            # Trigger cleanup callbacks
            for callback in self._cleanup_callbacks:
                try:
                    await callback(room_id)
                except Exception as e:
                    logger.error(f"Cleanup callback failed for room {room_id}: {e}")
            
            del self._tables[room_id]
            logger.info(f"[CLEANUP] Table {room_id} removed")
            return True

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

    def force_phase_change(
        self,
        room_id: str,
        target_phase: str,
        community_cards: list[str] | None = None,
    ) -> dict:
        """Force phase change for a table.
        
        Args:
            room_id: Table ID
            target_phase: Target phase (preflop, flop, turn, river, showdown)
            community_cards: Optional community cards to set
            
        Returns:
            Result dict with success status and data
        """
        from app.game.poker_table import GamePhase
        import random
        
        table = self._tables.get(room_id)
        if not table:
            return {"success": False, "error": "Table not found"}
        
        # Map string to GamePhase enum
        phase_map = {
            "waiting": GamePhase.WAITING,
            "preflop": GamePhase.PREFLOP,
            "flop": GamePhase.FLOP,
            "turn": GamePhase.TURN,
            "river": GamePhase.RIVER,
            "showdown": GamePhase.SHOWDOWN,
        }
        
        if target_phase not in phase_map:
            return {"success": False, "error": f"Invalid phase: {target_phase}"}
        
        new_phase = phase_map[target_phase]
        old_phase = table.phase
        
        # Generate community cards if needed
        if community_cards:
            table.community_cards = community_cards
        else:
            # Auto-generate cards based on phase
            existing_cards = set(table.community_cards)
            
            # Add player hole cards to used cards
            for seat, player in table.players.items():
                if player and player.hole_cards:
                    existing_cards.update(player.hole_cards)
            
            all_cards = [
                f"{r}{s}" for r in "23456789TJQKA" for s in "hdcs"
            ]
            available_cards = [c for c in all_cards if c not in existing_cards]
            
            if target_phase == "flop" and len(table.community_cards) < 3:
                needed = 3 - len(table.community_cards)
                new_cards = random.sample(available_cards, needed)
                table.community_cards.extend(new_cards)
            elif target_phase == "turn" and len(table.community_cards) < 4:
                needed = 4 - len(table.community_cards)
                new_cards = random.sample(available_cards, needed)
                table.community_cards.extend(new_cards)
            elif target_phase == "river" and len(table.community_cards) < 5:
                needed = 5 - len(table.community_cards)
                new_cards = random.sample(available_cards, needed)
                table.community_cards.extend(new_cards)
            elif target_phase == "showdown" and len(table.community_cards) < 5:
                needed = 5 - len(table.community_cards)
                new_cards = random.sample(available_cards, needed)
                table.community_cards.extend(new_cards)
        
        # Update phase
        table.phase = new_phase
        
        # Reset current bets for new betting round (except preflop)
        if target_phase in ("flop", "turn", "river"):
            for seat, player in table.players.items():
                if player:
                    player.current_bet = 0
            table.current_bet = 0
        
        return {
            "success": True,
            "old_phase": old_phase.value,
            "new_phase": new_phase.value,
            "community_cards": table.community_cards,
        }

    def inject_cards(
        self,
        room_id: str,
        hole_cards: dict[int, list[str]] | None = None,
        community_cards: list[str] | None = None,
    ) -> dict:
        """Inject specific cards for testing.
        
        Args:
            room_id: Table ID
            hole_cards: Dict of seat -> [card1, card2]
            community_cards: List of community cards
            
        Returns:
            Result dict with success status
        """
        table = self._tables.get(room_id)
        if not table:
            return {"success": False, "error": "Table not found"}
        
        # Store injected cards for next hand
        if not hasattr(table, '_injected_cards'):
            table._injected_cards = {"hole_cards": {}, "community_cards": []}
        
        if hole_cards:
            table._injected_cards["hole_cards"] = hole_cards
        
        if community_cards:
            table._injected_cards["community_cards"] = community_cards
        
        # If game is in progress, apply immediately to players
        if table.phase != table.phase.__class__.WAITING and hole_cards:
            for seat, cards in hole_cards.items():
                player = table.players.get(seat)
                if player:
                    player.hole_cards = cards
        
        if table.phase != table.phase.__class__.WAITING and community_cards:
            table.community_cards = community_cards
        
        return {
            "success": True,
            "injected": table._injected_cards,
            "applied_immediately": table.phase != table.phase.__class__.WAITING,
        }

    def force_pot(
        self,
        room_id: str,
        main_pot: int,
        side_pots: list[dict] | None = None,
    ) -> dict:
        """Force pot amount for testing.
        
        Args:
            room_id: Table ID
            main_pot: Main pot amount
            side_pots: Optional list of side pots
            
        Returns:
            Result dict with success status
        """
        table = self._tables.get(room_id)
        if not table:
            return {"success": False, "error": "Table not found"}
        
        table.pot = main_pot
        
        # Store side pots if provided
        if side_pots:
            if not hasattr(table, '_side_pots'):
                table._side_pots = []
            table._side_pots = side_pots
        
        return {
            "success": True,
            "pot": table.pot,
            "side_pots": getattr(table, '_side_pots', []),
        }

    def start_hand_immediately(self, room_id: str) -> dict:
        """Start a new hand immediately.
        
        Args:
            room_id: Table ID
            
        Returns:
            Result dict with hand info
        """
        table = self._tables.get(room_id)
        if not table:
            return {"success": False, "error": "Table not found"}
        
        # Check if we have enough players
        active_players = table.get_active_players()
        if len(active_players) < 2:
            return {"success": False, "error": "Need at least 2 players to start"}
        
        # Force waiting state if needed
        if table.phase != table.phase.__class__.WAITING:
            table.phase = table.phase.__class__.WAITING
            table._state = None
            table.current_player_seat = None
            table.current_bet = 0
            table.pot = 0
            table.community_cards = []
        
        # Start the hand
        result = table.start_new_hand()
        
        # Apply injected cards if any
        if hasattr(table, '_injected_cards') and table._injected_cards:
            injected = table._injected_cards
            
            # Apply hole cards
            if injected.get("hole_cards"):
                for seat, cards in injected["hole_cards"].items():
                    player = table.players.get(int(seat))
                    if player:
                        player.hole_cards = cards
            
            # Apply community cards (store for later phases)
            if injected.get("community_cards"):
                table._pending_community_cards = injected["community_cards"]
            
            # Clear injected cards after use
            table._injected_cards = {"hole_cards": {}, "community_cards": []}
        
        return result

    def add_bot_player(
        self,
        room_id: str,
        position: int | None = None,
        stack: int = 1000,
        strategy: str = "random",
        username: str | None = None,
    ) -> dict:
        """Add a bot player to the table.
        
        Args:
            room_id: Table ID
            position: Seat position (None for auto)
            stack: Initial stack
            strategy: Bot strategy (random, tight, loose)
            username: Bot username (auto-generated if None)
            
        Returns:
            Result dict with bot info
        """
        from app.game.poker_table import Player
        import uuid
        
        table = self._tables.get(room_id)
        if not table:
            return {"success": False, "error": "Table not found"}
        
        # Find available seat
        if position is None:
            for seat in range(table.max_players):
                if table.players.get(seat) is None:
                    position = seat
                    break
            if position is None:
                return {"success": False, "error": "No available seats"}
        else:
            if table.players.get(position) is not None:
                return {"success": False, "error": f"Seat {position} is occupied"}
        
        # Validate stack
        if stack < table.min_buy_in:
            stack = table.min_buy_in
        if stack > table.max_buy_in:
            stack = table.max_buy_in
        
        # Create bot player
        bot_id = f"bot_{uuid.uuid4().hex[:8]}"
        bot_username = username or f"Bot_{position}"
        
        bot_player = Player(
            user_id=bot_id,
            username=bot_username,
            seat=position,
            stack=stack,
            is_bot=True,
        )
        
        # Store bot strategy
        if not hasattr(table, '_bot_strategies'):
            table._bot_strategies = {}
        table._bot_strategies[bot_id] = strategy
        
        # Seat the bot
        success = table.seat_player(position, bot_player)
        if not success:
            return {"success": False, "error": "Failed to seat bot"}
        
        return {
            "success": True,
            "bot_id": bot_id,
            "username": bot_username,
            "position": position,
            "stack": stack,
            "strategy": strategy,
        }

    def force_action(
        self,
        room_id: str,
        position: int,
        action: str,
        amount: int | None = None,
    ) -> dict:
        """Force a player action.
        
        Args:
            room_id: Table ID
            position: Player seat position
            action: Action to perform (fold, check, call, raise, all_in)
            amount: Amount for raise/bet
            
        Returns:
            Result dict with action result
        """
        table = self._tables.get(room_id)
        if not table:
            return {"success": False, "error": "Table not found"}
        
        player = table.players.get(position)
        if not player:
            return {"success": False, "error": f"No player at position {position}"}
        
        # Process the action
        result = table.process_action(player.user_id, action, amount or 0)
        
        return result

    def get_table_full_state(self, room_id: str) -> dict | None:
        """Get full table state for debugging.
        
        Args:
            room_id: Table ID
            
        Returns:
            Full table state dict or None
        """
        table = self._tables.get(room_id)
        if not table:
            return None
        
        players_data = []
        for seat in range(table.max_players):
            player = table.players.get(seat)
            if player:
                players_data.append({
                    "seat": seat,
                    "user_id": player.user_id,
                    "username": player.username,
                    "stack": player.stack,
                    "status": player.status,
                    "current_bet": player.current_bet,
                    "hole_cards": player.hole_cards,
                    "is_bot": player.is_bot,
                })
            else:
                players_data.append(None)
        
        return {
            "room_id": table.room_id,
            "name": table.name,
            "small_blind": table.small_blind,
            "big_blind": table.big_blind,
            "min_buy_in": table.min_buy_in,
            "max_buy_in": table.max_buy_in,
            "max_players": table.max_players,
            "phase": table.phase.value,
            "pot": table.pot,
            "community_cards": table.community_cards,
            "current_player_seat": table.current_player_seat,
            "current_bet": table.current_bet,
            "dealer_seat": table.dealer_seat,
            "hand_number": table.hand_number,
            "players": players_data,
        }

    def force_timeout(
        self,
        room_id: str,
        position: int | None = None,
    ) -> dict:
        """Force timeout for current player (triggers auto-fold).
        
        Args:
            room_id: Table ID
            position: Specific position to timeout (None for current turn)
            
        Returns:
            Result dict with action result
        """
        table = self._tables.get(room_id)
        if not table:
            return {"success": False, "error": "Table not found"}
        
        # Determine which position to timeout
        target_position = position if position is not None else table.current_player_seat
        
        if target_position is None:
            return {"success": False, "error": "No active turn to timeout"}
        
        player = table.players.get(target_position)
        if not player:
            return {"success": False, "error": f"No player at position {target_position}"}
        
        # Check if it's actually this player's turn
        if table.current_player_seat != target_position:
            return {
                "success": False,
                "error": f"Position {target_position} is not the current turn",
            }
        
        # Force fold action (timeout = auto-fold)
        result = table.process_action(player.user_id, "fold", 0)
        
        if result.get("success"):
            result["timeout"] = True
            result["timed_out_position"] = target_position
        
        return result

    def set_timer(
        self,
        room_id: str,
        remaining_seconds: int,
        paused: bool | None = None,
    ) -> dict:
        """Set timer value for current turn.
        
        Args:
            room_id: Table ID
            remaining_seconds: Remaining time in seconds
            paused: Whether to pause the timer
            
        Returns:
            Result dict with timer info
        """
        from datetime import datetime, timedelta
        
        table = self._tables.get(room_id)
        if not table:
            return {"success": False, "error": "Table not found"}
        
        if table.current_player_seat is None:
            return {"success": False, "error": "No active turn"}
        
        # Store timer override on table
        now = datetime.utcnow()
        deadline = now + timedelta(seconds=remaining_seconds)
        
        if not hasattr(table, '_timer_override'):
            table._timer_override = {}
        
        table._timer_override = {
            "remaining_seconds": remaining_seconds,
            "paused": paused if paused is not None else False,
            "deadline": deadline.isoformat(),
            "set_at": now.isoformat(),
            "position": table.current_player_seat,
        }
        
        return {
            "success": True,
            "position": table.current_player_seat,
            "remaining_seconds": remaining_seconds,
            "paused": table._timer_override["paused"],
            "deadline": table._timer_override["deadline"],
        }


# Singleton instance
game_manager = GameManager()
