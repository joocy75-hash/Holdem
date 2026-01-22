"""FraudAutoBlocker 단위 테스트.

부정행위 자동 차단 서비스의 핵심 기능을 검증합니다:
- 봇 탐지 (빠른 응답, 일정한 패턴)
- 담합 탐지 (같은 IP 동시 접속)
- 칩 덤핑 탐지 (특정 상대에게 반복 패배)
- 다중 계정 탐지 (같은 IP 다중 계정)
- 자동 차단 임계값
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.fraud_auto_blocker import (
    AUTO_BLOCK_THRESHOLD,
    BOT_FAST_RESPONSE_MS,
    BOT_FAST_RESPONSE_PENALTY,
    COLLUSION_SAME_IP_PENALTY,
    CHIP_DUMP_SAME_WINNER_PENALTY,
    MULTI_ACCOUNT_SAME_IP_PENALTY,
    BlockReason,
    FraudAutoBlocker,
    FraudScore,
    FraudType,
    get_fraud_blocker,
    init_fraud_blocker,
)


# =============================================================================
# FraudScore 테스트
# =============================================================================


class TestFraudScore:
    """FraudScore 데이터클래스 테스트."""

    def test_total_score_calculation(self):
        """전체 점수 계산 테스트."""
        score = FraudScore(
            user_id="user1",
            collusion_score=50.0,
            bot_score=30.0,
            chip_dumping_score=20.0,
            multi_account_score=10.0,
        )

        # 가중치: collusion 0.35, bot 0.25, chip_dumping 0.25, multi_account 0.15
        expected = (
            50.0 * 0.35 +  # 17.5
            30.0 * 0.25 +  # 7.5
            20.0 * 0.25 +  # 5.0
            10.0 * 0.15    # 1.5
        )  # = 31.5

        assert score.total_score == pytest.approx(expected, rel=0.01)

    def test_total_score_capped_at_100(self):
        """전체 점수 100점 상한 테스트."""
        score = FraudScore(
            user_id="user1",
            collusion_score=200.0,
            bot_score=200.0,
            chip_dumping_score=200.0,
            multi_account_score=200.0,
        )

        assert score.total_score == 100.0

    def test_should_auto_block_below_threshold(self):
        """임계값 이하면 차단하지 않음."""
        score = FraudScore(user_id="user1", collusion_score=50.0)
        assert not score.should_auto_block(threshold=70.0)

    def test_should_auto_block_above_threshold(self):
        """임계값 이상이면 차단."""
        score = FraudScore(
            user_id="user1",
            collusion_score=100.0,
            bot_score=100.0,
            chip_dumping_score=100.0,
        )
        assert score.should_auto_block(threshold=70.0)

    def test_get_primary_reason(self):
        """주요 차단 사유 추출 테스트."""
        score = FraudScore(
            user_id="user1",
            collusion_score=10.0,
            bot_score=80.0,  # 가장 높음
            chip_dumping_score=20.0,
            multi_account_score=5.0,
        )

        assert score.get_primary_reason() == BlockReason.BOT_BEHAVIOR

    def test_evidence_tracking(self):
        """증거 목록 추적 테스트."""
        score = FraudScore(user_id="user1")
        score.evidence.append("빠른 응답: 100ms")
        score.evidence.append("같은 IP 동시 접속")

        assert len(score.evidence) == 2
        assert "빠른 응답: 100ms" in score.evidence


# =============================================================================
# FraudAutoBlocker 봇 탐지 테스트
# =============================================================================


class TestBotDetection:
    """봇 탐지 기능 테스트."""

    @pytest.fixture
    def blocker(self):
        """테스트용 FraudAutoBlocker 인스턴스."""
        return FraudAutoBlocker(
            redis_client=None,
            auto_block_enabled=False,  # 테스트에서는 자동 차단 비활성화
        )

    @pytest.mark.asyncio
    async def test_fast_response_increases_bot_score(self, blocker):
        """빠른 응답 시 봇 점수 증가."""
        user_id = "bot_suspect"

        # 매우 빠른 응답 (100ms)
        await blocker.process_player_action(
            user_id=user_id,
            room_id="room1",
            action_type="fold",
            response_time_ms=100,
        )

        score = blocker.get_user_fraud_score(user_id)
        assert score is not None
        assert score.bot_score >= BOT_FAST_RESPONSE_PENALTY

    @pytest.mark.asyncio
    async def test_normal_response_no_penalty(self, blocker):
        """정상 응답 시간은 페널티 없음."""
        user_id = "normal_user"

        # 정상 응답 (2초)
        await blocker.process_player_action(
            user_id=user_id,
            room_id="room1",
            action_type="fold",
            response_time_ms=2000,
        )

        score = blocker.get_user_fraud_score(user_id)
        # 봇 점수가 없거나 매우 낮아야 함
        assert score is None or score.bot_score < BOT_FAST_RESPONSE_PENALTY

    @pytest.mark.asyncio
    async def test_consistent_timing_pattern_detected(self, blocker):
        """일정한 타이밍 패턴 감지."""
        user_id = "bot_timing"

        # 10회 연속 거의 동일한 응답 시간 (봇 의심)
        for _ in range(12):
            await blocker.process_player_action(
                user_id=user_id,
                room_id="room1",
                action_type="call",
                response_time_ms=1000,  # 정확히 1초
            )

        score = blocker.get_user_fraud_score(user_id)
        assert score is not None
        # 일정한 패턴 페널티가 적용되어야 함
        assert "일정한 응답 패턴" in str(score.evidence)


# =============================================================================
# FraudAutoBlocker 담합 탐지 테스트
# =============================================================================


class TestCollusionDetection:
    """담합 탐지 기능 테스트."""

    @pytest.fixture
    def blocker(self):
        """테스트용 FraudAutoBlocker 인스턴스."""
        return FraudAutoBlocker(
            redis_client=None,
            auto_block_enabled=False,
        )

    @pytest.mark.asyncio
    async def test_same_ip_collusion_detected(self, blocker):
        """같은 IP 동시 접속 담합 감지."""
        ip = "192.168.1.100"
        user1 = "colluder1"
        user2 = "colluder2"

        # 두 사용자가 같은 IP로 세션 시작
        await blocker.process_session_start(user1, ip)
        await blocker.process_session_start(user2, ip)

        # 같은 테이블에서 핸드 완료
        await blocker.process_hand_completed(
            hand_id="hand1",
            room_id="room1",
            participants=[
                {"user_id": user1, "bet_amount": 100, "won_amount": 0},
                {"user_id": user2, "bet_amount": 100, "won_amount": 200},
            ],
            pot_size=200,
        )

        # 두 사용자 모두 담합 점수 증가
        score1 = blocker.get_user_fraud_score(user1)
        score2 = blocker.get_user_fraud_score(user2)

        assert score1 is not None
        assert score2 is not None
        assert score1.collusion_score >= COLLUSION_SAME_IP_PENALTY
        assert score2.collusion_score >= COLLUSION_SAME_IP_PENALTY

    @pytest.mark.asyncio
    async def test_different_ip_no_collusion(self, blocker):
        """다른 IP면 담합으로 감지하지 않음."""
        user1 = "player1"
        user2 = "player2"

        # 다른 IP로 세션 시작
        await blocker.process_session_start(user1, "192.168.1.1")
        await blocker.process_session_start(user2, "192.168.1.2")

        # 같은 테이블에서 핸드 완료
        await blocker.process_hand_completed(
            hand_id="hand1",
            room_id="room1",
            participants=[
                {"user_id": user1, "bet_amount": 100, "won_amount": 0},
                {"user_id": user2, "bet_amount": 100, "won_amount": 200},
            ],
            pot_size=200,
        )

        score1 = blocker.get_user_fraud_score(user1)
        score2 = blocker.get_user_fraud_score(user2)

        # 담합 점수가 없거나 낮아야 함
        assert score1 is None or score1.collusion_score == 0
        assert score2 is None or score2.collusion_score == 0


# =============================================================================
# FraudAutoBlocker 칩 덤핑 탐지 테스트
# =============================================================================


class TestChipDumpingDetection:
    """칩 덤핑 탐지 기능 테스트."""

    @pytest.fixture
    def blocker(self):
        """테스트용 FraudAutoBlocker 인스턴스."""
        return FraudAutoBlocker(
            redis_client=None,
            auto_block_enabled=False,
        )

    @pytest.mark.asyncio
    async def test_repeated_losses_to_same_opponent(self, blocker):
        """같은 상대에게 반복 패배 시 칩 덤핑 감지."""
        dumper = "chip_dumper"
        receiver = "chip_receiver"

        # 5번 연속 같은 상대에게 패배
        for i in range(5):
            await blocker.process_hand_completed(
                hand_id=f"hand{i}",
                room_id="room1",
                participants=[
                    {"user_id": dumper, "bet_amount": 500, "won_amount": 0},
                    {"user_id": receiver, "bet_amount": 100, "won_amount": 600},
                ],
                pot_size=600,
            )

        score = blocker.get_user_fraud_score(dumper)
        assert score is not None
        assert score.chip_dumping_score > 0
        assert "칩 덤핑 의심" in str(score.evidence)

    @pytest.mark.asyncio
    async def test_normal_losses_no_dumping(self, blocker):
        """정상적인 패배는 덤핑으로 감지하지 않음."""
        player = "normal_player"
        opponent1 = "opponent1"
        opponent2 = "opponent2"
        opponent3 = "opponent3"

        # 다양한 상대에게 패배 (정상)
        opponents = [opponent1, opponent2, opponent3]
        for i, opp in enumerate(opponents):
            await blocker.process_hand_completed(
                hand_id=f"hand{i}",
                room_id="room1",
                participants=[
                    {"user_id": player, "bet_amount": 100, "won_amount": 0},
                    {"user_id": opp, "bet_amount": 100, "won_amount": 200},
                ],
                pot_size=200,
            )

        score = blocker.get_user_fraud_score(player)
        # 칩 덤핑 점수가 없거나 낮아야 함
        assert score is None or score.chip_dumping_score < CHIP_DUMP_SAME_WINNER_PENALTY


# =============================================================================
# FraudAutoBlocker 다중 계정 탐지 테스트
# =============================================================================


class TestMultiAccountDetection:
    """다중 계정 탐지 기능 테스트."""

    @pytest.fixture
    def blocker(self):
        """테스트용 FraudAutoBlocker 인스턴스."""
        return FraudAutoBlocker(
            redis_client=None,
            auto_block_enabled=False,
        )

    @pytest.mark.asyncio
    async def test_same_ip_different_account_detected(self, blocker):
        """같은 IP에서 다른 계정 접속 시 다중 계정 감지."""
        ip = "192.168.1.50"
        account1 = "main_account"
        account2 = "alt_account"

        # 첫 번째 계정 접속
        await blocker.process_session_start(account1, ip)

        # 같은 IP로 두 번째 계정 접속
        await blocker.process_session_start(account2, ip)

        score = blocker.get_user_fraud_score(account2)
        assert score is not None
        assert score.multi_account_score >= MULTI_ACCOUNT_SAME_IP_PENALTY

    @pytest.mark.asyncio
    async def test_same_account_same_ip_ok(self, blocker):
        """같은 계정 재접속은 문제없음."""
        ip = "192.168.1.50"
        account = "my_account"

        # 같은 계정으로 여러 번 접속
        await blocker.process_session_start(account, ip)
        await blocker.process_session_start(account, ip)

        score = blocker.get_user_fraud_score(account)
        # 다중 계정 점수가 없어야 함
        assert score is None or score.multi_account_score == 0


# =============================================================================
# FraudAutoBlocker 자동 차단 테스트
# =============================================================================


class TestAutoBlock:
    """자동 차단 기능 테스트."""

    @pytest.fixture
    def blocker_with_redis(self):
        """Redis mock이 있는 FraudAutoBlocker."""
        mock_redis = AsyncMock()
        return FraudAutoBlocker(
            redis_client=mock_redis,
            auto_block_enabled=True,
            block_threshold=70.0,
        )

    @pytest.mark.asyncio
    async def test_auto_block_when_threshold_exceeded(self, blocker_with_redis):
        """임계값 초과 시 자동 차단."""
        blocker = blocker_with_redis
        user_id = "bad_actor"

        # 점수를 수동으로 설정 (임계값 초과)
        score = blocker._get_or_create_score(user_id)
        score.collusion_score = 100.0
        score.bot_score = 100.0
        score.chip_dumping_score = 100.0
        score.evidence = ["테스트 증거"]

        # 차단 체크 실행
        blocked = await blocker._check_and_block_user(user_id)

        assert blocked is True
        # Redis에 차단 이벤트 발행되었는지 확인
        blocker.redis.publish.assert_called_once()
        call_args = blocker.redis.publish.call_args
        assert call_args[0][0] == "fraud:auto_block"

    @pytest.mark.asyncio
    async def test_no_auto_block_below_threshold(self, blocker_with_redis):
        """임계값 이하면 차단하지 않음."""
        blocker = blocker_with_redis
        user_id = "normal_user"

        # 낮은 점수
        score = blocker._get_or_create_score(user_id)
        score.collusion_score = 10.0

        blocked = await blocker._check_and_block_user(user_id)

        assert blocked is False
        blocker.redis.publish.assert_not_called()

    @pytest.mark.asyncio
    async def test_auto_block_disabled(self):
        """자동 차단 비활성화 시 차단하지 않음."""
        blocker = FraudAutoBlocker(
            redis_client=AsyncMock(),
            auto_block_enabled=False,  # 비활성화
        )
        user_id = "any_user"

        # 높은 점수
        score = blocker._get_or_create_score(user_id)
        score.collusion_score = 200.0

        blocked = await blocker._check_and_block_user(user_id)

        assert blocked is False


# =============================================================================
# FraudAutoBlocker 데이터 관리 테스트
# =============================================================================


class TestDataManagement:
    """데이터 관리 기능 테스트."""

    @pytest.fixture
    def blocker(self):
        """테스트용 FraudAutoBlocker 인스턴스."""
        return FraudAutoBlocker(redis_client=None, auto_block_enabled=False)

    def test_reset_user_score(self, blocker):
        """사용자 점수 초기화 테스트."""
        user_id = "user_to_reset"

        # 데이터 추가
        score = blocker._get_or_create_score(user_id)
        score.bot_score = 50.0
        blocker._user_actions[user_id] = [{"action": "fold"}]
        blocker._user_vs_user_stats[user_id] = {"opponent": {"wins": 1}}

        # 초기화
        blocker.reset_user_score(user_id)

        assert blocker.get_user_fraud_score(user_id) is None
        assert user_id not in blocker._user_actions
        assert user_id not in blocker._user_vs_user_stats

    @pytest.mark.asyncio
    async def test_cleanup_old_data(self, blocker):
        """오래된 데이터 정리 테스트."""
        # 오래된 점수 추가
        old_user = "old_user"
        score = blocker._get_or_create_score(old_user)
        score.last_updated = datetime.now(timezone.utc) - timedelta(hours=48)
        score.bot_score = 10.0  # 낮은 점수

        # 최근 점수 추가
        new_user = "new_user"
        new_score = blocker._get_or_create_score(new_user)
        new_score.bot_score = 10.0

        # 24시간 기준 정리
        cleaned = await blocker.cleanup_old_data(max_age_hours=24)

        assert cleaned == 1
        assert blocker.get_user_fraud_score(old_user) is None
        assert blocker.get_user_fraud_score(new_user) is not None


# =============================================================================
# 싱글톤 테스트
# =============================================================================


class TestSingleton:
    """싱글톤 인스턴스 테스트."""

    def test_init_fraud_blocker(self):
        """FraudAutoBlocker 초기화 테스트."""
        mock_redis = MagicMock()
        blocker = init_fraud_blocker(
            redis_client=mock_redis,
            auto_block_enabled=True,
            block_threshold=80.0,
        )

        assert blocker is not None
        assert blocker.enabled is True
        assert blocker.auto_block_enabled is True
        assert blocker.block_threshold == 80.0

    def test_get_fraud_blocker(self):
        """싱글톤 인스턴스 조회 테스트."""
        # init 후 get 테스트
        mock_redis = MagicMock()
        init_fraud_blocker(mock_redis)

        blocker = get_fraud_blocker()
        assert blocker is not None

    def test_disabled_without_redis(self):
        """Redis 없이 초기화 시 비활성화."""
        blocker = init_fraud_blocker(redis_client=None)

        assert blocker.enabled is False


# =============================================================================
# 통합 시나리오 테스트
# =============================================================================


class TestIntegrationScenarios:
    """통합 시나리오 테스트."""

    @pytest.fixture
    def blocker(self):
        """테스트용 FraudAutoBlocker 인스턴스."""
        mock_redis = AsyncMock()
        return FraudAutoBlocker(
            redis_client=mock_redis,
            auto_block_enabled=True,
            block_threshold=70.0,
        )

    @pytest.mark.asyncio
    async def test_combined_fraud_detection(self, blocker):
        """복합 부정행위 탐지 시나리오."""
        user_id = "combined_cheater"
        ip = "192.168.1.200"

        # 1. 다중 계정 의심 (같은 IP에서 다른 계정 존재)
        blocker._ip_to_users[ip] = {"other_account"}
        await blocker.process_session_start(user_id, ip)

        # 2. 봇 의심 (빠른 응답)
        for _ in range(5):
            await blocker.process_player_action(
                user_id=user_id,
                room_id="room1",
                action_type="fold",
                response_time_ms=200,
                ip_address=ip,
            )

        score = blocker.get_user_fraud_score(user_id)
        assert score is not None
        assert score.multi_account_score > 0
        assert score.bot_score > 0
        assert score.total_score > 0

    @pytest.mark.asyncio
    async def test_legitimate_player_not_blocked(self, blocker):
        """정상 플레이어는 차단되지 않음."""
        user_id = "legitimate_player"

        # 정상적인 플레이 패턴
        for i in range(20):
            await blocker.process_player_action(
                user_id=user_id,
                room_id="room1",
                action_type="call" if i % 3 == 0 else "fold",
                response_time_ms=2000 + (i * 100),  # 다양한 응답 시간
            )

        # 정상적인 승패
        opponents = ["opp1", "opp2", "opp3", "opp4"]
        for i, opp in enumerate(opponents):
            await blocker.process_hand_completed(
                hand_id=f"hand{i}",
                room_id="room1",
                participants=[
                    {
                        "user_id": user_id,
                        "bet_amount": 100,
                        "won_amount": 200 if i % 2 == 0 else 0,
                    },
                    {
                        "user_id": opp,
                        "bet_amount": 100,
                        "won_amount": 0 if i % 2 == 0 else 200,
                    },
                ],
                pot_size=200,
            )

        score = blocker.get_user_fraud_score(user_id)
        # 점수가 없거나 임계값보다 낮아야 함
        assert score is None or score.total_score < 70.0
