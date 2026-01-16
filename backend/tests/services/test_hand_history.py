"""Tests for HandHistoryService.

Property-based tests for hand history storage and retrieval.

**Property 8: 핸드 히스토리 저장**
**Validates: Requirements 5.3**
"""

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from hypothesis import given, settings, strategies as st

from app.services.hand_history import HandHistoryService


# ============================================================================
# Strategies for Property-Based Testing
# ============================================================================

user_id_strategy = st.uuids().map(str)
hand_id_strategy = st.uuids().map(str)
table_id_strategy = st.uuids().map(str)

card_strategy = st.sampled_from([
    f"{r}{s}" for r in "23456789TJQKA" for s in "hdcs"
])

hole_cards_strategy = st.lists(card_strategy, min_size=2, max_size=2)

community_cards_strategy = st.lists(card_strategy, min_size=0, max_size=5)

final_action_strategy = st.sampled_from([
    "fold", "showdown", "all_in_won", "timeout", "unknown"
])

participant_strategy = st.fixed_dictionaries({
    "user_id": user_id_strategy,
    "seat": st.integers(min_value=0, max_value=8),
    "hole_cards": st.one_of(st.none(), hole_cards_strategy),
    "bet_amount": st.integers(min_value=0, max_value=1000000),
    "won_amount": st.integers(min_value=0, max_value=1000000),
    "final_action": final_action_strategy,
})


# ============================================================================
# Mock Fixtures
# ============================================================================

def create_mock_db_session():
    """Create a mock async database session."""
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.get = AsyncMock(return_value=None)
    return mock_session


def create_mock_hand(
    hand_id: str,
    table_id: str,
    hand_number: int = 1,
    pot_size: int = 1000,
    community_cards: list[str] | None = None,
):
    """Create a mock Hand object."""
    mock_hand = MagicMock()
    mock_hand.id = hand_id
    mock_hand.table_id = table_id
    mock_hand.hand_number = hand_number
    mock_hand.started_at = datetime.utcnow() - timedelta(minutes=5)
    mock_hand.ended_at = datetime.utcnow()
    mock_hand.initial_state = {"participants": []}
    mock_hand.result = {
        "pot_total": pot_size,
        "community_cards": community_cards or ["Ah", "Kd", "Qc", "Js", "Th"],
        "winners": [],
    }
    mock_hand.participants = []
    mock_hand.events = []
    return mock_hand


def create_mock_participant(
    hand_id: str,
    user_id: str,
    seat: int = 0,
    hole_cards: list[str] | None = None,
    bet_amount: int = 100,
    won_amount: int = 0,
    final_action: str = "fold",
):
    """Create a mock HandParticipant object."""
    mock_participant = MagicMock()
    mock_participant.id = str(uuid4())
    mock_participant.hand_id = hand_id
    mock_participant.user_id = user_id
    mock_participant.seat = seat
    mock_participant.hole_cards = json.dumps(hole_cards) if hole_cards else None
    mock_participant.bet_amount = bet_amount
    mock_participant.won_amount = won_amount
    mock_participant.final_action = final_action
    mock_participant.created_at = datetime.utcnow()
    return mock_participant


# ============================================================================
# Unit Tests
# ============================================================================

class TestHandHistoryServiceInit:
    """HandHistoryService 초기화 테스트."""

    def test_init_with_db_session(self):
        """DB 세션으로 초기화."""
        mock_db = create_mock_db_session()
        service = HandHistoryService(mock_db)
        assert service._db is mock_db


