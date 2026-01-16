"""
Anti-Collusion Service Tests - 공모 탐지 서비스 테스트
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.services.anti_collusion import AntiCollusionService


class TestDetectSameIpPlayers:
    """detect_same_ip_players 메서드 테스트"""
    
    @pytest.fixture
    def mock_main_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_admin_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def service(self, mock_main_db, mock_admin_db):
        return AntiCollusionService(mock_main_db, mock_admin_db)
    
    @pytest.mark.asyncio
    async def test_detects_same_ip_players(self, service, mock_main_db):
        """동일 IP 플레이어 탐지"""
        mock_row = MagicMock()
        mock_row.ip_address = "192.168.1.1"
        mock_row.user_ids = ["user-1", "user-2"]
        mock_row.user_count = 2
        
        result = MagicMock()
        result.fetchall.return_value = [mock_row]
        mock_main_db.execute.return_value = result
        
        groups = await service.detect_same_ip_players("room-123")
        
        assert len(groups) == 1
        assert groups[0]["ip_address"] == "192.168.1.1"
        assert groups[0]["user_count"] == 2
        assert groups[0]["detection_type"] == "same_ip"
    
    @pytest.mark.asyncio
    async def test_returns_empty_on_no_matches(self, service, mock_main_db):
        """매칭 없을 때 빈 목록 반환"""
        result = MagicMock()
        result.fetchall.return_value = []
        mock_main_db.execute.return_value = result
        
        groups = await service.detect_same_ip_players("room-123")
        
        assert groups == []
    
    @pytest.mark.asyncio
    async def test_handles_exception(self, service, mock_main_db):
        """예외 발생 시 빈 목록 반환"""
        mock_main_db.execute.side_effect = Exception("Database error")
        
        groups = await service.detect_same_ip_players("room-123")
        
        assert groups == []


class TestDetectSameDevicePlayers:
    """detect_same_device_players 메서드 테스트"""
    
    @pytest.fixture
    def mock_main_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_admin_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def service(self, mock_main_db, mock_admin_db):
        return AntiCollusionService(mock_main_db, mock_admin_db)
    
    @pytest.mark.asyncio
    async def test_detects_same_device_players(self, service, mock_main_db):
        """동일 기기 플레이어 탐지"""
        mock_row = MagicMock()
        mock_row.device_id = "device-abc123"
        mock_row.user_ids = ["user-1", "user-2", "user-3"]
        mock_row.user_count = 3
        
        result = MagicMock()
        result.fetchall.return_value = [mock_row]
        mock_main_db.execute.return_value = result
        
        groups = await service.detect_same_device_players("room-123")
        
        assert len(groups) == 1
        assert groups[0]["device_id"] == "device-abc123"
        assert groups[0]["user_count"] == 3
        assert groups[0]["detection_type"] == "same_device"


class TestDetectFrequentSameTable:
    """detect_frequent_same_table 메서드 테스트"""
    
    @pytest.fixture
    def mock_main_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_admin_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def service(self, mock_main_db, mock_admin_db):
        return AntiCollusionService(mock_main_db, mock_admin_db)
    
    @pytest.mark.asyncio
    async def test_detects_frequent_same_table(self, service, mock_main_db):
        """자주 같은 테이블에 앉는 플레이어 탐지"""
        mock_row = MagicMock()
        mock_row.other_user_id = "user-2"
        mock_row.same_table_count = 10
        
        result = MagicMock()
        result.fetchall.return_value = [mock_row]
        mock_main_db.execute.return_value = result
        
        players = await service.detect_frequent_same_table("user-1")
        
        assert len(players) == 1
        assert players[0]["other_user_id"] == "user-2"
        assert players[0]["same_table_count"] == 10
        assert players[0]["detection_type"] == "frequent_same_table"


class TestFlagSuspiciousActivity:
    """flag_suspicious_activity 메서드 테스트"""
    
    @pytest.fixture
    def mock_main_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_admin_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def service(self, mock_main_db, mock_admin_db):
        return AntiCollusionService(mock_main_db, mock_admin_db)
    
    @pytest.mark.asyncio
    async def test_flags_suspicious_activity(self, service, mock_admin_db):
        """의심 활동 플래깅"""
        flag_id = await service.flag_suspicious_activity(
            detection_type="same_ip_collusion",
            user_ids=["user-1", "user-2"],
            details={"ip_address": "192.168.1.1"},
            severity="high"
        )
        
        assert flag_id != ""
        assert mock_admin_db.commit.called
    
    @pytest.mark.asyncio
    async def test_handles_exception(self, service, mock_admin_db):
        """예외 발생 시 빈 문자열 반환"""
        mock_admin_db.execute.side_effect = Exception("Database error")
        
        flag_id = await service.flag_suspicious_activity(
            detection_type="same_ip_collusion",
            user_ids=["user-1"],
            details={}
        )
        
        assert flag_id == ""


class TestRunCollusionScan:
    """run_collusion_scan 메서드 테스트"""
    
    @pytest.fixture
    def mock_main_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_admin_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def service(self, mock_main_db, mock_admin_db):
        return AntiCollusionService(mock_main_db, mock_admin_db)
    
    @pytest.mark.asyncio
    async def test_runs_full_scan(self, service, mock_main_db, mock_admin_db):
        """전체 스캔 실행"""
        # Mock empty results
        result = MagicMock()
        result.fetchall.return_value = []
        mock_main_db.execute.return_value = result
        
        scan_result = await service.run_collusion_scan("room-123")
        
        assert scan_result["room_id"] == "room-123"
        assert "same_ip_groups" in scan_result
        assert "same_device_groups" in scan_result
        assert "flagged_count" in scan_result
