"""Table Persistence Service - 캐시 게임 테이블 Redis 영속성.

P0-4: 캐시 게임 테이블 상태를 Redis에 저장하여 서버 재시작 시 복구 가능.

CLAUDE.md 아키텍처 방향성:
- GameManager → Redis (주 저장소) → DB (영구 백업)
- 상태 변경 시 Redis에 저장 (플레이어 착석, 스택 변경, 핸드 진행)
- 서버 재시작 시 Redis에서 복구
"""

import gzip
import hashlib
import hmac
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PlayerSnapshot:
    """플레이어 스냅샷."""

    user_id: str
    username: str
    seat: int
    stack: int
    status: str = "active"
    is_bot: bool = False


@dataclass
class TableSnapshot:
    """테이블 스냅샷."""

    room_id: str
    name: str
    small_blind: int
    big_blind: int
    min_buy_in: int
    max_buy_in: int
    max_players: int

    # 게임 상태
    dealer_seat: int = -1
    hand_number: int = 0
    phase: str = "waiting"

    # 플레이어
    players: dict[int, PlayerSnapshot] = field(default_factory=dict)

    # 메타데이터
    created_at: str = ""
    updated_at: str = ""
    snapshot_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리로 변환."""
        return {
            "room_id": self.room_id,
            "name": self.name,
            "small_blind": self.small_blind,
            "big_blind": self.big_blind,
            "min_buy_in": self.min_buy_in,
            "max_buy_in": self.max_buy_in,
            "max_players": self.max_players,
            "dealer_seat": self.dealer_seat,
            "hand_number": self.hand_number,
            "phase": self.phase,
            "players": {
                str(seat): asdict(p) for seat, p in self.players.items()
            },
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "snapshot_version": self.snapshot_version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TableSnapshot":
        """딕셔너리에서 생성."""
        players = {}
        for seat_str, p_data in data.get("players", {}).items():
            seat = int(seat_str)
            players[seat] = PlayerSnapshot(**p_data)

        return cls(
            room_id=data["room_id"],
            name=data["name"],
            small_blind=data["small_blind"],
            big_blind=data["big_blind"],
            min_buy_in=data["min_buy_in"],
            max_buy_in=data["max_buy_in"],
            max_players=data["max_players"],
            dealer_seat=data.get("dealer_seat", -1),
            hand_number=data.get("hand_number", 0),
            phase=data.get("phase", "waiting"),
            players=players,
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            snapshot_version=data.get("snapshot_version", 1),
        )


class TablePersistenceService:
    """캐시 게임 테이블 영속성 서비스.

    테이블 상태를 Redis에 저장하고 복구합니다.

    키 패턴:
    - game:table:{room_id} - 테이블 상태 (JSON)
    - game:table:list - 활성 테이블 ID 목록 (SET)
    """

    KEY_PREFIX = "game:table"
    TABLE_LIST_KEY = "game:table:list"

    def __init__(self, redis_client, hmac_key: str = "table-persistence-key"):
        """Initialize table persistence service.

        Args:
            redis_client: Redis 클라이언트
            hmac_key: HMAC 서명 키
        """
        self.redis = redis_client
        self._hmac_key = hmac_key.encode()

    def _table_key(self, room_id: str) -> str:
        """테이블 키 생성."""
        return f"{self.KEY_PREFIX}:{room_id}"

    def _compute_checksum(self, data: bytes) -> str:
        """데이터 체크섬 계산."""
        return hmac.new(self._hmac_key, data, hashlib.sha256).hexdigest()

    def _verify_checksum(self, data: bytes, checksum: str) -> bool:
        """체크섬 검증."""
        computed = self._compute_checksum(data)
        return hmac.compare_digest(computed, checksum)

    async def save_table(self, table) -> bool:
        """테이블 상태 저장.

        Args:
            table: PokerTable 인스턴스

        Returns:
            저장 성공 여부
        """
        try:
            from app.game.poker_table import PokerTable

            # 스냅샷 생성
            players = {}
            for seat, player in table.players.items():
                if player:
                    players[seat] = PlayerSnapshot(
                        user_id=player.user_id,
                        username=player.username,
                        seat=player.seat,
                        stack=player.stack,
                        status=player.status,
                        is_bot=player.is_bot,
                    )

            snapshot = TableSnapshot(
                room_id=table.room_id,
                name=table.name,
                small_blind=table.small_blind,
                big_blind=table.big_blind,
                min_buy_in=table.min_buy_in,
                max_buy_in=table.max_buy_in,
                max_players=table.max_players,
                dealer_seat=table.dealer_seat,
                hand_number=table.hand_number,
                phase=table.phase.value,
                players=players,
                updated_at=datetime.now(timezone.utc).isoformat(),
            )

            # JSON 직렬화 + 압축
            data = json.dumps(snapshot.to_dict(), ensure_ascii=False).encode()
            compressed = gzip.compress(data)
            checksum = self._compute_checksum(compressed)

            # Redis에 저장
            await self.redis.set(
                self._table_key(table.room_id),
                compressed,
            )
            await self.redis.hset(
                f"{self._table_key(table.room_id)}:meta",
                mapping={
                    "checksum": checksum,
                    "updated_at": snapshot.updated_at,
                },
            )

            # 테이블 목록에 추가
            await self.redis.sadd(self.TABLE_LIST_KEY, table.room_id)

            logger.debug(f"[PERSISTENCE] 테이블 저장: {table.room_id}")
            return True

        except Exception as e:
            logger.error(f"[PERSISTENCE] 테이블 저장 실패: {table.room_id}, {e}")
            return False

    async def load_table(self, room_id: str) -> TableSnapshot | None:
        """테이블 상태 로드.

        Args:
            room_id: 테이블 ID

        Returns:
            테이블 스냅샷 또는 None
        """
        try:
            compressed = await self.redis.get(self._table_key(room_id))
            if not compressed:
                return None

            # 메타데이터에서 체크섬 확인
            meta = await self.redis.hgetall(f"{self._table_key(room_id)}:meta")
            if meta:
                stored_checksum = meta.get(b"checksum", b"").decode()
                if stored_checksum and not self._verify_checksum(compressed, stored_checksum):
                    logger.error(f"[PERSISTENCE] 체크섬 검증 실패: {room_id}")
                    return None

            # 압축 해제 + JSON 파싱
            data = gzip.decompress(compressed)
            snapshot_dict = json.loads(data.decode())

            return TableSnapshot.from_dict(snapshot_dict)

        except Exception as e:
            logger.error(f"[PERSISTENCE] 테이블 로드 실패: {room_id}, {e}")
            return None

    async def delete_table(self, room_id: str) -> bool:
        """테이블 상태 삭제.

        Args:
            room_id: 테이블 ID

        Returns:
            삭제 성공 여부
        """
        try:
            await self.redis.delete(self._table_key(room_id))
            await self.redis.delete(f"{self._table_key(room_id)}:meta")
            await self.redis.srem(self.TABLE_LIST_KEY, room_id)

            logger.debug(f"[PERSISTENCE] 테이블 삭제: {room_id}")
            return True

        except Exception as e:
            logger.error(f"[PERSISTENCE] 테이블 삭제 실패: {room_id}, {e}")
            return False

    async def list_tables(self) -> list[str]:
        """저장된 테이블 ID 목록 조회.

        Returns:
            테이블 ID 목록
        """
        try:
            members = await self.redis.smembers(self.TABLE_LIST_KEY)
            return [m.decode() if isinstance(m, bytes) else m for m in members]
        except Exception as e:
            logger.error(f"[PERSISTENCE] 테이블 목록 조회 실패: {e}")
            return []

    async def restore_to_manager(self, game_manager) -> int:
        """저장된 모든 테이블을 GameManager에 복원.

        Args:
            game_manager: GameManager 인스턴스

        Returns:
            복원된 테이블 수
        """
        from app.game.poker_table import PokerTable, Player, GamePhase

        restored = 0
        table_ids = await self.list_tables()

        for room_id in table_ids:
            try:
                snapshot = await self.load_table(room_id)
                if not snapshot:
                    continue

                # 핸드 진행 중인 테이블은 복구하지 않음 (상태 불일치 위험)
                if snapshot.phase != "waiting":
                    logger.warning(
                        f"[PERSISTENCE] 핸드 진행 중인 테이블 복구 스킵: "
                        f"{room_id} (phase={snapshot.phase})"
                    )
                    # 플레이어만 있는 경우 스택만 복구
                    continue

                # 테이블 생성
                table = game_manager.create_table_sync(
                    room_id=snapshot.room_id,
                    name=snapshot.name,
                    small_blind=snapshot.small_blind,
                    big_blind=snapshot.big_blind,
                    min_buy_in=snapshot.min_buy_in,
                    max_buy_in=snapshot.max_buy_in,
                    max_players=snapshot.max_players,
                )

                # 딜러 좌석 복원
                table.dealer_seat = snapshot.dealer_seat
                table.hand_number = snapshot.hand_number

                # 플레이어 복원
                for seat, p_snapshot in snapshot.players.items():
                    player = Player(
                        user_id=p_snapshot.user_id,
                        username=p_snapshot.username,
                        seat=p_snapshot.seat,
                        stack=p_snapshot.stack,
                        is_bot=p_snapshot.is_bot,
                    )
                    player.status = p_snapshot.status
                    table.players[seat] = player

                restored += 1
                logger.info(
                    f"[PERSISTENCE] 테이블 복원: {room_id}, "
                    f"플레이어 {len(snapshot.players)}명"
                )

            except Exception as e:
                logger.error(f"[PERSISTENCE] 테이블 복원 실패: {room_id}, {e}")
                continue

        return restored


# 싱글톤 인스턴스
_persistence_service: TablePersistenceService | None = None


async def get_table_persistence_service():
    """Get table persistence service singleton."""
    global _persistence_service
    if _persistence_service is None:
        from app.utils.redis_client import get_redis
        redis = get_redis()
        if redis:
            _persistence_service = TablePersistenceService(redis)
    return _persistence_service


async def init_table_persistence(redis_client) -> TablePersistenceService:
    """Initialize table persistence service.

    Args:
        redis_client: Redis 클라이언트

    Returns:
        초기화된 서비스 인스턴스
    """
    global _persistence_service
    _persistence_service = TablePersistenceService(redis_client)
    return _persistence_service
