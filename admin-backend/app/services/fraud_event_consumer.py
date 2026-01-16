"""Fraud Event Consumer - 부정 행위 이벤트 소비자 서비스.

Redis Pub/Sub 채널을 구독하여 게임 서버에서 발행한 이벤트를 수신하고
기존 탐지 서비스들을 호출하여 부정 행위를 분석합니다.

Channels:
- fraud:hand_completed - 핸드 완료 이벤트 → ChipDumpingDetector
- fraud:player_action - 플레이어 액션 이벤트 → BotDetector
- fraud:player_stats - 플레이어 세션 통계 이벤트 → AnomalyDetector
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from redis.asyncio import Redis
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Redis Pub/Sub 채널 이름
CHANNEL_HAND_COMPLETED = "fraud:hand_completed"
CHANNEL_PLAYER_ACTION = "fraud:player_action"
CHANNEL_PLAYER_STATS = "fraud:player_stats"


class FraudEventConsumer:
    """부정 행위 이벤트 소비자 서비스.
    
    Redis Pub/Sub 채널을 구독하여 게임 서버에서 발행한 이벤트를 수신하고
    기존 탐지 서비스들을 호출하여 부정 행위를 분석합니다.
    """

    def __init__(
        self,
        redis_client: "Redis",
        main_db_factory: Callable[[], "AsyncSession"],
        admin_db_factory: Callable[[], "AsyncSession"],
    ):
        """Initialize FraudEventConsumer.
        
        Args:
            redis_client: Redis 클라이언트
            main_db_factory: 메인 DB 세션 팩토리
            admin_db_factory: Admin DB 세션 팩토리
        """
        self.redis = redis_client
        self._main_db_factory = main_db_factory
        self._admin_db_factory = admin_db_factory
        self._running = False
        self._task: asyncio.Task | None = None
        self._pubsub = None
        
        # 플레이어별 액션 데이터 버퍼 (봇 탐지용)
        self._action_buffer: dict[str, list[dict]] = {}
        self._action_buffer_size = 20  # 버퍼 크기

    async def start(self) -> None:
        """이벤트 구독 시작."""
        if self._running:
            logger.warning("FraudEventConsumer already running")
            return

        self._running = True
        self._pubsub = self.redis.pubsub()
        
        await self._pubsub.subscribe(
            CHANNEL_HAND_COMPLETED,
            CHANNEL_PLAYER_ACTION,
            CHANNEL_PLAYER_STATS,
        )
        
        logger.info(
            f"FraudEventConsumer subscribed to channels: "
            f"{CHANNEL_HAND_COMPLETED}, {CHANNEL_PLAYER_ACTION}, {CHANNEL_PLAYER_STATS}"
        )
        
        self._task = asyncio.create_task(self._listen_loop())

    async def stop(self) -> None:
        """이벤트 구독 중지."""
        self._running = False
        
        if self._pubsub:
            await self._pubsub.unsubscribe()
            await self._pubsub.close()
            self._pubsub = None
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        
        logger.info("FraudEventConsumer stopped")

    async def _listen_loop(self) -> None:
        """이벤트 수신 루프."""
        logger.info("FraudEventConsumer listen loop started")
        
        try:
            while self._running:
                try:
                    message = await self._pubsub.get_message(
                        ignore_subscribe_messages=True,
                        timeout=1.0,
                    )
                    
                    if message is None:
                        continue
                    
                    if message["type"] != "message":
                        continue
                    
                    channel = message["channel"]
                    if isinstance(channel, bytes):
                        channel = channel.decode("utf-8")
                    
                    data = message["data"]
                    if isinstance(data, bytes):
                        data = data.decode("utf-8")
                    
                    await self._handle_message(channel, data)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in listen loop: {e}")
                    await asyncio.sleep(1)
                    
        except asyncio.CancelledError:
            pass
        finally:
            logger.info("FraudEventConsumer listen loop ended")

    async def _handle_message(self, channel: str, data: str) -> None:
        """메시지 처리.
        
        Args:
            channel: 채널 이름
            data: JSON 문자열 데이터
        """
        try:
            event = json.loads(data)
            
            if channel == CHANNEL_HAND_COMPLETED:
                await self.handle_hand_completed(event)
            elif channel == CHANNEL_PLAYER_ACTION:
                await self.handle_player_action(event)
            elif channel == CHANNEL_PLAYER_STATS:
                await self.handle_player_stats(event)
            else:
                logger.warning(f"Unknown channel: {channel}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")
        except Exception as e:
            logger.error(f"Error handling message from {channel}: {e}")

    async def handle_hand_completed(self, event: dict) -> None:
        """핸드 완료 이벤트 처리.
        
        ChipDumpingDetector를 호출하여 칩 밀어주기 패턴을 분석합니다.
        
        Args:
            event: 핸드 완료 이벤트 데이터
        """
        hand_id = event.get("hand_id")
        room_id = event.get("room_id")
        participants = event.get("participants", [])
        
        logger.debug(
            f"Processing hand_completed event: hand_id={hand_id}, "
            f"room_id={room_id}, participants={len(participants)}"
        )
        
        # 참가자가 2명 이상인 경우에만 분석
        if len(participants) < 2:
            return
        
        try:
            # DB 세션 생성
            main_db = self._main_db_factory()
            admin_db = self._admin_db_factory()
            
            try:
                from app.services.chip_dumping_detector import ChipDumpingDetector
                
                detector = ChipDumpingDetector(main_db, admin_db)
                
                # 일방적 칩 흐름 탐지 (최근 핸드 기반)
                # Note: 실시간 분석을 위해 시간 범위를 짧게 설정
                suspicious_patterns = await detector.detect_one_way_chip_flow(
                    time_window_hours=1,
                    min_hands=3,
                    min_win_rate=0.9,
                )
                
                if suspicious_patterns:
                    logger.warning(
                        f"Chip dumping patterns detected: {len(suspicious_patterns)} patterns"
                    )
                    
                    # 의심 활동 플래깅
                    for pattern in suspicious_patterns:
                        await self._flag_suspicious_activity(
                            detection_type="chip_dumping",
                            user_ids=[pattern["loser_id"], pattern["winner_id"]],
                            details=pattern,
                            severity="high" if pattern["win_rate"] >= 0.95 else "medium",
                        )
                        
            finally:
                await main_db.close()
                await admin_db.close()
                
        except Exception as e:
            logger.error(f"Error in handle_hand_completed: {e}")

    async def handle_player_action(self, event: dict) -> None:
        """플레이어 액션 이벤트 처리.
        
        BotDetector를 호출하여 봇 행동 패턴을 분석합니다.
        
        Args:
            event: 플레이어 액션 이벤트 데이터
        """
        user_id = event.get("user_id")
        action_type = event.get("action_type")
        response_time_ms = event.get("response_time_ms", 0)
        
        logger.debug(
            f"Processing player_action event: user_id={user_id}, "
            f"action={action_type}, response_time={response_time_ms}ms"
        )
        
        # 액션 데이터 버퍼에 추가
        if user_id not in self._action_buffer:
            self._action_buffer[user_id] = []
        
        self._action_buffer[user_id].append({
            "action_type": action_type,
            "response_time_ms": response_time_ms,
            "timestamp": event.get("timestamp"),
        })
        
        # 버퍼 크기 제한
        if len(self._action_buffer[user_id]) > self._action_buffer_size:
            self._action_buffer[user_id] = self._action_buffer[user_id][-self._action_buffer_size:]
        
        # 충분한 데이터가 모이면 분석
        if len(self._action_buffer[user_id]) >= self._action_buffer_size:
            await self._analyze_bot_behavior(user_id)

    async def _analyze_bot_behavior(self, user_id: str) -> None:
        """봇 행동 분석.
        
        Args:
            user_id: 사용자 ID
        """
        actions = self._action_buffer.get(user_id, [])
        if not actions:
            return
        
        try:
            # 응답 시간 분석
            response_times = [a["response_time_ms"] for a in actions if a.get("response_time_ms")]
            
            if len(response_times) < 10:
                return
            
            import statistics
            
            avg_time = statistics.mean(response_times)
            std_dev = statistics.stdev(response_times) if len(response_times) > 1 else 0
            min_time = min(response_times)
            
            # 봇 의심 조건
            is_suspicious = False
            reasons = []
            
            # 표준편차가 매우 낮음 (일정한 응답 시간)
            if std_dev < 100 and len(response_times) >= 15:
                is_suspicious = True
                reasons.append("very_consistent_timing")
            
            # 최소 응답 시간이 비정상적으로 빠름
            if min_time < 100:
                is_suspicious = True
                reasons.append("superhuman_reaction")
            
            if is_suspicious:
                logger.warning(
                    f"Bot behavior detected for user {user_id}: "
                    f"avg={avg_time:.0f}ms, std={std_dev:.0f}ms, min={min_time}ms, "
                    f"reasons={reasons}"
                )
                
                await self._flag_suspicious_activity(
                    detection_type="bot_detection",
                    user_ids=[user_id],
                    details={
                        "avg_response_time_ms": round(avg_time, 2),
                        "std_dev_ms": round(std_dev, 2),
                        "min_time_ms": min_time,
                        "sample_size": len(response_times),
                        "reasons": reasons,
                    },
                    severity="high" if "superhuman_reaction" in reasons else "medium",
                )
                
                # 버퍼 초기화 (중복 탐지 방지)
                self._action_buffer[user_id] = []
                
        except Exception as e:
            logger.error(f"Error in _analyze_bot_behavior: {e}")

    async def handle_player_stats(self, event: dict) -> None:
        """플레이어 세션 통계 이벤트 처리.
        
        AnomalyDetector를 호출하여 이상 패턴을 분석합니다.
        
        Args:
            event: 플레이어 세션 통계 이벤트 데이터
        """
        user_id = event.get("user_id")
        room_id = event.get("room_id")
        hands_played = event.get("hands_played", 0)
        total_bet = event.get("total_bet", 0)
        total_won = event.get("total_won", 0)
        session_duration = event.get("session_duration_seconds", 0)
        
        logger.debug(
            f"Processing player_stats event: user_id={user_id}, "
            f"hands={hands_played}, bet={total_bet}, won={total_won}"
        )
        
        # 최소 핸드 수 체크
        if hands_played < 5:
            return
        
        try:
            # 간단한 이상 탐지 (세션 기반)
            win_rate = total_won / total_bet if total_bet > 0 else 0
            profit = total_won - total_bet
            
            is_suspicious = False
            reasons = []
            
            # 비정상적으로 높은 승률
            if win_rate > 2.0 and hands_played >= 10:
                is_suspicious = True
                reasons.append("excessive_win_rate")
            
            # 비정상적으로 높은 수익
            if profit > total_bet * 2 and hands_played >= 10:
                is_suspicious = True
                reasons.append("excessive_profit")
            
            # 비정상적으로 긴 세션
            if session_duration > 12 * 3600:  # 12시간 이상
                is_suspicious = True
                reasons.append("excessive_session_duration")
            
            if is_suspicious:
                logger.warning(
                    f"Anomaly detected for user {user_id}: "
                    f"win_rate={win_rate:.2f}, profit={profit}, "
                    f"duration={session_duration}s, reasons={reasons}"
                )
                
                await self._flag_suspicious_activity(
                    detection_type="anomaly_detection",
                    user_ids=[user_id],
                    details={
                        "room_id": room_id,
                        "hands_played": hands_played,
                        "total_bet": total_bet,
                        "total_won": total_won,
                        "win_rate": round(win_rate, 4),
                        "profit": profit,
                        "session_duration_seconds": session_duration,
                        "reasons": reasons,
                    },
                    severity="high" if len(reasons) >= 2 else "medium",
                )
                
        except Exception as e:
            logger.error(f"Error in handle_player_stats: {e}")

    async def _flag_suspicious_activity(
        self,
        detection_type: str,
        user_ids: list[str],
        details: dict,
        severity: str = "medium",
    ) -> None:
        """의심 활동 플래깅 및 자동 제재 평가.
        
        Args:
            detection_type: 탐지 유형
            user_ids: 관련 사용자 ID 목록
            details: 상세 정보
            severity: 심각도 (low, medium, high)
        """
        try:
            main_db = self._main_db_factory()
            admin_db = self._admin_db_factory()
            
            try:
                from app.services.auto_ban import AutoBanService
                
                auto_ban = AutoBanService(main_db, admin_db)
                
                # 플래그 생성
                flag_id = await auto_ban.create_flag(
                    user_id=user_ids[0],
                    detection_type=detection_type,
                    reasons=details.get("reasons", [detection_type]),
                    severity=severity,
                    details=details,
                )
                
                if flag_id:
                    logger.info(
                        f"Created suspicious activity flag: id={flag_id}, "
                        f"type={detection_type}, users={user_ids}, severity={severity}"
                    )
                
                # 심각도가 높으면 관리자 알림
                if severity == "high":
                    await auto_ban.notify_admins(
                        user_id=user_ids[0],
                        reasons=details.get("reasons", [detection_type]),
                        severity=severity,
                    )
                    
            finally:
                await main_db.close()
                await admin_db.close()
                
        except Exception as e:
            logger.error(f"Error in _flag_suspicious_activity: {e}")


# 싱글톤 인스턴스
_fraud_consumer: FraudEventConsumer | None = None


def get_fraud_consumer() -> FraudEventConsumer | None:
    """Get the global FraudEventConsumer instance."""
    return _fraud_consumer


def init_fraud_consumer(
    redis_client: "Redis",
    main_db_factory: Callable[[], "AsyncSession"],
    admin_db_factory: Callable[[], "AsyncSession"],
) -> FraudEventConsumer:
    """Initialize the global FraudEventConsumer instance.
    
    Args:
        redis_client: Redis 클라이언트
        main_db_factory: 메인 DB 세션 팩토리
        admin_db_factory: Admin DB 세션 팩토리
        
    Returns:
        초기화된 FraudEventConsumer 인스턴스
    """
    global _fraud_consumer
    _fraud_consumer = FraudEventConsumer(redis_client, main_db_factory, admin_db_factory)
    logger.info("FraudEventConsumer initialized")
    return _fraud_consumer
