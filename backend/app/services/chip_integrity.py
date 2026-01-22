"""Chip Integrity Service - 칩 무결성 검증 서비스.

P0-3: 칩 트랜잭션 원자성 및 무결성 보장.

핵심 원칙:
1. 칩 보존 법칙: 핸드 전/후 총 칩 합계 = 동일 (레이크 제외)
2. 원자적 업데이트: 칩 변경은 모두 성공하거나 모두 실패
3. 복구 가능성: 실패 시 이전 상태로 복원 가능
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ChipSnapshot:
    """핸드 시작 시점의 칩 스냅샷."""

    table_id: str
    hand_number: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # 좌석별 스택 (seat -> stack)
    stacks: dict[int, int] = field(default_factory=dict)

    # 총 칩 합계 (검증용)
    total_chips: int = 0

    # 무결성 해시
    integrity_hash: str = ""

    def compute_hash(self) -> str:
        """스냅샷 무결성 해시 계산."""
        data = f"{self.table_id}:{self.hand_number}:{self.total_chips}:"
        data += ",".join(f"{s}:{c}" for s, c in sorted(self.stacks.items()))
        return hashlib.sha256(data.encode()).hexdigest()

    def verify_hash(self) -> bool:
        """무결성 해시 검증."""
        return self.integrity_hash == self.compute_hash()


@dataclass
class ChipChangeResult:
    """칩 변경 결과."""

    success: bool
    total_before: int
    total_after: int
    rake_collected: int = 0
    discrepancy: int = 0  # 불일치 칩 (0이어야 정상)
    error: str | None = None

    @property
    def is_valid(self) -> bool:
        """칩 보존 법칙 충족 여부.

        total_before = total_after + rake_collected
        """
        return self.discrepancy == 0


class ChipIntegrityService:
    """칩 무결성 검증 서비스.

    핸드 시작/종료 시 칩 합계를 검증하여 무결성을 보장합니다.
    """

    # 최대 허용 불일치 (반올림 오차)
    MAX_ALLOWED_DISCREPANCY = 0

    def __init__(self):
        """Initialize chip integrity service."""
        # 진행 중인 핸드 스냅샷 (table_id -> snapshot)
        self._hand_snapshots: dict[str, ChipSnapshot] = {}

    def capture_hand_start(
        self,
        table_id: str,
        hand_number: int,
        player_stacks: dict[int, int],
    ) -> ChipSnapshot:
        """핸드 시작 시 스냅샷 캡처.

        Args:
            table_id: 테이블 ID
            hand_number: 핸드 번호
            player_stacks: 좌석별 스택 {seat: stack}

        Returns:
            캡처된 스냅샷
        """
        total_chips = sum(player_stacks.values())

        snapshot = ChipSnapshot(
            table_id=table_id,
            hand_number=hand_number,
            stacks=player_stacks.copy(),
            total_chips=total_chips,
        )
        snapshot.integrity_hash = snapshot.compute_hash()

        self._hand_snapshots[table_id] = snapshot

        logger.debug(
            f"[CHIP_INTEGRITY] 핸드 시작 스냅샷: table={table_id}, "
            f"hand={hand_number}, total={total_chips:,}"
        )

        return snapshot

    def validate_hand_completion(
        self,
        table_id: str,
        final_stacks: dict[int, int],
        rake_collected: int = 0,
    ) -> ChipChangeResult:
        """핸드 완료 시 칩 무결성 검증.

        칩 보존 법칙: 시작 총합 = 종료 총합 + 레이크

        Args:
            table_id: 테이블 ID
            final_stacks: 최종 좌석별 스택 {seat: stack}
            rake_collected: 수집된 레이크

        Returns:
            검증 결과
        """
        snapshot = self._hand_snapshots.get(table_id)

        if not snapshot:
            logger.warning(f"[CHIP_INTEGRITY] 스냅샷 없음: table={table_id}")
            return ChipChangeResult(
                success=False,
                total_before=0,
                total_after=sum(final_stacks.values()),
                error="핸드 시작 스냅샷이 없습니다",
            )

        # 스냅샷 무결성 검증
        if not snapshot.verify_hash():
            logger.error(f"[CHIP_INTEGRITY] 스냅샷 무결성 검증 실패: table={table_id}")
            return ChipChangeResult(
                success=False,
                total_before=snapshot.total_chips,
                total_after=sum(final_stacks.values()),
                error="스냅샷 무결성 검증 실패 - 데이터 변조 의심",
            )

        total_before = snapshot.total_chips
        total_after = sum(final_stacks.values())

        # 칩 보존 법칙 검증
        expected_after = total_before - rake_collected
        discrepancy = abs(expected_after - total_after)

        result = ChipChangeResult(
            success=discrepancy <= self.MAX_ALLOWED_DISCREPANCY,
            total_before=total_before,
            total_after=total_after,
            rake_collected=rake_collected,
            discrepancy=discrepancy,
        )

        if result.success:
            logger.info(
                f"[CHIP_INTEGRITY] 검증 성공: table={table_id}, "
                f"hand={snapshot.hand_number}, "
                f"before={total_before:,}, after={total_after:,}, rake={rake_collected:,}"
            )
        else:
            logger.error(
                f"[CHIP_INTEGRITY] 검증 실패: table={table_id}, "
                f"hand={snapshot.hand_number}, "
                f"before={total_before:,}, after={total_after:,}, rake={rake_collected:,}, "
                f"discrepancy={discrepancy:,}"
            )
            result.error = (
                f"칩 보존 법칙 위반: 불일치 {discrepancy:,} 칩 "
                f"(예상: {expected_after:,}, 실제: {total_after:,})"
            )

        # 스냅샷 정리
        del self._hand_snapshots[table_id]

        return result

    def get_snapshot(self, table_id: str) -> ChipSnapshot | None:
        """테이블의 현재 스냅샷 조회."""
        return self._hand_snapshots.get(table_id)

    def has_snapshot(self, table_id: str) -> bool:
        """테이블의 스냅샷 존재 여부."""
        return table_id in self._hand_snapshots

    def clear_snapshot(self, table_id: str) -> None:
        """테이블의 스냅샷 제거."""
        self._hand_snapshots.pop(table_id, None)

    def get_all_snapshots(self) -> dict[str, ChipSnapshot]:
        """모든 진행 중인 스냅샷 조회."""
        return self._hand_snapshots.copy()


# 싱글톤 인스턴스
_chip_integrity_service: ChipIntegrityService | None = None


def get_chip_integrity_service() -> ChipIntegrityService:
    """Get chip integrity service singleton."""
    global _chip_integrity_service
    if _chip_integrity_service is None:
        _chip_integrity_service = ChipIntegrityService()
    return _chip_integrity_service
