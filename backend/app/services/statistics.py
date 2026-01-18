"""플레이어 통계 서비스.

포커 플레이 스타일 분석을 위한 통계 지표 계산.

주요 지표:
- VPIP: Voluntarily Put Money In Pot (자발적으로 팟에 돈을 넣은 비율)
- PFR: Pre-Flop Raise (프리플롭 레이즈 비율)
- 3Bet: 3벳 비율
- AF: Aggression Factor (공격성 지수)
- WTSD: Went to Showdown (쇼다운까지 간 비율)
- WSD: Won at Showdown (쇼다운에서 승리한 비율)
- Win Rate: 승률
- BB/100: 100핸드당 Big Blind 수익
"""

import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hand import HandParticipant

logger = logging.getLogger(__name__)


@dataclass
class PlayerStats:
    """플레이어 통계 데이터."""

    # 기본 정보
    total_hands: int = 0
    total_winnings: int = 0
    hands_won: int = 0
    biggest_pot: int = 0

    # 스타일 지표 (%)
    vpip: float = 0.0      # Voluntarily Put Money In Pot
    pfr: float = 0.0       # Pre-Flop Raise
    three_bet: float = 0.0 # 3-Bet %
    
    # 공격성
    af: float = 0.0        # Aggression Factor
    agg_freq: float = 0.0  # Aggression Frequency %

    # 쇼다운
    wtsd: float = 0.0      # Went to Showdown %
    wsd: float = 0.0       # Won at Showdown %
    
    # 수익성
    win_rate: float = 0.0  # 승률 %
    bb_per_100: float = 0.0  # BB/100

    # 포지션별 승률 (선택적)
    position_stats: dict[str, float] | None = None


