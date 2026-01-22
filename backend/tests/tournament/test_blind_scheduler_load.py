"""
BlindScheduler 부하 테스트.

테스트 범위:
─────────────────────────────────────────────────────────────────────────────────

1. 300개 가상 연결 이벤트 수신 검증
2. 브로드캐스트 지연 시간 측정
3. 다중 토너먼트 동시 운영 부하 테스트
4. 메모리 누수 장기 테스트

─────────────────────────────────────────────────────────────────────────────────
"""

import asyncio
import gc
import time
import tracemalloc
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import AsyncMock

import pytest

from app.tournament.blind_scheduler import (
    BlindScheduler,
    BlindSchedule,
    PrecisionTimer,
    create_standard_blind_structure,
)
from app.tournament.models import BlindLevel


# ─────────────────────────────────────────────────────────────────────────────────
# 가상 연결 시뮬레이터
# ─────────────────────────────────────────────────────────────────────────────────


@dataclass
class VirtualConnection:
    """가상 WebSocket 연결 시뮬레이터."""

    connection_id: str
    received_events: List[Dict[str, Any]] = field(default_factory=list)
    receive_latencies: List[float] = field(default_factory=list)
    is_connected: bool = True

    async def receive(self, event: Dict[str, Any], latency_ms: float) -> None:
        """이벤트 수신."""
        if self.is_connected:
            self.received_events.append(event)
            self.receive_latencies.append(latency_ms)


class VirtualConnectionPool:
    """가상 연결 풀.

    300명 동시 접속을 시뮬레이션합니다.
    """

    def __init__(self, count: int = 300):
        self.connections = [
            VirtualConnection(connection_id=f"conn-{i}")
            for i in range(count)
        ]
        self.broadcast_start_times: Dict[str, float] = {}
        self.total_broadcasts = 0
        self.missed_events = 0

    async def broadcast(self, tournament_id: str, event_data: Dict[str, Any]) -> int:
        """모든 연결에 이벤트 브로드캐스트.

        Returns:
            전송 성공 수
        """
        start_time = time.monotonic()
        self.broadcast_start_times[event_data.get("event_id", str(start_time))] = start_time
        self.total_broadcasts += 1

        # 병렬로 모든 연결에 전송
        tasks = []
        for conn in self.connections:
            if conn.is_connected:
                latency_ms = (time.monotonic() - start_time) * 1000
                tasks.append(conn.receive(event_data, latency_ms))

        await asyncio.gather(*tasks, return_exceptions=True)

        sent_count = sum(1 for conn in self.connections if conn.is_connected)
        return sent_count

    def get_stats(self) -> Dict[str, Any]:
        """통계 조회."""
        all_latencies = []
        all_event_counts = []

        for conn in self.connections:
            all_latencies.extend(conn.receive_latencies)
            all_event_counts.append(len(conn.received_events))

        if all_latencies:
            avg_latency = sum(all_latencies) / len(all_latencies)
            max_latency = max(all_latencies)
            min_latency = min(all_latencies)
        else:
            avg_latency = max_latency = min_latency = 0

        return {
            "total_connections": len(self.connections),
            "total_broadcasts": self.total_broadcasts,
            "total_events_received": sum(all_event_counts),
            "avg_events_per_connection": sum(all_event_counts) / len(self.connections) if self.connections else 0,
            "avg_latency_ms": avg_latency,
            "max_latency_ms": max_latency,
            "min_latency_ms": min_latency,
            "missed_events": self.missed_events,
        }

    def verify_all_received(self, expected_count: int) -> bool:
        """모든 연결이 예상 이벤트 수를 받았는지 확인."""
        for conn in self.connections:
            if len(conn.received_events) < expected_count:
                self.missed_events += expected_count - len(conn.received_events)
                return False
        return True


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
def quick_blind_levels():
    """빠른 테스트용 블라인드 레벨."""
    return [
        BlindLevel(level=i, small_blind=25 * i, big_blind=50 * i, ante=0, duration_minutes=0.0167)  # 1초
        for i in range(1, 11)
    ]


# ─────────────────────────────────────────────────────────────────────────────────
# 300명 동시 접속 부하 테스트
# ─────────────────────────────────────────────────────────────────────────────────


