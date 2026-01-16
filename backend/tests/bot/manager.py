"""Bot manager for running automated poker games.

Provides infrastructure for running bots with various strategies
against each other for scenario testing.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from app.engine.core import PokerKitWrapper
    from app.engine.state import PlayerAction, TableState
    from tests.bot.strategy.base import Strategy


@dataclass
class HandSummary:
    """Summary of a completed hand."""
    
    hand_number: int
    final_pot: int
    winner_positions: tuple[int, ...]
    actions_count: int


@dataclass
class BotPlayer:
    """A bot player with a strategy."""
    
    name: str
    strategy: "Strategy"
    buy_in: int
    position: int | None = None


class BotManager:
    """Manages bot players and runs automated games.
    
    Provides methods to:
    - Add bots with different strategies
    - Create table state with bots seated
    - Play hands automatically
    - Track game progress via callbacks
    """

    def __init__(
        self,
        wrapper: "PokerKitWrapper",
        skip_delay: bool = False,
    ):
        """Initialize bot manager.
        
        Args:
            wrapper: PokerKit wrapper instance
            skip_delay: If True, skip artificial delays between actions
        """
        self.wrapper = wrapper
        self.skip_delay = skip_delay
        self.bots: list[BotPlayer] = []
        self._action_callbacks: list[Callable[["TableState", "PlayerAction | None"], None]] = []

    def add_bot(
        self,
        name: str,
        strategy: "Strategy",
        buy_in: int,
    ) -> None:
        """Add a bot player.
        
        Args:
            name: Bot name/identifier
            strategy: Playing strategy
            buy_in: Initial chip stack
        """
        self.bots.append(BotPlayer(
            name=name,
            strategy=strategy,
            buy_in=buy_in,
        ))

    def on_action(
        self,
        callback: Callable[["TableState", "PlayerAction | None"], None],
    ) -> None:
        """Register callback for action events.
        
        Args:
            callback: Function called with (new_state, action) after each action
        """
        self._action_callbacks.append(callback)

    def create_table_state(
        self,
        small_blind: int = 10,
        big_blind: int = 20,
    ) -> "TableState":
        """Create initial table state with bots seated.
        
        Args:
            small_blind: Small blind amount
            big_blind: Big blind amount
            
        Returns:
            TableState with all bots seated
        """
        from app.engine.state import (
            Player,
            SeatState,
            SeatStatus,
            TableConfig,
            TableState,
        )

        if len(self.bots) < 2:
            raise ValueError("Need at least 2 bots to create a table")

        # Create table config
        config = TableConfig(
            max_seats=max(6, len(self.bots)),
            small_blind=small_blind,
            big_blind=big_blind,
            min_buy_in=big_blind * 10,
            max_buy_in=big_blind * 100,
        )

        # Create seats with bots
        seats = []
        for i, bot in enumerate(self.bots):
            bot.position = i
            player = Player(
                user_id=f"bot_{bot.name}",
                nickname=bot.name,
            )
            seat = SeatState(
                position=i,
                player=player,
                stack=bot.buy_in,
                status=SeatStatus.ACTIVE,
            )
            seats.append(seat)

        # Fill remaining seats as empty
        for i in range(len(self.bots), config.max_seats):
            seats.append(SeatState(
                position=i,
                player=None,
                stack=0,
                status=SeatStatus.EMPTY,
            ))

        return TableState(
            table_id="test_table",
            config=config,
            seats=tuple(seats),
            hand=None,
            dealer_position=0,
            state_version=0,
            updated_at=datetime.utcnow(),
        )

    async def play_hand(self, state: "TableState") -> "TableState":
        """Play a single hand to completion.
        
        Args:
            state: Table state with hand initialized
            
        Returns:
            Final table state after hand completes
        """
        if state.hand is None:
            raise ValueError("No hand to play - call create_initial_hand first")

        max_actions = 1000  # Safety limit
        action_count = 0

        while not self.wrapper.is_hand_finished(state) and action_count < max_actions:
            current_turn = state.hand.current_turn
            if current_turn is None:
                break

            # Find bot at current position
            bot = self._get_bot_at_position(current_turn)
            if bot is None:
                raise ValueError(f"No bot at position {current_turn}")

            # Get valid actions
            valid_actions = self.wrapper.get_valid_actions(state, current_turn)
            if not valid_actions:
                break

            # Get bot's decision
            action_request = bot.strategy.decide(state, valid_actions, current_turn)

            # Apply action
            try:
                state, player_action = self.wrapper.apply_action(
                    state, current_turn, action_request
                )
                action_count += 1

                # Notify callbacks
                for callback in self._action_callbacks:
                    callback(state, player_action)

            except Exception as e:
                # Log error but try to continue
                import logging
                logging.warning(f"Action failed: {e}, trying fold")
                
                # Try to fold as fallback
                from app.engine.state import ActionRequest, ActionType
                import uuid
                fold_request = ActionRequest(
                    request_id=str(uuid.uuid4()),
                    action_type=ActionType.FOLD,
                )
                try:
                    state, player_action = self.wrapper.apply_action(
                        state, current_turn, fold_request
                    )
                    action_count += 1
                except Exception:
                    # If fold fails too, check is available
                    check_request = ActionRequest(
                        request_id=str(uuid.uuid4()),
                        action_type=ActionType.CHECK,
                    )
                    state, player_action = self.wrapper.apply_action(
                        state, current_turn, check_request
                    )
                    action_count += 1

        return state

    async def play_n_hands(
        self,
        state: "TableState",
        n: int,
    ) -> list[HandSummary]:
        """Play multiple hands.
        
        Args:
            state: Initial table state
            n: Number of hands to play
            
        Returns:
            List of HandSummary for each completed hand
        """
        summaries = []
        current_state = state

        for hand_num in range(n):
            # Update stacks from previous hand results
            current_state = self._update_stacks_from_state(current_state)
            
            # Check if we have enough players with chips
            active_count = sum(
                1 for seat in current_state.seats
                if seat.player is not None and seat.stack > 0
            )
            if active_count < 2:
                # Rebuy all bots
                current_state = self._rebuy_all_bots(current_state)

            # Create new hand
            try:
                current_state = self.wrapper.create_initial_hand(current_state)
            except ValueError:
                # Not enough players - rebuy and retry
                current_state = self._rebuy_all_bots(current_state)
                current_state = self.wrapper.create_initial_hand(current_state)

            # Track actions for this hand
            actions_this_hand = [0]
            
            def count_action(s, a):
                actions_this_hand[0] += 1
            
            self._action_callbacks.append(count_action)

            # Play the hand
            final_state = await self.play_hand(current_state)

            # Remove counter callback
            self._action_callbacks.remove(count_action)

            # Extract results
            pot_total = 0
            winner_positions = []
            
            if final_state.hand:
                pot_total = final_state.hand.pot.total
                
                # Try to get winners from hand result
                try:
                    result = self.wrapper.evaluate_hand(final_state)
                    winner_positions = tuple(w.position for w in result.winners)
                except Exception:
                    winner_positions = ()

            summaries.append(HandSummary(
                hand_number=hand_num + 1,
                final_pot=pot_total,
                winner_positions=winner_positions,
                actions_count=actions_this_hand[0],
            ))

            current_state = final_state

        return summaries

    def _get_bot_at_position(self, position: int) -> BotPlayer | None:
        """Get bot at given seat position."""
        for bot in self.bots:
            if bot.position == position:
                return bot
        return None

    def _update_stacks_from_state(self, state: "TableState") -> "TableState":
        """Update bot stacks from current state."""
        from dataclasses import replace
        from app.engine.state import SeatState, SeatStatus

        new_seats = []
        for seat in state.seats:
            if seat.player is not None:
                # Find corresponding bot
                bot = self._get_bot_at_position(seat.position)
                if bot:
                    # Update status based on stack
                    status = SeatStatus.ACTIVE if seat.stack > 0 else SeatStatus.SITTING_OUT
                    new_seats.append(replace(seat, status=status))
                else:
                    new_seats.append(seat)
            else:
                new_seats.append(seat)

        return replace(
            state,
            seats=tuple(new_seats),
            hand=None,  # Clear hand for next round
        )

    def _rebuy_all_bots(self, state: "TableState") -> "TableState":
        """Rebuy all bots to their original buy-in."""
        from dataclasses import replace
        from app.engine.state import SeatStatus

        new_seats = []
        for seat in state.seats:
            if seat.player is not None:
                bot = self._get_bot_at_position(seat.position)
                if bot:
                    new_seats.append(replace(
                        seat,
                        stack=bot.buy_in,
                        status=SeatStatus.ACTIVE,
                    ))
                else:
                    new_seats.append(seat)
            else:
                new_seats.append(seat)

        return replace(
            state,
            seats=tuple(new_seats),
            hand=None,
        )