class TestSaveHandResult:
    """save_hand_result 메서드 테스트."""

    @pytest.mark.asyncio
    async def test_save_hand_result_success(self):
        """핸드 결과 저장 성공."""
        mock_db = create_mock_db_session()
        service = HandHistoryService(mock_db)

        hand_result = {
            "hand_id": str(uuid4()),
            "table_id": str(uuid4()),
            "hand_number": 42,
            "pot_size": 1500,
            "community_cards": ["Ah", "Kd", "Qc", "Js", "Th"],
            "participants": [
                {
                    "user_id": str(uuid4()),
                    "seat": 0,
                    "hole_cards": ["As", "Ad"],
                    "bet_amount": 500,
                    "won_amount": 1500,
                    "final_action": "showdown",
                },
                {
                    "user_id": str(uuid4()),
                    "seat": 1,
                    "hole_cards": ["Kh", "Kc"],
                    "bet_amount": 500,
                    "won_amount": 0,
                    "final_action": "showdown",
                },
            ],
        }

        result = await service.save_hand_result(hand_result)

        assert result == hand_result["hand_id"]
        # Hand + 2 participants = 3 add calls
        assert mock_db.add.call_count == 3
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_hand_result_generates_hand_id(self):
        """hand_id가 없으면 자동 생성."""
        mock_db = create_mock_db_session()
        service = HandHistoryService(mock_db)

        hand_result = {
            "table_id": str(uuid4()),
            "hand_number": 1,
            "participants": [
                {
                    "user_id": str(uuid4()),
                    "seat": 0,
                    "bet_amount": 100,
                    "won_amount": 0,
                    "final_action": "fold",
                },
            ],
        }

        result = await service.save_hand_result(hand_result)

        assert result is not None
        assert len(result) == 36  # UUID format

    @pytest.mark.asyncio
    async def test_save_hand_result_missing_required_field(self):
        """필수 필드 누락 시 ValueError."""
        mock_db = create_mock_db_session()
        service = HandHistoryService(mock_db)

        # Missing table_id
        hand_result = {
            "hand_number": 1,
            "participants": [],
        }

        with pytest.raises(ValueError, match="Missing required field: table_id"):
            await service.save_hand_result(hand_result)

    @pytest.mark.asyncio
    async def test_save_hand_result_updates_existing_hand(self):
        """기존 핸드가 있으면 업데이트."""
        mock_db = create_mock_db_session()
        
        # Mock existing hand
        existing_hand = create_mock_hand(
            hand_id="existing-hand-id",
            table_id="table-id",
        )
        mock_db.get = AsyncMock(return_value=existing_hand)
        
        service = HandHistoryService(mock_db)

        hand_result = {
            "hand_id": "existing-hand-id",
            "table_id": "table-id",
            "hand_number": 1,
            "pot_size": 2000,
            "community_cards": ["Ah", "Kd", "Qc"],
            "participants": [
                {
                    "user_id": str(uuid4()),
                    "seat": 0,
                    "bet_amount": 1000,
                    "won_amount": 2000,
                    "final_action": "showdown",
                },
            ],
        }

        result = await service.save_hand_result(hand_result)

        assert result == "existing-hand-id"
        assert existing_hand.ended_at is not None
        assert existing_hand.result["pot_total"] == 2000

    @pytest.mark.asyncio
    async def test_save_hand_result_skips_participant_without_user_id(self):
        """user_id가 없는 참가자는 스킵."""
        mock_db = create_mock_db_session()
        service = HandHistoryService(mock_db)

        hand_result = {
            "table_id": str(uuid4()),
            "hand_number": 1,
            "participants": [
                {
                    "user_id": str(uuid4()),
                    "seat": 0,
                    "bet_amount": 100,
                    "won_amount": 0,
                    "final_action": "fold",
                },
                {
                    # No user_id - should be skipped
                    "seat": 1,
                    "bet_amount": 100,
                    "won_amount": 0,
                    "final_action": "fold",
                },
            ],
        }

        await service.save_hand_result(hand_result)

        # Hand + 1 participant (second one skipped) = 2 add calls
        assert mock_db.add.call_count == 2


class TestGetUserHandHistory:
    """get_user_hand_history 메서드 테스트."""

    @pytest.mark.asyncio
    async def test_get_user_hand_history_success(self):
        """사용자 핸드 히스토리 조회 성공."""
        mock_db = create_mock_db_session()
        
        user_id = str(uuid4())
        hand_id = str(uuid4())
        table_id = str(uuid4())
        
        # Create mock hand and participant
        mock_hand = create_mock_hand(hand_id, table_id, pot_size=1500)
        mock_participant = create_mock_participant(
            hand_id=hand_id,
            user_id=user_id,
            seat=0,
            hole_cards=["As", "Ad"],
            bet_amount=500,
            won_amount=1500,
            final_action="showdown",
        )
        mock_participant.hand = mock_hand
        
        # Mock query result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_participant]
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        service = HandHistoryService(mock_db)

        hands = await service.get_user_hand_history(user_id, limit=50)

        assert len(hands) == 1
        assert hands[0]["hand_id"] == hand_id
        assert hands[0]["table_id"] == table_id
        assert hands[0]["pot_size"] == 1500
        assert hands[0]["user_seat"] == 0
        assert hands[0]["user_hole_cards"] == ["As", "Ad"]
        assert hands[0]["user_bet_amount"] == 500
        assert hands[0]["user_won_amount"] == 1500
        assert hands[0]["user_final_action"] == "showdown"
        assert hands[0]["net_result"] == 1000  # 1500 - 500

    @pytest.mark.asyncio
    async def test_get_user_hand_history_empty(self):
        """핸드 히스토리가 없는 경우."""
        mock_db = create_mock_db_session()
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        service = HandHistoryService(mock_db)

        hands = await service.get_user_hand_history(str(uuid4()))

        assert hands == []

    @pytest.mark.asyncio
    async def test_get_user_hand_history_with_pagination(self):
        """페이지네이션 테스트."""
        mock_db = create_mock_db_session()
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        service = HandHistoryService(mock_db)

        await service.get_user_hand_history(str(uuid4()), limit=10, offset=20)

        # Verify execute was called (pagination is in the query)
        mock_db.execute.assert_called_once()