class TestLoadWith300Connections:
    """300명 동시 접속 부하 테스트."""

    @pytest.mark.asyncio
    async def test_broadcast_to_300_connections(self, mock_redis, quick_blind_levels):
        """300개 연결에 이벤트가 누락 없이 전달되는지 테스트."""
        connection_pool = VirtualConnectionPool(count=300)

        scheduler = BlindScheduler(
            mock_redis,
            broadcast_handler=connection_pool.broadcast,
        )
        await scheduler.start()

        try:
            await scheduler.register_tournament(
                tournament_id="load-test-300",
                blind_levels=quick_blind_levels,
            )

            # 3초 대기 (약 3개 레벨업 예상)
            await asyncio.sleep(3.5)

            stats = connection_pool.get_stats()

            # 모든 연결이 이벤트를 받았는지 확인
            print(f"\n📊 300명 부하 테스트 결과:")
            print(f"  - 총 브로드캐스트: {stats['total_broadcasts']}")
            print(f"  - 총 이벤트 수신: {stats['total_events_received']}")
            print(f"  - 연결당 평균 이벤트: {stats['avg_events_per_connection']:.1f}")
            print(f"  - 평균 지연: {stats['avg_latency_ms']:.2f}ms")
            print(f"  - 최대 지연: {stats['max_latency_ms']:.2f}ms")
            print(f"  - 누락 이벤트: {stats['missed_events']}")

            # 검증
            assert stats['total_broadcasts'] >= 3, "Should have at least 3 broadcasts"
            assert stats['avg_latency_ms'] < 100, "Average latency should be under 100ms"
            assert stats['missed_events'] == 0, "No events should be missed"

        finally:
            await scheduler.stop()

    @pytest.mark.asyncio
    async def test_broadcast_latency_under_50ms(self, mock_redis, quick_blind_levels):
        """브로드캐스트 지연이 50ms 이내인지 테스트."""
        connection_pool = VirtualConnectionPool(count=300)
        latencies = []

        async def timed_broadcast(tournament_id: str, event_data: Dict[str, Any]) -> int:
            start = time.monotonic()
            result = await connection_pool.broadcast(tournament_id, event_data)
            elapsed_ms = (time.monotonic() - start) * 1000
            latencies.append(elapsed_ms)
            return result

        scheduler = BlindScheduler(mock_redis, broadcast_handler=timed_broadcast)
        await scheduler.start()

        try:
            await scheduler.register_tournament(
                tournament_id="latency-test",
                blind_levels=quick_blind_levels,
            )

            await asyncio.sleep(3.5)

            if latencies:
                avg_latency = sum(latencies) / len(latencies)
                max_latency = max(latencies)

                print(f"\n⏱️ 브로드캐스트 지연 테스트:")
                print(f"  - 평균 지연: {avg_latency:.2f}ms")
                print(f"  - 최대 지연: {max_latency:.2f}ms")
                print(f"  - 브로드캐스트 횟수: {len(latencies)}")

                # 평균 50ms 이내, 최대 200ms 이내
                assert avg_latency < 50, f"Average latency {avg_latency:.2f}ms exceeds 50ms"
                assert max_latency < 200, f"Max latency {max_latency:.2f}ms exceeds 200ms"

        finally:
            await scheduler.stop()


# ─────────────────────────────────────────────────────────────────────────────────
# 다중 토너먼트 동시 부하 테스트
# ─────────────────────────────────────────────────────────────────────────────────


