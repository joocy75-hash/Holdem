"""
Chip Dumping Detector - 칩 밀어주기 탐지 서비스
의심스러운 칩 이동 패턴을 탐지합니다.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import uuid


class ChipDumpingDetector:
    """칩 밀어주기 탐지 서비스"""
    
    def __init__(self, main_db: AsyncSession, admin_db: AsyncSession):
        self.main_db = main_db
        self.admin_db = admin_db
    
    async def detect_one_way_chip_flow(
        self,
        time_window_hours: int = 24,
        min_hands: int = 5,
        min_win_rate: float = 0.8
    ) -> list[dict]:
        """
        일방적인 칩 흐름 탐지 (한 플레이어가 다른 플레이어에게 지속적으로 칩을 잃는 패턴)
        
        Args:
            time_window_hours: 탐지 시간 범위 (시간)
            min_hands: 최소 핸드 수
            min_win_rate: 최소 승률 (한쪽이 이기는 비율)
        
        Returns:
            의심 패턴 목록
        """
        since = datetime.now(timezone.utc) - timedelta(hours=time_window_hours)
        
        try:
            query = text("""
                WITH player_pairs AS (
                    SELECT 
                        hp1.user_id as loser_id,
                        hp2.user_id as winner_id,
                        COUNT(*) as total_hands,
                        SUM(CASE WHEN hp2.won_amount > hp1.won_amount THEN 1 ELSE 0 END) as winner_wins
                    FROM hand_participants hp1
                    JOIN hand_participants hp2 ON hp1.hand_id = hp2.hand_id AND hp1.user_id != hp2.user_id
                    JOIN hand_history h ON hp1.hand_id = h.id
                    WHERE h.created_at >= :since
                    GROUP BY hp1.user_id, hp2.user_id
                    HAVING COUNT(*) >= :min_hands
                )
                SELECT loser_id, winner_id, total_hands, winner_wins,
                       CAST(winner_wins AS FLOAT) / total_hands as win_rate
                FROM player_pairs
                WHERE CAST(winner_wins AS FLOAT) / total_hands >= :min_win_rate
                ORDER BY win_rate DESC, total_hands DESC
            """)
            result = await self.main_db.execute(query, {
                "since": since,
                "min_hands": min_hands,
                "min_win_rate": min_win_rate
            })
            rows = result.fetchall()
            
            suspicious_patterns = []
            for row in rows:
                suspicious_patterns.append({
                    "loser_id": row.loser_id,
                    "winner_id": row.winner_id,
                    "total_hands": row.total_hands,
                    "winner_wins": row.winner_wins,
                    "win_rate": round(row.win_rate, 3),
                    "detection_type": "one_way_chip_flow"
                })
            
            return suspicious_patterns
        except Exception:
            return []
    
    async def detect_soft_play(
        self,
        time_window_hours: int = 24,
        min_hands: int = 10
    ) -> list[dict]:
        """
        소프트 플레이 탐지 (특정 플레이어 간 베팅이 비정상적으로 적은 패턴)
        
        Args:
            time_window_hours: 탐지 시간 범위 (시간)
            min_hands: 최소 핸드 수
        
        Returns:
            의심 패턴 목록
        """
        since = datetime.now(timezone.utc) - timedelta(hours=time_window_hours)
        
        try:
            query = text("""
                WITH player_pair_bets AS (
                    SELECT 
                        hp1.user_id as player1_id,
                        hp2.user_id as player2_id,
                        COUNT(*) as total_hands,
                        AVG(hp1.bet_amount + hp2.bet_amount) as avg_combined_bet,
                        AVG(h.pot_size) as avg_pot_size
                    FROM hand_participants hp1
                    JOIN hand_participants hp2 ON hp1.hand_id = hp2.hand_id AND hp1.user_id < hp2.user_id
                    JOIN hand_history h ON hp1.hand_id = h.id
                    WHERE h.created_at >= :since
                    GROUP BY hp1.user_id, hp2.user_id
                    HAVING COUNT(*) >= :min_hands
                ),
                avg_bets AS (
                    SELECT AVG(avg_combined_bet) as overall_avg_bet
                    FROM player_pair_bets
                )
                SELECT ppb.player1_id, ppb.player2_id, ppb.total_hands, 
                       ppb.avg_combined_bet, ppb.avg_pot_size,
                       ppb.avg_combined_bet / NULLIF(ab.overall_avg_bet, 0) as bet_ratio
                FROM player_pair_bets ppb
                CROSS JOIN avg_bets ab
                WHERE ppb.avg_combined_bet < ab.overall_avg_bet * 0.3
                ORDER BY bet_ratio ASC
            """)
            result = await self.main_db.execute(query, {
                "since": since,
                "min_hands": min_hands
            })
            rows = result.fetchall()
            
            suspicious_patterns = []
            for row in rows:
                suspicious_patterns.append({
                    "player1_id": row.player1_id,
                    "player2_id": row.player2_id,
                    "total_hands": row.total_hands,
                    "avg_combined_bet": round(float(row.avg_combined_bet), 2),
                    "avg_pot_size": round(float(row.avg_pot_size), 2),
                    "bet_ratio": round(float(row.bet_ratio), 3) if row.bet_ratio else 0,
                    "detection_type": "soft_play"
                })
            
            return suspicious_patterns
        except Exception:
            return []
    
    async def detect_intentional_loss(
        self,
        user_id: str,
        time_window_hours: int = 24
    ) -> list[dict]:
        """
        의도적 패배 탐지 (강한 핸드로 폴드하는 패턴)
        
        Args:
            user_id: 대상 사용자 ID
            time_window_hours: 탐지 시간 범위 (시간)
        
        Returns:
            의심 핸드 목록
        """
        since = datetime.now(timezone.utc) - timedelta(hours=time_window_hours)
        
        try:
            # 강한 핸드(페어 이상)로 폴드한 경우 탐지
            query = text("""
                SELECT hp.hand_id, hp.cards, hp.bet_amount, hp.won_amount,
                       h.pot_size, h.created_at
                FROM hand_participants hp
                JOIN hand_history h ON hp.hand_id = h.id
                WHERE hp.user_id = :user_id
                  AND h.created_at >= :since
                  AND hp.won_amount = 0
                  AND hp.bet_amount < h.pot_size * 0.1
                  AND hp.cards IS NOT NULL
                ORDER BY h.created_at DESC
                LIMIT 50
            """)
            result = await self.main_db.execute(query, {
                "user_id": user_id,
                "since": since
            })
            rows = result.fetchall()
            
            suspicious_hands = []
            for row in rows:
                # 간단한 핸드 강도 체크 (실제로는 더 정교한 로직 필요)
                cards = row.cards or ""
                if self._is_strong_hand(cards):
                    suspicious_hands.append({
                        "hand_id": str(row.hand_id),
                        "cards": cards,
                        "bet_amount": float(row.bet_amount),
                        "pot_size": float(row.pot_size),
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                        "detection_type": "intentional_loss"
                    })
            
            return suspicious_hands
        except Exception:
            return []
    
    def _is_strong_hand(self, cards: str) -> bool:
        """간단한 핸드 강도 체크 (페어 이상)"""
        if not cards:
            return False
        
        # 카드 파싱 (예: "As Kh" -> ["As", "Kh"])
        card_list = cards.split()
        if len(card_list) < 2:
            return False
        
        # 랭크 추출
        ranks = [card[0] if len(card) > 0 else '' for card in card_list]
        
        # 페어 체크
        if len(ranks) >= 2 and ranks[0] == ranks[1]:
            return True
        
        # 높은 카드 체크 (A, K, Q)
        high_cards = ['A', 'K', 'Q']
        if all(r in high_cards for r in ranks[:2]):
            return True
        
        return False
    
    async def flag_chip_dumping(
        self,
        detection_type: str,
        user_ids: list[str],
        details: dict,
        severity: str = "high"
    ) -> str:
        """
        칩 밀어주기 의심 활동 플래깅
        
        Args:
            detection_type: 탐지 유형
            user_ids: 관련 사용자 ID 목록
            details: 상세 정보
            severity: 심각도
        
        Returns:
            생성된 플래그 ID
        """
        flag_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        try:
            query = text("""
                INSERT INTO suspicious_activities 
                (id, detection_type, user_ids, details, severity, status, created_at)
                VALUES (:id, :detection_type, :user_ids, :details, :severity, 'pending', :created_at)
            """)
            await self.admin_db.execute(query, {
                "id": flag_id,
                "detection_type": detection_type,
                "user_ids": user_ids,
                "details": str(details),
                "severity": severity,
                "created_at": now
            })
            await self.admin_db.commit()
            
            return flag_id
        except Exception:
            return ""
    
    async def run_chip_dumping_scan(self) -> dict:
        """
        전체 칩 밀어주기 스캔 실행
        
        Returns:
            스캔 결과
        """
        one_way_flows = await self.detect_one_way_chip_flow()
        soft_plays = await self.detect_soft_play()
        
        flagged_count = 0
        
        for pattern in one_way_flows:
            if pattern["win_rate"] >= 0.9:
                await self.flag_chip_dumping(
                    detection_type="chip_dumping_one_way",
                    user_ids=[pattern["loser_id"], pattern["winner_id"]],
                    details=pattern,
                    severity="high"
                )
                flagged_count += 1
        
        for pattern in soft_plays:
            await self.flag_chip_dumping(
                detection_type="chip_dumping_soft_play",
                user_ids=[pattern["player1_id"], pattern["player2_id"]],
                details=pattern,
                severity="medium"
            )
            flagged_count += 1
        
        return {
            "one_way_flow_patterns": len(one_way_flows),
            "soft_play_patterns": len(soft_plays),
            "flagged_count": flagged_count
        }
