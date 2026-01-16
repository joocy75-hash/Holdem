"""
Anomaly Detector - 이상 탐지 서비스
통계 기반 이상 탐지 알고리즘을 사용합니다.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import statistics
import math


class AnomalyDetector:
    """이상 탐지 서비스"""
    
    def __init__(self, main_db: AsyncSession, admin_db: AsyncSession):
        self.main_db = main_db
        self.admin_db = admin_db
    
    async def detect_win_rate_anomaly(
        self,
        user_id: str,
        time_window_days: int = 30,
        z_score_threshold: float = 3.0
    ) -> dict:
        """
        승률 이상 탐지
        전체 플레이어 대비 비정상적으로 높은 승률 탐지
        
        Args:
            user_id: 대상 사용자 ID
            time_window_days: 분석 시간 범위 (일)
            z_score_threshold: Z-score 임계값
        
        Returns:
            이상 탐지 결과
        """
        since = datetime.now(timezone.utc) - timedelta(days=time_window_days)
        
        try:
            # 전체 플레이어 승률 통계
            stats_query = text("""
                SELECT 
                    user_id,
                    COUNT(*) as total_hands,
                    SUM(CASE WHEN won_amount > 0 THEN 1 ELSE 0 END) as wins,
                    CAST(SUM(CASE WHEN won_amount > 0 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) as win_rate
                FROM hand_participants hp
                JOIN hand_history h ON hp.hand_id = h.id
                WHERE h.created_at >= :since
                GROUP BY user_id
                HAVING COUNT(*) >= 50
            """)
            result = await self.main_db.execute(stats_query, {"since": since})
            rows = result.fetchall()
            
            if len(rows) < 10:
                return {
                    "user_id": user_id,
                    "is_anomaly": False,
                    "reason": "insufficient_population"
                }
            
            win_rates = [row.win_rate for row in rows]
            mean_win_rate = statistics.mean(win_rates)
            std_dev = statistics.stdev(win_rates) if len(win_rates) > 1 else 0.1
            
            # 대상 사용자 승률 조회
            user_data = next((row for row in rows if row.user_id == user_id), None)
            
            if not user_data:
                return {
                    "user_id": user_id,
                    "is_anomaly": False,
                    "reason": "user_not_found_or_insufficient_hands"
                }
            
            user_win_rate = user_data.win_rate
            z_score = (user_win_rate - mean_win_rate) / std_dev if std_dev > 0 else 0
            
            is_anomaly = abs(z_score) > z_score_threshold
            
            return {
                "user_id": user_id,
                "user_win_rate": round(user_win_rate, 4),
                "population_mean": round(mean_win_rate, 4),
                "population_std_dev": round(std_dev, 4),
                "z_score": round(z_score, 2),
                "total_hands": user_data.total_hands,
                "is_anomaly": is_anomaly,
                "anomaly_type": "high_win_rate" if z_score > 0 else "low_win_rate" if is_anomaly else None
            }
        except Exception:
            return {
                "user_id": user_id,
                "is_anomaly": False,
                "reason": "error"
            }
    
    async def detect_profit_anomaly(
        self,
        user_id: str,
        time_window_days: int = 30,
        z_score_threshold: float = 3.0
    ) -> dict:
        """
        수익 이상 탐지
        전체 플레이어 대비 비정상적으로 높은 수익 탐지
        
        Args:
            user_id: 대상 사용자 ID
            time_window_days: 분석 시간 범위 (일)
            z_score_threshold: Z-score 임계값
        
        Returns:
            이상 탐지 결과
        """
        since = datetime.now(timezone.utc) - timedelta(days=time_window_days)
        
        try:
            stats_query = text("""
                SELECT 
                    user_id,
                    SUM(won_amount - bet_amount) as net_profit,
                    COUNT(*) as total_hands
                FROM hand_participants hp
                JOIN hand_history h ON hp.hand_id = h.id
                WHERE h.created_at >= :since
                GROUP BY user_id
                HAVING COUNT(*) >= 50
            """)
            result = await self.main_db.execute(stats_query, {"since": since})
            rows = result.fetchall()
            
            if len(rows) < 10:
                return {
                    "user_id": user_id,
                    "is_anomaly": False,
                    "reason": "insufficient_population"
                }
            
            profits = [float(row.net_profit) for row in rows]
            mean_profit = statistics.mean(profits)
            std_dev = statistics.stdev(profits) if len(profits) > 1 else 1
            
            user_data = next((row for row in rows if row.user_id == user_id), None)
            
            if not user_data:
                return {
                    "user_id": user_id,
                    "is_anomaly": False,
                    "reason": "user_not_found_or_insufficient_hands"
                }
            
            user_profit = float(user_data.net_profit)
            z_score = (user_profit - mean_profit) / std_dev if std_dev > 0 else 0
            
            is_anomaly = z_score > z_score_threshold  # 높은 수익만 이상으로 간주
            
            return {
                "user_id": user_id,
                "user_net_profit": round(user_profit, 2),
                "population_mean": round(mean_profit, 2),
                "population_std_dev": round(std_dev, 2),
                "z_score": round(z_score, 2),
                "total_hands": user_data.total_hands,
                "is_anomaly": is_anomaly,
                "anomaly_type": "excessive_profit" if is_anomaly else None
            }
        except Exception:
            return {
                "user_id": user_id,
                "is_anomaly": False,
                "reason": "error"
            }
    
    async def detect_betting_pattern_anomaly(
        self,
        user_id: str,
        time_window_hours: int = 24
    ) -> dict:
        """
        베팅 패턴 이상 탐지
        비정상적인 베팅 패턴 탐지
        
        Args:
            user_id: 대상 사용자 ID
            time_window_hours: 분석 시간 범위 (시간)
        
        Returns:
            이상 탐지 결과
        """
        since = datetime.now(timezone.utc) - timedelta(hours=time_window_hours)
        
        try:
            query = text("""
                SELECT bet_amount
                FROM hand_participants hp
                JOIN hand_history h ON hp.hand_id = h.id
                WHERE hp.user_id = :user_id
                  AND h.created_at >= :since
                  AND hp.bet_amount > 0
                ORDER BY h.created_at DESC
                LIMIT 100
            """)
            result = await self.main_db.execute(query, {
                "user_id": user_id,
                "since": since
            })
            rows = result.fetchall()
            
            if len(rows) < 20:
                return {
                    "user_id": user_id,
                    "is_anomaly": False,
                    "reason": "insufficient_data"
                }
            
            bet_amounts = [float(row.bet_amount) for row in rows]
            
            mean_bet = statistics.mean(bet_amounts)
            std_dev = statistics.stdev(bet_amounts) if len(bet_amounts) > 1 else 0
            
            # 베팅 패턴 이상 조건:
            # 1. 표준편차가 매우 낮음 (항상 같은 금액 베팅)
            # 2. 베팅 금액이 특정 패턴을 따름
            
            is_anomaly = False
            reasons = []
            
            coefficient_of_variation = std_dev / mean_bet if mean_bet > 0 else 0
            
            if coefficient_of_variation < 0.1 and len(bet_amounts) >= 30:
                is_anomaly = True
                reasons.append("constant_bet_size")
            
            # 연속 동일 베팅 체크
            consecutive_same = 1
            max_consecutive = 1
            for i in range(1, len(bet_amounts)):
                if abs(bet_amounts[i] - bet_amounts[i-1]) < 0.01:
                    consecutive_same += 1
                    max_consecutive = max(max_consecutive, consecutive_same)
                else:
                    consecutive_same = 1
            
            if max_consecutive >= 10:
                is_anomaly = True
                reasons.append("repetitive_betting")
            
            return {
                "user_id": user_id,
                "sample_size": len(bet_amounts),
                "mean_bet": round(mean_bet, 2),
                "std_dev": round(std_dev, 2),
                "coefficient_of_variation": round(coefficient_of_variation, 4),
                "max_consecutive_same_bet": max_consecutive,
                "is_anomaly": is_anomaly,
                "reasons": reasons
            }
        except Exception:
            return {
                "user_id": user_id,
                "is_anomaly": False,
                "reason": "error"
            }
    
    async def run_full_anomaly_detection(self, user_id: str) -> dict:
        """
        특정 사용자에 대한 전체 이상 탐지 실행
        
        Args:
            user_id: 대상 사용자 ID
        
        Returns:
            종합 이상 탐지 결과
        """
        win_rate_result = await self.detect_win_rate_anomaly(user_id)
        profit_result = await self.detect_profit_anomaly(user_id)
        betting_result = await self.detect_betting_pattern_anomaly(user_id)
        
        anomaly_count = sum([
            win_rate_result.get("is_anomaly", False),
            profit_result.get("is_anomaly", False),
            betting_result.get("is_anomaly", False)
        ])
        
        return {
            "user_id": user_id,
            "anomaly_count": anomaly_count,
            "is_suspicious": anomaly_count >= 2,
            "win_rate_analysis": win_rate_result,
            "profit_analysis": profit_result,
            "betting_analysis": betting_result
        }
