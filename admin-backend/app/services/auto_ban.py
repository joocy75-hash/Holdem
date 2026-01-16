"""
Auto Ban Service - 자동 제재 서비스
봇 의심 시 자동으로 플래깅하고 관리자에게 알림을 보냅니다.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import uuid

from app.services.bot_detector import BotDetector
from app.services.anomaly_detector import AnomalyDetector
from app.services.audit_service import AuditService
from app.services.telegram_notifier import TelegramNotifier

logger = logging.getLogger(__name__)


# 심각도별 자동 조치 정의
SEVERITY_ACTIONS = {
    "low": "monitor",      # 모니터링만
    "medium": "warning",   # 경고
    "high": "temp_ban",    # 임시 제재
}


class AutoBanService:
    """자동 제재 서비스"""
    
    def __init__(
        self,
        main_db: AsyncSession,
        admin_db: AsyncSession,
        audit_service: Optional[AuditService] = None,
        telegram_notifier: Optional[TelegramNotifier] = None,
    ):
        self.main_db = main_db
        self.admin_db = admin_db
        self.bot_detector = BotDetector(main_db, admin_db)
        self.anomaly_detector = AnomalyDetector(main_db, admin_db)
        self._audit_service = audit_service
        self._telegram_notifier = telegram_notifier
    
    async def evaluate_user(self, user_id: str) -> dict:
        """
        사용자 평가 및 자동 플래깅
        
        Args:
            user_id: 대상 사용자 ID
        
        Returns:
            평가 결과
        """
        bot_result = await self.bot_detector.run_bot_detection(user_id)
        anomaly_result = await self.anomaly_detector.run_full_anomaly_detection(user_id)
        
        should_flag = False
        flag_reasons = []
        severity = "low"
        
        # 봇 탐지 결과 평가
        if bot_result.get("is_likely_bot"):
            should_flag = True
            flag_reasons.append("likely_bot")
            severity = "high"
        elif bot_result.get("suspicion_score", 0) >= 40:
            should_flag = True
            flag_reasons.append("possible_bot")
            severity = "medium"
        
        # 이상 탐지 결과 평가
        if anomaly_result.get("is_suspicious"):
            should_flag = True
            flag_reasons.append("statistical_anomaly")
            if severity != "high":
                severity = "medium"
        
        # 심각도에 따른 자동 조치 결정
        action_taken = SEVERITY_ACTIONS.get(severity, "monitor")
        
        result = {
            "user_id": user_id,
            "should_flag": should_flag,
            "flag_reasons": flag_reasons,
            "severity": severity,
            "action_taken": action_taken,
            "bot_detection": bot_result,
            "anomaly_detection": anomaly_result
        }
        
        # 자동 플래깅
        if should_flag:
            flag_id = await self.create_flag(
                user_id=user_id,
                detection_type="auto_detection",
                reasons=flag_reasons,
                severity=severity,
                details=result
            )
            result["flag_id"] = flag_id
            
            # 감사 로그 기록
            await self._log_auto_ban_decision(
                user_id=user_id,
                severity=severity,
                action_taken=action_taken,
                flag_reasons=flag_reasons,
                flag_id=flag_id,
                details=result,
            )
            
            # 관리자 알림
            await self.notify_admins(user_id, flag_reasons, severity)
        
        return result
    
    async def _log_auto_ban_decision(
        self,
        user_id: str,
        severity: str,
        action_taken: str,
        flag_reasons: list[str],
        flag_id: str,
        details: dict,
    ) -> None:
        """
        자동 제재 결정을 감사 로그에 기록
        
        Args:
            user_id: 대상 사용자 ID
            severity: 심각도
            action_taken: 취해진 조치
            flag_reasons: 플래그 사유 목록
            flag_id: 생성된 플래그 ID
            details: 상세 정보
        """
        if not self._audit_service:
            logger.warning("AuditService not configured, skipping audit log")
            return
        
        try:
            await self._audit_service.log_action(
                admin_user_id="system",
                admin_username="auto_ban_system",
                action=f"auto_{action_taken}",
                target_type="user",
                target_id=user_id,
                details={
                    "severity": severity,
                    "action_taken": action_taken,
                    "flag_reasons": flag_reasons,
                    "flag_id": flag_id,
                    "bot_suspicion_score": details.get("bot_detection", {}).get("suspicion_score"),
                    "is_likely_bot": details.get("bot_detection", {}).get("is_likely_bot"),
                    "is_suspicious": details.get("anomaly_detection", {}).get("is_suspicious"),
                },
                ip_address=None,
            )
            logger.info(
                f"Auto-ban decision logged: user={user_id}, "
                f"severity={severity}, action={action_taken}"
            )
        except Exception as e:
            logger.error(f"Failed to log auto-ban decision: {e}")
    
    async def create_flag(
        self,
        user_id: str,
        detection_type: str,
        reasons: list[str],
        severity: str,
        details: dict
    ) -> str:
        """
        의심 활동 플래그 생성
        
        Args:
            user_id: 사용자 ID
            detection_type: 탐지 유형
            reasons: 플래그 사유 목록
            severity: 심각도
            details: 상세 정보
        
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
                "user_ids": [user_id],
                "details": str({"reasons": reasons, **details}),
                "severity": severity,
                "created_at": now
            })
            await self.admin_db.commit()
            
            return flag_id
        except Exception:
            return ""
    
    async def notify_admins(
        self,
        user_id: str,
        reasons: list[str],
        severity: str
    ) -> bool:
        """
        관리자에게 알림 전송
        
        Args:
            user_id: 의심 사용자 ID
            reasons: 플래그 사유 목록
            severity: 심각도
        
        Returns:
            알림 전송 성공 여부
        """
        db_success = False
        telegram_success = False
        
        try:
            # 알림 기록 저장
            notification_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            
            query = text("""
                INSERT INTO admin_notifications 
                (id, type, title, message, severity, is_read, created_at)
                VALUES (:id, :type, :title, :message, :severity, false, :created_at)
            """)
            await self.admin_db.execute(query, {
                "id": notification_id,
                "type": "suspicious_activity",
                "title": f"의심 활동 감지: {user_id[:8]}...",
                "message": f"사유: {', '.join(reasons)}",
                "severity": severity,
                "created_at": now
            })
            await self.admin_db.commit()
            db_success = True
        except Exception as e:
            logger.error(f"Failed to save admin notification: {e}")
        
        # Telegram 알림 전송
        if self._telegram_notifier:
            telegram_success = await self._send_telegram_alert(
                user_id=user_id,
                reasons=reasons,
                severity=severity,
            )
        
        return db_success or telegram_success
    
    async def _send_telegram_alert(
        self,
        user_id: str,
        reasons: list[str],
        severity: str,
    ) -> bool:
        """
        Telegram으로 자동 제재 알림 전송
        
        Args:
            user_id: 의심 사용자 ID
            reasons: 플래그 사유 목록
            severity: 심각도
        
        Returns:
            알림 전송 성공 여부
        """
        if not self._telegram_notifier or not self._telegram_notifier.is_configured:
            logger.debug("Telegram notifier not configured, skipping alert")
            return False
        
        try:
            # 심각도별 이모지
            severity_emoji = {
                "low": "ℹ️",
                "medium": "⚠️",
                "high": "🚨",
            }
            
            action = SEVERITY_ACTIONS.get(severity, "monitor")
            action_text = {
                "monitor": "모니터링",
                "warning": "경고",
                "temp_ban": "임시 제재",
            }
            
            message = (
                f"{severity_emoji.get(severity, '⚠️')} <b>[자동 제재 알림]</b>\n\n"
                f"👤 User: <code>{user_id}</code>\n"
                f"📊 심각도: <b>{severity.upper()}</b>\n"
                f"🔧 조치: <b>{action_text.get(action, action)}</b>\n"
                f"📋 사유: {', '.join(reasons)}\n\n"
                "관리자 대시보드에서 확인해주세요."
            )
            
            if self._telegram_notifier.admin_chat_id:
                return await self._telegram_notifier._send_message(
                    int(self._telegram_notifier.admin_chat_id),
                    message,
                )
            return False
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
            return False
    
    async def batch_evaluate_users(
        self,
        user_ids: list[str]
    ) -> dict:
        """
        여러 사용자 일괄 평가
        
        Args:
            user_ids: 평가할 사용자 ID 목록
        
        Returns:
            일괄 평가 결과
        """
        results = []
        flagged_count = 0
        
        for user_id in user_ids:
            result = await self.evaluate_user(user_id)
            results.append(result)
            if result.get("should_flag"):
                flagged_count += 1
        
        return {
            "total_evaluated": len(user_ids),
            "flagged_count": flagged_count,
            "results": results
        }
    
    async def get_active_players_for_scan(
        self,
        min_hands: int = 50,
        time_window_hours: int = 24
    ) -> list[str]:
        """
        스캔 대상 활성 플레이어 목록 조회
        
        Args:
            min_hands: 최소 핸드 수
            time_window_hours: 시간 범위 (시간)
        
        Returns:
            사용자 ID 목록
        """
        since = datetime.now(timezone.utc) - timedelta(hours=time_window_hours)
        
        try:
            query = text("""
                SELECT hp.user_id, COUNT(*) as hand_count
                FROM hand_participants hp
                JOIN hand_history h ON hp.hand_id = h.id
                WHERE h.created_at >= :since
                GROUP BY hp.user_id
                HAVING COUNT(*) >= :min_hands
            """)
            result = await self.main_db.execute(query, {
                "since": since,
                "min_hands": min_hands
            })
            rows = result.fetchall()
            
            return [row.user_id for row in rows]
        except Exception:
            return []


# SEVERITY_ACTIONS 상수는 파일 상단에 정의됨
