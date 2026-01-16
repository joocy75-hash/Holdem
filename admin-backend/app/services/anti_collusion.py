"""
Anti-Collusion Service - 공모 탐지 서비스
동일 IP/기기에서 접속한 플레이어들의 공모 행위를 탐지합니다.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import uuid


class AntiCollusionService:
    """공모 탐지 서비스"""
    
    def __init__(self, main_db: AsyncSession, admin_db: AsyncSession):
        self.main_db = main_db
        self.admin_db = admin_db
    
    async def detect_same_ip_players(
        self,
        room_id: str,
        time_window_hours: int = 24
    ) -> list[dict]:
        """
        같은 방에서 동일 IP로 접속한 플레이어 탐지
        
        Args:
            room_id: 방 ID
            time_window_hours: 탐지 시간 범위 (시간)
        
        Returns:
            의심 플레이어 그룹 목록
        """
        since = datetime.now(timezone.utc) - timedelta(hours=time_window_hours)
        
        try:
            query = text("""
                SELECT ip_address, array_agg(DISTINCT user_id) as user_ids, COUNT(DISTINCT user_id) as user_count
                FROM room_sessions
                WHERE room_id = :room_id
                  AND joined_at >= :since
                  AND ip_address IS NOT NULL
                GROUP BY ip_address
                HAVING COUNT(DISTINCT user_id) > 1
            """)
            result = await self.main_db.execute(query, {
                "room_id": room_id,
                "since": since
            })
            rows = result.fetchall()
            
            suspicious_groups = []
            for row in rows:
                suspicious_groups.append({
                    "ip_address": row.ip_address,
                    "user_ids": list(row.user_ids),
                    "user_count": row.user_count,
                    "room_id": room_id,
                    "detection_type": "same_ip"
                })
            
            return suspicious_groups
        except Exception:
            return []
    
    async def detect_same_device_players(
        self,
        room_id: str,
        time_window_hours: int = 24
    ) -> list[dict]:
        """
        같은 방에서 동일 기기로 접속한 플레이어 탐지
        
        Args:
            room_id: 방 ID
            time_window_hours: 탐지 시간 범위 (시간)
        
        Returns:
            의심 플레이어 그룹 목록
        """
        since = datetime.now(timezone.utc) - timedelta(hours=time_window_hours)
        
        try:
            query = text("""
                SELECT device_id, array_agg(DISTINCT user_id) as user_ids, COUNT(DISTINCT user_id) as user_count
                FROM room_sessions
                WHERE room_id = :room_id
                  AND joined_at >= :since
                  AND device_id IS NOT NULL
                GROUP BY device_id
                HAVING COUNT(DISTINCT user_id) > 1
            """)
            result = await self.main_db.execute(query, {
                "room_id": room_id,
                "since": since
            })
            rows = result.fetchall()
            
            suspicious_groups = []
            for row in rows:
                suspicious_groups.append({
                    "device_id": row.device_id,
                    "user_ids": list(row.user_ids),
                    "user_count": row.user_count,
                    "room_id": room_id,
                    "detection_type": "same_device"
                })
            
            return suspicious_groups
        except Exception:
            return []
    
    async def detect_frequent_same_table(
        self,
        user_id: str,
        min_occurrences: int = 5,
        time_window_days: int = 7
    ) -> list[dict]:
        """
        특정 사용자와 자주 같은 테이블에 앉는 플레이어 탐지
        
        Args:
            user_id: 대상 사용자 ID
            min_occurrences: 최소 동석 횟수
            time_window_days: 탐지 시간 범위 (일)
        
        Returns:
            의심 플레이어 목록
        """
        since = datetime.now(timezone.utc) - timedelta(days=time_window_days)
        
        try:
            query = text("""
                WITH user_rooms AS (
                    SELECT room_id, joined_at
                    FROM room_sessions
                    WHERE user_id = :user_id AND joined_at >= :since
                )
                SELECT rs.user_id as other_user_id, COUNT(*) as same_table_count
                FROM room_sessions rs
                JOIN user_rooms ur ON rs.room_id = ur.room_id
                WHERE rs.user_id != :user_id
                  AND rs.joined_at >= :since
                  AND ABS(EXTRACT(EPOCH FROM (rs.joined_at - ur.joined_at))) < 3600
                GROUP BY rs.user_id
                HAVING COUNT(*) >= :min_occurrences
                ORDER BY same_table_count DESC
            """)
            result = await self.main_db.execute(query, {
                "user_id": user_id,
                "since": since,
                "min_occurrences": min_occurrences
            })
            rows = result.fetchall()
            
            suspicious_players = []
            for row in rows:
                suspicious_players.append({
                    "user_id": user_id,
                    "other_user_id": row.other_user_id,
                    "same_table_count": row.same_table_count,
                    "detection_type": "frequent_same_table"
                })
            
            return suspicious_players
        except Exception:
            return []
    
    async def flag_suspicious_activity(
        self,
        detection_type: str,
        user_ids: list[str],
        details: dict,
        severity: str = "medium"
    ) -> str:
        """
        의심 활동 플래깅
        
        Args:
            detection_type: 탐지 유형
            user_ids: 관련 사용자 ID 목록
            details: 상세 정보
            severity: 심각도 (low, medium, high)
        
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
    
    async def run_collusion_scan(self, room_id: str) -> dict:
        """
        특정 방에 대한 전체 공모 스캔 실행
        
        Args:
            room_id: 방 ID
        
        Returns:
            스캔 결과
        """
        same_ip = await self.detect_same_ip_players(room_id)
        same_device = await self.detect_same_device_players(room_id)
        
        flagged_count = 0
        
        for group in same_ip:
            if group["user_count"] >= 2:
                await self.flag_suspicious_activity(
                    detection_type="same_ip_collusion",
                    user_ids=group["user_ids"],
                    details=group,
                    severity="high" if group["user_count"] >= 3 else "medium"
                )
                flagged_count += 1
        
        for group in same_device:
            if group["user_count"] >= 2:
                await self.flag_suspicious_activity(
                    detection_type="same_device_collusion",
                    user_ids=group["user_ids"],
                    details=group,
                    severity="high"
                )
                flagged_count += 1
        
        return {
            "room_id": room_id,
            "same_ip_groups": len(same_ip),
            "same_device_groups": len(same_device),
            "flagged_count": flagged_count
        }
