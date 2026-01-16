"""Tests for detection service type definitions."""

import pytest
from dataclasses import FrozenInstanceError

from app.services.detection_types import (
    # Enums
    DetectionReason,
    Severity,
    DetectionType,
    # Bot detection
    ResponseTimeAnalysis,
    ActionPatternAnalysis,
    SessionPatternAnalysis,
    BotDetectionResult,
    # Anomaly detection
    WinRateAnomalyResult,
    ProfitAnomalyResult,
    BettingPatternAnomalyResult,
    FullAnomalyDetectionResult,
    # Chip dumping
    OneWayChipFlowPattern,
    SoftPlayPattern,
    IntentionalLossPattern,
    ChipDumpingScanResult,
    # Anti-collusion
    SameIPGroup,
    SameDeviceGroup,
    FrequentSameTablePattern,
    CollusionScanResult,
)


class TestEnums:
    """Test enum definitions."""

    def test_detection_reason_values(self):
        """Test DetectionReason enum has expected values."""
        assert DetectionReason.VERY_CONSISTENT_TIMING.value == "very_consistent_timing"
        assert DetectionReason.SUPERHUMAN_REACTION.value == "superhuman_reaction"
        assert DetectionReason.EXCESSIVE_PROFIT.value == "excessive_profit"

    def test_severity_values(self):
        """Test Severity enum has expected values."""
        assert Severity.LOW.value == "low"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.HIGH.value == "high"

    def test_detection_type_values(self):
        """Test DetectionType enum has expected values."""
        assert DetectionType.ONE_WAY_CHIP_FLOW.value == "one_way_chip_flow"
        assert DetectionType.SAME_IP.value == "same_ip"
        assert DetectionType.CHIP_DUMPING_ONE_WAY.value == "chip_dumping_one_way"


class TestBotDetectionTypes:
    """Test bot detection type definitions."""

    def test_response_time_analysis_creation(self):
        """Test ResponseTimeAnalysis can be created."""
        result = ResponseTimeAnalysis(
            user_id="user-123",
            sample_size=50,
            is_suspicious=True,
            avg_response_time_ms=150.5,
            std_dev_ms=10.2,
            min_time_ms=100,
            max_time_ms=200,
            reasons=("very_consistent_timing",),
        )
        
        assert result.user_id == "user-123"
        assert result.sample_size == 50
        assert result.is_suspicious is True
        assert result.avg_response_time_ms == 150.5
        assert "very_consistent_timing" in result.reasons

    def test_response_time_analysis_immutable(self):
        """Test ResponseTimeAnalysis is immutable."""
        result = ResponseTimeAnalysis(
            user_id="user-123",
            sample_size=50,
            is_suspicious=False,
        )
        
        with pytest.raises(FrozenInstanceError):
            result.is_suspicious = True

    def test_action_pattern_analysis_creation(self):
        """Test ActionPatternAnalysis can be created."""
        result = ActionPatternAnalysis(
            user_id="user-123",
            is_suspicious=True,
            total_actions=100,
            action_ratios={"fold": 0.8, "call": 0.15, "raise": 0.05},
            reasons=("excessive_folding",),
        )
        
        assert result.total_actions == 100
        assert result.action_ratios["fold"] == 0.8

    def test_bot_detection_result_creation(self):
        """Test BotDetectionResult can be created."""
        response = ResponseTimeAnalysis(
            user_id="user-123",
            sample_size=50,
            is_suspicious=True,
        )
        
        result = BotDetectionResult(
            user_id="user-123",
            suspicion_score=70,
            is_likely_bot=True,
            reasons=("very_consistent_timing", "excessive_folding"),
            response_analysis=response,
        )
        
        assert result.suspicion_score == 70
        assert result.is_likely_bot is True
        assert len(result.reasons) == 2


