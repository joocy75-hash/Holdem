"""
Bot Detector Tests - 봇 탐지 서비스 테스트
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.services.bot_detector import BotDetector


class TestAnalyzeResponseTimes:
    """analyze_response_times 메서드 테스트"""
    
    @pytest.fixture
    def mock_main_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_admin_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def service(self, mock_main_db, mock_admin_db):
        return BotDetector(mock_main_db, mock_admin_db)
    
    @pytest.mark.asyncio
    async def test_detects_consistent_timing(self, service, mock_main_db):
        """일정한 응답 시간 탐지"""
        # 매우 일정한 응답 시간 (봇 의심)
        mock_rows = [MagicMock(response_time_ms=500 + i % 10) for i in range(30)]
        
        result = MagicMock()
        result.fetchall.return_value = mock_rows
        mock_main_db.execute.return_value = result
        
        analysis = await service.analyze_response_times("user-1")
        
        assert analysis["sample_size"] == 30
        assert "avg_response_time_ms" in analysis
        assert "std_dev_ms" in analysis
    
    @pytest.mark.asyncio
    async def test_insufficient_data(self, service, mock_main_db):
        """데이터 부족 시 처리"""
        mock_rows = [MagicMock(response_time_ms=500) for _ in range(5)]
        
        result = MagicMock()
        result.fetchall.return_value = mock_rows
        mock_main_db.execute.return_value = result
        
        analysis = await service.analyze_response_times("user-1")
        
        assert analysis["is_suspicious"] is False
        assert analysis["reason"] == "insufficient_data"
    
    @pytest.mark.asyncio
    async def test_handles_exception(self, service, mock_main_db):
        """예외 발생 시 처리"""
        mock_main_db.execute.side_effect = Exception("Database error")
        
        analysis = await service.analyze_response_times("user-1")
        
        assert analysis["is_suspicious"] is False
        assert analysis["reason"] == "error"


class TestAnalyzeActionPatterns:
    """analyze_action_patterns 메서드 테스트"""
    
    @pytest.fixture
    def mock_main_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_admin_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def service(self, mock_main_db, mock_admin_db):
        return BotDetector(mock_main_db, mock_admin_db)
    
    @pytest.mark.asyncio
    async def test_detects_excessive_folding(self, service, mock_main_db):
        """과도한 폴드 탐지"""
        mock_rows = [
            MagicMock(action_type="fold", count=90),
            MagicMock(action_type="call", count=10),
        ]
        
        result = MagicMock()
        result.fetchall.return_value = mock_rows
        mock_main_db.execute.return_value = result
        
        analysis = await service.analyze_action_patterns("user-1")
        
        assert analysis["is_suspicious"] is True
        assert "excessive_folding" in analysis["reasons"]
    
    @pytest.mark.asyncio
    async def test_no_actions(self, service, mock_main_db):
        """액션 없을 때 처리"""
        result = MagicMock()
        result.fetchall.return_value = []
        mock_main_db.execute.return_value = result
        
        analysis = await service.analyze_action_patterns("user-1")
        
        assert analysis["is_suspicious"] is False
        assert analysis["reason"] == "no_actions"


class TestAnalyzeSessionPatterns:
    """analyze_session_patterns 메서드 테스트"""
    
    @pytest.fixture
    def mock_main_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_admin_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def service(self, mock_main_db, mock_admin_db):
        return BotDetector(mock_main_db, mock_admin_db)
    
    @pytest.mark.asyncio
    async def test_detects_excessive_play(self, service, mock_main_db):
        """과도한 플레이 시간 탐지"""
        mock_rows = [
            MagicMock(play_date=datetime(2026, 1, i), session_count=5, total_hours=15)
            for i in range(1, 8)
        ]
        
        result = MagicMock()
        result.fetchall.return_value = mock_rows
        mock_main_db.execute.return_value = result
        
        analysis = await service.analyze_session_patterns("user-1")
        
        assert analysis["is_suspicious"] is True
        assert "excessive_daily_play" in analysis["reasons"]
    
    @pytest.mark.asyncio
    async def test_insufficient_data(self, service, mock_main_db):
        """데이터 부족 시 처리"""
        mock_rows = [MagicMock(play_date=datetime(2026, 1, 1), session_count=1, total_hours=2)]
        
        result = MagicMock()
        result.fetchall.return_value = mock_rows
        mock_main_db.execute.return_value = result
        
        analysis = await service.analyze_session_patterns("user-1")
        
        assert analysis["is_suspicious"] is False
        assert analysis["reason"] == "insufficient_data"


class TestRunBotDetection:
    """run_bot_detection 메서드 테스트"""
    
    @pytest.fixture
    def mock_main_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_admin_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def service(self, mock_main_db, mock_admin_db):
        return BotDetector(mock_main_db, mock_admin_db)
    
    @pytest.mark.asyncio
    async def test_runs_full_detection(self, service, mock_main_db):
        """전체 탐지 실행"""
        result = MagicMock()
        result.fetchall.return_value = []
        mock_main_db.execute.return_value = result
        
        detection_result = await service.run_bot_detection("user-1")
        
        assert "user_id" in detection_result
        assert "suspicion_score" in detection_result
        assert "is_likely_bot" in detection_result
        assert "response_analysis" in detection_result
        assert "action_analysis" in detection_result
        assert "session_analysis" in detection_result
