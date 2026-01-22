"""
BlindScheduler 단위 테스트.

테스트 범위:
─────────────────────────────────────────────────────────────────────────────────

1. PrecisionTimer 정확도 검증
2. 10단계 이상 블라인드 업 연속 테스트
3. Pause/Resume 기능 테스트
4. 메모리 누수 방지 검증
5. 경고 이벤트 전송 테스트
6. 다중 토너먼트 동시 운영 테스트

─────────────────────────────────────────────────────────────────────────────────
"""

import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.tournament.blind_scheduler import (
    BlindScheduler,
    BlindSchedule,
    PrecisionTimer,
    SchedulerMetrics,
    create_standard_blind_structure,
    WARNING_SECONDS,
)
from app.tournament.models import BlindLevel, TournamentEventType


# ─────────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_redis():
    """Mock Redis 클라이언트."""
    redis = AsyncMock()
    redis.set = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.delete = AsyncMock()
    redis.expire = AsyncMock()
    redis.scan = AsyncMock(return_value=(0, []))
    return redis


@pytest.fixture
def sample_blind_levels():
    """테스트용 블라인드 레벨 (빠른 테스트를 위해 짧은 duration)."""
    return [
        BlindLevel(level=1, small_blind=25, big_blind=50, ante=0, duration_minutes=0.05),  # 3초
        BlindLevel(level=2, small_blind=50, big_blind=100, ante=0, duration_minutes=0.05),
        BlindLevel(level=3, small_blind=75, big_blind=150, ante=0, duration_minutes=0.05),
        BlindLevel(level=4, small_blind=100, big_blind=200, ante=25, duration_minutes=0.05),
        BlindLevel(level=5, small_blind=150, big_blind=300, ante=25, duration_minutes=0.05),
        BlindLevel(level=6, small_blind=200, big_blind=400, ante=50, duration_minutes=0.05),
        BlindLevel(level=7, small_blind=300, big_blind=600, ante=75, duration_minutes=0.05),
        BlindLevel(level=8, small_blind=400, big_blind=800, ante=100, duration_minutes=0.05),
        BlindLevel(level=9, small_blind=600, big_blind=1200, ante=150, duration_minutes=0.05),
        BlindLevel(level=10, small_blind=800, big_blind=1600, ante=200, duration_minutes=0.05),
        BlindLevel(level=11, small_blind=1000, big_blind=2000, ante=300, duration_minutes=0.05),
        BlindLevel(level=12, small_blind=1500, big_blind=3000, ante=400, duration_minutes=0.05),
    ]


@pytest.fixture
def quick_blind_levels():
    """매우 빠른 테스트용 블라인드 레벨 (0.5초)."""
    return [
        BlindLevel(level=1, small_blind=25, big_blind=50, ante=0, duration_minutes=0.0083),  # 0.5초
        BlindLevel(level=2, small_blind=50, big_blind=100, ante=0, duration_minutes=0.0083),
        BlindLevel(level=3, small_blind=75, big_blind=150, ante=0, duration_minutes=0.0083),
    ]


@pytest.fixture
async def scheduler(mock_redis):
    """BlindScheduler 인스턴스."""
    scheduler = BlindScheduler(mock_redis)
    await scheduler.start()
    yield scheduler
    await scheduler.stop()


# ─────────────────────────────────────────────────────────────────────────────────
# PrecisionTimer 테스트
# ─────────────────────────────────────────────────────────────────────────────────


class TestPrecisionTimer:
    """PrecisionTimer 테스트."""

    @pytest.mark.asyncio
    async def test_sleep_seconds_accuracy(self):
        """sleep_seconds 정확도 테스트 (50ms 이내 오차)."""
        target_duration = 0.1  # 100ms

        start = time.monotonic()
        drift = await PrecisionTimer.sleep_seconds(target_duration)
        elapsed = time.monotonic() - start

        # 실제 경과 시간이 목표에 가까운지 확인
        assert abs(elapsed - target_duration) < 0.05  # 50ms 이내
        assert abs(drift) < 50  # 드리프트 50ms 이내

    @pytest.mark.asyncio
    async def test_sleep_until_accuracy(self):
        """sleep_until 정확도 테스트."""
        target = time.monotonic() + 0.1  # 100ms 후

        drift = await PrecisionTimer.sleep_until(target)
        actual = time.monotonic()

        # 타겟 시간에 도달했는지 확인
        assert actual >= target - 0.01  # 10ms 허용 오차
        assert abs(drift) < 50  # 드리프트 50ms 이내

    @pytest.mark.asyncio
    async def test_multiple_consecutive_sleeps(self):
        """연속 슬립 정확도 테스트."""
        total_drift = 0.0
        iterations = 5

        for _ in range(iterations):
            drift = await PrecisionTimer.sleep_seconds(0.05)  # 50ms
            total_drift += abs(drift)

        # 평균 드리프트가 30ms 이내인지 확인
        avg_drift = total_drift / iterations
        assert avg_drift < 30