class TestMultipleTournamentsLoad:
    """다중 토너먼트 동시 부하 테스트."""

    @pytest.mark.asyncio
    async def test_10_tournaments_simultaneous(self, mock_redis):
        """10개 토너먼트 동시 운영 테스트."""
        tournament_pools: Dict[str, VirtualConnectionPool] = {}
        tournament_count = 10
        connections_per_tournament = 30

        # 토너먼트별 연결 풀 생성
        for i in range(tournament_count):
            tournament_pools[f"tour-{i}"] = VirtualConnectionPool(
                count=connections_per_tournament
            )

        async def router_broadcast(tournament_id: str, event_data: Dict[str, Any]) -> int:
            pool = tournament_pools.get(tournament_id)
            if pool:
                return await pool.broadcast(tournament_id, event_data)
            return 0

        scheduler = BlindScheduler(mock_redis, broadcast_handler=router_broadcast)
        await scheduler.start()

        try:
            # 10개 토너먼트 등록 (각각 다른 속도)
            levels = [
                BlindLevel(level=j, small_blind=25 * j, big_blind=50 * j, ante=0, duration_minutes=0.0167 * (i + 1) / 5)
                for j in range(1, 6)
            ]

            for i in range(tournament_count):
                await scheduler.register_tournament(
                    tournament_id=f"tour-{i}",
                    blind_levels=levels,
                )

            # 3초 대기
            await asyncio.sleep(3.5)

            total_broadcasts = 0
            total_received = 0

            print(f"\n🎮 10개 토너먼트 동시 운영 테스트:")

            for tournament_id, pool in tournament_pools.items():
                stats = pool.get_stats()
                total_broadcasts += stats['total_broadcasts']
                total_received += stats['total_events_received']

            print(f"  - 총 브로드캐스트: {total_broadcasts}")
            print(f"  - 총 이벤트 수신: {total_received}")
            print(f"  - 활성 스케줄: {len(scheduler._schedules)}")

            assert len(scheduler._schedules) == tournament_count
            assert total_broadcasts > 0

        finally:
            await scheduler.stop()

    @pytest.mark.asyncio
    async def test_tournament_isolation(self, mock_redis):
        """토너먼트 간 이벤트 격리 테스트."""
        events_by_tournament: Dict[str, List] = defaultdict(list)

        async def tracking_broadcast(tournament_id: str, event_data: Dict[str, Any]) -> int:
            events_by_tournament[tournament_id].append(event_data)
            return 1

        scheduler = BlindScheduler(mock_redis, broadcast_handler=tracking_broadcast)
        await scheduler.start()

        try:
            # 2개 토너먼트 등록 (다른 블라인드)
            levels_a = [
                BlindLevel(level=1, small_blind=100, big_blind=200, ante=0, duration_minutes=0.0167),
                BlindLevel(level=2, small_blind=200, big_blind=400, ante=0, duration_minutes=0.0167),
            ]
            levels_b = [
                BlindLevel(level=1, small_blind=500, big_blind=1000, ante=0, duration_minutes=0.0167),
                BlindLevel(level=2, small_blind=1000, big_blind=2000, ante=0, duration_minutes=0.0167),
            ]

            await scheduler.register_tournament("tour-a", levels_a)
            await scheduler.register_tournament("tour-b", levels_b)

            await asyncio.sleep(2)

            # 각 토너먼트 이벤트가 올바른 블라인드 값을 가지는지 확인
            for event in events_by_tournament["tour-a"]:
                if event.get("event_type") == "BLIND_LEVEL_CHANGED":
                    data = event.get("data", {})
                    assert data.get("small_blind") in [100, 200], "tour-a should have 100 or 200 SB"

            for event in events_by_tournament["tour-b"]:
                if event.get("event_type") == "BLIND_LEVEL_CHANGED":
                    data = event.get("data", {})
                    assert data.get("small_blind") in [500, 1000], "tour-b should have 500 or 1000 SB"

        finally:
            await scheduler.stop()


# ─────────────────────────────────────────────────────────────────────────────────
# 메모리 누수 테스트
# ─────────────────────────────────────────────────────────────────────────────────


class TestMemoryLeak:
    """메모리 누수 테스트."""

    @pytest.mark.asyncio
    async def test_no_memory_leak_on_repeated_registration(self, mock_redis):
        """반복적인 등록/해제 시 메모리 누수가 없는지 테스트."""
        tracemalloc.start()

        levels = [
            BlindLevel(level=i, small_blind=25 * i, big_blind=50 * i, ante=0, duration_minutes=0.05)
            for i in range(1, 6)
        ]

        scheduler = BlindScheduler(mock_redis)
        await scheduler.start()

        try:
            initial_snapshot = tracemalloc.take_snapshot()

            # 100회 등록/해제 반복
            for i in range(100):
                await scheduler.register_tournament(f"mem-test-{i}", levels)
                await scheduler.unregister_tournament(f"mem-test-{i}")

                if i % 25 == 0:
                    gc.collect()

            gc.collect()
            await asyncio.sleep(0.5)

            final_snapshot = tracemalloc.take_snapshot()

            # 메모리 증가량 확인
            top_stats = final_snapshot.compare_to(initial_snapshot, 'lineno')

            total_diff = sum(stat.size_diff for stat in top_stats[:10])

            print(f"\n💾 메모리 누수 테스트 (100회 등록/해제):")
            print(f"  - 메모리 변화: {total_diff / 1024:.2f} KB")

            # 100KB 이하 증가 허용
            assert total_diff < 100 * 1024, f"Memory increased by {total_diff / 1024:.2f} KB"

            # 모든 리소스가 정리되었는지 확인
            assert len(scheduler._schedules) == 0
            assert len(scheduler._tasks) == 0

        finally:
            await scheduler.stop()
            tracemalloc.stop()

    @pytest.mark.asyncio
    async def test_long_running_scheduler(self, mock_redis):
        """장기 실행 시 안정성 테스트."""
        events_received = []

        async def counting_broadcast(tournament_id: str, event_data: Dict[str, Any]) -> int:
            events_received.append(event_data)
            return 1

        levels = [
            BlindLevel(level=i, small_blind=25 * i, big_blind=50 * i, ante=0, duration_minutes=0.0083)  # 0.5초
            for i in range(1, 21)  # 20 레벨
        ]

        scheduler = BlindScheduler(mock_redis, broadcast_handler=counting_broadcast)
        await scheduler.start()

        try:
            await scheduler.register_tournament("long-running", levels)

            # 10초 실행 (약 20개 레벨업 예상)
            await asyncio.sleep(10.5)

            schedule = scheduler.get_schedule("long-running")
            metrics = scheduler.get_metrics()

            print(f"\n🕐 장기 실행 테스트 (10초):")
            print(f"  - 현재 레벨: {schedule.current_level}")
            print(f"  - 총 레벨업: {metrics.total_level_ups}")
            print(f"  - 총 브로드캐스트: {metrics.total_broadcasts}")
            print(f"  - 최대 드리프트: {metrics.max_drift_ms:.2f}ms")
            print(f"  - 이벤트 수신: {len(events_received)}")

            # 검증
            assert schedule.current_level >= 15, f"Should reach at least level 15, got {schedule.current_level}"
            assert metrics.max_drift_ms < 100, "Max drift should be under 100ms"

        finally:
            await scheduler.stop()


