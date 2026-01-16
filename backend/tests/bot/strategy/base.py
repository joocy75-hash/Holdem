"""Base strategy class for bot players."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.engine.state import ActionRequest, TableState, ValidAction


class Strategy(ABC):
    """Abstract base class for bot playing strategies.
    
    Strategies decide what action to take given the current game state
    and available actions.
    """

    def __init__(self, seed: int | None = None):
        """Initialize strategy with optional random seed.
        
        Args:
            seed: Random seed for reproducible behavior
        """
        self.seed = seed
        self._rng = None

    @property
    def rng(self):
        """Get random number generator, lazily initialized."""
        if self._rng is None:
            import random
            self._rng = random.Random(self.seed)
        return self._rng

    @abstractmethod
    def decide(
        self,
        table_state: "TableState",
        valid_actions: tuple["ValidAction", ...],
        position: int,
    ) -> "ActionRequest":
        """Decide which action to take.
        
        Args:
            table_state: Current table state
            valid_actions: Available actions for this player
            position: Player's seat position
            
        Returns:
            ActionRequest to execute
        """
        pass

    def _make_action_request(
        self,
        action_type: "ActionType",
        amount: int | None = None,
    ) -> "ActionRequest":
        """Helper to create an ActionRequest."""
        import uuid
        from app.engine.state import ActionRequest
        
        return ActionRequest(
            request_id=str(uuid.uuid4()),
            action_type=action_type,
            amount=amount,
        )
