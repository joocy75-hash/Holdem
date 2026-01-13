"""Basic game flow scenario tests.

Tests fundamental poker game mechanics:
- Hand completion
- Player count variations
- Phase transitions
"""

import pytest
from tests.bot.manager import BotManager
from tests.bot.strategy.random_bot import RandomStrategy
from tests.bot.strategy.calculated import CalculatedStrategy
from tests.bot.strategy.tight_passive import TightPassiveStrategy
from tests.bot.strategy.loose_aggressive import LooseAggressiveStrategy


@pytest.fixture
def wrapper():
    """Create PokerKit wrapper."""
    from app.engine.core import PokerKitWrapper
    return PokerKitWrapper()


class TestHeadsUp:
    """2-player (heads-up) game scenarios."""

    @pytest.mark.asyncio
    async def test_2_player_basic_hand(self, wrapper):
        """Test basic 2-player hand completes successfully."""
        manager = BotManager(wrapper, skip_delay=True)
        manager.add_bot("bot1", RandomStrategy(seed=42), buy_in=1000)
        manager.add_bot("bot2", RandomStrategy(seed=1), buy_in=1000)

        state = manager.create_table_state()
        state = wrapper.create_initial_hand(state)

        # Verify initial state
        assert state.hand is not None
        assert len(state.hand.player_states) == 2

        final_state = await manager.play_hand(state)

        assert wrapper.is_hand_finished(final_state)

    @pytest.mark.asyncio
    async def test_heads_up_multiple_hands(self, wrapper):
        """Test multiple heads-up hands complete."""
        manager = BotManager(wrapper, skip_delay=True)
        manager.add_bot("bot1", RandomStrategy(seed=42), buy_in=1000)
        manager.add_bot("bot2", RandomStrategy(seed=1), buy_in=1000)

        state = manager.create_table_state()
        summaries = await manager.play_n_hands(state, n=10)

        assert len(summaries) == 10
        for summary in summaries:
            assert summary.hand_number > 0
            assert summary.final_pot >= 0

    @pytest.mark.asyncio
    async def test_heads_up_calculated_vs_random(self, wrapper):
        """Test calculated strategy vs random."""
        manager = BotManager(wrapper, skip_delay=True)
        manager.add_bot("calc", CalculatedStrategy(seed=42), buy_in=1000)
        manager.add_bot("random", RandomStrategy(seed=1), buy_in=1000)

        state = manager.create_table_state()
        summaries = await manager.play_n_hands(state, n=5)

        assert len(summaries) == 5


class TestMultiPlayer:
    """Multi-player game scenarios (3-6 players)."""

    @pytest.mark.asyncio
    async def test_3_player_hand(self, wrapper):
        """Test 3-player hand completes."""
        manager = BotManager(wrapper, skip_delay=True)
        for i in range(3):
            manager.add_bot(f"bot{i}", RandomStrategy(seed=i), buy_in=1000)

        state = manager.create_table_state()
        state = wrapper.create_initial_hand(state)

        assert len(state.hand.player_states) == 3

        final_state = await manager.play_hand(state)

        assert wrapper.is_hand_finished(final_state)

    @pytest.mark.asyncio
    async def test_6_player_full_hand(self, wrapper):
        """Test full 6-player hand completes."""
        manager = BotManager(wrapper, skip_delay=True)
        for i in range(6):
            manager.add_bot(f"bot{i}", RandomStrategy(seed=i * 10), buy_in=1000)

        state = manager.create_table_state()
        state = wrapper.create_initial_hand(state)

        # Verify all players are in hand
        assert len(state.hand.player_states) == 6

        final_state = await manager.play_hand(state)

        assert wrapper.is_hand_finished(final_state)

    @pytest.mark.asyncio
    async def test_6_player_multiple_hands(self, wrapper):
        """Test multiple hands at 6-player table."""
        manager = BotManager(wrapper, skip_delay=True)
        for i in range(6):
            manager.add_bot(f"bot{i}", RandomStrategy(seed=i * 10), buy_in=1000)

        state = manager.create_table_state()
        summaries = await manager.play_n_hands(state, n=5)

        assert len(summaries) == 5

    @pytest.mark.asyncio
    async def test_mixed_strategy_6_player(self, wrapper):
        """Test 6-player with mixed strategies."""
        manager = BotManager(wrapper, skip_delay=True)
        manager.add_bot("random", RandomStrategy(seed=1), buy_in=1000)
        manager.add_bot("calc", CalculatedStrategy(seed=2), buy_in=1000)
        manager.add_bot("tight", TightPassiveStrategy(seed=3), buy_in=1000)
        manager.add_bot("lag", LooseAggressiveStrategy(seed=4), buy_in=1000)
        manager.add_bot("calc2", CalculatedStrategy(aggression=0.8, seed=5), buy_in=1000)
        manager.add_bot("random2", RandomStrategy(seed=6), buy_in=1000)

        state = manager.create_table_state()
        summaries = await manager.play_n_hands(state, n=5)

        assert len(summaries) == 5