class TestAnomalyDetectionTypes:
    """Test anomaly detection type definitions."""

    def test_win_rate_anomaly_result_creation(self):
        """Test WinRateAnomalyResult can be created."""
        result = WinRateAnomalyResult(
            user_id="user-123",
            is_anomaly=True,
            user_win_rate=0.75,
            population_mean=0.45,
            population_std_dev=0.08,
            z_score=3.75,
            total_hands=100,
            anomaly_type="high_win_rate",
        )
        
        assert result.is_anomaly is True
        assert result.z_score == 3.75
        assert result.anomaly_type == "high_win_rate"

    def test_profit_anomaly_result_creation(self):
        """Test ProfitAnomalyResult can be created."""
        result = ProfitAnomalyResult(
            user_id="user-123",
            is_anomaly=True,
            user_net_profit=50000.0,
            population_mean=1000.0,
            z_score=4.5,
        )
        
        assert result.user_net_profit == 50000.0

    def test_full_anomaly_detection_result_creation(self):
        """Test FullAnomalyDetectionResult can be created."""
        win_rate = WinRateAnomalyResult(
            user_id="user-123",
            is_anomaly=True,
        )
        
        result = FullAnomalyDetectionResult(
            user_id="user-123",
            anomaly_count=2,
            is_suspicious=True,
            win_rate_analysis=win_rate,
        )
        
        assert result.anomaly_count == 2
        assert result.is_suspicious is True


class TestChipDumpingTypes:
    """Test chip dumping detection type definitions."""

    def test_one_way_chip_flow_pattern_creation(self):
        """Test OneWayChipFlowPattern can be created."""
        pattern = OneWayChipFlowPattern(
            loser_id="user-1",
            winner_id="user-2",
            total_hands=20,
            winner_wins=18,
            win_rate=0.9,
        )
        
        assert pattern.loser_id == "user-1"
        assert pattern.winner_id == "user-2"
        assert pattern.win_rate == 0.9
        assert pattern.detection_type == "one_way_chip_flow"

    def test_soft_play_pattern_creation(self):
        """Test SoftPlayPattern can be created."""
        pattern = SoftPlayPattern(
            player1_id="user-1",
            player2_id="user-2",
            total_hands=30,
            avg_combined_bet=100.0,
            avg_pot_size=500.0,
            bet_ratio=0.2,
        )
        
        assert pattern.bet_ratio == 0.2
        assert pattern.detection_type == "soft_play"

    def test_chip_dumping_scan_result_creation(self):
        """Test ChipDumpingScanResult can be created."""
        result = ChipDumpingScanResult(
            one_way_flow_patterns=5,
            soft_play_patterns=3,
            flagged_count=8,
        )
        
        assert result.one_way_flow_patterns == 5
        assert result.flagged_count == 8


class TestAntiCollusionTypes:
    """Test anti-collusion type definitions."""

    def test_same_ip_group_creation(self):
        """Test SameIPGroup can be created."""
        group = SameIPGroup(
            ip_address="192.168.1.1",
            user_ids=("user-1", "user-2", "user-3"),
            user_count=3,
            room_id="room-123",
        )
        
        assert group.ip_address == "192.168.1.1"
        assert len(group.user_ids) == 3
        assert group.detection_type == "same_ip"

    def test_same_device_group_creation(self):
        """Test SameDeviceGroup can be created."""
        group = SameDeviceGroup(
            device_id="device-abc",
            user_ids=("user-1", "user-2"),
            user_count=2,
            room_id="room-123",
        )
        
        assert group.device_id == "device-abc"
        assert group.detection_type == "same_device"

    def test_collusion_scan_result_creation(self):
        """Test CollusionScanResult can be created."""
        result = CollusionScanResult(
            room_id="room-123",
            same_ip_groups=2,
            same_device_groups=1,
            flagged_count=3,
        )
        
        assert result.room_id == "room-123"
        assert result.flagged_count == 3


class TestImmutability:
    """Test that all dataclasses are immutable."""

    def test_all_types_are_frozen(self):
        """Test that all detection types are frozen dataclasses."""
        # Bot detection
        response = ResponseTimeAnalysis(user_id="u", sample_size=0, is_suspicious=False)
        with pytest.raises(FrozenInstanceError):
            response.user_id = "new"
        
        # Anomaly detection
        win_rate = WinRateAnomalyResult(user_id="u", is_anomaly=False)
        with pytest.raises(FrozenInstanceError):
            win_rate.is_anomaly = True
        
        # Chip dumping
        pattern = OneWayChipFlowPattern(
            loser_id="l", winner_id="w", total_hands=1, winner_wins=1, win_rate=1.0
        )
        with pytest.raises(FrozenInstanceError):
            pattern.win_rate = 0.5
        
        # Anti-collusion
        group = SameIPGroup(
            ip_address="1.1.1.1", user_ids=("u1",), user_count=1, room_id="r"
        )
        with pytest.raises(FrozenInstanceError):
            group.room_id = "new"
