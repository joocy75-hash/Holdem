"""Tests for Statistics Service - 매출 및 통계 집계."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal

from app.services.statistics_service import StatisticsService, StatisticsError


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = AsyncMock()
    return db


@pytest.fixture
def statistics_service(mock_db):
    """Create a StatisticsService instance with mock DB."""
    return StatisticsService(main_db=mock_db)


class TestGetRevenueSummary:
    """Tests for get_revenue_summary method."""
    
    @pytest.mark.asyncio
    async def test_get_revenue_summary_success(self, statistics_service, mock_db):
        """Test revenue summary retrieval."""
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.total_rake = Decimal("15000.50")
        mock_row.total_hands = 5000
        mock_row.unique_rooms = 25
        mock_result.fetchone.return_value = mock_row
        mock_db.execute.return_value = mock_result
        
        summary = await statistics_service.get_revenue_summary()
        
        assert summary["total_rake"] == 15000.50
        assert summary["total_hands"] == 5000
        assert summary["unique_rooms"] == 25
        assert "period" in summary
    
    @pytest.mark.asyncio
    async def test_get_revenue_summary_with_date_range(self, statistics_service, mock_db):
        """Test revenue summary with custom date range."""
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.total_rake = Decimal("5000.00")
        mock_row.total_hands = 1000
        mock_row.unique_rooms = 10
        mock_result.fetchone.return_value = mock_row
        mock_db.execute.return_value = mock_result
        
        start = datetime(2026, 1, 1)
        end = datetime(2026, 1, 15)
        
        summary = await statistics_service.get_revenue_summary(start, end)
        
        assert summary["period"]["start"] == start.isoformat()
        assert summary["period"]["end"] == end.isoformat()
    
    @pytest.mark.asyncio
    async def test_get_revenue_summary_raises_on_error(self, statistics_service, mock_db):
        """Test revenue summary raises StatisticsError on error."""
        mock_db.execute.side_effect = Exception("DB error")
        
        with pytest.raises(StatisticsError, match="Failed to get revenue summary"):
            await statistics_service.get_revenue_summary()


class TestGetDailyRevenue:
    """Tests for get_daily_revenue method."""
    
    @pytest.mark.asyncio
    async def test_get_daily_revenue_success(self, statistics_service, mock_db):
        """Test daily revenue retrieval."""
        mock_result = MagicMock()
        mock_rows = [
            MagicMock(date="2026-01-15", rake=Decimal("500.00"), hands=100),
            MagicMock(date="2026-01-14", rake=Decimal("450.00"), hands=90),
        ]
        mock_result.fetchall.return_value = mock_rows
        mock_db.execute.return_value = mock_result
        
        revenue = await statistics_service.get_daily_revenue(days=7)
        
        assert len(revenue) == 2
        assert revenue[0]["date"] == "2026-01-15"
        assert revenue[0]["rake"] == 500.00
    
    @pytest.mark.asyncio
    async def test_get_daily_revenue_raises_on_error(self, statistics_service, mock_db):
        """Test daily revenue raises StatisticsError on error."""
        mock_db.execute.side_effect = Exception("DB error")
        
        with pytest.raises(StatisticsError, match="Failed to get daily revenue"):
            await statistics_service.get_daily_revenue()


class TestGetWeeklyRevenue:
    """Tests for get_weekly_revenue method."""
    
    @pytest.mark.asyncio
    async def test_get_weekly_revenue_success(self, statistics_service, mock_db):
        """Test weekly revenue retrieval."""
        mock_result = MagicMock()
        mock_rows = [
            MagicMock(week_start=datetime(2026, 1, 13), rake=Decimal("3500.00"), hands=700),
            MagicMock(week_start=datetime(2026, 1, 6), rake=Decimal("3200.00"), hands=640),
        ]
        mock_result.fetchall.return_value = mock_rows
        mock_db.execute.return_value = mock_result
        
        revenue = await statistics_service.get_weekly_revenue(weeks=4)
        
        assert len(revenue) == 2
        assert revenue[0]["week_start"] == "2026-01-13"
        assert revenue[0]["rake"] == 3500.00
    
    @pytest.mark.asyncio
    async def test_get_weekly_revenue_raises_on_error(self, statistics_service, mock_db):
        """Test weekly revenue raises StatisticsError on error."""
        mock_db.execute.side_effect = Exception("DB error")
        
        with pytest.raises(StatisticsError, match="Failed to get weekly revenue"):
            await statistics_service.get_weekly_revenue()


class TestGetMonthlyRevenue:
    """Tests for get_monthly_revenue method."""
    
    @pytest.mark.asyncio
    async def test_get_monthly_revenue_success(self, statistics_service, mock_db):
        """Test monthly revenue retrieval."""
        mock_result = MagicMock()
        mock_rows = [
            MagicMock(month_start=datetime(2026, 1, 1), rake=Decimal("15000.00"), hands=3000),
            MagicMock(month_start=datetime(2025, 12, 1), rake=Decimal("14000.00"), hands=2800),
        ]
        mock_result.fetchall.return_value = mock_rows
        mock_db.execute.return_value = mock_result
        
        revenue = await statistics_service.get_monthly_revenue(months=6)
        
        assert len(revenue) == 2
        assert revenue[0]["month"] == "2026-01"
        assert revenue[0]["rake"] == 15000.00
    
    @pytest.mark.asyncio
    async def test_get_monthly_revenue_raises_on_error(self, statistics_service, mock_db):
        """Test monthly revenue raises StatisticsError on error."""
        mock_db.execute.side_effect = Exception("DB error")
        
        with pytest.raises(StatisticsError, match="Failed to get monthly revenue"):
            await statistics_service.get_monthly_revenue()


class TestGetTopPlayersByRake:
    """Tests for get_top_players_by_rake method."""
    
    @pytest.mark.asyncio
    async def test_get_top_players_success(self, statistics_service, mock_db):
        """Test top players retrieval."""
        mock_result = MagicMock()
        mock_rows = [
            MagicMock(user_id="user1", total_rake=Decimal("500.00"), hands_played=100),
            MagicMock(user_id="user2", total_rake=Decimal("400.00"), hands_played=80),
        ]
        mock_result.fetchall.return_value = mock_rows
        mock_db.execute.return_value = mock_result
        
        players = await statistics_service.get_top_players_by_rake(limit=10)
        
        assert len(players) == 2
        assert players[0]["user_id"] == "user1"
        assert players[0]["total_rake"] == 500.00
    
    @pytest.mark.asyncio
    async def test_get_top_players_raises_on_error(self, statistics_service, mock_db):
        """Test top players raises StatisticsError on error."""
        mock_db.execute.side_effect = Exception("DB error")
        
        with pytest.raises(StatisticsError, match="Failed to get top players by rake"):
            await statistics_service.get_top_players_by_rake()


class TestGetGameStatistics:
    """Tests for get_game_statistics method."""
    
    @pytest.mark.asyncio
    async def test_get_game_statistics_success(self, statistics_service, mock_db):
        """Test game statistics retrieval."""
        # Mock today's stats
        today_result = MagicMock()
        today_row = MagicMock()
        today_row.hands_today = 150
        today_row.rake_today = Decimal("750.00")
        today_row.rooms_today = 5
        today_result.fetchone.return_value = today_row
        
        # Mock total stats
        total_result = MagicMock()
        total_row = MagicMock()
        total_row.total_hands = 50000
        total_row.total_rake = Decimal("250000.00")
        total_result.fetchone.return_value = total_row
        
        mock_db.execute.side_effect = [today_result, total_result]
        
        stats = await statistics_service.get_game_statistics()
        
        assert stats["today"]["hands"] == 150
        assert stats["today"]["rake"] == 750.00
        assert stats["total"]["hands"] == 50000
        assert stats["total"]["rake"] == 250000.00
    
    @pytest.mark.asyncio
    async def test_get_game_statistics_raises_on_error(self, statistics_service, mock_db):
        """Test game statistics raises StatisticsError on error."""
        mock_db.execute.side_effect = Exception("DB error")
        
        with pytest.raises(StatisticsError, match="Failed to get game statistics"):
            await statistics_service.get_game_statistics()


class TestGetRoomStatistics:
    """Tests for get_room_statistics method."""
    
    @pytest.mark.asyncio
    async def test_get_room_statistics_success(self, statistics_service, mock_db):
        """Test room statistics retrieval."""
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.total_rooms = 50
        mock_row.active_rooms = 20
        mock_row.waiting_rooms = 15
        mock_row.closed_rooms = 15
        mock_result.fetchone.return_value = mock_row
        mock_db.execute.return_value = mock_result
        
        stats = await statistics_service.get_room_statistics()
        
        assert stats["total_rooms"] == 50
        assert stats["active_rooms"] == 20
        assert stats["waiting_rooms"] == 15
        assert stats["closed_rooms"] == 15
    
    @pytest.mark.asyncio
    async def test_get_room_statistics_raises_on_error(self, statistics_service, mock_db):
        """Test room statistics raises StatisticsError on error."""
        mock_db.execute.side_effect = Exception("DB error")
        
        with pytest.raises(StatisticsError, match="Failed to get room statistics"):
            await statistics_service.get_room_statistics()


class TestGetPlayerDistribution:
    """Tests for get_player_distribution method."""
    
    @pytest.mark.asyncio
    async def test_get_player_distribution_success(self, statistics_service, mock_db):
        """Test player distribution retrieval."""
        mock_result = MagicMock()
        mock_rows = [
            MagicMock(stake_level="low", player_count=50, room_count=10),
            MagicMock(stake_level="medium", player_count=30, room_count=6),
            MagicMock(stake_level="high", player_count=10, room_count=2),
        ]
        mock_result.fetchall.return_value = mock_rows
        mock_db.execute.return_value = mock_result
        
        distribution = await statistics_service.get_player_distribution()
        
        assert len(distribution) == 3
        assert distribution[0]["stake_level"] == "low"
        assert distribution[0]["player_count"] == 50
        assert distribution[0]["room_count"] == 10
    
    @pytest.mark.asyncio
    async def test_get_player_distribution_raises_on_error(self, statistics_service, mock_db):
        """Test player distribution raises StatisticsError on error."""
        mock_db.execute.side_effect = Exception("DB error")
        
        with pytest.raises(StatisticsError, match="Failed to get player distribution"):
            await statistics_service.get_player_distribution()


class TestGetPlayerActivitySummary:
    """Tests for get_player_activity_summary method."""
    
    @pytest.mark.asyncio
    async def test_get_player_activity_summary_success(self, statistics_service, mock_db):
        """Test player activity summary retrieval."""
        # Mock today's activity
        today_result = MagicMock()
        today_row = MagicMock()
        today_row.active_players = 100
        today_row.total_actions = 500
        today_result.fetchone.return_value = today_row
        
        # Mock week's activity
        week_result = MagicMock()
        week_row = MagicMock()
        week_row.active_players = 500
        week_result.fetchone.return_value = week_row
        
        # Mock month's activity
        month_result = MagicMock()
        month_row = MagicMock()
        month_row.active_players = 1500
        month_result.fetchone.return_value = month_row
        
        mock_db.execute.side_effect = [today_result, week_result, month_result]
        
        summary = await statistics_service.get_player_activity_summary()
        
        assert summary["today"]["active_players"] == 100
        assert summary["today"]["total_actions"] == 500
        assert summary["week"]["active_players"] == 500
        assert summary["month"]["active_players"] == 1500
    
    @pytest.mark.asyncio
    async def test_get_player_activity_summary_raises_on_error(self, statistics_service, mock_db):
        """Test player activity summary raises StatisticsError on error."""
        mock_db.execute.side_effect = Exception("DB error")
        
        with pytest.raises(StatisticsError, match="Failed to get player activity summary"):
            await statistics_service.get_player_activity_summary()


class TestGetHourlyPlayerActivity:
    """Tests for get_hourly_player_activity method."""
    
    @pytest.mark.asyncio
    async def test_get_hourly_player_activity_success(self, statistics_service, mock_db):
        """Test hourly player activity retrieval."""
        mock_result = MagicMock()
        mock_rows = [
            MagicMock(hour=datetime(2026, 1, 16, 14, 0), unique_players=50, total_hands=100),
            MagicMock(hour=datetime(2026, 1, 16, 13, 0), unique_players=45, total_hands=90),
        ]
        mock_result.fetchall.return_value = mock_rows
        mock_db.execute.return_value = mock_result
        
        activity = await statistics_service.get_hourly_player_activity(hours=24)
        
        assert len(activity) == 2
        assert activity[0]["unique_players"] == 50
        assert activity[0]["total_hands"] == 100
    
    @pytest.mark.asyncio
    async def test_get_hourly_player_activity_raises_on_error(self, statistics_service, mock_db):
        """Test hourly player activity raises StatisticsError on error."""
        mock_db.execute.side_effect = Exception("DB error")
        
        with pytest.raises(StatisticsError, match="Failed to get hourly player activity"):
            await statistics_service.get_hourly_player_activity()


class TestGetStakeLevelStatistics:
    """Tests for get_stake_level_statistics method."""
    
    @pytest.mark.asyncio
    async def test_get_stake_level_statistics_success(self, statistics_service, mock_db):
        """Test stake level statistics retrieval."""
        mock_result = MagicMock()
        mock_rows = [
            MagicMock(stake_level="low", total_hands=1000, total_rake=Decimal("500.00"), avg_pot_size=Decimal("50.00")),
            MagicMock(stake_level="medium", total_hands=500, total_rake=Decimal("750.00"), avg_pot_size=Decimal("150.00")),
            MagicMock(stake_level="high", total_hands=100, total_rake=Decimal("500.00"), avg_pot_size=Decimal("500.00")),
        ]
        mock_result.fetchall.return_value = mock_rows
        mock_db.execute.return_value = mock_result
        
        stats = await statistics_service.get_stake_level_statistics()
        
        assert len(stats) == 3
        assert stats[0]["stake_level"] == "low"
        assert stats[0]["total_hands"] == 1000
        assert stats[0]["total_rake"] == 500.00
        assert stats[0]["avg_pot_size"] == 50.00
    
    @pytest.mark.asyncio
    async def test_get_stake_level_statistics_raises_on_error(self, statistics_service, mock_db):
        """Test stake level statistics raises StatisticsError on error."""
        mock_db.execute.side_effect = Exception("DB error")
        
        with pytest.raises(StatisticsError, match="Failed to get stake level statistics"):
            await statistics_service.get_stake_level_statistics()


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    @pytest.mark.asyncio
    async def test_revenue_summary_with_none_values(self, statistics_service, mock_db):
        """Test revenue summary handles None values."""
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.total_rake = None
        mock_row.total_hands = None
        mock_row.unique_rooms = None
        mock_result.fetchone.return_value = mock_row
        mock_db.execute.return_value = mock_result
        
        summary = await statistics_service.get_revenue_summary()
        
        assert summary["total_rake"] == 0
        assert summary["total_hands"] == 0
        assert summary["unique_rooms"] == 0
    
    @pytest.mark.asyncio
    async def test_player_distribution_with_null_stake_level(self, statistics_service, mock_db):
        """Test player distribution handles null stake level."""
        mock_result = MagicMock()
        mock_rows = [
            MagicMock(stake_level=None, player_count=10, room_count=2),
        ]
        mock_result.fetchall.return_value = mock_rows
        mock_db.execute.return_value = mock_result
        
        distribution = await statistics_service.get_player_distribution()
        
        assert len(distribution) == 1
        assert distribution[0]["stake_level"] == "unknown"
    
    @pytest.mark.asyncio
    async def test_weekly_revenue_with_none_week_start(self, statistics_service, mock_db):
        """Test weekly revenue handles None week_start."""
        mock_result = MagicMock()
        mock_rows = [
            MagicMock(week_start=None, rake=Decimal("100.00"), hands=20),
        ]
        mock_result.fetchall.return_value = mock_rows
        mock_db.execute.return_value = mock_result
        
        revenue = await statistics_service.get_weekly_revenue()
        
        assert len(revenue) == 1
        assert revenue[0]["week_start"] == ""