class StatisticsService:
    """통계 서비스."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_player_stats(self, user_id: str) -> PlayerStats:
        """플레이어 전체 통계 조회.

        Args:
            user_id: 사용자 ID

        Returns:
            PlayerStats 객체
        """
        stats = PlayerStats()

        # 기본 통계 조회
        basic = await self._get_basic_stats(user_id)
        stats.total_hands = basic["total_hands"]
        stats.total_winnings = basic["total_winnings"]
        stats.hands_won = basic["hands_won"]
        stats.biggest_pot = basic["biggest_pot"]

        # VPIP, PFR 계산
        preflop = await self._get_preflop_stats(user_id)
        stats.vpip = preflop["vpip"]
        stats.pfr = preflop["pfr"]
        stats.three_bet = preflop["three_bet"]

        # 공격성 지표
        aggression = await self._get_aggression_stats(user_id)
        stats.af = aggression["af"]
        stats.agg_freq = aggression["agg_freq"]

        # 쇼다운 통계
        showdown = await self._get_showdown_stats(user_id)
        stats.wtsd = showdown["wtsd"]
        stats.wsd = showdown["wsd"]

        # 수익성 지표
        if stats.total_hands > 0:
            stats.win_rate = round(stats.hands_won / stats.total_hands * 100, 1)

        return stats

    async def get_stats_summary(self, user_id: str) -> dict[str, Any]:
        """통계 요약 (API용).

        Args:
            user_id: 사용자 ID

        Returns:
            통계 요약 딕셔너리
        """
        stats = await self.get_player_stats(user_id)

        return {
            # 기본 정보
            "totalHands": stats.total_hands,
            "totalWinnings": stats.total_winnings,
            "handsWon": stats.hands_won,
            "biggestPot": stats.biggest_pot,
            
            # 스타일 지표
            "vpip": stats.vpip,
            "pfr": stats.pfr,
            "threeBet": stats.three_bet,
            
            # 공격성
            "af": stats.af,
            "aggFreq": stats.agg_freq,
            
            # 쇼다운
            "wtsd": stats.wtsd,
            "wsd": stats.wsd,
            
            # 수익성
            "winRate": stats.win_rate,
            "bbPer100": stats.bb_per_100,
            
            # 플레이 스타일 분석
            "playStyle": self._analyze_play_style(stats),
        }

    async def _get_basic_stats(self, user_id: str) -> dict[str, int]:
        """기본 통계 (핸드 수, 승리 수, 수익)."""
        # 총 핸드 수
        total_result = await self.db.execute(
            select(func.count(HandParticipant.id))
            .where(HandParticipant.user_id == user_id)
        )
        total_hands = total_result.scalar() or 0

        # 승리 핸드 수
        won_result = await self.db.execute(
            select(func.count(HandParticipant.id))
            .where(HandParticipant.user_id == user_id)
            .where(HandParticipant.won_amount > 0)
        )
        hands_won = won_result.scalar() or 0

        # 총 수익
        winnings_result = await self.db.execute(
            select(func.sum(HandParticipant.won_amount - HandParticipant.bet_amount))
            .where(HandParticipant.user_id == user_id)
        )
        total_winnings = winnings_result.scalar() or 0

        # 가장 큰 팟
        biggest_result = await self.db.execute(
            select(func.max(HandParticipant.won_amount))
            .where(HandParticipant.user_id == user_id)
        )
        biggest_pot = biggest_result.scalar() or 0

        return {
            "total_hands": total_hands,
            "hands_won": hands_won,
            "total_winnings": total_winnings,
            "biggest_pot": biggest_pot,
        }

    async def _get_preflop_stats(self, user_id: str) -> dict[str, float]:
        """프리플롭 통계 (VPIP, PFR, 3Bet)."""
        query = text("""
            WITH user_hands AS (
                SELECT DISTINCT hp.hand_id
                FROM hand_participants hp
                WHERE hp.user_id = :user_id
            ),
            preflop_actions AS (
                SELECT
                    he.hand_id,
                    he.event_type,
                    (he.payload->>'user_id') as action_user_id,
                    he.seq_no
                FROM hand_events he
                JOIN user_hands uh ON he.hand_id = uh.hand_id
                WHERE he.event_type IN ('call', 'bet', 'raise', 'all_in', 'post_blind')
                  AND (
                      NOT EXISTS (
                          SELECT 1 FROM hand_events 
                          WHERE hand_id = he.hand_id AND event_type = 'deal_flop'
                      )
                      OR he.seq_no < (
                          SELECT MIN(seq_no) FROM hand_events
                          WHERE hand_id = he.hand_id AND event_type = 'deal_flop'
                      )
                  )
            ),
            raise_counts AS (
                SELECT hand_id, COUNT(*) as raise_count
                FROM preflop_actions
                WHERE event_type IN ('raise', 'bet')
                GROUP BY hand_id
            )
            SELECT
                -- VPIP: 자발적으로 팟에 돈 넣은 핸드
                COUNT(DISTINCT CASE
                    WHEN pa.action_user_id = CAST(:user_id AS text)
                         AND pa.event_type IN ('call', 'bet', 'raise', 'all_in')
                    THEN pa.hand_id
                END) as vpip_hands,
                -- PFR: 프리플롭 레이즈 핸드
                COUNT(DISTINCT CASE
                    WHEN pa.action_user_id = CAST(:user_id AS text)
                         AND pa.event_type IN ('bet', 'raise')
                    THEN pa.hand_id
                END) as pfr_hands,
                -- 3Bet: 레이즈 후 다시 레이즈
                COUNT(DISTINCT CASE
                    WHEN pa.action_user_id = CAST(:user_id AS text)
                         AND pa.event_type = 'raise'
                         AND rc.raise_count >= 2
                    THEN pa.hand_id
                END) as three_bet_hands,
                (SELECT COUNT(*) FROM user_hands) as total_hands
            FROM preflop_actions pa
            LEFT JOIN raise_counts rc ON pa.hand_id = rc.hand_id
        """)

        result = await self.db.execute(query, {"user_id": user_id})
        row = result.fetchone()

        if not row or row.total_hands == 0:
            return {"vpip": 0.0, "pfr": 0.0, "three_bet": 0.0}

        return {
            "vpip": round(row.vpip_hands / row.total_hands * 100, 1),
            "pfr": round(row.pfr_hands / row.total_hands * 100, 1),
            "three_bet": round(row.three_bet_hands / row.total_hands * 100, 1),
        }

    async def _get_aggression_stats(self, user_id: str) -> dict[str, float]:
        """공격성 통계 (AF, Aggression Frequency)."""
        query = text("""
            WITH user_actions AS (
                SELECT
                    he.event_type,
                    COUNT(*) as action_count
                FROM hand_events he
                JOIN hand_participants hp ON he.hand_id = hp.hand_id
                WHERE hp.user_id = :user_id
                  AND (he.payload->>'user_id') = CAST(:user_id AS text)
                  AND he.event_type IN ('bet', 'raise', 'call', 'check', 'fold')
                GROUP BY he.event_type
            )
            SELECT
                COALESCE(SUM(CASE WHEN event_type = 'bet' THEN action_count ELSE 0 END), 0) as bets,
                COALESCE(SUM(CASE WHEN event_type = 'raise' THEN action_count ELSE 0 END), 0) as raises,
                COALESCE(SUM(CASE WHEN event_type = 'call' THEN action_count ELSE 0 END), 0) as calls,
                COALESCE(SUM(CASE WHEN event_type = 'check' THEN action_count ELSE 0 END), 0) as checks,
                COALESCE(SUM(action_count), 0) as total_actions
            FROM user_actions
        """)

        result = await self.db.execute(query, {"user_id": user_id})
        row = result.fetchone()

        if not row or row.total_actions == 0:
            return {"af": 0.0, "agg_freq": 0.0}

        bets = row.bets or 0
        raises = row.raises or 0
        calls = row.calls or 0
        total = row.total_actions or 1

        # Aggression Factor = (Bets + Raises) / Calls
        af = (bets + raises) / calls if calls > 0 else (bets + raises)
        
        # Aggression Frequency = (Bets + Raises) / Total Actions
        agg_freq = (bets + raises) / total * 100 if total > 0 else 0

        return {
            "af": round(af, 2),
            "agg_freq": round(agg_freq, 1),
        }

    async def _get_showdown_stats(self, user_id: str) -> dict[str, float]:
        """쇼다운 통계 (WTSD, WSD)."""
        query = text("""
            WITH user_hands AS (
                SELECT hp.hand_id, hp.won_amount, hp.final_action
                FROM hand_participants hp
                WHERE hp.user_id = :user_id
            ),
            showdown_hands AS (
                SELECT uh.hand_id, uh.won_amount
                FROM user_hands uh
                WHERE uh.final_action = 'showdown'
            )
            SELECT
                (SELECT COUNT(*) FROM user_hands) as total_hands,
                (SELECT COUNT(*) FROM showdown_hands) as showdown_hands,
                (SELECT COUNT(*) FROM showdown_hands WHERE won_amount > 0) as won_showdowns
        """)

        result = await self.db.execute(query, {"user_id": user_id})
        row = result.fetchone()

        if not row or row.total_hands == 0:
            return {"wtsd": 0.0, "wsd": 0.0}

        wtsd = row.showdown_hands / row.total_hands * 100 if row.total_hands > 0 else 0
        wsd = row.won_showdowns / row.showdown_hands * 100 if row.showdown_hands > 0 else 0

        return {
            "wtsd": round(wtsd, 1),
            "wsd": round(wsd, 1),
        }

    def _analyze_play_style(self, stats: PlayerStats) -> dict[str, Any]:
        """플레이 스타일 분석.

        VPIP/PFR 조합으로 플레이 스타일 판단:
        - Tight-Aggressive (TAG): 낮은 VPIP, 높은 PFR
        - Loose-Aggressive (LAG): 높은 VPIP, 높은 PFR
        - Tight-Passive: 낮은 VPIP, 낮은 PFR
        - Loose-Passive (Fish): 높은 VPIP, 낮은 PFR
        """
        if stats.total_hands < 50:
            return {
                "style": "unknown",
                "description": "핸드 수가 부족합니다 (최소 50핸드 필요)",
                "emoji": "❓",
            }

        # VPIP 분류 (25% 기준)
        is_loose = stats.vpip > 25

        # PFR 분류 (15% 기준)
        is_aggressive = stats.pfr > 15

        if not is_loose and is_aggressive:
            return {
                "style": "TAG",
                "description": "타이트-어그레시브 (정석 스타일)",
                "emoji": "🦈",
                "characteristics": ["선별적 핸드 선택", "공격적 베팅", "좋은 수익성"],
            }
        elif is_loose and is_aggressive:
            return {
                "style": "LAG",
                "description": "루즈-어그레시브 (공격적 스타일)",
                "emoji": "🔥",
                "characteristics": ["다양한 핸드 플레이", "적극적 베팅", "블러프 많음"],
            }
        elif not is_loose and not is_aggressive:
            return {
                "style": "Nit",
                "description": "타이트-패시브 (보수적 스타일)",
                "emoji": "🐢",
                "characteristics": ["프리미엄 핸드만 플레이", "체크/콜 위주", "블러프 적음"],
            }
        else:  # is_loose and not is_aggressive
            return {
                "style": "Calling Station",
                "description": "루즈-패시브 (콜링 스테이션)",
                "emoji": "🐟",
                "characteristics": ["많은 핸드 참여", "콜 위주", "수익성 낮음"],
            }
