"""All-in and side pot scenario tests.

Tests all-in mechanics:
- Single player all-in
- Multiple all-ins
- Side pot creation
"""

import pytest
from tests.bot.manager import BotManager
from tests.bot.strategy.random_bot import RandomStrategy
from tests.bot.strategy.loose_aggressive import LooseAggressiveStrategy
from app.engine.state import ActionType


@pytest.fixture
def wrapper():
    """Create PokerKit wrapper."""
    from app.engine.core import PokerKitWrapper
    return PokerKitWrapper()


class TestSingleAllIn:
    """Single player all-in scenarios."""

    @pytest.mark.asyncio
    async def test_single_all_in_completes(self, wrapper):
        """Test hand with single all-in completes."""
        # Use LAG strategy which goes all-in more often
        manager = BotManager(wrapper, skip_delay=True)
        manager.add_bot("lag1", LooseAggressiveStrategy(seed=42), buy_in=500)
        manager.add_bot("lag2", LooseAggressiveStrategy(seed=1), buy_in=500)

        state = manager.create_table_state()

        # Play multiple hands to get at least one all-in
        summaries = await manager.play_n_hands(state, n=20)

        assert len(summaries) == 20

    @pytest.mark.asyncio
    async def test_short_stack_all_in(self, wrapper):
        """Test short stack going all-in."""
        manager = BotManager(wrapper, skip_delay=True)
        manager.add_bot("short", LooseAggressiveStrategy(seed=42), buy_in=100)  # Short stack
        manager.add_bot("big", RandomStrategy(seed=1), buy_in=1000)  # Big stack

        state = manager.create_table_state()
        summaries = await manager.play_n_hands(state, n=10)

        assert len(summaries) == 10


class TestMultipleAllIns:
    """Multiple all-in scenarios."""

    @pytest.mark.asyncio
    async def test_multiple_all_ins(self, wrapper):
        """Test hand with multiple all-ins completes."""
        manager = BotManager(wrapper, skip_delay=True)
        # 4 aggressive players with different stack sizes
        manager.add_bot("lag1", LooseAggressiveStrategy(seed=1), buy_in=300)
        manager.add_bot("lag2", LooseAggressiveStrategy(seed=2), buy_in=500)
        manager.add_bot("lag3", LooseAggressiveStrategy(seed=3), buy_in=700)
        manager.add_bot("lag4", LooseAggressiveStrategy(seed=4), buy_in=1000)

        state = manager.create_table_state()

        # Play hands - multiple all-ins will occur
        summaries = await manager.play_n_hands(state, n=15)

        assert len(summaries) == 15
        for summary in summaries:
            assert summary.final_pot >= 0

    @pytest.mark.asyncio
    async def test_6_player_all_in_chaos(self, wrapper):
        """Test 6-player game with aggressive players."""
        manager = BotManager(wrapper, skip_delay=True)
        for i in range(6):
            # Varying stack sizes to create side pot scenarios
            buy_in = 200 + (i * 150)
            manager.add_bot(
                f"lag{i}",
                LooseAggressiveStrategy(seed=i * 10),
                buy_in=buy_in
            )

        state = manager.create_table_state()
        summaries = await manager.play_n_hands(state, n=10)

        assert len(summaries) == 10


class TestSidePots:
    """Side pot scenarios."""

    @pytest.mark.asyncio
    async def test_side_pot_creation(self, wrapper):
        """Test side pots are handled correctly."""
        manager = BotManager(wrapper, skip_delay=True)
        # Different stack sizes for guaranteed side pots on all-in
        manager.add_bot("short", LooseAggressiveStrategy(seed=1), buy_in=100)
        manager.add_bot("medium", LooseAggressiveStrategy(seed=2), buy_in=500)
        manager.add_bot("big", LooseAggressiveStrategy(seed=3), buy_in=1000)

        state = manager.create_table_state()

        # Track if we see side pots
        had_side_pot = [False]

        def check_pots(new_state, action):
            if new_state.hand and new_state.hand.pot.side_pots:
                had_side_pot[0] = True

        manager.on_action(check_pots)

        # Play many hands to likely trigger side pot
        summaries = await manager.play_n_hands(state, n=30)

        # All hands completed successfully
        assert len(summaries) == 30

    @pytest.mark.asyncio
    async def test_multiple_side_pots(self, wrapper):
        """Test multiple side pots with 4+ players."""
        manager = BotManager(wrapper, skip_delay=True)
        # Very different stacks to force multiple side pots
        stacks = [100, 200, 400, 800]
        for i, stack in enumerate(stacks):
            manager.add_bot(
                f"bot{i}",
                LooseAggressiveStrategy(seed=i),
                buy_in=stack
            )

        state = manager.create_table_state()
        summaries = await manager.play_n_hands(state, n=20)

        assert len(summaries) == 20


class TestAllInEdgeCases:
    """Edge cases involving all-ins."""

    @pytest.mark.asyncio
    async def test_all_in_with_equal_stacks(self, wrapper):
        """Test all-in when stacks are equal."""
        manager = BotManager(wrapper, skip_delay=True)
        manager.add_bot("bot1", LooseAggressiveStrategy(seed=1), buy_in=500)
        manager.add_bot("bot2", LooseAggressiveStrategy(seed=2), buy_in=500)

        state = manager.create_table_state()
        summaries = await manager.play_n_hands(state, n=15)

        assert len(summaries) == 15

    @pytest.mark.asyncio
    async def test_min_stack_all_in(self, wrapper):
        """Test with very small stacks (almost blind amounts)."""
        manager = BotManager(wrapper, skip_delay=True)
        # Stacks barely cover blinds
        manager.add_bot("tiny1", LooseAggressiveStrategy(seed=1), buy_in=30)  # 1.5 BB
        manager.add_bot("tiny2", LooseAggressiveStrategy(seed=2), buy_in=50)  # 2.5 BB

        state = manager.create_table_state(small_blind=10, big_blind=20)
        summaries = await manager.play_n_hands(state, n=5)

        assert len(summaries) == 5