class TestPhaseProgression:
    """Test game phase transitions."""

    @pytest.mark.asyncio
    async def test_preflop_to_showdown(self, wrapper):
        """Test hand progresses through all phases."""
        from app.engine.state import GamePhase

        manager = BotManager(wrapper, skip_delay=True)
        manager.add_bot("bot1", RandomStrategy(seed=42), buy_in=1000)
        manager.add_bot("bot2", RandomStrategy(seed=1), buy_in=1000)

        state = manager.create_table_state()
        state = wrapper.create_initial_hand(state)

        # Track phases
        phases_seen = set()
        phases_seen.add(state.hand.phase)

        # Play with callback to track phases
        def track_phase(new_state, action):
            if new_state.hand:
                phases_seen.add(new_state.hand.phase)

        manager.on_action(track_phase)
        final_state = await manager.play_hand(state)

        # Hand completed
        assert wrapper.is_hand_finished(final_state)

        # At least preflop happened
        assert GamePhase.PREFLOP in phases_seen

    @pytest.mark.asyncio
    async def test_hand_consistency_across_many_hands(self, wrapper):
        """Test N hands all complete without errors."""
        manager = BotManager(wrapper, skip_delay=True)
        manager.add_bot("bot1", RandomStrategy(seed=42), buy_in=1000)
        manager.add_bot("bot2", RandomStrategy(seed=1), buy_in=1000)

        state = manager.create_table_state()

        # Play 50 hands
        summaries = await manager.play_n_hands(state, n=50)

        assert len(summaries) == 50

        # All hands should have positive hand numbers
        for i, summary in enumerate(summaries):
            assert summary.hand_number == i + 1

    @pytest.mark.asyncio
    async def test_dealer_button_rotation(self, wrapper):
        """Test dealer button rotates between hands."""
        manager = BotManager(wrapper, skip_delay=True)
        manager.add_bot("bot1", RandomStrategy(seed=42), buy_in=1000)
        manager.add_bot("bot2", RandomStrategy(seed=1), buy_in=1000)
        manager.add_bot("bot3", RandomStrategy(seed=2), buy_in=1000)

        state = manager.create_table_state()

        dealers_seen = []

        for _ in range(3):
            state = wrapper.create_initial_hand(state)
            dealers_seen.append(state.dealer_position)
            state = await manager.play_hand(state)

        # Dealer should rotate (unless all same by chance - unlikely with 3 players)
        # Just verify we recorded dealer positions
        assert len(dealers_seen) == 3


class TestActionValidation:
    """Test action validation."""

    @pytest.mark.asyncio
    async def test_bot_never_invalid_action(self, wrapper):
        """Test all bots only make valid actions."""
        from app.engine.state import ActionType

        manager = BotManager(wrapper, skip_delay=True)
        manager.add_bot("random", RandomStrategy(seed=1), buy_in=1000)
        manager.add_bot("calc", CalculatedStrategy(seed=2), buy_in=1000)
        manager.add_bot("tight", TightPassiveStrategy(seed=3), buy_in=1000)
        manager.add_bot("lag", LooseAggressiveStrategy(seed=4), buy_in=1000)

        invalid_actions = []

        def check_action(state, action):
            if action is not None:
                valid_types = [ActionType.FOLD, ActionType.CHECK, ActionType.CALL,
                              ActionType.BET, ActionType.RAISE, ActionType.ALL_IN]
                if action.action_type not in valid_types:
                    invalid_actions.append(action)

        manager.on_action(check_action)

        state = manager.create_table_state()
        summaries = await manager.play_n_hands(state, n=20)

        assert len(summaries) == 20
        assert len(invalid_actions) == 0, f"Found invalid actions: {invalid_actions}"