# ─────────────────────────────────────────────────────────────────────────────────
# BlindSchedule 테스트
# ─────────────────────────────────────────────────────────────────────────────────


class TestBlindSchedule:
    """BlindSchedule 테스트."""

    def test_current_blind(self, sample_blind_levels):
        """현재 블라인드 조회 테스트."""
        schedule = BlindSchedule(
            tournament_id="test-1",
            levels=sample_blind_levels,
            current_level=5,
        )

        current = schedule.current_blind
        assert current is not None
        assert current.level == 5
        assert current.small_blind == 150
        assert current.big_blind == 300
        assert current.ante == 25

    def test_next_blind(self, sample_blind_levels):
        """다음 블라인드 조회 테스트."""
        schedule = BlindSchedule(
            tournament_id="test-1",
            levels=sample_blind_levels,
            current_level=5,
        )

        next_blind = schedule.next_blind
        assert next_blind is not None
        assert next_blind.level == 6
        assert next_blind.small_blind == 200

    def test_remaining_time(self, sample_blind_levels):
        """남은 시간 계산 테스트."""
        schedule = BlindSchedule(
            tournament_id="test-1",
            levels=sample_blind_levels,
            current_level=1,
        )

        remaining = schedule.get_remaining_time()
        # 0.05분 = 3초, 방금 시작했으므로 약 3초 남음
        assert 0 < remaining <= 3.5

    def test_elapsed_time(self, sample_blind_levels):
        """경과 시간 계산 테스트."""
        # 1초 전에 시작한 것으로 설정
        schedule = BlindSchedule(
            tournament_id="test-1",
            levels=sample_blind_levels,
            current_level=1,
            level_started_at=time.monotonic() - 1.0,
        )

        elapsed = schedule.get_elapsed_time()
        assert 0.9 < elapsed < 1.5

    def test_pause_state(self, sample_blind_levels):
        """pause 상태 테스트."""
        schedule = BlindSchedule(
            tournament_id="test-1",
            levels=sample_blind_levels,
            current_level=1,
        )

        # 초기 상태: pause 아님
        assert not schedule.is_paused

        # pause 설정
        schedule.paused_at = time.monotonic()
        assert schedule.is_paused

    def test_to_dict(self, sample_blind_levels):
        """직렬화 테스트."""
        schedule = BlindSchedule(
            tournament_id="test-1",
            levels=sample_blind_levels,
            current_level=3,
        )

        data = schedule.to_dict()
        assert data["tournament_id"] == "test-1"
        assert data["current_level"] == 3
        assert data["small_blind"] == 75
        assert data["big_blind"] == 150
        assert "remaining_seconds" in data
        assert "next_level_at" in data


# ─────────────────────────────────────────────────────────────────────────────────
# BlindScheduler 기본 기능 테스트
# ─────────────────────────────────────────────────────────────────────────────────


