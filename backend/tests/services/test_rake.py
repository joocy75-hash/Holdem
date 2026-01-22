"""Tests for RakeService.

Phase 6.1: Rake & Economy System tests.
"""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.engine.state import GamePhase
from app.services.rake import (
    DEFAULT_RAKE_CONFIG,
    RAKE_CONFIGS,
    RakeConfigData,
    RakeResult,
    RakeService,
)


class TestRakeConfig:
    """Tests for rake configuration."""
    
    def test_default_config_exists(self):
        """Default config should exist."""
        assert DEFAULT_RAKE_CONFIG is not None
        assert DEFAULT_RAKE_CONFIG.percentage > 0
        assert DEFAULT_RAKE_CONFIG.cap_bb > 0
    
    def test_rake_configs_defined(self):
        """Rake configs should be defined for common blind levels."""
        assert len(RAKE_CONFIGS) > 0
        
        # Check some expected blind levels
        assert (1000, 2000) in RAKE_CONFIGS
        assert (5000, 10000) in RAKE_CONFIGS
    
    def test_rake_config_values_reasonable(self):
        """Rake percentages and caps should be reasonable."""
        for (sb, bb), config in RAKE_CONFIGS.items():
            # Percentage should be between 0 and 10%
            assert Decimal("0") < config.percentage <= Decimal("0.10")
            # Cap should be between 1 and 10 BB
            assert 1 <= config.cap_bb <= 10


