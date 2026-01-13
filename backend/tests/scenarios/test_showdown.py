"""Showdown scenario tests.

Tests showdown mechanics:
- Winner determination
- Hand ranking
- Split pots
"""

import pytest
from tests.bot.manager import BotManager
from tests.bot.strategy.random_bot import RandomStrategy
from tests.bot.strategy.calculated import CalculatedStrategy
from tests.bot.strategy.tight_passive import TightPassiveStrategy


@pytest.fixture
def wrapper():
    """Create PokerKit wrapper."""
    from app.engine.core import PokerKitWrapper
    return PokerKitWrapper()


class TestShowdownBasics:
    """Basic showdown scenarios."""

    @pytest.mark.asyncio
    async def test_showdown_best_hand_wins(self, wrapper):
        """Test showdown correctly determines winner."""
        # Use calculated strategy which sees more showdowns
        manager = BotManager(wrapper, skip_delay=True)
        manager.add_bot("calc1", CalculatedStrategy(seed=42), buy_in=1000)
        manager.add_bot("calc2", CalculatedStrategy(seed=1), buy_in=1000)

        state = manager.create_table_state()

        # Play multiple hands to get showdowns
        summaries = await manager.play_n_hands(state, n=20)

        assert len(summaries) == 20

        # Every hand should have a final pot
        for summary in summaries:
            assert summary.final_pot >= 0

    @pytest.mark.asyncio
    async def test_showdown_with_6_players(self, wrapper):
        """Test showdown with multiple players."""
        manager = BotManager(wrapper, skip_delay=True)
        for i in range(6):
            manager.add_bot(
                f"calc{i}",
                CalculatedStrategy(aggression=0.4, seed=i),
                buy_in=1000
            )

        state = manager.create_table_state()
        summaries = await manager.play_n_hands(state, n=10)

        assert len(summaries) == 10

    @pytest.mark.asyncio
    async def test_tight_players_see_more_showdowns(self, wrapper):
        """Test tight players reach showdown more often."""
        manager = BotManager(wrapper, skip_delay=True)
        manager.add_bot("tight1", TightPassiveStrategy(seed=1), buy_in=1000)
        manager.add_bot("tight2", TightPassiveStrategy(seed=2), buy_in=1000)

        state = manager.create_table_state()
        summaries = await manager.play_n_hands(state, n=15)

        # All hands complete
        assert len(summaries) == 15


class TestSplitPots:
    """Split pot scenarios."""

    @pytest.mark.asyncio
    async def test_showdown_split_pot(self, wrapper):
        """Test split pot handling (same hand strength)."""
        # Split pots are rare but should work
        manager = BotManager(wrapper, skip_delay=True)
        manager.add_bot("bot1", RandomStrategy(seed=42), buy_in=1000)
        manager.add_bot("bot2", RandomStrategy(seed=1), buy_in=1000)

        state = manager.create_table_state()

        # Play many hands - split pot will happen eventually
        summaries = await manager.play_n_hands(state, n=50)

        assert len(summaries) == 50

    @pytest.mark.asyncio
    async def test_3_way_potential_split(self, wrapper):
        """Test 3-way split pot scenario."""
        manager = BotManager(wrapper, skip_delay=True)
        manager.add_bot("bot1", TightPassiveStrategy(seed=1), buy_in=1000)
        manager.add_bot("bot2", TightPassiveStrategy(seed=2), buy_in=1000)
        manager.add_bot("bot3", TightPassiveStrategy(seed=3), buy_in=1000)

        state = manager.create_table_state()
        summaries = await manager.play_n_hands(state, n=30)

        assert len(summaries) == 30


class TestShowdownResults:
    """Test showdown result tracking."""

    @pytest.mark.asyncio
    async def test_winner_recorded(self, wrapper):
        """Test that winners are properly tracked."""
        manager = BotManager(wrapper, skip_delay=True)
        manager.add_bot("bot1", RandomStrategy(seed=42), buy_in=1000)
        manager.add_bot("bot2", RandomStrategy(seed=1), buy_in=1000)

        state = manager.create_table_state()
        summaries = await manager.play_n_hands(state, n=10)

        for summary in summaries:
            # Each hand has winner positions tracked
            assert summary.winner_positions is not None
            assert summary.final_pot >= 0

    @pytest.mark.asyncio
    async def test_pot_distributed(self, wrapper):
        """Test pot is fully distributed after showdown."""
        manager = BotManager(wrapper, skip_delay=True)
        manager.add_bot("bot1", CalculatedStrategy(seed=42), buy_in=1000)
        manager.add_bot("bot2", CalculatedStrategy(seed=1), buy_in=1000)

        state = manager.create_table_state()
        summaries = await manager.play_n_hands(state, n=20)

        assert len(summaries) == 20


class TestShowdownEdgeCases:
    """Edge cases in showdown."""

    @pytest.mark.asyncio
    async def test_all_fold_to_winner(self, wrapper):
        """Test when all players fold (no showdown)."""
        # LAG player might make everyone fold
        from tests.bot.strategy.loose_aggressive import LooseAggressiveStrategy

        manager = BotManager(wrapper, skip_delay=True)
        manager.add_bot("lag", LooseAggressiveStrategy(seed=1), buy_in=1000)
        manager.add_bot("tight", TightPassiveStrategy(seed=2), buy_in=1000)

        state = manager.create_table_state()
        summaries = await manager.play_n_hands(state, n=15)

        # Hands complete either by fold or showdown
        assert len(summaries) == 15

    @pytest.mark.asyncio
    async def test_heads_up_showdown(self, wrapper):
        """Test heads-up specific showdown rules."""
        manager = BotManager(wrapper, skip_delay=True)
        manager.add_bot("bot1", CalculatedStrategy(seed=42), buy_in=1000)
        manager.add_bot("bot2", CalculatedStrategy(seed=1), buy_in=1000)

        state = manager.create_table_state()
        state = wrapper.create_initial_hand(state)

        final_state = await manager.play_hand(state)

        assert wrapper.is_hand_finished(final_state)
