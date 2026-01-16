"""Fraud Event Publisher - 부정 행위 탐지용 이벤트 발행 서비스.

게임 서버에서 발생하는 이벤트를 Redis Pub/Sub을 통해 admin-backend로 전달합니다.

Channels:
- fraud:hand_completed - 핸드 완료 이벤트
- fraud:player_action - 플레이어 액션 이벤트
- fraud:player_stats - 플레이어 세션 통계 이벤트
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from redis.asyncio import Redis

logger = logging.getLogger(__name__)

# Redis Pub/Sub 채널 이름
CHANNEL_HAND_COMPLETED = "fraud:hand_completed"
CHANNEL_PLAYER_ACTION = "fraud:player_action"
CHANNEL_PLAYER_STATS = "fraud:player_stats"


class HandParticipant(BaseModel):
    """핸드 참가자 정보."""
    user_id: str
    seat: int
    hole_cards: list[str] | None = None
    bet_amount: int
    won_amount: int
    final_action: str  # fold, showdown, all_in_won, etc.


class HandCompletedEvent(BaseModel):
    """핸드 완료 이벤트 스키마."""
    event_type: str = "hand_completed"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    hand_id: str
    room_id: str
    hand_number: int
    pot_size: int
    community_cards: list[str]
    participants: list[HandParticipant]


class PlayerActionEvent(BaseModel):
    """플레이어 액션 이벤트 스키마."""
    event_type: str = "player_action"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    user_id: str
    room_id: str
    hand_id: str
    action_type: str
    amount: int
    response_time_ms: int
    turn_start_time: str


class PlayerStatsEvent(BaseModel):
    """플레이어 세션 통계 이벤트 스키마."""
    event_type: str = "player_stats"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    user_id: str
    room_id: str
    session_duration_seconds: int
    hands_played: int
    total_bet: int
    total_won: int
    join_time: str
    leave_time: str


class FraudEventPublisher:
    """부정 행위 탐지용 이벤트 발행 서비스.
    
    게임 서버에서 발생하는 이벤트를 Redis Pub/Sub을 통해 admin-backend로 전달합니다.
    모든 발행은 비동기로 처리되어 게임 응답 시간에 영향을 주지 않습니다.
    """

    def __init__(self, redis_client: "Redis | None" = None):
        """Initialize FraudEventPublisher.
        
        Args:
            redis_client: Redis 클라이언트 (None이면 이벤트 발행 비활성화)
        """
        self.redis = redis_client
        self._enabled = redis_client is not None

    @property
    def enabled(self) -> bool:
        """이벤트 발행 활성화 여부."""
        return self._enabled

    async def publish_hand_completed(
        self,
        hand_id: str,
        room_id: str,
        hand_number: int,
        pot_size: int,
        community_cards: list[str],
        participants: list[dict[str, Any]],
    ) -> bool:
        """핸드 완료 이벤트 발행.
        
        Args:
            hand_id: 핸드 고유 ID
            room_id: 방 ID
            hand_number: 핸드 번호
            pot_size: 팟 크기
            community_cards: 커뮤니티 카드
            participants: 참가자 정보 리스트
            
        Returns:
            발행 성공 여부
        """
        if not self._enabled:
            logger.debug("FraudEventPublisher disabled, skipping hand_completed event")
            return False

        try:
            # 참가자 정보 변환
            participant_models = [
                HandParticipant(
                    user_id=p["user_id"],
                    seat=p["seat"],
                    hole_cards=p.get("hole_cards"),
                    bet_amount=p.get("bet_amount", 0),
                    won_amount=p.get("won_amount", 0),
                    final_action=p.get("final_action", "unknown"),
                )
                for p in participants
            ]

            event = HandCompletedEvent(
                hand_id=hand_id,
                room_id=room_id,
                hand_number=hand_number,
                pot_size=pot_size,
                community_cards=community_cards,
                participants=participant_models,
            )

            await self.redis.publish(
                CHANNEL_HAND_COMPLETED,
                event.model_dump_json(),
            )

            logger.info(
                f"Published hand_completed event: hand_id={hand_id}, "
                f"room_id={room_id}, participants={len(participants)}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to publish hand_completed event: {e}")
            return False

    async def publish_player_action(
        self,
        user_id: str,
        room_id: str,
        hand_id: str,
        action_type: str,
        amount: int,
        response_time_ms: int,
        turn_start_time: str,
    ) -> bool:
        """플레이어 액션 이벤트 발행.
        
        Args:
            user_id: 사용자 ID
            room_id: 방 ID
            hand_id: 핸드 ID
            action_type: 액션 유형 (fold, check, call, raise, bet, all_in)
            amount: 베팅 금액
            response_time_ms: 응답 시간 (밀리초)
            turn_start_time: 턴 시작 시간 (ISO 형식)
            
        Returns:
            발행 성공 여부
        """
        if not self._enabled:
            logger.debug("FraudEventPublisher disabled, skipping player_action event")
            return False

        try:
            event = PlayerActionEvent(
                user_id=user_id,
                room_id=room_id,
                hand_id=hand_id,
                action_type=action_type,
                amount=amount,
                response_time_ms=response_time_ms,
                turn_start_time=turn_start_time,
            )

            await self.redis.publish(
                CHANNEL_PLAYER_ACTION,
                event.model_dump_json(),
            )

            logger.debug(
                f"Published player_action event: user_id={user_id}, "
                f"action={action_type}, response_time={response_time_ms}ms"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to publish player_action event: {e}")
            return False

    async def publish_player_stats(
        self,
        user_id: str,
        room_id: str,
        session_duration_seconds: int,
        hands_played: int,
        total_bet: int,
        total_won: int,
        join_time: str,
        leave_time: str,
    ) -> bool:
        """플레이어 세션 통계 이벤트 발행.
        
        Args:
            user_id: 사용자 ID
            room_id: 방 ID
            session_duration_seconds: 세션 지속 시간 (초)
            hands_played: 플레이한 핸드 수
            total_bet: 총 베팅 금액
            total_won: 총 승리 금액
            join_time: 입장 시간 (ISO 형식)
            leave_time: 퇴장 시간 (ISO 형식)
            
        Returns:
            발행 성공 여부
        """
        if not self._enabled:
            logger.debug("FraudEventPublisher disabled, skipping player_stats event")
            return False

        try:
            event = PlayerStatsEvent(
                user_id=user_id,
                room_id=room_id,
                session_duration_seconds=session_duration_seconds,
                hands_played=hands_played,
                total_bet=total_bet,
                total_won=total_won,
                join_time=join_time,
                leave_time=leave_time,
            )

            await self.redis.publish(
                CHANNEL_PLAYER_STATS,
                event.model_dump_json(),
            )

            logger.info(
                f"Published player_stats event: user_id={user_id}, "
                f"room_id={room_id}, hands={hands_played}, "
                f"bet={total_bet}, won={total_won}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to publish player_stats event: {e}")
            return False


# 싱글톤 인스턴스 (Redis 클라이언트 설정 후 초기화)
_fraud_publisher: FraudEventPublisher | None = None


def get_fraud_publisher() -> FraudEventPublisher | None:
    """Get the global FraudEventPublisher instance."""
    return _fraud_publisher


def init_fraud_publisher(redis_client: "Redis | None") -> FraudEventPublisher:
    """Initialize the global FraudEventPublisher instance.
    
    Args:
        redis_client: Redis 클라이언트
        
    Returns:
        초기화된 FraudEventPublisher 인스턴스
    """
    global _fraud_publisher
    _fraud_publisher = FraudEventPublisher(redis_client)
    logger.info(f"FraudEventPublisher initialized (enabled={_fraud_publisher.enabled})")
    return _fraud_publisher