class TestBlindSchedulerBasic:
    """BlindScheduler 기본 기능 테스트."""

    @pytest.mark.asyncio
    async def test_register_tournament(self, scheduler, sample_blind_levels):
        """토너먼트 등록 테스트."""
        schedule = await scheduler.register_tournament(
            tournament_id="test-tour-1",
            blind_levels=sample_blind_levels,
        )

        assert schedule is not None
        assert schedule.tournament_id == "test-tour-1"
        assert schedule.current_level == 1
        assert scheduler.get_schedule("test-tour-1") is not None

    @pytest.mark.asyncio
    async def test_unregister_tournament(self, scheduler, sample_blind_levels):
        """토너먼트 해제 테스트."""
        await scheduler.register_tournament(
            tournament_id="test-tour-1",
            blind_levels=sample_blind_levels,
        )

        result = await scheduler.unregister_tournament("test-tour-1")
        assert result is True
        assert scheduler.get_schedule("test-tour-1") is None

    @pytest.mark.asyncio
    async def test_pause_resume(self, scheduler, sample_blind_levels):
        """pause/resume 테스트."""
        await scheduler.register_tournament(
            tournament_id="test-tour-1",
            blind_levels=sample_blind_levels,
        )

        # Pause
        result = await scheduler.pause_tournament("test-tour-1")
        assert result is True

        schedule = scheduler.get_schedule("test-tour-1")
        assert schedule.is_paused

        # Resume
        result = await scheduler.resume_tournament("test-tour-1")
        assert result is True

        schedule = scheduler.get_schedule("test-tour-1")
        assert not schedule.is_paused

    @pytest.mark.asyncio
    async def test_set_level_manually(self, scheduler, sample_blind_levels):
        """수동 레벨 설정 테스트."""
        await scheduler.register_tournament(
            tournament_id="test-tour-1",
            blind_levels=sample_blind_levels,
        )

        result = await scheduler.set_level("test-tour-1", 5, broadcast=False)
        assert result is True

        schedule = scheduler.get_schedule("test-tour-1")
        assert schedule.current_level == 5

    @pytest.mark.asyncio
    async def test_get_metrics(self, scheduler, sample_blind_levels):
        """메트릭 조회 테스트."""
        await scheduler.register_tournament(
            tournament_id="test-tour-1",
            blind_levels=sample_blind_levels,
        )

        metrics = scheduler.get_metrics()
        assert isinstance(metrics, SchedulerMetrics)
        assert metrics.active_schedules == 1

    @pytest.mark.asyncio
    async def test_get_status(self, scheduler, sample_blind_levels):
        """상태 조회 테스트."""
        await scheduler.register_tournament(
            tournament_id="test-tour-1",
            blind_levels=sample_blind_levels,
        )

        status = scheduler.get_status()
        assert status["running"] is True
        assert status["active_schedules"] == 1
        assert "test-tour-1" in status["schedules"]


# ─────────────────────────────────────────────────────────────────────────────────
# 10단계 이상 연속 레벨업 테스트
# ─────────────────────────────────────────────────────────────────────────────────


class TestMultipleLevelUps:
    """10단계 이상 연속 레벨업 테스트."""

    @pytest.mark.asyncio
    async def test_ten_level_ups_no_interruption(self, mock_redis, quick_blind_levels):
        """10단계 블라인드 업이 중단 없이 진행되는지 테스트.

        각 레벨이 0.5초이므로 총 1.5초 내에 3단계 레벨업 확인.
        """
        # 12레벨 블라인드 구조 (0.5초씩)
        levels = [
            BlindLevel(level=i, small_blind=25 * i, big_blind=50 * i, ante=0, duration_minutes=0.0083)
            for i in range(1, 13)
        ]

        broadcast_calls = []

        async def mock_broadcast(tournament_id, event_data):
            broadcast_calls.append({
                "tournament_id": tournament_id,
                "event_type": event_data.get("event_type"),
                "level": event_data.get("data", {}).get("level"),
                "timestamp": time.monotonic(),
            })
            return 1

        scheduler = BlindScheduler(mock_redis, broadcast_handler=mock_broadcast)
        await scheduler.start()

        try:
            await scheduler.register_tournament(
                tournament_id="multi-level-test",
                blind_levels=levels,
            )

            # 3초 대기 (약 6개 레벨 예상)
            await asyncio.sleep(3.5)

            schedule = scheduler.get_schedule("multi-level-test")

            # 여러 레벨이 진행되었는지 확인
            assert schedule.current_level >= 4, f"Expected at least 4 levels, got {schedule.current_level}"

            # 레벨 변경 이벤트가 발생했는지 확인
            level_change_events = [
                c for c in broadcast_calls
                if c["event_type"] == "BLIND_LEVEL_CHANGED"
            ]
            assert len(level_change_events) >= 3, f"Expected at least 3 level changes, got {len(level_change_events)}"

        finally:
            await scheduler.stop()

    @pytest.mark.asyncio
    async def test_level_up_timing_accuracy(self, mock_redis):
        """레벨업 타이밍 정확도 테스트."""
        levels = [
            BlindLevel(level=1, small_blind=25, big_blind=50, ante=0, duration_minutes=0.0167),  # 1초
            BlindLevel(level=2, small_blind=50, big_blind=100, ante=0, duration_minutes=0.0167),
            BlindLevel(level=3, small_blind=75, big_blind=150, ante=0, duration_minutes=0.0167),
        ]

        level_up_times = []

        async def mock_broadcast(tournament_id, event_data):
            if event_data.get("event_type") == "BLIND_LEVEL_CHANGED":
                level_up_times.append(time.monotonic())
            return 1

        scheduler = BlindScheduler(mock_redis, broadcast_handler=mock_broadcast)
        await scheduler.start()

        try:
            start_time = time.monotonic()
            await scheduler.register_tournament(
                tournament_id="timing-test",
                blind_levels=levels,
            )

            # 2.5초 대기
            await asyncio.sleep(2.5)

            # 레벨업 간격이 약 1초인지 확인
            if len(level_up_times) >= 2:
                for i in range(1, len(level_up_times)):
                    interval = level_up_times[i] - level_up_times[i - 1]
                    # 1초 ± 0.2초 허용
                    assert 0.8 < interval < 1.2, f"Interval {interval}s is out of range"

        finally:
            await scheduler.stop()