class TestGetHandDetail:
    """get_hand_detail 메서드 테스트."""

    @pytest.mark.asyncio
    async def test_get_hand_detail_success(self):
        """핸드 상세 정보 조회 성공."""
        mock_db = create_mock_db_session()
        
        hand_id = str(uuid4())
        table_id = str(uuid4())
        user_id = str(uuid4())
        
        # Create mock hand with participants and events
        mock_hand = create_mock_hand(hand_id, table_id, pot_size=1500)
        mock_participant = create_mock_participant(
            hand_id=hand_id,
            user_id=user_id,
            seat=0,
            hole_cards=["As", "Ad"],
            bet_amount=500,
            won_amount=1500,
            final_action="showdown",
        )
        mock_hand.participants = [mock_participant]
        
        # Create mock event
        mock_event = MagicMock()
        mock_event.seq_no = 1
        mock_event.event_type = "raise"
        mock_event.payload = {"amount": 100}
        mock_event.created_at = datetime.utcnow()
        mock_hand.events = [mock_event]
        
        # Mock query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_hand
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        service = HandHistoryService(mock_db)

        detail = await service.get_hand_detail(hand_id)

        assert detail is not None
        assert detail["hand_id"] == hand_id
        assert detail["table_id"] == table_id
        assert len(detail["participants"]) == 1
        assert detail["participants"][0]["user_id"] == user_id
        assert detail["participants"][0]["hole_cards"] == ["As", "Ad"]
        assert len(detail["events"]) == 1
        assert detail["events"][0]["event_type"] == "raise"

    @pytest.mark.asyncio
    async def test_get_hand_detail_not_found(self):
        """핸드를 찾을 수 없는 경우."""
        mock_db = create_mock_db_session()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        service = HandHistoryService(mock_db)

        detail = await service.get_hand_detail(str(uuid4()))

        assert detail is None


class TestGetHandsForFraudAnalysis:
    """get_hands_for_fraud_analysis 메서드 테스트."""

    @pytest.mark.asyncio
    async def test_get_hands_for_fraud_analysis_success(self):
        """부정 행위 분석용 핸드 조회 성공."""
        mock_db = create_mock_db_session()
        
        user_id_1 = str(uuid4())
        user_id_2 = str(uuid4())
        hand_id = str(uuid4())
        table_id = str(uuid4())
        
        # Create mock hand and participants
        mock_hand = create_mock_hand(hand_id, table_id, pot_size=2000)
        
        mock_participant_1 = create_mock_participant(
            hand_id=hand_id,
            user_id=user_id_1,
            seat=0,
            bet_amount=1000,
            won_amount=2000,
            final_action="showdown",
        )
        mock_participant_1.hand = mock_hand
        
        mock_participant_2 = create_mock_participant(
            hand_id=hand_id,
            user_id=user_id_2,
            seat=1,
            bet_amount=1000,
            won_amount=0,
            final_action="showdown",
        )
        mock_participant_2.hand = mock_hand
        
        # Mock query result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            mock_participant_1,
            mock_participant_2,
        ]
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        service = HandHistoryService(mock_db)

        hands = await service.get_hands_for_fraud_analysis(
            [user_id_1, user_id_2],
            hours=24,
        )

        assert len(hands) == 1
        assert hands[0]["hand_id"] == hand_id
        assert hands[0]["pot_size"] == 2000
        assert len(hands[0]["participants"]) == 2


# ============================================================================
# Property-Based Tests
# ============================================================================

