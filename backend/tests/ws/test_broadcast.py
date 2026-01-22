"""Tests for PersonalizedBroadcaster class."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.ws.broadcast import PersonalizedBroadcaster


class MockConnection:
    """Mock connection for testing."""

    def __init__(self, user_id: str):
        self.user_id = user_id


@pytest.fixture
def sample_hand_result():
    """Sample hand result data."""
    return {
        "winners": [{"seat": 0, "userId": "user1", "amount": 1000}],
        "pot": 1000,
        "showdown": [
            {"seat": 0, "userId": "user1", "cards": ["Ah", "Ks"], "handRank": "Two Pair"},
            {"seat": 1, "userId": "user2", "cards": ["Qh", "Jd"], "handRank": "Pair"},
            {"seat": 2, "userId": "user3", "cards": ["Th", "9d"], "handRank": "High Card"},
        ],
    }


@pytest.fixture
def player_seats():
    """Player seat mapping."""
    return {
        "user1": 0,
        "user2": 1,
        "user3": 2,
    }


@pytest.fixture
def mock_manager():
    """Create mock ConnectionManager."""
    manager = MagicMock()
    return manager


class TestFilterShowdownForViewer:
    """_filter_showdown_for_viewer 메서드 단위 테스트."""

    def test_player_sees_own_cards_and_winner_cards(
        self, mock_manager, sample_hand_result
    ):
        """플레이어가 자신의 카드와 승자 카드를 볼 수 있는지 확인.

        user2(패배자)가 조회할 때:
        - user1(승자) 카드: 보임
        - user2(본인) 카드: 보임
        - user3(다른 패배자) 카드: 마스킹
        """
        broadcaster = PersonalizedBroadcaster(mock_manager)
        original_showdown = sample_hand_result["showdown"]
        winner_seats = {0}  # user1 is winner

        # user2 (seat 1, 패배자)가 본인 시점에서 조회
        filtered = broadcaster._filter_showdown_for_viewer(
            original_showdown=original_showdown,
            viewer_seat=1,  # user2's seat
            winner_seats=winner_seats,
        )

        assert len(filtered) == 3

        # 승자(user1)의 카드는 보임
        user1_entry = next(e for e in filtered if e["seat"] == 0)
        assert user1_entry["cards"] == ["Ah", "Ks"]
        assert user1_entry["handRank"] == "Two Pair"

        # 본인(user2)의 카드도 보임
        user2_entry = next(e for e in filtered if e["seat"] == 1)
        assert user2_entry["cards"] == ["Qh", "Jd"]
        assert user2_entry["handRank"] == "Pair"

        # 다른 플레이어(user3)의 카드는 마스킹
        user3_entry = next(e for e in filtered if e["seat"] == 2)
        assert user3_entry["cards"] is None
        assert user3_entry["handRank"] == "High Card"  # handRank는 보존

    def test_spectator_sees_only_winner_cards(self, mock_manager, sample_hand_result):
        """관전자(테이블에 앉지 않은 사용자)가 승자 카드만 볼 수 있는지 확인.

        관전자의 viewer_seat는 None이므로:
        - user1(승자) 카드: 보임
        - user2, user3 카드: 마스킹
        """
        broadcaster = PersonalizedBroadcaster(mock_manager)
        original_showdown = sample_hand_result["showdown"]
        winner_seats = {0}  # user1 is winner

        # 관전자 (viewer_seat=None)
        filtered = broadcaster._filter_showdown_for_viewer(
            original_showdown=original_showdown,
            viewer_seat=None,  # spectator
            winner_seats=winner_seats,
        )

        assert len(filtered) == 3

        # 승자(user1)의 카드만 보임
        user1_entry = next(e for e in filtered if e["seat"] == 0)
        assert user1_entry["cards"] == ["Ah", "Ks"]

        # 나머지 플레이어 카드는 마스킹
        user2_entry = next(e for e in filtered if e["seat"] == 1)
        assert user2_entry["cards"] is None

        user3_entry = next(e for e in filtered if e["seat"] == 2)
        assert user3_entry["cards"] is None

    def test_non_winner_cards_are_masked(self, mock_manager, sample_hand_result):
        """승자가 아닌 다른 플레이어 카드가 None으로 마스킹되는지 확인.

        user1(승자)가 조회할 때도 다른 패배자 카드는 마스킹됨.
        """
        broadcaster = PersonalizedBroadcaster(mock_manager)
        original_showdown = sample_hand_result["showdown"]
        winner_seats = {0}  # user1 is winner

        # user1 (seat 0, 승자)가 본인 시점에서 조회
        filtered = broadcaster._filter_showdown_for_viewer(
            original_showdown=original_showdown,
            viewer_seat=0,  # user1's seat (winner)
            winner_seats=winner_seats,
        )

        assert len(filtered) == 3

        # 본인(승자)의 카드는 보임
        user1_entry = next(e for e in filtered if e["seat"] == 0)
        assert user1_entry["cards"] == ["Ah", "Ks"]

        # 다른 플레이어 카드는 마스킹
        user2_entry = next(e for e in filtered if e["seat"] == 1)
        assert user2_entry["cards"] is None

        user3_entry = next(e for e in filtered if e["seat"] == 2)
        assert user3_entry["cards"] is None

    def test_multiple_winners_all_cards_visible(self, mock_manager):
        """여러 승자가 있을 때 모든 승자 카드가 보이는지 확인 (스플릿 팟 케이스)."""
        broadcaster = PersonalizedBroadcaster(mock_manager)

        # 스플릿 팟: user1과 user2가 승자
        showdown_with_split = [
            {"seat": 0, "userId": "user1", "cards": ["Ah", "Ks"], "handRank": "Straight"},
            {"seat": 1, "userId": "user2", "cards": ["Ac", "Kd"], "handRank": "Straight"},
            {"seat": 2, "userId": "user3", "cards": ["Th", "9d"], "handRank": "Pair"},
        ]
        winner_seats = {0, 1}  # 두 명이 승자

        # user3 (seat 2, 패배자)가 조회
        filtered = broadcaster._filter_showdown_for_viewer(
            original_showdown=showdown_with_split,
            viewer_seat=2,  # user3's seat (loser)
            winner_seats=winner_seats,
        )

        assert len(filtered) == 3

        # 두 승자(user1, user2)의 카드 모두 보임
        user1_entry = next(e for e in filtered if e["seat"] == 0)
        assert user1_entry["cards"] == ["Ah", "Ks"]

        user2_entry = next(e for e in filtered if e["seat"] == 1)
        assert user2_entry["cards"] == ["Ac", "Kd"]

        # user3 본인의 카드도 보임 (본인 카드)
        user3_entry = next(e for e in filtered if e["seat"] == 2)
        assert user3_entry["cards"] == ["Th", "9d"]

    def test_multiple_winners_spectator_view(self, mock_manager):
        """스플릿 팟에서 관전자가 모든 승자 카드를 볼 수 있는지 확인."""
        broadcaster = PersonalizedBroadcaster(mock_manager)

        showdown_with_split = [
            {"seat": 0, "userId": "user1", "cards": ["Ah", "Ks"], "handRank": "Straight"},
            {"seat": 1, "userId": "user2", "cards": ["Ac", "Kd"], "handRank": "Straight"},
            {"seat": 2, "userId": "user3", "cards": ["Th", "9d"], "handRank": "Pair"},
        ]
        winner_seats = {0, 1}  # 두 명이 승자

        # 관전자 시점
        filtered = broadcaster._filter_showdown_for_viewer(
            original_showdown=showdown_with_split,
            viewer_seat=None,  # spectator
            winner_seats=winner_seats,
        )

        # 두 승자의 카드만 보임
        user1_entry = next(e for e in filtered if e["seat"] == 0)
        assert user1_entry["cards"] == ["Ah", "Ks"]

        user2_entry = next(e for e in filtered if e["seat"] == 1)
        assert user2_entry["cards"] == ["Ac", "Kd"]

        # 패배자 카드는 마스킹
        user3_entry = next(e for e in filtered if e["seat"] == 2)
        assert user3_entry["cards"] is None

    def test_empty_showdown_handled(self, mock_manager):
        """showdown 데이터가 비어있을 때 정상 처리되는지 확인."""
        broadcaster = PersonalizedBroadcaster(mock_manager)

        # 빈 showdown 데이터
        filtered = broadcaster._filter_showdown_for_viewer(
            original_showdown=[],
            viewer_seat=0,
            winner_seats={0},
        )

        assert filtered == []
        assert len(filtered) == 0

    def test_empty_winner_seats_all_masked(self, mock_manager, sample_hand_result):
        """승자가 없는 경우 (모두 폴드) 본인 카드만 보이는지 확인."""
        broadcaster = PersonalizedBroadcaster(mock_manager)
        original_showdown = sample_hand_result["showdown"]

        # 승자 없음 (특이 케이스)
        filtered = broadcaster._filter_showdown_for_viewer(
            original_showdown=original_showdown,
            viewer_seat=1,  # user2's seat
            winner_seats=set(),  # no winners
        )

        # 본인(user2)의 카드만 보임
        user2_entry = next(e for e in filtered if e["seat"] == 1)
        assert user2_entry["cards"] == ["Qh", "Jd"]

        # 나머지 모두 마스킹
        user1_entry = next(e for e in filtered if e["seat"] == 0)
        assert user1_entry["cards"] is None

        user3_entry = next(e for e in filtered if e["seat"] == 2)
        assert user3_entry["cards"] is None

    def test_original_data_not_mutated(self, mock_manager, sample_hand_result):
        """원본 showdown 데이터가 변경되지 않는지 확인."""
        broadcaster = PersonalizedBroadcaster(mock_manager)
        original_showdown = sample_hand_result["showdown"]

        # 원본 데이터 복사본 저장
        original_cards = [entry["cards"] for entry in original_showdown]

        # 필터링 실행
        broadcaster._filter_showdown_for_viewer(
            original_showdown=original_showdown,
            viewer_seat=None,  # spectator - 많은 카드가 마스킹됨
            winner_seats={0},
        )

        # 원본 데이터가 변경되지 않았는지 확인
        for i, entry in enumerate(original_showdown):
            assert entry["cards"] == original_cards[i]


class TestBroadcastHandResult:
    """broadcast_hand_result 메서드 통합 테스트."""

    @pytest.mark.asyncio
    async def test_player_sees_own_cards_and_winner_cards(
        self, sample_hand_result, player_seats
    ):
        """플레이어가 브로드캐스트에서 자신의 카드와 승자 카드를 볼 수 있는지 확인."""
        manager = MagicMock()

        # 연결 설정: user1, user2, user3
        connections = {
            "conn1": MockConnection("user1"),
            "conn2": MockConnection("user2"),
            "conn3": MockConnection("user3"),
        }

        manager.get_channel_subscribers.return_value = ["conn1", "conn2", "conn3"]
        manager.get_connection.side_effect = lambda cid: connections.get(cid)
        manager.send_to_connection = AsyncMock(return_value=True)

        broadcaster = PersonalizedBroadcaster(manager)

        sent_count = await broadcaster.broadcast_hand_result(
            room_id="table-123",
            hand_result=sample_hand_result,
            player_seats=player_seats,
        )

        assert sent_count == 3
        assert manager.send_to_connection.call_count == 3

        # 각 연결에 전송된 메시지 확인
        calls = manager.send_to_connection.call_args_list

        # user2에게 전송된 메시지 찾기
        for call in calls:
            conn_id, message = call.args
            if conn_id == "conn2":
                showdown = message["payload"]["showdown"]
                # user2는 승자(user1)와 본인 카드를 볼 수 있음
                user1_entry = next(e for e in showdown if e["seat"] == 0)
                user2_entry = next(e for e in showdown if e["seat"] == 1)
                user3_entry = next(e for e in showdown if e["seat"] == 2)

                assert user1_entry["cards"] == ["Ah", "Ks"]  # 승자 카드 보임
                assert user2_entry["cards"] == ["Qh", "Jd"]  # 본인 카드 보임
                assert user3_entry["cards"] is None  # 다른 패배자 카드 마스킹

    @pytest.mark.asyncio
    async def test_spectator_sees_only_winner_cards(
        self, sample_hand_result, player_seats
    ):
        """관전자가 브로드캐스트에서 승자 카드만 볼 수 있는지 확인."""
        manager = MagicMock()

        # 연결 설정: user1, user2, user3 (플레이어) + spectator
        connections = {
            "conn1": MockConnection("user1"),
            "conn_spectator": MockConnection("spectator1"),
        }

        manager.get_channel_subscribers.return_value = ["conn1", "conn_spectator"]
        manager.get_connection.side_effect = lambda cid: connections.get(cid)
        manager.send_to_connection = AsyncMock(return_value=True)

        broadcaster = PersonalizedBroadcaster(manager)

        sent_count = await broadcaster.broadcast_hand_result(
            room_id="table-123",
            hand_result=sample_hand_result,
            player_seats=player_seats,  # spectator1은 여기 없음
        )

        assert sent_count == 2

        # 관전자에게 전송된 메시지 찾기
        calls = manager.send_to_connection.call_args_list
        for call in calls:
            conn_id, message = call.args
            if conn_id == "conn_spectator":
                showdown = message["payload"]["showdown"]
                # 관전자는 승자 카드만 볼 수 있음
                user1_entry = next(e for e in showdown if e["seat"] == 0)
                user2_entry = next(e for e in showdown if e["seat"] == 1)
                user3_entry = next(e for e in showdown if e["seat"] == 2)

                assert user1_entry["cards"] == ["Ah", "Ks"]  # 승자 카드 보임
                assert user2_entry["cards"] is None  # 패배자 카드 마스킹
                assert user3_entry["cards"] is None  # 패배자 카드 마스킹

    @pytest.mark.asyncio
    async def test_non_winner_cards_are_masked(
        self, sample_hand_result, player_seats
    ):
        """브로드캐스트에서 승자가 아닌 다른 플레이어 카드가 마스킹되는지 확인."""
        manager = MagicMock()

        connections = {
            "conn1": MockConnection("user1"),
            "conn2": MockConnection("user2"),
        }

        manager.get_channel_subscribers.return_value = ["conn1", "conn2"]
        manager.get_connection.side_effect = lambda cid: connections.get(cid)
        manager.send_to_connection = AsyncMock(return_value=True)

        broadcaster = PersonalizedBroadcaster(manager)

        await broadcaster.broadcast_hand_result(
            room_id="table-123",
            hand_result=sample_hand_result,
            player_seats=player_seats,
        )

        # user1(승자)에게 전송된 메시지 확인
        calls = manager.send_to_connection.call_args_list
        for call in calls:
            conn_id, message = call.args
            if conn_id == "conn1":
                showdown = message["payload"]["showdown"]
                # user1은 자신의 카드를 보고, 다른 플레이어 카드는 마스킹
                user1_entry = next(e for e in showdown if e["seat"] == 0)
                user2_entry = next(e for e in showdown if e["seat"] == 1)
                user3_entry = next(e for e in showdown if e["seat"] == 2)

                assert user1_entry["cards"] == ["Ah", "Ks"]
                assert user2_entry["cards"] is None
                assert user3_entry["cards"] is None

    @pytest.mark.asyncio
    async def test_multiple_winners_all_cards_visible(self, player_seats):
        """스플릿 팟에서 모든 승자 카드가 브로드캐스트되는지 확인."""
        manager = MagicMock()

        # 스플릿 팟 핸드 결과
        split_pot_result = {
            "winners": [
                {"seat": 0, "userId": "user1", "amount": 500},
                {"seat": 1, "userId": "user2", "amount": 500},
            ],
            "pot": 1000,
            "showdown": [
                {"seat": 0, "userId": "user1", "cards": ["Ah", "Ks"], "handRank": "Straight"},
                {"seat": 1, "userId": "user2", "cards": ["Ac", "Kd"], "handRank": "Straight"},
                {"seat": 2, "userId": "user3", "cards": ["Th", "9d"], "handRank": "Pair"},
            ],
        }

        connections = {
            "conn3": MockConnection("user3"),
        }

        manager.get_channel_subscribers.return_value = ["conn3"]
        manager.get_connection.side_effect = lambda cid: connections.get(cid)
        manager.send_to_connection = AsyncMock(return_value=True)

        broadcaster = PersonalizedBroadcaster(manager)

        await broadcaster.broadcast_hand_result(
            room_id="table-123",
            hand_result=split_pot_result,
            player_seats=player_seats,
        )

        # user3에게 전송된 메시지 확인
        call = manager.send_to_connection.call_args
        _, message = call.args
        showdown = message["payload"]["showdown"]

        # 두 승자 카드 모두 보임
        user1_entry = next(e for e in showdown if e["seat"] == 0)
        user2_entry = next(e for e in showdown if e["seat"] == 1)
        user3_entry = next(e for e in showdown if e["seat"] == 2)

        assert user1_entry["cards"] == ["Ah", "Ks"]
        assert user2_entry["cards"] == ["Ac", "Kd"]
        assert user3_entry["cards"] == ["Th", "9d"]  # 본인 카드도 보임

    @pytest.mark.asyncio
    async def test_empty_showdown_handled(self, player_seats):
        """빈 showdown 데이터가 브로드캐스트에서 정상 처리되는지 확인."""
        manager = MagicMock()

        empty_result = {
            "winners": [{"seat": 0, "userId": "user1", "amount": 1000}],
            "pot": 1000,
            "showdown": [],
        }

        connections = {
            "conn1": MockConnection("user1"),
        }

        manager.get_channel_subscribers.return_value = ["conn1"]
        manager.get_connection.side_effect = lambda cid: connections.get(cid)
        manager.send_to_connection = AsyncMock(return_value=True)

        broadcaster = PersonalizedBroadcaster(manager)

        sent_count = await broadcaster.broadcast_hand_result(
            room_id="table-123",
            hand_result=empty_result,
            player_seats=player_seats,
        )

        assert sent_count == 1

        call = manager.send_to_connection.call_args
        _, message = call.args
        assert message["payload"]["showdown"] == []

    @pytest.mark.asyncio
    async def test_no_connections_returns_zero(self, sample_hand_result, player_seats):
        """연결이 없을 때 0을 반환하는지 확인."""
        manager = MagicMock()
        manager.get_channel_subscribers.return_value = []

        broadcaster = PersonalizedBroadcaster(manager)

        sent_count = await broadcaster.broadcast_hand_result(
            room_id="table-123",
            hand_result=sample_hand_result,
            player_seats=player_seats,
        )

        assert sent_count == 0
        manager.send_to_connection.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_hand_result_returns_zero(self, player_seats):
        """빈 핸드 결과일 때 0을 반환하는지 확인."""
        manager = MagicMock()

        broadcaster = PersonalizedBroadcaster(manager)

        sent_count = await broadcaster.broadcast_hand_result(
            room_id="table-123",
            hand_result={},
            player_seats=player_seats,
        )

        assert sent_count == 0

    @pytest.mark.asyncio
    async def test_none_hand_result_returns_zero(self, player_seats):
        """None 핸드 결과일 때 0을 반환하는지 확인."""
        manager = MagicMock()

        broadcaster = PersonalizedBroadcaster(manager)

        sent_count = await broadcaster.broadcast_hand_result(
            room_id="table-123",
            hand_result=None,
            player_seats=player_seats,
        )

        assert sent_count == 0

    @pytest.mark.asyncio
    async def test_partial_send_failure(self, sample_hand_result, player_seats):
        """일부 전송 실패 시 성공 카운트만 반환되는지 확인."""
        manager = MagicMock()

        connections = {
            "conn1": MockConnection("user1"),
            "conn2": MockConnection("user2"),
            "conn3": MockConnection("user3"),
        }

        manager.get_channel_subscribers.return_value = ["conn1", "conn2", "conn3"]
        manager.get_connection.side_effect = lambda cid: connections.get(cid)
        # conn2에만 전송 실패
        manager.send_to_connection = AsyncMock(
            side_effect=[True, False, True]
        )

        broadcaster = PersonalizedBroadcaster(manager)

        sent_count = await broadcaster.broadcast_hand_result(
            room_id="table-123",
            hand_result=sample_hand_result,
            player_seats=player_seats,
        )

        assert sent_count == 2  # 3개 중 2개만 성공

    @pytest.mark.asyncio
    async def test_connection_not_found_skipped(
        self, sample_hand_result, player_seats
    ):
        """연결을 찾을 수 없을 때 건너뛰는지 확인."""
        manager = MagicMock()

        connections = {
            "conn1": MockConnection("user1"),
            # conn2 없음
            "conn3": MockConnection("user3"),
        }

        manager.get_channel_subscribers.return_value = ["conn1", "conn2", "conn3"]
        manager.get_connection.side_effect = lambda cid: connections.get(cid)
        manager.send_to_connection = AsyncMock(return_value=True)

        broadcaster = PersonalizedBroadcaster(manager)

        sent_count = await broadcaster.broadcast_hand_result(
            room_id="table-123",
            hand_result=sample_hand_result,
            player_seats=player_seats,
        )

        assert sent_count == 2  # conn2는 건너뜀
        assert manager.send_to_connection.call_count == 2

    @pytest.mark.asyncio
    async def test_message_envelope_structure(
        self, sample_hand_result, player_seats
    ):
        """전송되는 메시지 구조가 올바른지 확인."""
        manager = MagicMock()

        connections = {
            "conn1": MockConnection("user1"),
        }

        manager.get_channel_subscribers.return_value = ["conn1"]
        manager.get_connection.side_effect = lambda cid: connections.get(cid)
        manager.send_to_connection = AsyncMock(return_value=True)

        broadcaster = PersonalizedBroadcaster(manager)

        await broadcaster.broadcast_hand_result(
            room_id="table-123",
            hand_result=sample_hand_result,
            player_seats=player_seats,
        )

        call = manager.send_to_connection.call_args
        _, message = call.args

        # MessageEnvelope 구조 확인
        assert message["type"] == "HAND_RESULT"
        assert "ts" in message
        assert "traceId" in message
        assert "payload" in message

        # payload 내용 확인
        payload = message["payload"]
        assert payload["tableId"] == "table-123"
        assert payload["winners"] == sample_hand_result["winners"]
        assert payload["pot"] == sample_hand_result["pot"]
        assert "showdown" in payload