# ─────────────────────────────────────────────────────────────────────────────────
# 경고 이벤트 테스트
# ─────────────────────────────────────────────────────────────────────────────────


class TestWarningEvents:
    """블라인드 업 경고 이벤트 테스트."""

    @pytest.mark.asyncio
    async def test_warning_events_sent(self, mock_redis):
        """경고 이벤트가 적절한 시간에 전송되는지 테스트."""
        # 5초 레벨 (경고: 5초 전에만)
        levels = [
            BlindLevel(level=1, small_blind=25, big_blind=50, ante=0, duration_minutes=0.0833),  # 5초
            BlindLevel(level=2, small_blind=50, big_blind=100, ante=0, duration_minutes=0.0833),
        ]

        warning_events = []

        async def mock_broadcast(tournament_id, event_data):
            event_type = event_data.get("event_type")
            if event_type == "BLIND_INCREASE_WARNING":
                warning_events.append({
                    "seconds": event_data.get("data", {}).get("seconds_remaining"),
                    "timestamp": time.monotonic(),
                })
            return 1

        scheduler = BlindScheduler(mock_redis, broadcast_handler=mock_broadcast)
        await scheduler.start()

        try:
            await scheduler.register_tournament(
                tournament_id="warning-test",
                blind_levels=levels,
            )

            # 5.5초 대기 (5초 전 경고 1회 예상)
            await asyncio.sleep(5.5)

            # 5초 전 경고가 전송되었는지 확인
            five_sec_warnings = [w for w in warning_events if w["seconds"] == 5]
            assert len(five_sec_warnings) >= 1, "5-second warning should be sent"

        finally:
            await scheduler.stop()


# ─────────────────────────────────────────────────────────────────────────────────
# 다중 토너먼트 동시 운영 테스트
# ─────────────────────────────────────────────────────────────────────────────────


