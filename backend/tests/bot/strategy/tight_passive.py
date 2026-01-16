"""Tight-passive strategy - plays few hands, rarely raises."""

from typing import TYPE_CHECKING

from tests.bot.strategy.base import Strategy

if TYPE_CHECKING:
    from app.engine.state import ActionRequest, TableState, ValidAction


class TightPassiveStrategy(Strategy):
    """Strategy that plays tight (few hands) and passive (rarely raises).
    
    Characteristics:
    - Only plays strong starting hands
    - Prefers checking and calling over betting and raising
    - Folds weak hands to aggression
    """

    def __init__(self, seed: int | None = None):
        """Initialize tight-passive strategy.
        
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
        """Make a tight-passive decision.
        
        Args:
            table_state: Current table state
            valid_actions: Available actions for this player
            position: Player's seat position
            
        Returns:
            ActionRequest favoring passive play
        """
        from app.engine.state import ActionType, GamePhase

        if not valid_actions:
            return self._make_action_request(ActionType.FOLD)

        action_types = {a.action_type for a in valid_actions}
        
        # Evaluate hand strength
        hand_strength = self._evaluate_hand_strength(table_state, position)
        
        # Preflop: only play strong hands
        if table_state.hand and table_state.hand.phase == GamePhase.PREFLOP:
            if hand_strength < 0.5:
                # Weak hand preflop
                if ActionType.CHECK in action_types:
                    return self._make_action_request(ActionType.CHECK)
                return self._make_action_request(ActionType.FOLD)

        # Post-flop: passive play
        if hand_strength > 0.7:
            # Strong hand - still prefer calling over raising
            if ActionType.CALL in action_types:
                action = self._get_action(valid_actions, ActionType.CALL)
                return self._make_action_request(ActionType.CALL, action.min_amount)
            elif ActionType.CHECK in action_types:
                return self._make_action_request(ActionType.CHECK)
            # Occasionally raise with very strong hands
            elif ActionType.RAISE in action_types and self.rng.random() < 0.2:
                action = self._get_action(valid_actions, ActionType.RAISE)
                return self._make_action_request(ActionType.RAISE, action.min_amount)
            elif ActionType.BET in action_types and self.rng.random() < 0.2:
                action = self._get_action(valid_actions, ActionType.BET)
                return self._make_action_request(ActionType.BET, action.min_amount)
                
        elif hand_strength > 0.4:
            # Medium hand - check/call
            if ActionType.CHECK in action_types:
                return self._make_action_request(ActionType.CHECK)
            elif ActionType.CALL in action_types:
                action = self._get_action(valid_actions, ActionType.CALL)
                # Only call small bets
                if action.min_amount and action.min_amount < 100:
                    return self._make_action_request(ActionType.CALL, action.min_amount)
                return self._make_action_request(ActionType.FOLD)
                
        else:
            # Weak hand - check/fold
            if ActionType.CHECK in action_types:
                return self._make_action_request(ActionType.CHECK)
            return self._make_action_request(ActionType.FOLD)

        # Fallback
        if ActionType.CHECK in action_types:
            return self._make_action_request(ActionType.CHECK)
        if ActionType.FOLD in action_types:
            return self._make_action_request(ActionType.FOLD)
            
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

        strength = 0.2

        # Pocket pairs
        if hole_cards[0].rank == hole_cards[1].rank:
            strength += 0.35
            if hole_cards[0].rank.value >= 10:
                strength += 0.2

        # High cards
        high_card = max(hole_cards[0].rank.value, hole_cards[1].rank.value)
        if high_card >= 12:  # Q, K, A
            strength += 0.15

        # Both high cards
        low_card = min(hole_cards[0].rank.value, hole_cards[1].rank.value)
        if low_card >= 10:
            strength += 0.1

        # Suited
        if hole_cards[0].suit == hole_cards[1].suit:
            strength += 0.08

        # Board interaction
        if community:
            for card in community:
                if card.rank == hole_cards[0].rank or card.rank == hole_cards[1].rank:
                    strength += 0.2

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
