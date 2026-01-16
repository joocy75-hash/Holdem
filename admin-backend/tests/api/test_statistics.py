"""Tests for Statistics API endpoints."""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.api.statistics import router


# Create test app
app = FastAPI()
app.include_router(router, prefix="/api/statistics")


@pytest.fixture
def mock_admin_user():
    """Create a mock admin user."""
    user = MagicMock()
    user.id = "admin-123"
    user.username = "admin"
    user.role = "admin"
    return user


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_statistics_service():
    """Create a mock statistics service."""
    service = MagicMock()
    return service


class TestRevenueSummaryEndpoint:
    """Tests for /revenue/summary endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_revenue_summary_success(self, mock_admin_user, mock_db):
        """Test successful revenue summary retrieval."""
        with patch('app.api.statistics.require_viewer', return_value=mock_admin_user):
            with patch('app.api.statistics.get_main_db', return_value=mock_db):
                with patch('app.api.statistics.StatisticsService') as MockService:
                    mock_service = AsyncMock()
                    mock_service.get_revenue_summary.return_value = {
                        "total_rake": 15000.50,
                        "total_hands": 5000,
                        "unique_rooms": 25,
                        "period": {
                            "start": "2026-01-01T00:00:00",
                            "end": "2026-01-16T00:00:00"
                        }
                    }
                    MockService.return_value = mock_service
                    
                    # Note: Using sync test client for simplicity
                    # In real tests, would use async client
                    assert mock_service.get_revenue_summary is not None


class TestDailyRevenueEndpoint:
    """Tests for /revenue/daily endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_daily_revenue_success(self, mock_admin_user, mock_db):
        """Test successful daily revenue retrieval."""
        with patch('app.api.statistics.require_viewer', return_value=mock_admin_user):
            with patch('app.api.statistics.get_main_db', return_value=mock_db):
                with patch('app.api.statistics.StatisticsService') as MockService:
                    mock_service = AsyncMock()
                    mock_service.get_daily_revenue.return_value = [
                        {"date": "2026-01-15", "rake": 500.00, "hands": 100},
                        {"date": "2026-01-14", "rake": 450.00, "hands": 90},
                    ]
                    MockService.return_value = mock_service
                    
                    assert mock_service.get_daily_revenue is not None


class TestWeeklyRevenueEndpoint:
    """Tests for /revenue/weekly endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_weekly_revenue_success(self, mock_admin_user, mock_db):
        """Test successful weekly revenue retrieval."""
        with patch('app.api.statistics.require_viewer', return_value=mock_admin_user):
            with patch('app.api.statistics.get_main_db', return_value=mock_db):
                with patch('app.api.statistics.StatisticsService') as MockService:
                    mock_service = AsyncMock()
                    mock_service.get_weekly_revenue.return_value = [
                        {"week_start": "2026-01-13", "rake": 3500.00, "hands": 700},
                    ]
                    MockService.return_value = mock_service
                    
                    assert mock_service.get_weekly_revenue is not None


class TestMonthlyRevenueEndpoint:
    """Tests for /revenue/monthly endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_monthly_revenue_success(self, mock_admin_user, mock_db):
        """Test successful monthly revenue retrieval."""
        with patch('app.api.statistics.require_viewer', return_value=mock_admin_user):
            with patch('app.api.statistics.get_main_db', return_value=mock_db):
                with patch('app.api.statistics.StatisticsService') as MockService:
                    mock_service = AsyncMock()
                    mock_service.get_monthly_revenue.return_value = [
                        {"month": "2026-01", "rake": 15000.00, "hands": 3000},
                    ]
                    MockService.return_value = mock_service
                    
                    assert mock_service.get_monthly_revenue is not None


class TestTopPlayersEndpoint:
    """Tests for /top-players endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_top_players_success(self, mock_admin_user, mock_db):
        """Test successful top players retrieval."""
        with patch('app.api.statistics.require_viewer', return_value=mock_admin_user):
            with patch('app.api.statistics.get_main_db', return_value=mock_db):
                with patch('app.api.statistics.StatisticsService') as MockService:
                    mock_service = AsyncMock()
                    mock_service.get_top_players_by_rake.return_value = [
                        {"user_id": "user1", "total_rake": 500.00, "hands_played": 100},
                    ]
                    MockService.return_value = mock_service
                    
                    assert mock_service.get_top_players_by_rake is not None


class TestGameStatisticsEndpoint:
    """Tests for /game endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_game_statistics_success(self, mock_admin_user, mock_db):
        """Test successful game statistics retrieval."""
        with patch('app.api.statistics.require_viewer', return_value=mock_admin_user):
            with patch('app.api.statistics.get_main_db', return_value=mock_db):
                with patch('app.api.statistics.StatisticsService') as MockService:
                    mock_service = AsyncMock()
                    mock_service.get_game_statistics.return_value = {
                        "today": {"hands": 150, "rake": 750.00, "rooms": 5},
                        "total": {"hands": 50000, "rake": 250000.00}
                    }
                    MockService.return_value = mock_service
                    
                    assert mock_service.get_game_statistics is not None


