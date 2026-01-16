"""Type definitions for detection services.

Provides structured return types for bot detection, anomaly detection,
chip dumping detection, and anti-collusion services.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class DetectionReason(str, Enum):
    """Reasons for detection flags."""
    # Bot detection reasons
    VERY_CONSISTENT_TIMING = "very_consistent_timing"
    SUPERHUMAN_REACTION = "superhuman_reaction"
    NARROW_TIME_RANGE = "narrow_time_range"
    EXCESSIVE_FOLDING = "excessive_folding"
    NEVER_FOLDS = "never_folds"
    EXCESSIVE_RAISING = "excessive_raising"
    EXCESSIVE_DAILY_PLAY = "excessive_daily_play"
    SUPERHUMAN_SESSION = "superhuman_session"
    ROBOTIC_SCHEDULE = "robotic_schedule"
    
    # Anomaly detection reasons
    HIGH_WIN_RATE = "high_win_rate"
    LOW_WIN_RATE = "low_win_rate"
    EXCESSIVE_PROFIT = "excessive_profit"
    CONSTANT_BET_SIZE = "constant_bet_size"
    REPETITIVE_BETTING = "repetitive_betting"
    
    # Error/insufficient data
    INSUFFICIENT_DATA = "insufficient_data"
    ERROR = "error"
    NO_ACTIONS = "no_actions"
    USER_NOT_FOUND = "user_not_found_or_insufficient_hands"
    INSUFFICIENT_POPULATION = "insufficient_population"


class Severity(str, Enum):
    """Severity levels for suspicious activities."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DetectionType(str, Enum):
    """Types of detection."""
    ONE_WAY_CHIP_FLOW = "one_way_chip_flow"
    SOFT_PLAY = "soft_play"
    INTENTIONAL_LOSS = "intentional_loss"
    SAME_IP = "same_ip"
    SAME_DEVICE = "same_device"
    FREQUENT_SAME_TABLE = "frequent_same_table"
    SAME_IP_COLLUSION = "same_ip_collusion"
    SAME_DEVICE_COLLUSION = "same_device_collusion"
    CHIP_DUMPING_ONE_WAY = "chip_dumping_one_way"
    CHIP_DUMPING_SOFT_PLAY = "chip_dumping_soft_play"


# ============== Bot Detection Types ==============

@dataclass(frozen=True)
class ResponseTimeAnalysis:
    """Result of response time analysis for bot detection."""
    user_id: str
    sample_size: int
    is_suspicious: bool
    avg_response_time_ms: Optional[float] = None
    std_dev_ms: Optional[float] = None
    min_time_ms: Optional[int] = None
    max_time_ms: Optional[int] = None
    reasons: tuple[str, ...] = field(default_factory=tuple)
    error_reason: Optional[str] = None


@dataclass(frozen=True)
class ActionPatternAnalysis:
    """Result of action pattern analysis for bot detection."""
    user_id: str
    is_suspicious: bool
    total_actions: int = 0
    action_ratios: Dict[str, float] = field(default_factory=dict)
    reasons: tuple[str, ...] = field(default_factory=tuple)
    error_reason: Optional[str] = None


@dataclass(frozen=True)
class SessionPatternAnalysis:
    """Result of session pattern analysis for bot detection."""
    user_id: str
    is_suspicious: bool
    days_analyzed: int = 0
    avg_daily_hours: float = 0.0
    max_daily_hours: float = 0.0
    reasons: tuple[str, ...] = field(default_factory=tuple)
    error_reason: Optional[str] = None


@dataclass(frozen=True)
class BotDetectionResult:
    """Comprehensive bot detection result."""
    user_id: str
    suspicion_score: int
    is_likely_bot: bool
    reasons: tuple[str, ...] = field(default_factory=tuple)
    response_analysis: Optional[ResponseTimeAnalysis] = None
    action_analysis: Optional[ActionPatternAnalysis] = None
    session_analysis: Optional[SessionPatternAnalysis] = None


