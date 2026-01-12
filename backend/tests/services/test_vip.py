"""Tests for VIPService.

Phase 6.2: VIP & Rakeback System tests.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.vip import (
    VIP_TIERS,
    VIPLevel,
    VIPService,
    VIPStatus,
    VIPTierConfig,
)


class TestVIPTierConfig:
    """Tests for VIP tier configuration."""
    
    def test_vip_tiers_ordered(self):
        """VIP tiers should be ordered by min_rake ascending."""
        prev_min = -1
        for tier in VIP_TIERS:
            assert tier.min_rake_krw > prev_min
            prev_min = tier.min_rake_krw
    
    def test_vip_tiers_rakeback_increasing(self):
        """Higher tiers should have higher rakeback."""
        prev_rakeback = Decimal("0")
        for tier in VIP_TIERS:
            assert tier.rakeback_pct >= prev_rakeback
            prev_rakeback = tier.rakeback_pct
    
    def test_bronze_is_default(self):
        """Bronze should be the default tier (0 rake required)."""
        bronze = VIP_TIERS[0]
        assert bronze.level == VIPLevel.BRONZE
        assert bronze.min_rake_krw == 0
    
    def test_all_levels_defined(self):
        """All VIP levels should have a tier config."""
        levels_in_tiers = {tier.level for tier in VIP_TIERS}
        assert VIPLevel.BRONZE in levels_in_tiers
        assert VIPLevel.SILVER in levels_in_tiers
        assert VIPLevel.GOLD in levels_in_tiers
        assert VIPLevel.PLATINUM in levels_in_tiers
        assert VIPLevel.DIAMOND in levels_in_tiers
    
    def test_rakeback_percentages_reasonable(self):
        """Rakeback percentages should be between 0 and 50%."""
        for tier in VIP_TIERS:
            assert Decimal("0") <= tier.rakeback_pct <= Decimal("0.50")


class TestVIPLevelCalculation:
    """Tests for VIP level calculation."""
    
    @pytest.fixture
    def vip_service(self):
        """Create VIPService with mocked session."""
        mock_session = MagicMock()
        return VIPService(mock_session)
    
    def test_calculate_bronze_level(self, vip_service):
        """Zero rake should be Bronze."""
        tier = vip_service.calculate_vip_level(0)
        assert tier.level == VIPLevel.BRONZE
    
    def test_calculate_silver_level(self, vip_service):
        """100,000 KRW rake should be Silver."""
        tier = vip_service.calculate_vip_level(100_000)
        assert tier.level == VIPLevel.SILVER
    
    def test_calculate_gold_level(self, vip_service):
        """500,000 KRW rake should be Gold."""
        tier = vip_service.calculate_vip_level(500_000)
        assert tier.level == VIPLevel.GOLD
    
    def test_calculate_platinum_level(self, vip_service):
        """2,000,000 KRW rake should be Platinum."""
        tier = vip_service.calculate_vip_level(2_000_000)
        assert tier.level == VIPLevel.PLATINUM
    
    def test_calculate_diamond_level(self, vip_service):
        """5,000,000 KRW rake should be Diamond."""
        tier = vip_service.calculate_vip_level(5_000_000)
        assert tier.level == VIPLevel.DIAMOND
    
    def test_calculate_level_just_below_threshold(self, vip_service):
        """Just below threshold should stay at lower level."""
        tier = vip_service.calculate_vip_level(99_999)
        assert tier.level == VIPLevel.BRONZE
        
        tier = vip_service.calculate_vip_level(499_999)
        assert tier.level == VIPLevel.SILVER
    
    def test_calculate_level_way_above_max(self, vip_service):
        """Very high rake should still be Diamond."""
        tier = vip_service.calculate_vip_level(100_000_000)
        assert tier.level == VIPLevel.DIAMOND


class TestRakebackCalculation:
    """Tests for rakeback calculation."""
    
    def test_bronze_rakeback_20_percent(self):
        """Bronze should get 20% rakeback."""
        bronze = next(t for t in VIP_TIERS if t.level == VIPLevel.BRONZE)
        assert bronze.rakeback_pct == Decimal("0.20")
        
        # 10,000 KRW rake -> 2,000 KRW rakeback
        rakeback = int(Decimal("10000") * bronze.rakeback_pct)
        assert rakeback == 2000
    
    def test_silver_rakeback_25_percent(self):
        """Silver should get 25% rakeback."""
        silver = next(t for t in VIP_TIERS if t.level == VIPLevel.SILVER)
        assert silver.rakeback_pct == Decimal("0.25")
        
        # 10,000 KRW rake -> 2,500 KRW rakeback
        rakeback = int(Decimal("10000") * silver.rakeback_pct)
        assert rakeback == 2500
    
    def test_gold_rakeback_30_percent(self):
        """Gold should get 30% rakeback."""
        gold = next(t for t in VIP_TIERS if t.level == VIPLevel.GOLD)
        assert gold.rakeback_pct == Decimal("0.30")
    
    def test_platinum_rakeback_35_percent(self):
        """Platinum should get 35% rakeback."""
        platinum = next(t for t in VIP_TIERS if t.level == VIPLevel.PLATINUM)
        assert platinum.rakeback_pct == Decimal("0.35")
    
    def test_diamond_rakeback_40_percent(self):
        """Diamond should get 40% rakeback."""
        diamond = next(t for t in VIP_TIERS if t.level == VIPLevel.DIAMOND)
        assert diamond.rakeback_pct == Decimal("0.40")
        
        # 100,000 KRW rake -> 40,000 KRW rakeback
        rakeback = int(Decimal("100000") * diamond.rakeback_pct)
        assert rakeback == 40000


class TestVIPStatusProgress:
    """Tests for VIP status and progress calculation."""
    
    @pytest.fixture
    def vip_service(self):
        """Create VIPService with mocked dependencies."""
        mock_session = MagicMock()
        service = VIPService(mock_session)
        
        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.hgetall.return_value = {}
        mock_redis.hset = AsyncMock()
        mock_redis.expire = AsyncMock()
        service._redis = mock_redis
        
        return service
    
    @pytest.mark.asyncio
    async def test_vip_status_bronze_progress(self, vip_service):
        """Bronze user should show progress to Silver."""
        # Mock user with 50,000 KRW rake
        mock_user = MagicMock()
        mock_user.total_rake_paid_krw = 50_000
        vip_service.session.get = AsyncMock(return_value=mock_user)
        
        status = await vip_service.get_vip_status("user-123")
        
        assert status.level == VIPLevel.BRONZE
        assert status.next_level == VIPLevel.SILVER
        assert status.rake_to_next == 50_000  # Need 50k more
        assert status.progress_pct == 50.0  # 50% progress
    
    @pytest.mark.asyncio
    async def test_vip_status_diamond_no_next(self, vip_service):
        """Diamond user should have no next level."""
        mock_user = MagicMock()
        mock_user.total_rake_paid_krw = 10_000_000
        vip_service.session.get = AsyncMock(return_value=mock_user)
        
        status = await vip_service.get_vip_status("user-123")
        
        assert status.level == VIPLevel.DIAMOND
        assert status.next_level is None
        assert status.rake_to_next == 0
        assert status.progress_pct == 100.0
    
    @pytest.mark.asyncio
    async def test_vip_status_uses_cache(self, vip_service):
        """Should use cached VIP data when available."""
        # Mock cached data
        vip_service._redis.hgetall.return_value = {
            b"total_rake": b"200000",
            b"updated_at": datetime.utcnow().isoformat().encode(),
        }
        
        status = await vip_service.get_vip_status("user-123")
        
        assert status.level == VIPLevel.SILVER
        assert status.total_rake_paid == 200_000
        
        # Should not have queried database
        vip_service.session.get.assert_not_called()
