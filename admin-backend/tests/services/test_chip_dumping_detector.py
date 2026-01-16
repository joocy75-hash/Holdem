"""
Chip Dumping Detector Tests - 칩 밀어주기 탐지 서비스 테스트
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.services.chip_dumping_detector import ChipDumpingDetector


class TestDetectOneWayChipFlow:
    """detect_one_way_chip_flow 메서드 테스트"""
    
    @pytest.fixture
    def mock_main_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_admin_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def service(self, mock_main_db, mock_admin_db):
        return ChipDumpingDetector(mock_main_db, mock_admin_db)
    
    @pytest.mark.asyncio
    async def test_detects_one_way_flow(self, service, mock_main_db):
        """일방적 칩 흐름 탐지"""
        mock_row = MagicMock()
        mock_row.loser_id = "user-1"
        mock_row.winner_id = "user-2"
        mock_row.total_hands = 10
        mock_row.winner_wins = 9
        mock_row.win_rate = 0.9
        
        result = MagicMock()
        result.fetchall.return_value = [mock_row]
        mock_main_db.execute.return_value = result
        
        patterns = await service.detect_one_way_chip_flow()
        
        assert len(patterns) == 1
        assert patterns[0]["loser_id"] == "user-1"
        assert patterns[0]["winner_id"] == "user-2"
        assert patterns[0]["win_rate"] == 0.9
        assert patterns[0]["detection_type"] == "one_way_chip_flow"
    
    @pytest.mark.asyncio
    async def test_returns_empty_on_no_matches(self, service, mock_main_db):
        """매칭 없을 때 빈 목록 반환"""
        result = MagicMock()
        result.fetchall.return_value = []
        mock_main_db.execute.return_value = result
        
        patterns = await service.detect_one_way_chip_flow()
        
        assert patterns == []
    
    @pytest.mark.asyncio
    async def test_handles_exception(self, service, mock_main_db):
        """예외 발생 시 빈 목록 반환"""
        mock_main_db.execute.side_effect = Exception("Database error")
        
        patterns = await service.detect_one_way_chip_flow()
        
        assert patterns == []


class TestDetectSoftPlay:
    """detect_soft_play 메서드 테스트"""
    
    @pytest.fixture
    def mock_main_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_admin_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def service(self, mock_main_db, mock_admin_db):
        return ChipDumpingDetector(mock_main_db, mock_admin_db)
    
    @pytest.mark.asyncio
    async def test_detects_soft_play(self, service, mock_main_db):
        """소프트 플레이 탐지"""
        mock_row = MagicMock()
        mock_row.player1_id = "user-1"
        mock_row.player2_id = "user-2"
        mock_row.total_hands = 15
        mock_row.avg_combined_bet = 10.0
        mock_row.avg_pot_size = 100.0
        mock_row.bet_ratio = 0.2
        
        result = MagicMock()
        result.fetchall.return_value = [mock_row]
        mock_main_db.execute.return_value = result
        
        patterns = await service.detect_soft_play()
        
        assert len(patterns) == 1
        assert patterns[0]["player1_id"] == "user-1"
        assert patterns[0]["player2_id"] == "user-2"
        assert patterns[0]["detection_type"] == "soft_play"


class TestDetectIntentionalLoss:
    """detect_intentional_loss 메서드 테스트"""
    
    @pytest.fixture
    def mock_main_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_admin_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def service(self, mock_main_db, mock_admin_db):
        return ChipDumpingDetector(mock_main_db, mock_admin_db)
    
    @pytest.mark.asyncio
    async def test_detects_intentional_loss(self, service, mock_main_db):
        """의도적 패배 탐지"""
        mock_row = MagicMock()
        mock_row.hand_id = "hand-123"
        mock_row.cards = "As Ah"  # 포켓 에이스
        mock_row.bet_amount = 5.0
        mock_row.won_amount = 0.0
        mock_row.pot_size = 100.0
        mock_row.created_at = datetime(2026, 1, 15)
        
        result = MagicMock()
        result.fetchall.return_value = [mock_row]
        mock_main_db.execute.return_value = result
        
        hands = await service.detect_intentional_loss("user-1")
        
        assert len(hands) == 1
        assert hands[0]["cards"] == "As Ah"
        assert hands[0]["detection_type"] == "intentional_loss"


class TestIsStrongHand:
    """_is_strong_hand 메서드 테스트"""
    
    @pytest.fixture
    def service(self):
        return ChipDumpingDetector(AsyncMock(), AsyncMock())
    
    def test_pocket_pair_is_strong(self, service):
        """포켓 페어는 강한 핸드"""
        assert service._is_strong_hand("As Ah") is True
        assert service._is_strong_hand("Ks Kh") is True
        assert service._is_strong_hand("2s 2h") is True
    
    def test_high_cards_are_strong(self, service):
        """높은 카드 조합은 강한 핸드"""
        assert service._is_strong_hand("As Kh") is True
        assert service._is_strong_hand("Ks Qh") is True
        assert service._is_strong_hand("As Qh") is True
    
    def test_low_cards_are_not_strong(self, service):
        """낮은 카드 조합은 약한 핸드"""
        assert service._is_strong_hand("7s 2h") is False
        assert service._is_strong_hand("9s 3h") is False
    
    def test_empty_cards_not_strong(self, service):
        """빈 카드는 강하지 않음"""
        assert service._is_strong_hand("") is False
        assert service._is_strong_hand(None) is False


class TestFlagChipDumping:
    """flag_chip_dumping 메서드 테스트"""
    
    @pytest.fixture
    def mock_main_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_admin_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def service(self, mock_main_db, mock_admin_db):
        return ChipDumpingDetector(mock_main_db, mock_admin_db)
    
    @pytest.mark.asyncio
    async def test_flags_chip_dumping(self, service, mock_admin_db):
        """칩 밀어주기 플래깅"""
        flag_id = await service.flag_chip_dumping(
            detection_type="chip_dumping_one_way",
            user_ids=["user-1", "user-2"],
            details={"win_rate": 0.95},
            severity="high"
        )
        
        assert flag_id != ""
        assert mock_admin_db.commit.called


class TestRunChipDumpingScan:
    """run_chip_dumping_scan 메서드 테스트"""
    
    @pytest.fixture
    def mock_main_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_admin_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def service(self, mock_main_db, mock_admin_db):
        return ChipDumpingDetector(mock_main_db, mock_admin_db)
    
    @pytest.mark.asyncio
    async def test_runs_full_scan(self, service, mock_main_db, mock_admin_db):
        """전체 스캔 실행"""
        result = MagicMock()
        result.fetchall.return_value = []
        mock_main_db.execute.return_value = result
        
        scan_result = await service.run_chip_dumping_scan()
        
        assert "one_way_flow_patterns" in scan_result
        assert "soft_play_patterns" in scan_result
        assert "flagged_count" in scan_result