class TestHandHistoryStorageProperty:
    """Property 8: 핸드 히스토리 저장.
    
    **Validates: Requirements 5.3**
    
    For any 완료된 핸드에 대해, Game_Server는 Hand 레코드와 관련 
    HandParticipant 레코드를 PostgreSQL에 저장해야 한다.
    """

    @given(
        table_id=table_id_strategy,
        hand_number=st.integers(min_value=1, max_value=10000),
        pot_size=st.integers(min_value=0, max_value=10000000),
        community_cards=community_cards_strategy,
        participants=st.lists(participant_strategy, min_size=2, max_size=9),
    )
    @settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_hand_history_storage_property(
        self,
        table_id: str,
        hand_number: int,
        pot_size: int,
        community_cards: list[str],
        participants: list[dict],
    ):
        """핸드 히스토리 저장 속성 검증.
        
        For any valid hand result:
        1. save_hand_result should return a valid hand_id
        2. Hand record should be created
        3. HandParticipant records should be created for each participant with user_id
        """
        mock_db = create_mock_db_session()
        service = HandHistoryService(mock_db)

        hand_result = {
            "table_id": table_id,
            "hand_number": hand_number,
            "pot_size": pot_size,
            "community_cards": community_cards,
            "participants": participants,
        }

        result = await service.save_hand_result(hand_result)

        # Property 1: Returns valid hand_id
        assert result is not None
        assert len(result) == 36  # UUID format

        # Property 2: Hand record created
        # Property 3: HandParticipant records created
        # Count participants with user_id
        valid_participants = [p for p in participants if p.get("user_id")]
        expected_add_calls = 1 + len(valid_participants)  # 1 Hand + N participants
        
        assert mock_db.add.call_count == expected_add_calls
        mock_db.commit.assert_called_once()

    @given(
        participants=st.lists(participant_strategy, min_size=2, max_size=9),
    )
    @settings(max_examples=30)
    @pytest.mark.asyncio
    async def test_participant_data_integrity(
        self,
        participants: list[dict],
    ):
        """참가자 데이터 무결성 검증.
        
        For any participant data:
        1. hole_cards should be stored as JSON string
        2. bet_amount and won_amount should be preserved
        3. final_action should be preserved
        """
        mock_db = create_mock_db_session()
        service = HandHistoryService(mock_db)

        hand_result = {
            "table_id": str(uuid4()),
            "hand_number": 1,
            "participants": participants,
        }

        await service.save_hand_result(hand_result)

        # Verify add was called for each valid participant
        valid_participants = [p for p in participants if p.get("user_id")]
        
        # Check that HandParticipant objects were created with correct data
        add_calls = mock_db.add.call_args_list
        
        # First call is Hand, rest are HandParticipants
        participant_calls = add_calls[1:]
        
        for i, call in enumerate(participant_calls):
            if i < len(valid_participants):
                added_obj = call[0][0]
                original = valid_participants[i]
                
                # Verify data integrity
                assert added_obj.user_id == original["user_id"]
                assert added_obj.seat == original["seat"]
                assert added_obj.bet_amount == original["bet_amount"]
                assert added_obj.won_amount == original["won_amount"]
                assert added_obj.final_action == original["final_action"]
                
                # Verify hole_cards JSON encoding
                if original.get("hole_cards"):
                    assert added_obj.hole_cards == json.dumps(original["hole_cards"])
                else:
                    assert added_obj.hole_cards is None

    @given(
        user_id=user_id_strategy,
        num_hands=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=20)
    @pytest.mark.asyncio
    async def test_user_history_retrieval_property(
        self,
        user_id: str,
        num_hands: int,
    ):
        """사용자 히스토리 조회 속성 검증.
        
        For any user with N hands:
        1. get_user_hand_history should return at most N hands
        2. Each hand should contain required fields
        3. net_result should equal won_amount - bet_amount
        """
        mock_db = create_mock_db_session()
        
        # Create mock participants for multiple hands
        mock_participants = []
        for i in range(num_hands):
            hand_id = str(uuid4())
            table_id = str(uuid4())
            bet_amount = (i + 1) * 100
            won_amount = (i + 1) * 150 if i % 2 == 0 else 0
            
            mock_hand = create_mock_hand(hand_id, table_id, pot_size=bet_amount * 2)
            mock_participant = create_mock_participant(
                hand_id=hand_id,
                user_id=user_id,
                seat=0,
                bet_amount=bet_amount,
                won_amount=won_amount,
                final_action="showdown" if won_amount > 0 else "fold",
            )
            mock_participant.hand = mock_hand
            mock_participants.append(mock_participant)
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_participants
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        service = HandHistoryService(mock_db)

        hands = await service.get_user_hand_history(user_id, limit=50)

        # Property 1: Returns at most N hands
        assert len(hands) <= num_hands

        # Property 2 & 3: Each hand has required fields and correct net_result
        for hand in hands:
            assert "hand_id" in hand
            assert "table_id" in hand
            assert "user_bet_amount" in hand
            assert "user_won_amount" in hand
            assert "net_result" in hand
            
            # Verify net_result calculation
            assert hand["net_result"] == hand["user_won_amount"] - hand["user_bet_amount"]
