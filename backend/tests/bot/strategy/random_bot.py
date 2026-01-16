"""Random strategy - makes random valid actions."""

from typing import TYPE_CHECKING

from tests.bot.strategy.base import Strategy

if TYPE_CHECKING:
    from app.engine.state import ActionRequest, TableState, ValidAction


class RandomStrategy(Strategy):
    """Strategy that makes random valid actions.
    
    Useful for stress testing and ensuring game handles all action types.
    """

    def __init__(self, seed: int | None = None):
        """Initialize random strategy.
        
        Args:
            seed: Random seed for reproducible behavior
        """
        super().__init__(seed=seed)

    def decide(
        self,
        table_state: "TableState",
        valid_actions: tuple["ValidAction", ...],
        position: int,
    ) -> "ActionRequest":
        """Make a random valid action.
        
        Args:
            table_state: Current table state
            valid_actions: Available actions for this player
            position: Player's seat position
            
        Returns:
            Random ActionRequest from valid options
        """
        from app.engine.state import ActionType

        if not valid_actions:
            # Fallback to fold if no valid actions (shouldn't happen)
            return self._make_action_request(ActionType.FOLD)

        # Pick a random action
        action = self.rng.choice(valid_actions)
        
        # Determine amount if needed
        amount = None
        if action.action_type in (ActionType.BET, ActionType.RAISE, ActionType.ALL_IN):
            if action.min_amount is not None and action.max_amount is not None:
                # Random amount between min and max
                amount = self.rng.randint(action.min_amount, action.max_amount)
            elif action.min_amount is not None:
                amount = action.min_amount
        elif action.action_type == ActionType.CALL:
            amount = action.min_amount

        return self._make_action_request(action.action_type, amount)
