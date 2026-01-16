"""Loose-aggressive strategy - plays many hands aggressively."""

from typing import TYPE_CHECKING

from tests.bot.strategy.base import Strategy

if TYPE_CHECKING:
    from app.engine.state import ActionRequest, TableState, ValidAction


class LooseAggressiveStrategy(Strategy):
    """Strategy that plays loose (many hands) and aggressive (lots of raises).
    
    Characteristics:
    - Plays a wide range of starting hands
    - Frequently bets and raises
    - Applies pressure with bluffs
    - Goes all-in more often
    """

    def __init__(self, seed: int | None = None):
        """Initialize loose-aggressive strategy.
        
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
        """Make a loose-aggressive decision.
        
        Args:
            table_state: Current table state
            valid_actions: Available actions for this player
            position: Player's seat position
            
        Returns:
            ActionRequest favoring aggressive play
        """
        from app.engine.state import ActionType

        if not valid_actions:
            return self._make_action_request(ActionType.FOLD)

        action_types = {a.action_type for a in valid_actions}
        
        # Evaluate hand strength
        hand_strength = self._evaluate_hand_strength(table_state, position)
        
        # Add aggression factor - LAG plays more hands aggressively
        aggression_roll = self.rng.random()
        
        # Strong hand or feeling aggressive
        if hand_strength > 0.5 or aggression_roll > 0.6:
            # Prefer raising/betting
            if ActionType.ALL_IN in action_types and (hand_strength > 0.8 or aggression_roll > 0.9):
                action = self._get_action(valid_actions, ActionType.ALL_IN)
                return self._make_action_request(ActionType.ALL_IN, action.max_amount)
            elif ActionType.RAISE in action_types:
                action = self._get_action(valid_actions, ActionType.RAISE)
                amount = self._calculate_aggressive_raise(action, hand_strength)
                return self._make_action_request(ActionType.RAISE, amount)
            elif ActionType.BET in action_types:
                action = self._get_action(valid_actions, ActionType.BET)
                amount = self._calculate_aggressive_raise(action, hand_strength)
                return self._make_action_request(ActionType.BET, amount)
            elif ActionType.CALL in action_types:
                action = self._get_action(valid_actions, ActionType.CALL)
                return self._make_action_request(ActionType.CALL, action.min_amount)
            elif ActionType.CHECK in action_types:
                return self._make_action_request(ActionType.CHECK)
                
        elif hand_strength > 0.3 or aggression_roll > 0.4:
            # Medium hand - still aggressive
            if ActionType.BET in action_types and self.rng.random() > 0.3:
                action = self._get_action(valid_actions, ActionType.BET)
                return self._make_action_request(ActionType.BET, action.min_amount)
            elif ActionType.RAISE in action_types and self.rng.random() > 0.5:
                action = self._get_action(valid_actions, ActionType.RAISE)
                return self._make_action_request(ActionType.RAISE, action.min_amount)
            elif ActionType.CALL in action_types:
                action = self._get_action(valid_actions, ActionType.CALL)
                return self._make_action_request(ActionType.CALL, action.min_amount)
            elif ActionType.CHECK in action_types:
                return self._make_action_request(ActionType.CHECK)
                
        else:
            # Weak hand - occasional bluff
            if self.rng.random() > 0.7:
                # Bluff!
                if ActionType.BET in action_types:
                    action = self._get_action(valid_actions, ActionType.BET)
                    return self._make_action_request(ActionType.BET, action.min_amount)
                elif ActionType.RAISE in action_types:
                    action = self._get_action(valid_actions, ActionType.RAISE)
                    return self._make_action_request(ActionType.RAISE, action.min_amount)
            
            if ActionType.CHECK in action_types:
                return self._make_action_request(ActionType.CHECK)
            return self._make_action_request(ActionType.FOLD)

        # Fallback
        if ActionType.CHECK in action_types:
            return self._make_action_request(ActionType.CHECK)
        if ActionType.CALL in action_types:
            action = self._get_action(valid_actions, ActionType.CALL)
            return self._make_action_request(ActionType.CALL, action.min_amount)
            
        action = valid_actions[0]
        amount = action.min_amount if action.min_amount else None
        return self._make_action_request(action.action_type, amount)

    def _evaluate_hand_strength(
        self,
        table_state: "TableState",
        position: int,
    ) -> float:
        """Evaluate hand strength (0.0 - 1.0)."""
        if table_state.hand is None:
            return 0.5

        player_state = table_state.hand.get_player_state(position)
        if player_state is None or player_state.hole_cards is None:
            return 0.5

        hole_cards = player_state.hole_cards
        community = table_state.hand.community_cards

        strength = 0.25  # LAG starts with higher base

        # Pocket pairs
        if hole_cards[0].rank == hole_cards[1].rank:
            strength += 0.3
            if hole_cards[0].rank.value >= 10:
                strength += 0.15

        # High cards
        high_card = max(hole_cards[0].rank.value, hole_cards[1].rank.value)
        strength += (high_card - 2) / 30

        # Suited
        if hole_cards[0].suit == hole_cards[1].suit:
            strength += 0.1

        # Connected
        rank_diff = abs(hole_cards[0].rank.value - hole_cards[1].rank.value)
        if rank_diff <= 3:
            strength += 0.08

        # Board interaction
        if community:
            for card in community:
                if card.rank == hole_cards[0].rank or card.rank == hole_cards[1].rank:
                    strength += 0.18

        return min(1.0, max(0.0, strength))

    def _get_action(
        self,
        valid_actions: tuple["ValidAction", ...],
        action_type: "ActionType",
    ) -> "ValidAction":
        """Get specific action from valid actions."""
        for action in valid_actions:
            if action.action_type == action_type:
                return action
        return valid_actions[0]

    def _calculate_aggressive_raise(
        self,
        action: "ValidAction",
        strength: float,
    ) -> int:
        """Calculate aggressive raise amount."""
        if action.min_amount is None or action.max_amount is None:
            return action.min_amount or 0

        # LAG raises bigger
        range_size = action.max_amount - action.min_amount
        
        # Higher strength = bigger raise, but always at least 50% of range
        raise_factor = 0.5 + (strength * 0.5)
        raise_factor *= (0.8 + self.rng.random() * 0.4)  # Add variance
        
        amount = action.min_amount + int(range_size * raise_factor)
        return max(action.min_amount, min(action.max_amount, amount))