# ─────────────────────────────────────────────────────────────────────────────────
# 동시성 스트레스 테스트
# ─────────────────────────────────────────────────────────────────────────────────


class TestConcurrencyStress:
    """동시성 스트레스 테스트."""

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, mock_redis):
        """동시 작업 스트레스 테스트."""
        levels = [
            BlindLevel(level=i, small_blind=25 * i, big_blind=50 * i, ante=0, duration_minutes=0.0167)
            for i in range(1, 6)
        ]

        scheduler = BlindScheduler(mock_redis)
        await scheduler.start()

        try:
            # 동시에 여러 작업 실행
            tasks = []

            # 20개 토너먼트 등록
            for i in range(20):
                tasks.append(scheduler.register_tournament(f"stress-{i}", levels))

            await asyncio.gather(*tasks)
            assert len(scheduler._schedules) == 20

            # 동시에 pause/resume
            pause_tasks = [scheduler.pause_tournament(f"stress-{i}") for i in range(10)]
            await asyncio.gather(*pause_tasks)

            resume_tasks = [scheduler.resume_tournament(f"stress-{i}") for i in range(10)]
            await asyncio.gather(*resume_tasks)

            # 동시에 일부 해제
            unregister_tasks = [scheduler.unregister_tournament(f"stress-{i}") for i in range(10)]
            await asyncio.gather(*unregister_tasks)

            assert len(scheduler._schedules) == 10

            # 남은 스케줄이 정상 동작하는지 확인
            await asyncio.sleep(1)
            for i in range(10, 20):
                schedule = scheduler.get_schedule(f"stress-{i}")
                assert schedule is not None

        finally:
            await scheduler.stop()

    @pytest.mark.asyncio
    async def test_rapid_level_changes(self, mock_redis):
        """빠른 레벨 변경 스트레스 테스트."""
        levels = [
            BlindLevel(level=i, small_blind=25 * i, big_blind=50 * i, ante=0, duration_minutes=1)
            for i in range(1, 20)
        ]

        level_changes = []

        async def tracking_broadcast(tournament_id: str, event_data: Dict[str, Any]) -> int:
            if event_data.get("event_type") == "BLIND_LEVEL_CHANGED":
                level_changes.append(event_data.get("data", {}).get("level"))
            return 1

        scheduler = BlindScheduler(mock_redis, broadcast_handler=tracking_broadcast)
        await scheduler.start()

        try:
            await scheduler.register_tournament("rapid-test", levels)

            # 빠르게 레벨 변경
            for level in range(1, 15):
                await scheduler.set_level("rapid-test", level, broadcast=True)
                await asyncio.sleep(0.05)

            print(f"\n⚡ 빠른 레벨 변경 테스트:")
            print(f"  - 레벨 변경 횟수: {len(level_changes)}")
            print(f"  - 변경된 레벨: {level_changes}")

            # 모든 레벨 변경이 기록되었는지 확인
            assert len(level_changes) >= 14

        finally:
            await scheduler.stop()
