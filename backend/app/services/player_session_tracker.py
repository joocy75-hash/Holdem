"""Player Session Tracker - 플레이어 세션 통계 추적 서비스.

플레이어가 테이블에 입장/퇴장할 때 세션 통계를 추적하고,
퇴장 시 fraud:player_stats 이벤트를 발행합니다.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.fraud_event_publisher import FraudEventPublisher

logger = logging.getLogger(__name__)


@dataclass
class PlayerSession:
    """플레이어 세션 정보."""
    user_id: str
    room_id: str
    join_time: datetime
    hands_played: int = 0
    total_bet: int = 0
    total_won: int = 0


class PlayerSessionTracker:
    """플레이어 세션 통계 추적 서비스.
    
    플레이어가 테이블에 입장하면 세션을 시작하고,
    핸드가 완료될 때마다 통계를 업데이트하며,
    퇴장 시 fraud:player_stats 이벤트를 발행합니다.
    """

    def __init__(self, fraud_publisher: "FraudEventPublisher | None" = None):
        """Initialize PlayerSessionTracker.
        
        Args:
            fraud_publisher: FraudEventPublisher 인스턴스
        """
        self._fraud_publisher = fraud_publisher
        # 세션 저장소: {room_id}:{user_id} -> PlayerSession
        self._sessions: dict[str, PlayerSession] = {}

    def _session_key(self, room_id: str, user_id: str) -> str:
        """세션 키 생성."""
        return f"{room_id}:{user_id}"

    def start_session(self, user_id: str, room_id: str) -> PlayerSession:
        """플레이어 세션 시작.
        
        Args:
            user_id: 사용자 ID
            room_id: 방 ID
            
        Returns:
            생성된 PlayerSession
        """
        key = self._session_key(room_id, user_id)
        
        # 이미 세션이 있으면 반환
        if key in self._sessions:
            logger.debug(f"Session already exists for {user_id} in {room_id}")
            return self._sessions[key]
        
        session = PlayerSession(
            user_id=user_id,
            room_id=room_id,
            join_time=datetime.now(timezone.utc),
        )
        self._sessions[key] = session
        
        logger.info(f"Session started for {user_id} in {room_id}")
        return session

    def get_session(self, user_id: str, room_id: str) -> PlayerSession | None:
        """플레이어 세션 조회.
        
        Args:
            user_id: 사용자 ID
            room_id: 방 ID
            
        Returns:
            PlayerSession 또는 None
        """
        key = self._session_key(room_id, user_id)
        return self._sessions.get(key)

    def update_hand_stats(
        self,
        user_id: str,
        room_id: str,
        bet_amount: int,
        won_amount: int,
    ) -> None:
        """핸드 완료 시 통계 업데이트.
        
        Args:
            user_id: 사용자 ID
            room_id: 방 ID
            bet_amount: 이번 핸드 베팅 금액
            won_amount: 이번 핸드 승리 금액
        """
        key = self._session_key(room_id, user_id)
        session = self._sessions.get(key)
        
        if session is None:
            logger.warning(f"No session found for {user_id} in {room_id}")
            return
        
        session.hands_played += 1
        session.total_bet += bet_amount
        session.total_won += won_amount
        
        logger.debug(
            f"Updated stats for {user_id}: hands={session.hands_played}, "
            f"bet={session.total_bet}, won={session.total_won}"
        )

    async def end_session(self, user_id: str, room_id: str) -> PlayerSession | None:
        """플레이어 세션 종료 및 통계 이벤트 발행.
        
        Args:
            user_id: 사용자 ID
            room_id: 방 ID
            
        Returns:
            종료된 PlayerSession 또는 None
        """
        key = self._session_key(room_id, user_id)
        session = self._sessions.pop(key, None)
        
        if session is None:
            logger.warning(f"No session to end for {user_id} in {room_id}")
            return None
        
        leave_time = datetime.now(timezone.utc)
        session_duration = int((leave_time - session.join_time).total_seconds())
        
        logger.info(
            f"Session ended for {user_id} in {room_id}: "
            f"duration={session_duration}s, hands={session.hands_played}, "
            f"bet={session.total_bet}, won={session.total_won}"
        )
        
        # Fraud detection 이벤트 발행
        if self._fraud_publisher and self._fraud_publisher.enabled:
            await self._fraud_publisher.publish_player_stats(
                user_id=user_id,
                room_id=room_id,
                session_duration_seconds=session_duration,
                hands_played=session.hands_played,
                total_bet=session.total_bet,
                total_won=session.total_won,
                join_time=session.join_time.isoformat(),
                leave_time=leave_time.isoformat(),
            )
        
        return session

    def clear_room_sessions(self, room_id: str) -> int:
        """방의 모든 세션 정리 (방 삭제 시).
        
        Args:
            room_id: 방 ID
            
        Returns:
            정리된 세션 수
        """
        keys_to_remove = [
            key for key in self._sessions.keys()
            if key.startswith(f"{room_id}:")
        ]
        
        for key in keys_to_remove:
            del self._sessions[key]
        
        if keys_to_remove:
            logger.info(f"Cleared {len(keys_to_remove)} sessions for room {room_id}")
        
        return len(keys_to_remove)

    def get_all_sessions(self) -> dict[str, PlayerSession]:
        """모든 세션 조회 (디버깅용)."""
        return self._sessions.copy()


# 싱글톤 인스턴스
_session_tracker: PlayerSessionTracker | None = None


def get_session_tracker() -> PlayerSessionTracker | None:
    """Get the global PlayerSessionTracker instance."""
    return _session_tracker


def init_session_tracker(fraud_publisher: "FraudEventPublisher | None") -> PlayerSessionTracker:
    """Initialize the global PlayerSessionTracker instance.
    
    Args:
        fraud_publisher: FraudEventPublisher 인스턴스
        
    Returns:
        초기화된 PlayerSessionTracker 인스턴스
    """
    global _session_tracker
    _session_tracker = PlayerSessionTracker(fraud_publisher)
    logger.info("PlayerSessionTracker initialized")
    return _session_tracker
