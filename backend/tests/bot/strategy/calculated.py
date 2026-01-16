"""Calculated strategy - makes decisions based on hand strength and pot odds."""

from typing import TYPE_CHECKING

from tests.bot.strategy.base import Strategy

if TYPE_CHECKING:
    from app.engine.state import ActionRequest, TableState, ValidAction


class CalculatedStrategy(Strategy):
    """Strategy that makes calculated decisions based on hand strength.
    
    Uses basic poker logic:
    - Strong hands: bet/raise
    - Medium hands: call/check
    - Weak hands: check/fold
    """

    def __init__(
        self,
        aggression: float = 0.5,
        seed: int | None = None,
    ):
        """Initialize calculated strategy.
        
        Args:
            aggression: Aggression factor 0.0-1.0 (higher = more aggressive)
            seed: Random seed for reproducible behavior
        """
        super().__init__(seed=seed)
        self.aggression = max(0.0, min(1.0, aggression))

    def decide(
        self,
        table_state: "TableState",
        valid_actions: tuple["ValidAction", ...],
        position: int,
    ) -> "ActionRequest":
        """Make a calculated decision based on hand strength.
        
        Args:
            table_state: Current table state
            valid_actions: Available actions for this player
            position: Player's seat position
            
        Returns:
            ActionRequest based on hand evaluation
        """
        from app.engine.state import ActionType

        if not valid_actions:
            return self._make_action_request(ActionType.FOLD)

        # Get available action types
        action_types = {a.action_type for a in valid_actions}
        
        # Calculate hand strength (simplified)
        hand_strength = self._evaluate_hand_strength(table_state, position)
        
        # Add some randomness based on aggression
        adjusted_strength = hand_strength + (self.rng.random() * 0.2 - 0.1)
        adjusted_strength += self.aggression * 0.15
        
        # Decision logic
        if adjusted_strength > 0.7:
            # Strong hand - bet/raise
            if ActionType.RAISE in action_types:
                action = self._get_action(valid_actions, ActionType.RAISE)
                amount = self._calculate_raise_amount(action, adjusted_strength)
                return self._make_action_request(ActionType.RAISE, amount)
            elif ActionType.BET in action_types:
                action = self._get_action(valid_actions, ActionType.BET)
                amount = self._calculate_raise_amount(action, adjusted_strength)
                return self._make_action_request(ActionType.BET, amount)
            elif ActionType.CALL in action_types:
                action = self._get_action(valid_actions, ActionType.CALL)
                return self._make_action_request(ActionType.CALL, action.min_amount)
            elif ActionType.CHECK in action_types:
                return self._make_action_request(ActionType.CHECK)
                
        elif adjusted_strength > 0.4:
            # Medium hand - call/check
            if ActionType.CHECK in action_types:
                return self._make_action_request(ActionType.CHECK)
            elif ActionType.CALL in action_types:
                action = self._get_action(valid_actions, ActionType.CALL)
                return self._make_action_request(ActionType.CALL, action.min_amount)
            elif ActionType.FOLD in action_types:
                return self._make_action_request(ActionType.FOLD)
                
        else:
            # Weak hand - check/fold
            if ActionType.CHECK in action_types:
                return self._make_action_request(ActionType.CHECK)
            elif ActionType.FOLD in action_types:
                return self._make_action_request(ActionType.FOLD)
            elif ActionType.CALL in action_types:
                # Reluctant call with weak hand
                if self.rng.random() < 0.3:
                    action = self._get_action(valid_actions, ActionType.CALL)
                    return self._make_action_request(ActionType.CALL, action.min_amount)
                return self._make_action_request(ActionType.FOLD)

        # Fallback - pick first available action
        action = valid_actions[0]
        amount = action.min_amount if action.min_amount else None
        return self._make_action_request(action.action_type, amount)

    def _evaluate_hand_strength(
        self,
        table_state: "TableState",
        position: int,
    ) -> float:
        """Evaluate hand strength (0.0 - 1.0).
        
        Simplified evaluation based on hole cards and community cards.
        """
        if table_state.hand is None:
            return 0.5

        player_state = table_state.hand.get_player_state(position)
        if player_state is None or player_state.hole_cards is None:
            return 0.5

        hole_cards = player_state.hole_cards
        community = table_state.hand.community_cards

        # Basic hand strength calculation
        strength = 0.3  # Base strength

        # Check for pairs in hole cards
        if hole_cards[0].rank == hole_cards[1].rank:
            strength += 0.3
            # High pair bonus
            if hole_cards[0].rank.value >= 10:
                strength += 0.15

        # High cards bonus
        high_card_value = max(hole_cards[0].rank.value, hole_cards[1].rank.value)
        strength += (high_card_value - 2) / 24  # 0 to ~0.5

        # Suited bonus
        if hole_cards[0].suit == hole_cards[1].suit:
            strength += 0.1

        # Connected cards bonus
        rank_diff = abs(hole_cards[0].rank.value - hole_cards[1].rank.value)
        if rank_diff <= 2:
            strength += 0.05

        # Community card interaction (simplified)
        if community:
            for card in community:
                if card.rank == hole_cards[0].rank or card.rank == hole_cards[1].rank:
                    strength += 0.15  # Paired with board

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

    def _calculate_raise_amount(
        self,
        action: "ValidAction",
        strength: float,
    ) -> int:
        """Calculate raise amount based on hand strength."""
        if action.min_amount is None or action.max_amount is None:
            return action.min_amount or 0

        # Stronger hands = larger raises
        range_size = action.max_amount - action.min_amount
        raise_factor = strength * self.aggression
        
        amount = action.min_amount + int(range_size * raise_factor * self.rng.random())
        return max(action.min_amount, min(action.max_amount, amount))
