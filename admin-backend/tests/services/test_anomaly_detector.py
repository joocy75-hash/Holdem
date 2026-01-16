"""
Anomaly Detector Tests - 이상 탐지 서비스 테스트
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.services.anomaly_detector import AnomalyDetector


class TestDetectWinRateAnomaly:
    """detect_win_rate_anomaly 메서드 테스트"""
    
    @pytest.fixture
    def mock_main_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_admin_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def service(self, mock_main_db, mock_admin_db):
        return AnomalyDetector(mock_main_db, mock_admin_db)
    
    @pytest.mark.asyncio
    async def test_detects_high_win_rate(self, service, mock_main_db):
        """높은 승률 이상 탐지"""
        # 대부분 플레이어는 30% 승률, 대상 플레이어는 80% 승률
        mock_rows = [
            MagicMock(user_id=f"user-{i}", total_hands=100, wins=30, win_rate=0.3)
            for i in range(20)
        ]
        mock_rows.append(MagicMock(user_id="target-user", total_hands=100, wins=80, win_rate=0.8))
        
        result = MagicMock()
        result.fetchall.return_value = mock_rows
        mock_main_db.execute.return_value = result
        
        analysis = await service.detect_win_rate_anomaly("target-user")
        
        assert "user_win_rate" in analysis
        assert "z_score" in analysis
        assert analysis["user_win_rate"] == 0.8
    
    @pytest.mark.asyncio
    async def test_insufficient_population(self, service, mock_main_db):
        """인구 부족 시 처리"""
        mock_rows = [MagicMock(user_id="user-1", total_hands=100, wins=30, win_rate=0.3)]
        
        result = MagicMock()
        result.fetchall.return_value = mock_rows
        mock_main_db.execute.return_value = result
        
        analysis = await service.detect_win_rate_anomaly("user-1")
        
        assert analysis["is_anomaly"] is False
        assert analysis["reason"] == "insufficient_population"
    
    @pytest.mark.asyncio
    async def test_handles_exception(self, service, mock_main_db):
        """예외 발생 시 처리"""
        mock_main_db.execute.side_effect = Exception("Database error")
        
        analysis = await service.detect_win_rate_anomaly("user-1")
        
        assert analysis["is_anomaly"] is False
        assert analysis["reason"] == "error"


class TestDetectProfitAnomaly:
    """detect_profit_anomaly 메서드 테스트"""
    
    @pytest.fixture
    def mock_main_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_admin_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def service(self, mock_main_db, mock_admin_db):
        return AnomalyDetector(mock_main_db, mock_admin_db)
    
    @pytest.mark.asyncio
    async def test_detects_excessive_profit(self, service, mock_main_db):
        """과도한 수익 이상 탐지"""
        mock_rows = [
            MagicMock(user_id=f"user-{i}", net_profit=-100 + i * 10, total_hands=100)
            for i in range(20)
        ]
        mock_rows.append(MagicMock(user_id="target-user", net_profit=10000, total_hands=100))
        
        result = MagicMock()
        result.fetchall.return_value = mock_rows
        mock_main_db.execute.return_value = result
        
        analysis = await service.detect_profit_anomaly("target-user")
        
        assert "user_net_profit" in analysis
        assert "z_score" in analysis


class TestDetectBettingPatternAnomaly:
    """detect_betting_pattern_anomaly 메서드 테스트"""
    
    @pytest.fixture
    def mock_main_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_admin_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def service(self, mock_main_db, mock_admin_db):
        return AnomalyDetector(mock_main_db, mock_admin_db)
    
    @pytest.mark.asyncio
    async def test_detects_constant_betting(self, service, mock_main_db):
        """일정한 베팅 패턴 탐지"""
        # 항상 같은 금액 베팅
        mock_rows = [MagicMock(bet_amount=100.0) for _ in range(50)]
        
        result = MagicMock()
        result.fetchall.return_value = mock_rows
        mock_main_db.execute.return_value = result
        
        analysis = await service.detect_betting_pattern_anomaly("user-1")
        
        assert analysis["is_anomaly"] is True
        assert "constant_bet_size" in analysis["reasons"]
    
    @pytest.mark.asyncio
    async def test_detects_repetitive_betting(self, service, mock_main_db):
        """반복적인 베팅 패턴 탐지"""
        # 연속 15회 같은 금액 베팅
        mock_rows = [MagicMock(bet_amount=100.0) for _ in range(15)]
        mock_rows.extend([MagicMock(bet_amount=200.0) for _ in range(10)])
        
        result = MagicMock()
        result.fetchall.return_value = mock_rows
        mock_main_db.execute.return_value = result
        
        analysis = await service.detect_betting_pattern_anomaly("user-1")
        
        assert analysis["max_consecutive_same_bet"] >= 10
    
    @pytest.mark.asyncio
    async def test_insufficient_data(self, service, mock_main_db):
        """데이터 부족 시 처리"""
        mock_rows = [MagicMock(bet_amount=100.0) for _ in range(5)]
        
        result = MagicMock()
        result.fetchall.return_value = mock_rows
        mock_main_db.execute.return_value = result
        
        analysis = await service.detect_betting_pattern_anomaly("user-1")
        
        assert analysis["is_anomaly"] is False
        assert analysis["reason"] == "insufficient_data"


class TestRunFullAnomalyDetection:
    """run_full_anomaly_detection 메서드 테스트"""
    
    @pytest.fixture
    def mock_main_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_admin_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def service(self, mock_main_db, mock_admin_db):
        return AnomalyDetector(mock_main_db, mock_admin_db)
    
    @pytest.mark.asyncio
    async def test_runs_full_detection(self, service, mock_main_db):
        """전체 이상 탐지 실행"""
        result = MagicMock()
        result.fetchall.return_value = []
        mock_main_db.execute.return_value = result
        
        detection_result = await service.run_full_anomaly_detection("user-1")
        
        assert "user_id" in detection_result
        assert "anomaly_count" in detection_result
        assert "is_suspicious" in detection_result
        assert "win_rate_analysis" in detection_result
        assert "profit_analysis" in detection_result
        assert "betting_analysis" in detection_result