# ============== Anomaly Detection Types ==============

@dataclass(frozen=True)
class WinRateAnomalyResult:
    """Result of win rate anomaly detection."""
    user_id: str
    is_anomaly: bool
    user_win_rate: Optional[float] = None
    population_mean: Optional[float] = None
    population_std_dev: Optional[float] = None
    z_score: Optional[float] = None
    total_hands: int = 0
    anomaly_type: Optional[str] = None
    error_reason: Optional[str] = None


@dataclass(frozen=True)
class ProfitAnomalyResult:
    """Result of profit anomaly detection."""
    user_id: str
    is_anomaly: bool
    user_net_profit: Optional[float] = None
    population_mean: Optional[float] = None
    population_std_dev: Optional[float] = None
    z_score: Optional[float] = None
    total_hands: int = 0
    anomaly_type: Optional[str] = None
    error_reason: Optional[str] = None


@dataclass(frozen=True)
class BettingPatternAnomalyResult:
    """Result of betting pattern anomaly detection."""
    user_id: str
    is_anomaly: bool
    sample_size: int = 0
    mean_bet: float = 0.0
    std_dev: float = 0.0
    coefficient_of_variation: float = 0.0
    max_consecutive_same_bet: int = 0
    reasons: tuple[str, ...] = field(default_factory=tuple)
    error_reason: Optional[str] = None


@dataclass(frozen=True)
class FullAnomalyDetectionResult:
    """Comprehensive anomaly detection result."""
    user_id: str
    anomaly_count: int
    is_suspicious: bool
    win_rate_analysis: Optional[WinRateAnomalyResult] = None
    profit_analysis: Optional[ProfitAnomalyResult] = None
    betting_analysis: Optional[BettingPatternAnomalyResult] = None


# ============== Chip Dumping Detection Types ==============

@dataclass(frozen=True)
class OneWayChipFlowPattern:
    """Pattern of one-way chip flow between players."""
    loser_id: str
    winner_id: str
    total_hands: int
    winner_wins: int
    win_rate: float
    detection_type: str = DetectionType.ONE_WAY_CHIP_FLOW.value


@dataclass(frozen=True)
class SoftPlayPattern:
    """Pattern of soft play between players."""
    player1_id: str
    player2_id: str
    total_hands: int
    avg_combined_bet: float
    avg_pot_size: float
    bet_ratio: float
    detection_type: str = DetectionType.SOFT_PLAY.value


@dataclass(frozen=True)
class IntentionalLossPattern:
    """Pattern of intentional loss (folding strong hands)."""
    hand_id: str
    cards: str
    bet_amount: float
    pot_size: float
    created_at: Optional[str] = None
    detection_type: str = DetectionType.INTENTIONAL_LOSS.value


@dataclass(frozen=True)
class ChipDumpingScanResult:
    """Result of chip dumping scan."""
    one_way_flow_patterns: int
    soft_play_patterns: int
    flagged_count: int


# ============== Anti-Collusion Types ==============

@dataclass(frozen=True)
class SameIPGroup:
    """Group of players from same IP address."""
    ip_address: str
    user_ids: tuple[str, ...]
    user_count: int
    room_id: str
    detection_type: str = DetectionType.SAME_IP.value


@dataclass(frozen=True)
class SameDeviceGroup:
    """Group of players from same device."""
    device_id: str
    user_ids: tuple[str, ...]
    user_count: int
    room_id: str
    detection_type: str = DetectionType.SAME_DEVICE.value


@dataclass(frozen=True)
class FrequentSameTablePattern:
    """Pattern of players frequently at same table."""
    user_id: str
    other_user_id: str
    same_table_count: int
    detection_type: str = DetectionType.FREQUENT_SAME_TABLE.value


@dataclass(frozen=True)
class CollusionScanResult:
    """Result of collusion scan."""
    room_id: str
    same_ip_groups: int
    same_device_groups: int
    flagged_count: int