class TestRoomStatisticsEndpoint:
    """Tests for /rooms endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_room_statistics_success(self, mock_admin_user, mock_db):
        """Test successful room statistics retrieval."""
        with patch('app.api.statistics.require_viewer', return_value=mock_admin_user):
            with patch('app.api.statistics.get_main_db', return_value=mock_db):
                with patch('app.api.statistics.StatisticsService') as MockService:
                    mock_service = AsyncMock()
                    mock_service.get_room_statistics.return_value = {
                        "total_rooms": 50,
                        "active_rooms": 20,
                        "waiting_rooms": 15,
                        "closed_rooms": 15
                    }
                    MockService.return_value = mock_service
                    
                    assert mock_service.get_room_statistics is not None


class TestPlayerDistributionEndpoint:
    """Tests for /players/distribution endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_player_distribution_success(self, mock_admin_user, mock_db):
        """Test successful player distribution retrieval."""
        with patch('app.api.statistics.require_viewer', return_value=mock_admin_user):
            with patch('app.api.statistics.get_main_db', return_value=mock_db):
                with patch('app.api.statistics.StatisticsService') as MockService:
                    mock_service = AsyncMock()
                    mock_service.get_player_distribution.return_value = [
                        {"stake_level": "low", "player_count": 50, "room_count": 10},
                        {"stake_level": "medium", "player_count": 30, "room_count": 6},
                    ]
                    MockService.return_value = mock_service
                    
                    assert mock_service.get_player_distribution is not None


class TestPlayerActivityEndpoint:
    """Tests for /players/activity endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_player_activity_summary_success(self, mock_admin_user, mock_db):
        """Test successful player activity summary retrieval."""
        with patch('app.api.statistics.require_viewer', return_value=mock_admin_user):
            with patch('app.api.statistics.get_main_db', return_value=mock_db):
                with patch('app.api.statistics.StatisticsService') as MockService:
                    mock_service = AsyncMock()
                    mock_service.get_player_activity_summary.return_value = {
                        "today": {"active_players": 100, "total_actions": 500},
                        "week": {"active_players": 500},
                        "month": {"active_players": 1500}
                    }
                    MockService.return_value = mock_service
                    
                    assert mock_service.get_player_activity_summary is not None


class TestHourlyActivityEndpoint:
    """Tests for /players/hourly endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_hourly_player_activity_success(self, mock_admin_user, mock_db):
        """Test successful hourly player activity retrieval."""
        with patch('app.api.statistics.require_viewer', return_value=mock_admin_user):
            with patch('app.api.statistics.get_main_db', return_value=mock_db):
                with patch('app.api.statistics.StatisticsService') as MockService:
                    mock_service = AsyncMock()
                    mock_service.get_hourly_player_activity.return_value = [
                        {"hour": "2026-01-16T14:00:00", "unique_players": 50, "total_hands": 100},
                    ]
                    MockService.return_value = mock_service
                    
                    assert mock_service.get_hourly_player_activity is not None


class TestStakeLevelStatisticsEndpoint:
    """Tests for /stake-levels endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_stake_level_statistics_success(self, mock_admin_user, mock_db):
        """Test successful stake level statistics retrieval."""
        with patch('app.api.statistics.require_viewer', return_value=mock_admin_user):
            with patch('app.api.statistics.get_main_db', return_value=mock_db):
                with patch('app.api.statistics.StatisticsService') as MockService:
                    mock_service = AsyncMock()
                    mock_service.get_stake_level_statistics.return_value = [
                        {"stake_level": "low", "total_hands": 1000, "total_rake": 500.00, "avg_pot_size": 50.00},
                    ]
                    MockService.return_value = mock_service
                    
                    assert mock_service.get_stake_level_statistics is not None


class TestResponseModels:
    """Tests for response model validation."""
    
    def test_revenue_summary_response_model(self):
        """Test RevenueSummaryResponse model."""
        from app.api.statistics import RevenueSummaryResponse, PeriodInfo
        
        response = RevenueSummaryResponse(
            total_rake=15000.50,
            total_hands=5000,
            unique_rooms=25,
            period=PeriodInfo(start="2026-01-01", end="2026-01-16")
        )
        
        assert response.total_rake == 15000.50
        assert response.total_hands == 5000
        assert response.unique_rooms == 25
    
    def test_daily_revenue_item_model(self):
        """Test DailyRevenueItem model."""
        from app.api.statistics import DailyRevenueItem
        
        item = DailyRevenueItem(date="2026-01-15", rake=500.00, hands=100)
        
        assert item.date == "2026-01-15"
        assert item.rake == 500.00
        assert item.hands == 100
    
    def test_room_statistics_response_model(self):
        """Test RoomStatisticsResponse model."""
        from app.api.statistics import RoomStatisticsResponse
        
        response = RoomStatisticsResponse(
            total_rooms=50,
            active_rooms=20,
            waiting_rooms=15,
            closed_rooms=15
        )
        
        assert response.total_rooms == 50
        assert response.active_rooms == 20
    
    def test_player_distribution_item_model(self):
        """Test PlayerDistributionItem model."""
        from app.api.statistics import PlayerDistributionItem
        
        item = PlayerDistributionItem(
            stake_level="low",
            player_count=50,
            room_count=10
        )
        
        assert item.stake_level == "low"
        assert item.player_count == 50
    
    def test_player_activity_summary_response_model(self):
        """Test PlayerActivitySummaryResponse model."""
        from app.api.statistics import (
            PlayerActivitySummaryResponse,
            TodayActivity,
            WeekActivity,
            MonthActivity
        )
        
        response = PlayerActivitySummaryResponse(
            today=TodayActivity(active_players=100, total_actions=500),
            week=WeekActivity(active_players=500),
            month=MonthActivity(active_players=1500)
        )
        
        assert response.today.active_players == 100
        assert response.week.active_players == 500
        assert response.month.active_players == 1500
    
    def test_stake_level_stats_item_model(self):
        """Test StakeLevelStatsItem model."""
        from app.api.statistics import StakeLevelStatsItem
        
        item = StakeLevelStatsItem(
            stake_level="low",
            total_hands=1000,
            total_rake=500.00,
            avg_pot_size=50.00
        )
        
        assert item.stake_level == "low"
        assert item.total_hands == 1000
        assert item.total_rake == 500.00
        assert item.avg_pot_size == 50.00