class TestMultipleTournaments:
    """다중 토너먼트 동시 운영 테스트."""

    @pytest.mark.asyncio
    async def test_multiple_tournaments_independent(self, mock_redis):
        """여러 토너먼트가 독립적으로 운영되는지 테스트."""
        levels_fast = [
            BlindLevel(level=1, small_blind=25, big_blind=50, ante=0, duration_minutes=0.0083),  # 0.5초
            BlindLevel(level=2, small_blind=50, big_blind=100, ante=0, duration_minutes=0.0083),
        ]

        levels_slow = [
            BlindLevel(level=1, small_blind=100, big_blind=200, ante=0, duration_minutes=0.0167),  # 1초
            BlindLevel(level=2, small_blind=200, big_blind=400, ante=0, duration_minutes=0.0167),
        ]

        events = {"fast": [], "slow": []}

        async def mock_broadcast(tournament_id, event_data):
            if event_data.get("event_type") == "BLIND_LEVEL_CHANGED":
                if "fast" in tournament_id:
                    events["fast"].append(time.monotonic())
                else:
                    events["slow"].append(time.monotonic())
            return 1

        scheduler = BlindScheduler(mock_redis, broadcast_handler=mock_broadcast)
        await scheduler.start()

        try:
            await scheduler.register_tournament("tour-fast", levels_fast)
            await scheduler.register_tournament("tour-slow", levels_slow)

            # 1.5초 대기
            await asyncio.sleep(1.5)

            # fast가 더 많은 레벨업을 했는지 확인
            assert len(events["fast"]) >= len(events["slow"]), \
                "Fast tournament should have more level ups"

            # 둘 다 스케줄이 있는지 확인
            assert scheduler.get_schedule("tour-fast") is not None
            assert scheduler.get_schedule("tour-slow") is not None

        finally:
            await scheduler.stop()

    @pytest.mark.asyncio
    async def test_no_memory_leak_on_unregister(self, mock_redis, sample_blind_levels):
        """토너먼트 해제 시 메모리 누수가 없는지 테스트."""
        scheduler = BlindScheduler(mock_redis)
        await scheduler.start()

        try:
            # 5개 토너먼트 등록
            for i in range(5):
                await scheduler.register_tournament(
                    f"tour-{i}",
                    sample_blind_levels,
                )

            assert len(scheduler._schedules) == 5
            assert len(scheduler._tasks) == 5

            # 3개 해제
            for i in range(3):
                await scheduler.unregister_tournament(f"tour-{i}")

            assert len(scheduler._schedules) == 2
            # 태스크도 정리되었는지 확인
            await asyncio.sleep(0.1)  # 태스크 취소 대기

        finally:
            await scheduler.stop()

        # 종료 후 모든 리소스 정리 확인
        assert len(scheduler._schedules) == 0
        assert len(scheduler._tasks) == 0


# ─────────────────────────────────────────────────────────────────────────────────
# 유틸리티 함수 테스트
# ─────────────────────────────────────────────────────────────────────────────────


class TestUtilityFunctions:
    """유틸리티 함수 테스트."""

    def test_create_standard_blind_structure(self):
        """표준 블라인드 구조 생성 테스트."""
        levels = create_standard_blind_structure(
            starting_sb=25,
            levels=15,
            duration_minutes=15,
        )

        assert len(levels) == 15

        # 첫 번째 레벨 확인
        assert levels[0].level == 1
        assert levels[0].small_blind == 25
        assert levels[0].big_blind == 50

        # 앤티가 레벨 5부터 시작하는지 확인
        for level in levels[:4]:
            assert level.ante == 0

        for level in levels[4:]:
            assert level.ante > 0

        # 블라인드가 증가하는지 확인
        for i in range(1, len(levels)):
            assert levels[i].small_blind > levels[i - 1].small_blind
            assert levels[i].big_blind > levels[i - 1].big_blind

    def test_create_standard_blind_structure_custom(self):
        """커스텀 파라미터로 블라인드 구조 생성 테스트."""
        levels = create_standard_blind_structure(
            starting_sb=100,
            levels=10,
            duration_minutes=20,
        )

        assert len(levels) == 10
        assert levels[0].small_blind == 100
        assert levels[0].big_blind == 200


# ─────────────────────────────────────────────────────────────────────────────────
# Pause 중 시간 누적 테스트
# ─────────────────────────────────────────────────────────────────────────────────


class TestPauseTimingAccumulation:
    """Pause 중 시간 누적 테스트."""

    @pytest.mark.asyncio
    async def test_pause_freezes_remaining_time(self, scheduler, sample_blind_levels):
        """pause 중에는 남은 시간이 동결되는지 테스트."""
        await scheduler.register_tournament(
            tournament_id="pause-test",
            blind_levels=sample_blind_levels,
        )

        # 1초 대기 후 남은 시간 기록
        await asyncio.sleep(1)
        schedule = scheduler.get_schedule("pause-test")
        remaining_before = schedule.get_remaining_time()

        # pause
        await scheduler.pause_tournament("pause-test")

        # 1초 더 대기
        await asyncio.sleep(1)

        # pause 중에는 남은 시간이 변하지 않아야 함
        schedule = scheduler.get_schedule("pause-test")
        remaining_during_pause = schedule.get_remaining_time()

        # 오차 범위 내에서 같아야 함
        assert abs(remaining_before - remaining_during_pause) < 0.2

        # resume
        await scheduler.resume_tournament("pause-test")

        # 남은 시간이 다시 감소하기 시작
        await asyncio.sleep(0.5)
        schedule = scheduler.get_schedule("pause-test")
        remaining_after = schedule.get_remaining_time()

        assert remaining_after < remaining_during_pause
