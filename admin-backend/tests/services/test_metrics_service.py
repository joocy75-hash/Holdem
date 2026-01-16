"""Tests for Metrics Service - CCU/DAU 및 서버 상태 집계."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.metrics_service import (
    MetricsService,
    get_metrics_service,
    get_redis_client,
)


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    redis = AsyncMock()
    return redis


@pytest.fixture
def metrics_service(mock_redis):
    """Create a MetricsService instance with mock Redis."""
    return MetricsService(redis_client=mock_redis)


class TestGetCCU:
    """Tests for get_ccu method."""
    
    @pytest.mark.asyncio
    async def test_get_ccu_from_online_users(self, metrics_service, mock_redis):
        """Test CCU retrieval from online_users set."""
        mock_redis.scard.return_value = 150
        
        ccu = await metrics_service.get_ccu()
        
        assert ccu == 150
        mock_redis.scard.assert_called_once_with("online_users")
    
    @pytest.mark.asyncio
    async def test_get_ccu_fallback_to_ws_connections(self, metrics_service, mock_redis):
        """Test CCU fallback to ws_connections_count when online_users is None."""
        mock_redis.scard.return_value = None
        mock_redis.get.return_value = "200"
        
        ccu = await metrics_service.get_ccu()
        
        assert ccu == 200
        mock_redis.get.assert_called_once_with("ws_connections_count")
    
    @pytest.mark.asyncio
    async def test_get_ccu_returns_zero_on_error(self, metrics_service, mock_redis):
        """Test CCU returns 0 on Redis error."""
        mock_redis.scard.side_effect = Exception("Redis connection error")
        
        ccu = await metrics_service.get_ccu()
        
        assert ccu == 0
    
    @pytest.mark.asyncio
    async def test_get_ccu_returns_zero_when_no_data(self, metrics_service, mock_redis):
        """Test CCU returns 0 when no data available."""
        mock_redis.scard.return_value = None
        mock_redis.get.return_value = None
        
        ccu = await metrics_service.get_ccu()
        
        assert ccu == 0


class TestGetDAU:
    """Tests for get_dau method."""
    
    @pytest.mark.asyncio
    async def test_get_dau_today(self, metrics_service, mock_redis):
        """Test DAU retrieval for today."""
        mock_redis.pfcount.return_value = 5000
        
        dau = await metrics_service.get_dau()
        
        assert dau == 5000
        # Verify the key format
        today_key = datetime.utcnow().strftime("%Y-%m-%d")
        mock_redis.pfcount.assert_called_once_with(f"dau:{today_key}")
    
    @pytest.mark.asyncio
    async def test_get_dau_specific_date(self, metrics_service, mock_redis):
        """Test DAU retrieval for a specific date."""
        mock_redis.pfcount.return_value = 4500
        specific_date = datetime(2026, 1, 15)
        
        dau = await metrics_service.get_dau(specific_date)
        
        assert dau == 4500
        mock_redis.pfcount.assert_called_once_with("dau:2026-01-15")
    
    @pytest.mark.asyncio
    async def test_get_dau_returns_zero_on_error(self, metrics_service, mock_redis):
        """Test DAU returns 0 on Redis error."""
        mock_redis.pfcount.side_effect = Exception("Redis error")
        
        dau = await metrics_service.get_dau()
        
        assert dau == 0
    
    @pytest.mark.asyncio
    async def test_get_dau_returns_zero_when_no_data(self, metrics_service, mock_redis):
        """Test DAU returns 0 when no data available."""
        mock_redis.pfcount.return_value = None
        
        dau = await metrics_service.get_dau()
        
        assert dau == 0


class TestGetCCUHistory:
    """Tests for get_ccu_history method."""
    
    @pytest.mark.asyncio
    async def test_get_ccu_history_default_hours(self, metrics_service, mock_redis):
        """Test CCU history retrieval for default 24 hours."""
        # Mock Redis to return different values for each hour
        mock_redis.get.side_effect = [str(100 + i) for i in range(24)]
        
        history = await metrics_service.get_ccu_history()
        
        assert len(history) == 24
        assert all("timestamp" in item for item in history)
        assert all("hour" in item for item in history)
        assert all("ccu" in item for item in history)
    
    @pytest.mark.asyncio
    async def test_get_ccu_history_custom_hours(self, metrics_service, mock_redis):
        """Test CCU history retrieval for custom hours."""
        mock_redis.get.side_effect = [str(50 + i) for i in range(12)]
        
        history = await metrics_service.get_ccu_history(hours=12)
        
        assert len(history) == 12
    
    @pytest.mark.asyncio
    async def test_get_ccu_history_returns_empty_on_error(self, metrics_service, mock_redis):
        """Test CCU history returns empty list on error."""
        mock_redis.get.side_effect = Exception("Redis error")
        
        history = await metrics_service.get_ccu_history()
        
        assert history == []
    
    @pytest.mark.asyncio
    async def test_get_ccu_history_handles_none_values(self, metrics_service, mock_redis):
        """Test CCU history handles None values gracefully."""
        mock_redis.get.side_effect = [None, "100", None, "150"]
        
        history = await metrics_service.get_ccu_history(hours=4)
        
        assert len(history) == 4
        # None values should be converted to 0
        assert any(item["ccu"] == 0 for item in history)


class TestGetDAUHistory:
    """Tests for get_dau_history method."""
    
    @pytest.mark.asyncio
    async def test_get_dau_history_default_days(self, metrics_service, mock_redis):
        """Test DAU history retrieval for default 30 days."""
        mock_redis.pfcount.side_effect = [1000 + i * 10 for i in range(30)]
        
        history = await metrics_service.get_dau_history()
        
        assert len(history) == 30
        assert all("date" in item for item in history)
        assert all("dau" in item for item in history)
    
    @pytest.mark.asyncio
    async def test_get_dau_history_custom_days(self, metrics_service, mock_redis):
        """Test DAU history retrieval for custom days."""
        mock_redis.pfcount.side_effect = [2000 + i * 5 for i in range(7)]
        
        history = await metrics_service.get_dau_history(days=7)
        
        assert len(history) == 7
    
    @pytest.mark.asyncio
    async def test_get_dau_history_returns_empty_on_error(self, metrics_service, mock_redis):
        """Test DAU history returns empty list on error."""
        mock_redis.pfcount.side_effect = Exception("Redis error")
        
        history = await metrics_service.get_dau_history()
        
        assert history == []


class TestGetActiveRooms:
    """Tests for get_active_rooms method."""
    
    @pytest.mark.asyncio
    async def test_get_active_rooms_success(self, metrics_service, mock_redis):
        """Test active rooms retrieval."""
        mock_redis.scard.side_effect = [10, 5, 6, 4, 3, 2]  # 10 rooms, then players per room
        mock_redis.smembers.return_value = {b"room1", b"room2", b"room3", b"room4", b"room5"}
        
        # Reset scard to return room count first, then player counts
        mock_redis.scard.reset_mock()
        mock_redis.scard.side_effect = [10, 5, 6, 4, 3, 2, 5, 4, 3, 2, 1]
        
        stats = await metrics_service.get_active_rooms()
        
        assert "active_rooms" in stats
        assert "total_players" in stats
        assert "avg_players_per_room" in stats
    
    @pytest.mark.asyncio
    async def test_get_active_rooms_returns_zeros_on_error(self, metrics_service, mock_redis):
        """Test active rooms returns zeros on error."""
        mock_redis.scard.side_effect = Exception("Redis error")
        
        stats = await metrics_service.get_active_rooms()
        
        assert stats["active_rooms"] == 0
        assert stats["total_players"] == 0
        assert stats["avg_players_per_room"] == 0
    
    @pytest.mark.asyncio
    async def test_get_active_rooms_handles_empty_rooms(self, metrics_service, mock_redis):
        """Test active rooms handles empty room set."""
        mock_redis.scard.return_value = 0
        mock_redis.smembers.return_value = set()
        
        stats = await metrics_service.get_active_rooms()
        
        assert stats["active_rooms"] == 0
        assert stats["total_players"] == 0


class TestGetRoomDistribution:
    """Tests for get_room_distribution method."""
    
    @pytest.mark.asyncio
    async def test_get_room_distribution_success(self, metrics_service, mock_redis):
        """Test room distribution retrieval."""
        mock_redis.scard.side_effect = [5, 2, 3]  # cash, tournament, sit_n_go
        
        distribution = await metrics_service.get_room_distribution()
        
        assert len(distribution) == 3
        assert distribution[0]["type"] == "cash"
        assert distribution[0]["count"] == 5
        assert distribution[1]["type"] == "tournament"
        assert distribution[1]["count"] == 2
        assert distribution[2]["type"] == "sit_n_go"
        assert distribution[2]["count"] == 3
    
    @pytest.mark.asyncio
    async def test_get_room_distribution_returns_empty_on_error(self, metrics_service, mock_redis):
        """Test room distribution returns empty list on error."""
        mock_redis.scard.side_effect = Exception("Redis error")
        
        distribution = await metrics_service.get_room_distribution()
        
        assert distribution == []


class TestGetServerHealth:
    """Tests for get_server_health method."""
    
    @pytest.mark.asyncio
    async def test_get_server_health_healthy(self, metrics_service, mock_redis):
        """Test server health returns healthy status."""
        mock_redis.get.side_effect = ["45.5", "60.0", "50"]  # cpu, memory, latency
        
        health = await metrics_service.get_server_health()
        
        assert health["cpu"] == 45.5
        assert health["memory"] == 60.0
        assert health["latency"] == 50.0
        assert health["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_get_server_health_warning(self, metrics_service, mock_redis):
        """Test server health returns warning status."""
        mock_redis.get.side_effect = ["75.0", "65.0", "100"]  # cpu > 70
        
        health = await metrics_service.get_server_health()
        
        assert health["status"] == "warning"
    
    @pytest.mark.asyncio
    async def test_get_server_health_critical(self, metrics_service, mock_redis):
        """Test server health returns critical status."""
        mock_redis.get.side_effect = ["95.0", "85.0", "100"]  # cpu > 90
        
        health = await metrics_service.get_server_health()
        
        assert health["status"] == "critical"
    
    @pytest.mark.asyncio
    async def test_get_server_health_critical_high_latency(self, metrics_service, mock_redis):
        """Test server health returns critical status on high latency."""
        mock_redis.get.side_effect = ["50.0", "50.0", "600"]  # latency > 500
        
        health = await metrics_service.get_server_health()
        
        assert health["status"] == "critical"
    
    @pytest.mark.asyncio
    async def test_get_server_health_returns_unknown_on_error(self, metrics_service, mock_redis):
        """Test server health returns unknown status on error."""
        mock_redis.get.side_effect = Exception("Redis error")
        
        health = await metrics_service.get_server_health()
        
        assert health["status"] == "unknown"
        assert health["cpu"] == 0
        assert health["memory"] == 0
        assert health["latency"] == 0


class TestGetDashboardSummary:
    """Tests for get_dashboard_summary method."""
    
    @pytest.mark.asyncio
    async def test_get_dashboard_summary_success(self, metrics_service, mock_redis):
        """Test dashboard summary retrieval."""
        # Setup mocks for all sub-methods
        mock_redis.scard.side_effect = [150, 10, 5, 6, 4, 3]  # CCU, rooms, players
        mock_redis.pfcount.return_value = 5000  # DAU
        mock_redis.get.side_effect = ["50.0", "60.0", "100"]  # server health
        mock_redis.smembers.return_value = set()
        
        summary = await metrics_service.get_dashboard_summary()
        
        assert "ccu" in summary
        assert "dau" in summary
        assert "active_rooms" in summary
        assert "total_players" in summary
        assert "server_health" in summary


class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    @pytest.mark.asyncio
    async def test_get_redis_client_creates_client(self):
        """Test Redis client creation."""
        with patch('app.services.metrics_service._redis_client', None):
            with patch('app.services.metrics_service.redis.from_url') as mock_from_url:
                mock_client = AsyncMock()
                mock_from_url.return_value = mock_client
                
                with patch('app.services.metrics_service.get_settings') as mock_settings:
                    mock_settings.return_value.redis_url = "redis://localhost:6379"
                    
                    client = await get_redis_client()
                    
                    mock_from_url.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_metrics_service_returns_instance(self):
        """Test MetricsService instance creation."""
        with patch('app.services.metrics_service.get_redis_client') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_get_redis.return_value = mock_redis
            
            service = await get_metrics_service()
            
            assert isinstance(service, MetricsService)
            assert service.redis == mock_redis


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    @pytest.mark.asyncio
    async def test_ccu_with_bytes_response(self, metrics_service, mock_redis):
        """Test CCU handles bytes response from Redis."""
        mock_redis.scard.return_value = None
        mock_redis.get.return_value = b"100"  # bytes response
        
        ccu = await metrics_service.get_ccu()
        
        assert ccu == 100
    
    @pytest.mark.asyncio
    async def test_active_rooms_with_bytes_room_ids(self, metrics_service, mock_redis):
        """Test active rooms handles bytes room IDs."""
        mock_redis.scard.side_effect = [3, 5, 4, 3]  # 3 rooms, then players
        mock_redis.smembers.return_value = {b"room1", b"room2", b"room3"}
        
        stats = await metrics_service.get_active_rooms()
        
        assert stats["active_rooms"] == 3
    
    @pytest.mark.asyncio
    async def test_server_health_with_none_values(self, metrics_service, mock_redis):
        """Test server health handles None values."""
        mock_redis.get.side_effect = [None, None, None]
        
        health = await metrics_service.get_server_health()
        
        assert health["cpu"] == 0
        assert health["memory"] == 0
        assert health["latency"] == 0
        assert health["status"] == "healthy"  # All zeros = healthy
