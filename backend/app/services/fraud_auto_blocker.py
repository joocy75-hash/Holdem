"""Fraud Auto Blocker - 부정행위 자동 차단 서비스.

Redis Pub/Sub에서 fraud 이벤트를 분석하고 의심스러운 패턴이 감지되면
자동으로 사용자를 차단합니다.

탐지 패턴:
1. 담합 의심 (같은 IP에서 동시 접속 + 비정상적 행동)
2. 봇 의심 (지나치게 빠른 응답 시간, 규칙적 패턴)
3. 칩 덤핑 (의도적으로 상대에게 칩 전달)
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class FraudType(str, Enum):
    """부정행위 유형."""

    COLLUSION = "collusion"  # 담합
    BOT = "bot"  # 봇 사용
    CHIP_DUMPING = "chip_dumping"  # 칩 덤핑
    MULTI_ACCOUNT = "multi_account"  # 다중 계정


class BlockReason(str, Enum):
    """차단 사유."""

    COLLUSION_DETECTED = "담합 행위 감지"
    BOT_BEHAVIOR = "봇 사용 의심"
    CHIP_DUMPING = "칩 덤핑 감지"
    MULTI_ACCOUNT = "다중 계정 사용"
    MANUAL_ADMIN = "관리자 수동 차단"


@dataclass
class FraudScore:
    """부정행위 의심 점수."""

    user_id: str
    collusion_score: float = 0.0
    bot_score: float = 0.0
    chip_dumping_score: float = 0.0
    multi_account_score: float = 0.0
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    evidence: list[str] = field(default_factory=list)

    @property
    def total_score(self) -> float:
        """전체 의심 점수 (0-100)."""
        return min(100.0, (
            self.collusion_score * 0.35 +
            self.bot_score * 0.25 +
            self.chip_dumping_score * 0.25 +
            self.multi_account_score * 0.15
        ))

    def should_auto_block(self, threshold: float = 70.0) -> bool:
        """자동 차단 여부 결정."""
        return self.total_score >= threshold

    def get_primary_reason(self) -> BlockReason:
        """주요 차단 사유 반환."""
        scores = {
            BlockReason.COLLUSION_DETECTED: self.collusion_score,
            BlockReason.BOT_BEHAVIOR: self.bot_score,
            BlockReason.CHIP_DUMPING: self.chip_dumping_score,
            BlockReason.MULTI_ACCOUNT: self.multi_account_score,
        }
        return max(scores, key=scores.get)


class FraudBlockEvent(BaseModel):
    """부정행위 차단 이벤트."""

    event_type: str = "fraud_block"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    user_id: str
    block_reason: str
    fraud_score: float
    evidence: list[str]
    auto_blocked: bool = True


# =============================================================================
# 탐지 설정
# =============================================================================

# 담합 탐지 설정
COLLUSION_SAME_IP_PENALTY = 30.0  # 같은 IP 동시 접속
COLLUSION_FOLD_TO_FRIEND_PENALTY = 25.0  # 특정 상대에게만 폴드
COLLUSION_WIN_PATTERN_PENALTY = 20.0  # 비정상적 승률 패턴

# 봇 탐지 설정
BOT_FAST_RESPONSE_MS = 500  # 500ms 이하 응답
BOT_FAST_RESPONSE_PENALTY = 5.0  # 빠른 응답 1회당 페널티
BOT_CONSISTENT_TIMING_PENALTY = 30.0  # 일정한 타이밍 패턴
BOT_OPTIMAL_PLAY_PENALTY = 25.0  # GTO에 가까운 완벽한 플레이

# 칩 덤핑 탐지 설정
CHIP_DUMP_LARGE_LOSS_THRESHOLD = 0.5  # 스택의 50% 이상 손실
CHIP_DUMP_SAME_WINNER_PENALTY = 35.0  # 같은 상대에게 반복 패배
CHIP_DUMP_INTENTIONAL_PENALTY = 40.0  # 의도적 올인 후 패배

# 다중 계정 탐지 설정
MULTI_ACCOUNT_SAME_IP_PENALTY = 20.0  # 같은 IP에서 다중 계정
MULTI_ACCOUNT_DEVICE_PENALTY = 30.0  # 같은 디바이스 핑거프린트

# 자동 차단 임계값
AUTO_BLOCK_THRESHOLD = 70.0


class FraudAutoBlocker:
    """부정행위 자동 차단 서비스.

    플레이어 행동을 분석하고 의심스러운 패턴이 감지되면
    자동으로 사용자를 차단합니다.
    """

    def __init__(
        self,
        redis_client: "Redis | None" = None,
        auto_block_enabled: bool = True,
        block_threshold: float = AUTO_BLOCK_THRESHOLD,
    ):
        """Initialize FraudAutoBlocker.

        Args:
            redis_client: Redis 클라이언트
            auto_block_enabled: 자동 차단 활성화 여부
            block_threshold: 자동 차단 임계값 (0-100)
        """
        self.redis = redis_client
        self.auto_block_enabled = auto_block_enabled
        self.block_threshold = block_threshold
        self._enabled = redis_client is not None

        # 메모리 캐시 (실시간 분석용)
        self._fraud_scores: dict[str, FraudScore] = {}
        self._ip_to_users: dict[str, set[str]] = {}  # IP -> user_ids
        self._user_actions: dict[str, list[dict]] = {}  # user_id -> recent actions
        self._user_vs_user_stats: dict[str, dict[str, dict]] = {}  # user_id -> opponent -> stats

        # Race condition 방지를 위한 Lock
        self._block_locks: dict[str, asyncio.Lock] = {}

    @property
    def enabled(self) -> bool:
        """서비스 활성화 여부."""
        return self._enabled

    # =========================================================================
    # 이벤트 처리
    # =========================================================================

    async def process_hand_completed(
        self,
        hand_id: str,
        room_id: str,
        participants: list[dict[str, Any]],
        pot_size: int,
    ) -> list[str]:
        """핸드 완료 이벤트 처리.

        Returns:
            차단된 사용자 ID 목록
        """
        blocked_users = []

        # 참가자별 통계 업데이트
        for p in participants:
            user_id = p["user_id"]
            won_amount = p.get("won_amount", 0)
            bet_amount = p.get("bet_amount", 0)

            # 상대방 통계 업데이트 (담합/칩덤핑 탐지용)
            for opponent in participants:
                if opponent["user_id"] != user_id:
                    self._update_vs_stats(
                        user_id=user_id,
                        opponent_id=opponent["user_id"],
                        won=won_amount > 0,
                        amount=won_amount if won_amount > 0 else bet_amount,
                    )

        # 칩 덤핑 분석
        await self._analyze_chip_dumping(participants, pot_size)

        # 담합 분석
        await self._analyze_collusion_pattern(participants, room_id)

        # 자동 차단 체크
        for p in participants:
            user_id = p["user_id"]
            if await self._check_and_block_user(user_id):
                blocked_users.append(user_id)

        return blocked_users

    async def process_player_action(
        self,
        user_id: str,
        room_id: str,
        action_type: str,
        response_time_ms: int,
        ip_address: str | None = None,
    ) -> bool:
        """플레이어 액션 이벤트 처리.

        Returns:
            차단 여부
        """
        # 액션 기록 저장
        if user_id not in self._user_actions:
            self._user_actions[user_id] = []

        self._user_actions[user_id].append({
            "action": action_type,
            "response_time_ms": response_time_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "room_id": room_id,
        })

        # 최근 100개만 유지
        if len(self._user_actions[user_id]) > 100:
            self._user_actions[user_id] = self._user_actions[user_id][-100:]

        # IP 추적 (담합 탐지용)
        if ip_address:
            if ip_address not in self._ip_to_users:
                self._ip_to_users[ip_address] = set()
            self._ip_to_users[ip_address].add(user_id)

        # 봇 분석
        await self._analyze_bot_behavior(user_id, response_time_ms)

        # 자동 차단 체크
        return await self._check_and_block_user(user_id)

    async def process_session_start(
        self,
        user_id: str,
        ip_address: str,
        device_fingerprint: str | None = None,
    ) -> bool:
        """세션 시작 이벤트 처리 (다중 계정 탐지).

        Returns:
            차단 여부
        """
        # IP 추적
        if ip_address not in self._ip_to_users:
            self._ip_to_users[ip_address] = set()

        existing_users = self._ip_to_users[ip_address]

        # 같은 IP에서 다른 계정이 이미 접속 중이면 의심
        if existing_users and user_id not in existing_users:
            score = self._get_or_create_score(user_id)
            score.multi_account_score += MULTI_ACCOUNT_SAME_IP_PENALTY
            score.evidence.append(
                f"같은 IP({ip_address[:10]}...)에서 다른 계정 감지"
            )
            # 로그에서 user_id 마스킹 (보안)
            logger.warning(
                f"다중 계정 의심: {user_id[:8]}..., IP에 기존 사용자 {len(existing_users)}명"
            )

        self._ip_to_users[ip_address].add(user_id)

        return await self._check_and_block_user(user_id)

    # =========================================================================
    # 분석 로직
    # =========================================================================

    async def _analyze_bot_behavior(self, user_id: str, response_time_ms: int) -> None:
        """봇 행동 분석."""
        score = self._get_or_create_score(user_id)

        # 빠른 응답 체크
        if response_time_ms < BOT_FAST_RESPONSE_MS:
            score.bot_score += BOT_FAST_RESPONSE_PENALTY
            score.evidence.append(f"빠른 응답: {response_time_ms}ms")

        # 응답 시간 패턴 분석 (일정한 타이밍 = 봇 의심)
        actions = self._user_actions.get(user_id, [])
        if len(actions) >= 10:
            recent_times = [a["response_time_ms"] for a in actions[-10:]]
            avg = sum(recent_times) / len(recent_times)
            variance = sum((t - avg) ** 2 for t in recent_times) / len(recent_times)
            std_dev = variance ** 0.5

            # 표준편차가 너무 낮으면 의심 (인간은 변동이 큼)
            if std_dev < 100 and avg < 2000:
                if "일정한 응답 패턴" not in str(score.evidence):
                    score.bot_score += BOT_CONSISTENT_TIMING_PENALTY
                    score.evidence.append(
                        f"일정한 응답 패턴 감지: 평균 {avg:.0f}ms, 표준편차 {std_dev:.0f}ms"
                    )

        score.last_updated = datetime.now(timezone.utc)

    async def _analyze_chip_dumping(
        self,
        participants: list[dict[str, Any]],
        pot_size: int,
    ) -> None:
        """칩 덤핑 분석."""
        # 큰 팟을 특정 상대에게만 반복해서 잃는 패턴 감지
        for p in participants:
            user_id = p["user_id"]
            bet_amount = p.get("bet_amount", 0)
            won_amount = p.get("won_amount", 0)

            # 큰 손실 발생
            if bet_amount > 0 and won_amount == 0:
                loss_ratio = bet_amount / pot_size if pot_size > 0 else 0

                if loss_ratio >= CHIP_DUMP_LARGE_LOSS_THRESHOLD:
                    # 누가 이겼는지 확인
                    winners = [
                        op for op in participants
                        if op.get("won_amount", 0) > 0 and op["user_id"] != user_id
                    ]

                    for winner in winners:
                        vs_stats = self._get_vs_stats(user_id, winner["user_id"])

                        # 같은 상대에게 반복 패배
                        if vs_stats["losses"] >= 3:
                            loss_rate = vs_stats["losses"] / max(vs_stats["total"], 1)
                            if loss_rate >= 0.8:  # 80% 이상 패배
                                score = self._get_or_create_score(user_id)
                                score.chip_dumping_score += CHIP_DUMP_SAME_WINNER_PENALTY
                                score.evidence.append(
                                    f"칩 덤핑 의심: {winner['user_id'][:8]}에게 "
                                    f"{vs_stats['losses']}/{vs_stats['total']} 패배"
                                )

    async def _analyze_collusion_pattern(
        self,
        participants: list[dict[str, Any]],
        room_id: str,
    ) -> None:
        """담합 패턴 분석."""
        user_ids = [p["user_id"] for p in participants]

        # 같은 IP 체크
        ip_groups = self._find_same_ip_users(user_ids)

        for ip, users_in_room in ip_groups.items():
            if len(users_in_room) >= 2:
                for user_id in users_in_room:
                    score = self._get_or_create_score(user_id)
                    score.collusion_score += COLLUSION_SAME_IP_PENALTY
                    score.evidence.append(
                        f"담합 의심: 같은 IP에서 {len(users_in_room)}명 동시 플레이"
                    )
                    # 로그에서 user_id 마스킹 (보안)
                    logger.warning(
                        f"담합 의심: {user_id[:8]}... - 같은 IP에서 {len(users_in_room)}명 동시 접속"
                    )

    def _find_same_ip_users(self, user_ids: list[str]) -> dict[str, list[str]]:
        """같은 IP를 사용하는 사용자 그룹 찾기."""
        result: dict[str, list[str]] = {}

        for ip, users in self._ip_to_users.items():
            matched = [uid for uid in user_ids if uid in users]
            if len(matched) >= 2:
                result[ip] = matched

        return result

    # =========================================================================
    # 차단 처리
    # =========================================================================

    async def _check_and_block_user(self, user_id: str) -> bool:
        """사용자 차단 여부 체크 및 실행.

        Race condition 방지를 위해 사용자별 Lock 사용.

        Returns:
            차단 실행 여부
        """
        if not self.auto_block_enabled:
            return False

        # 사용자별 Lock 생성/획득
        if user_id not in self._block_locks:
            self._block_locks[user_id] = asyncio.Lock()

        async with self._block_locks[user_id]:
            score = self._fraud_scores.get(user_id)
            if not score or not score.should_auto_block(self.block_threshold):
                return False

            # 차단 이벤트 발행
            reason = score.get_primary_reason()
            event = FraudBlockEvent(
                user_id=user_id,
                block_reason=reason.value,
                fraud_score=score.total_score,
                evidence=score.evidence[-10:],  # 최근 10개 증거만
            )

            # Redis에 차단 이벤트 발행 (admin-backend에서 처리)
            if self.redis:
                await self.redis.publish(
                    "fraud:auto_block",
                    event.model_dump_json(),
                )

            # 점수 초기화 (중복 차단 방지)
            self._fraud_scores[user_id] = FraudScore(user_id=user_id)

            # 로그에서 user_id 마스킹 (보안)
            logger.warning(
                f"자동 차단 요청: {user_id[:8]}..., 사유: {reason.value}, "
                f"점수: {score.total_score:.1f}"
            )

            return True

    async def block_user_db(
        self,
        db: AsyncSession,
        user_id: str,
        reason: BlockReason,
        evidence: list[str],
    ) -> bool:
        """DB에서 사용자 차단 처리.

        Args:
            db: DB 세션
            user_id: 차단할 사용자 ID
            reason: 차단 사유
            evidence: 증거 목록

        Returns:
            차단 성공 여부
        """
        from app.models.user import User, UserStatus

        try:
            # 사용자 상태를 SUSPENDED로 변경
            stmt = (
                update(User)
                .where(User.id == user_id)
                .where(User.status == UserStatus.ACTIVE.value)
                .values(status=UserStatus.SUSPENDED.value)
            )
            result = await db.execute(stmt)

            if result.rowcount == 0:
                logger.warning(f"차단 실패: 사용자 {user_id}를 찾을 수 없거나 이미 차단됨")
                return False

            # 차단 기록 저장 (Redis)
            if self.redis:
                block_record = {
                    "user_id": user_id,
                    "reason": reason.value,
                    "evidence": evidence,
                    "blocked_at": datetime.now(timezone.utc).isoformat(),
                    "auto_blocked": True,
                }
                await self.redis.hset(
                    "fraud:blocked_users",
                    user_id,
                    json.dumps(block_record),
                )

            logger.info(f"사용자 차단 완료: {user_id}, 사유: {reason.value}")
            return True

        except Exception as e:
            logger.error(f"사용자 차단 실패: {user_id}, 에러: {e}")
            return False

    # =========================================================================
    # 점수 관리
    # =========================================================================

    def _get_or_create_score(self, user_id: str) -> FraudScore:
        """사용자의 부정행위 점수 조회/생성."""
        if user_id not in self._fraud_scores:
            self._fraud_scores[user_id] = FraudScore(user_id=user_id)
        return self._fraud_scores[user_id]

    def _update_vs_stats(
        self,
        user_id: str,
        opponent_id: str,
        won: bool,
        amount: int,
    ) -> None:
        """상대방 대비 통계 업데이트."""
        if user_id not in self._user_vs_user_stats:
            self._user_vs_user_stats[user_id] = {}

        if opponent_id not in self._user_vs_user_stats[user_id]:
            self._user_vs_user_stats[user_id][opponent_id] = {
                "wins": 0,
                "losses": 0,
                "total": 0,
                "total_won": 0,
                "total_lost": 0,
            }

        stats = self._user_vs_user_stats[user_id][opponent_id]
        stats["total"] += 1

        if won:
            stats["wins"] += 1
            stats["total_won"] += amount
        else:
            stats["losses"] += 1
            stats["total_lost"] += amount

    def _get_vs_stats(self, user_id: str, opponent_id: str) -> dict:
        """상대방 대비 통계 조회."""
        return self._user_vs_user_stats.get(user_id, {}).get(opponent_id, {
            "wins": 0,
            "losses": 0,
            "total": 0,
            "total_won": 0,
            "total_lost": 0,
        })

    def get_user_fraud_score(self, user_id: str) -> FraudScore | None:
        """사용자의 현재 부정행위 점수 조회."""
        return self._fraud_scores.get(user_id)

    def reset_user_score(self, user_id: str) -> None:
        """사용자의 부정행위 점수 초기화."""
        if user_id in self._fraud_scores:
            del self._fraud_scores[user_id]
        if user_id in self._user_actions:
            del self._user_actions[user_id]
        if user_id in self._user_vs_user_stats:
            del self._user_vs_user_stats[user_id]

    async def cleanup_old_data(self, max_age_hours: int = 24) -> int:
        """오래된 데이터 정리.

        메모리 누수 방지를 위해 모든 관련 딕셔너리를 정리합니다.

        Args:
            max_age_hours: 최대 보관 시간

        Returns:
            정리된 항목 수
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        cleaned = 0

        # 1. 오래된 점수 정리 (낮은 점수만)
        score_to_remove = [
            user_id for user_id, score in self._fraud_scores.items()
            if score.last_updated < cutoff and score.total_score < 30
        ]

        for user_id in score_to_remove:
            del self._fraud_scores[user_id]
            cleaned += 1

        # 2. 관련 user_actions 정리 (점수가 없는 사용자)
        actions_to_remove = [
            user_id for user_id in self._user_actions
            if user_id not in self._fraud_scores
        ]
        for user_id in actions_to_remove:
            del self._user_actions[user_id]

        # 3. 관련 user_vs_user_stats 정리 (점수가 없는 사용자)
        stats_to_remove = [
            user_id for user_id in self._user_vs_user_stats
            if user_id not in self._fraud_scores
        ]
        for user_id in stats_to_remove:
            del self._user_vs_user_stats[user_id]

        # 4. 빈 IP 매핑 정리
        ip_to_remove = [
            ip for ip, users in self._ip_to_users.items()
            if len(users) == 0
        ]
        for ip in ip_to_remove:
            del self._ip_to_users[ip]

        # 5. 사용하지 않는 Lock 정리
        lock_to_remove = [
            user_id for user_id in self._block_locks
            if user_id not in self._fraud_scores
        ]
        for user_id in lock_to_remove:
            del self._block_locks[user_id]

        if cleaned > 0:
            logger.info(
                f"오래된 fraud 데이터 정리: 점수 {cleaned}개, "
                f"액션 {len(actions_to_remove)}개, 통계 {len(stats_to_remove)}개"
            )

        return cleaned


# =============================================================================
# 싱글톤 인스턴스
# =============================================================================

_fraud_blocker: FraudAutoBlocker | None = None


def get_fraud_blocker() -> FraudAutoBlocker | None:
    """Get the global FraudAutoBlocker instance."""
    return _fraud_blocker


def init_fraud_blocker(
    redis_client: "Redis | None",
    auto_block_enabled: bool = True,
    block_threshold: float = AUTO_BLOCK_THRESHOLD,
) -> FraudAutoBlocker:
    """Initialize the global FraudAutoBlocker instance.

    Args:
        redis_client: Redis 클라이언트
        auto_block_enabled: 자동 차단 활성화 여부
        block_threshold: 자동 차단 임계값

    Returns:
        초기화된 FraudAutoBlocker 인스턴스
    """
    global _fraud_blocker
    _fraud_blocker = FraudAutoBlocker(
        redis_client=redis_client,
        auto_block_enabled=auto_block_enabled,
        block_threshold=block_threshold,
    )
    logger.info(
        f"FraudAutoBlocker initialized "
        f"(enabled={_fraud_blocker.enabled}, auto_block={auto_block_enabled})"
    )
    return _fraud_blocker
