"""Personalized broadcast utilities for WebSocket messages."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.ws.events import EventType
from app.ws.messages import MessageEnvelope
from app.logging_config import get_logger

if TYPE_CHECKING:
    from app.ws.manager import ConnectionManager

logger = get_logger(__name__)


class PersonalizedBroadcaster:
    """Broadcasts personalized messages to players.

    Used for HAND_RESULT events to filter showdown data:
    - Each player sees their own cards + winner cards
    - Spectators see only winner cards
    - Other players' cards are masked (None)
    """

    def __init__(self, manager: ConnectionManager):
        self.manager = manager

    async def broadcast_hand_result(
        self,
        room_id: str,
        hand_result: dict[str, Any],
        player_seats: dict[str, int],  # user_id -> seat 매핑
    ) -> int:
        """Broadcast hand result with personalized showdown data.

        Args:
            room_id: Room ID
            hand_result: Hand result containing winners, pot, showdown
            player_seats: Mapping of user_id to seat number

        Returns:
            Number of messages sent
        """
        if not hand_result:
            return 0

        # 승자 좌석 번호 추출
        winners = hand_result.get("winners", [])
        winner_seats: set[int] = {w.get("seat") for w in winners if w.get("seat") is not None}

        # 원본 showdown 데이터
        original_showdown = hand_result.get("showdown", [])

        # 채널 멤버 목록 가져오기
        channel = f"table:{room_id}"
        connection_ids = self.manager.get_channel_subscribers(channel)

        if not connection_ids:
            logger.debug(
                "no_connections_for_hand_result",
                room_id=room_id,
            )
            return 0

        sent_count = 0

        for connection_id in connection_ids:
            conn = self.manager.get_connection(connection_id)
            if not conn:
                continue

            user_id = conn.user_id

            # 이 사용자의 좌석 찾기 (플레이어인 경우)
            viewer_seat = player_seats.get(user_id)

            # 필터링된 showdown 데이터 생성
            filtered_showdown = self._filter_showdown_for_viewer(
                original_showdown=original_showdown,
                viewer_seat=viewer_seat,
                winner_seats=winner_seats,
            )

            # 개인화된 메시지 생성
            personalized_payload = {
                "tableId": room_id,
                "winners": winners,
                "pot": hand_result.get("pot", 0),
                "showdown": filtered_showdown,
            }

            message = MessageEnvelope.create(
                event_type=EventType.HAND_RESULT,
                payload=personalized_payload,
            )

            # 개별 연결에 전송
            success = await self.manager.send_to_connection(
                connection_id,
                message.to_dict(),
            )

            if success:
                sent_count += 1

        logger.info(
            "personalized_hand_result_broadcast",
            room_id=room_id,
            total_connections=len(connection_ids),
            sent_count=sent_count,
            winner_seats=list(winner_seats),
        )

        return sent_count

    def _filter_showdown_for_viewer(
        self,
        original_showdown: list[dict[str, Any]],
        viewer_seat: int | None,
        winner_seats: set[int],
    ) -> list[dict[str, Any]]:
        """Filter showdown data for a specific viewer.

        Args:
            original_showdown: Original showdown data with all cards
            viewer_seat: Viewer's seat number (None if spectator)
            winner_seats: Set of winner seat numbers

        Returns:
            Filtered showdown data
        """
        filtered = []

        for entry in original_showdown:
            seat = entry.get("seat")

            # 승자의 카드: 모든 사람에게 공개
            if seat in winner_seats:
                filtered.append(entry.copy())
                continue

            # 본인의 카드: 본인에게만 공개
            if viewer_seat is not None and seat == viewer_seat:
                filtered.append(entry.copy())
                continue

            # 그 외: 카드 마스킹
            masked_entry = entry.copy()
            masked_entry["cards"] = None
            filtered.append(masked_entry)

        return filtered