class TestRakeServiceCalculation:
    """Tests for rake calculation logic."""
    
    @pytest.fixture
    def rake_service(self):
        """Create RakeService with mocked session."""
        mock_session = MagicMock()
        return RakeService(mock_session)
    
    def test_get_rake_config_exact_match(self, rake_service):
        """Should return exact config for known blind level."""
        config = rake_service.get_rake_config(1000, 2000)
        assert config == RAKE_CONFIGS[(1000, 2000)]
    
    def test_get_rake_config_closest_match(self, rake_service):
        """Should return closest config for unknown blind level."""
        # Unknown blind level should find closest
        config = rake_service.get_rake_config(1500, 3000)
        assert config is not None
        assert config.percentage > 0
    
    def test_calculate_rake_basic(self, rake_service):
        """Basic rake calculation."""
        result = rake_service.calculate_rake(
            pot_total=100000,  # ₩100,000 pot
            small_blind=1000,
            big_blind=2000,
            phase=GamePhase.RIVER,
            winners=[{"position": 0, "amount": 100000}],
        )
        
        assert isinstance(result, RakeResult)
        assert result.total_rake > 0
        assert result.pot_after_rake == 100000 - result.total_rake
        assert not result.applied_nfnd
    
    def test_calculate_rake_with_cap(self, rake_service):
        """Rake should be capped at max BB."""
        # Large pot should hit the cap
        result = rake_service.calculate_rake(
            pot_total=1000000,  # ₩1,000,000 pot
            small_blind=1000,
            big_blind=2000,
            phase=GamePhase.RIVER,
            winners=[{"position": 0, "amount": 1000000}],
        )
        
        config = rake_service.get_rake_config(1000, 2000)
        max_rake = 2000 * config.cap_bb
        
        assert result.total_rake <= max_rake
    
    def test_no_flop_no_drop_preflop_fold(self, rake_service):
        """No rake when hand ends preflop with fold."""
        result = rake_service.calculate_rake(
            pot_total=3000,  # Small pot (1.5 BB)
            small_blind=1000,
            big_blind=2000,
            phase=GamePhase.PREFLOP,
            winners=[{"position": 0, "amount": 3000}],
        )
        
        assert result.total_rake == 0
        assert result.applied_nfnd
        assert result.pot_after_rake == 3000
    
    def test_no_flop_no_drop_finished_small_pot(self, rake_service):
        """No rake when hand finishes with small pot (likely preflop)."""
        result = rake_service.calculate_rake(
            pot_total=4000,  # 2 BB pot
            small_blind=1000,
            big_blind=2000,
            phase=GamePhase.FINISHED,
            winners=[{"position": 0, "amount": 4000}],
        )
        
        assert result.total_rake == 0
        assert result.applied_nfnd
    
    def test_rake_after_flop(self, rake_service):
        """Rake should be collected after flop."""
        result = rake_service.calculate_rake(
            pot_total=50000,
            small_blind=1000,
            big_blind=2000,
            phase=GamePhase.FLOP,
            winners=[{"position": 0, "amount": 50000}],
        )
        
        assert result.total_rake > 0
        assert not result.applied_nfnd
    
    def test_minimum_rake_threshold(self, rake_service):
        """Very small pots should not collect rake."""
        result = rake_service.calculate_rake(
            pot_total=1000,  # Very small pot
            small_blind=500,
            big_blind=1000,
            phase=GamePhase.RIVER,
            winners=[{"position": 0, "amount": 1000}],
        )
        
        # Rake would be ₩50 (5% of 1000), below ₩100 threshold
        assert result.total_rake == 0
    
    def test_rake_distribution_single_winner(self, rake_service):
        """Single winner pays all rake."""
        result = rake_service.calculate_rake(
            pot_total=100000,
            small_blind=1000,
            big_blind=2000,
            phase=GamePhase.RIVER,
            winners=[{"position": 2, "amount": 100000}],
        )
        
        assert len(result.rake_per_winner) == 1
        assert 2 in result.rake_per_winner
        assert result.rake_per_winner[2] == result.total_rake
    
    def test_rake_distribution_multiple_winners(self, rake_service):
        """Multiple winners split rake proportionally."""
        result = rake_service.calculate_rake(
            pot_total=100000,
            small_blind=1000,
            big_blind=2000,
            phase=GamePhase.RIVER,
            winners=[
                {"position": 0, "amount": 60000},  # 60%
                {"position": 1, "amount": 40000},  # 40%
            ],
        )
        
        assert len(result.rake_per_winner) == 2
        
        # Check proportional distribution
        total_distributed = sum(result.rake_per_winner.values())
        assert total_distributed == result.total_rake
        
        # Position 0 should pay more (60% of rake)
        assert result.rake_per_winner[0] > result.rake_per_winner[1]
    
    def test_rake_distribution_split_pot(self, rake_service):
        """Equal split pot should split rake equally."""
        result = rake_service.calculate_rake(
            pot_total=100000,
            small_blind=1000,
            big_blind=2000,
            phase=GamePhase.RIVER,
            winners=[
                {"position": 0, "amount": 50000},
                {"position": 1, "amount": 50000},
            ],
        )
        
        # Should be roughly equal (may differ by 1 due to rounding)
        diff = abs(result.rake_per_winner[0] - result.rake_per_winner[1])
        assert diff <= 1


class TestRakeServiceHighStakes:
    """Tests for high stakes rake calculation."""
    
    @pytest.fixture
    def rake_service(self):
        """Create RakeService with mocked session."""
        mock_session = MagicMock()
        return RakeService(mock_session)
    
    def test_high_stakes_lower_percentage(self, rake_service):
        """High stakes should have lower rake percentage."""
        low_stakes_config = rake_service.get_rake_config(1000, 2000)
        high_stakes_config = rake_service.get_rake_config(50000, 100000)
        
        # High stakes should have lower or equal percentage
        assert high_stakes_config.percentage <= low_stakes_config.percentage
    
    def test_high_stakes_rake_cap(self, rake_service):
        """High stakes rake cap should be reasonable."""
        result = rake_service.calculate_rake(
            pot_total=10000000,  # ₩10,000,000 pot
            small_blind=50000,
            big_blind=100000,
            phase=GamePhase.RIVER,
            winners=[{"position": 0, "amount": 10000000}],
        )
        
        # Cap should limit rake to 5 BB = ₩500,000
        config = rake_service.get_rake_config(50000, 100000)
        max_rake = 100000 * config.cap_bb
        
        assert result.total_rake <= max_rake
