"""Tests for FraudEventPublisher service.

Property-based tests for event schema validation and publishing.
"""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from hypothesis import given, settings, strategies as st

from app.services.fraud_event_publisher import (
    CHANNEL_HAND_COMPLETED,
    CHANNEL_PLAYER_ACTION,
    CHANNEL_PLAYER_STATS,
    FraudEventPublisher,
    HandCompletedEvent,
    HandParticipant,
    PlayerActionEvent,
    PlayerStatsEvent,
    get_fraud_publisher,
    init_fraud_publisher,
)


# ============================================================================
# Strategies for Property-Based Testing
# ============================================================================

user_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-"),
    min_size=1,
    max_size=36,
)

room_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-"),
    min_size=1,
    max_size=36,
)

hand_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-"),
    min_size=1,
    max_size=36,
)

card_strategy = st.sampled_from([
    f"{r}{s}" for r in "23456789TJQKA" for s in "hdcs"
])

hole_cards_strategy = st.lists(card_strategy, min_size=2, max_size=2)

community_cards_strategy = st.lists(card_strategy, min_size=0, max_size=5)

action_type_strategy = st.sampled_from(["fold", "check", "call", "raise", "bet", "all_in"])

final_action_strategy = st.sampled_from(["fold", "showdown", "all_in_won", "timeout", "unknown"])

participant_strategy = st.fixed_dictionaries({
    "user_id": user_id_strategy,
    "seat": st.integers(min_value=0, max_value=8),
    "hole_cards": st.one_of(st.none(), hole_cards_strategy),
    "bet_amount": st.integers(min_value=0, max_value=1000000),
    "won_amount": st.integers(min_value=0, max_value=1000000),
    "final_action": final_action_strategy,
})


# ============================================================================
# Unit Tests
# ============================================================================

class TestFraudEventPublisherInit:
    """FraudEventPublisher 초기화 테스트."""

    def test_init_with_redis(self):
        """Redis 클라이언트가 있으면 활성화."""
        mock_redis = MagicMock()
        publisher = FraudEventPublisher(mock_redis)
        assert publisher.enabled is True

    def test_init_without_redis(self):
        """Redis 클라이언트가 없으면 비활성화."""
        publisher = FraudEventPublisher(None)
        assert publisher.enabled is False

    def test_global_instance(self):
        """글로벌 인스턴스 초기화 테스트."""
        mock_redis = MagicMock()
        publisher = init_fraud_publisher(mock_redis)
        assert get_fraud_publisher() is publisher
        assert publisher.enabled is True


class TestHandCompletedEvent:
    """핸드 완료 이벤트 테스트."""

    @pytest.mark.asyncio
    async def test_publish_hand_completed_success(self):
        """핸드 완료 이벤트 발행 성공."""
        mock_redis = AsyncMock()
        publisher = FraudEventPublisher(mock_redis)

        result = await publisher.publish_hand_completed(
            hand_id="hand-123",
            room_id="room-456",
            hand_number=42,
            pot_size=1500,
            community_cards=["Ah", "Kd", "Qc", "Js", "Th"],
            participants=[
                {
                    "user_id": "user-1",
                    "seat": 0,
                    "hole_cards": ["As", "Ad"],
                    "bet_amount": 500,
                    "won_amount": 1500,
                    "final_action": "showdown",
                }
            ],
        )

        assert result is True
        mock_redis.publish.assert_called_once()
        
        # 발행된 메시지 검증
        call_args = mock_redis.publish.call_args
        assert call_args[0][0] == CHANNEL_HAND_COMPLETED
        
        event_data = json.loads(call_args[0][1])
        assert event_data["event_type"] == "hand_completed"
        assert event_data["hand_id"] == "hand-123"
        assert event_data["room_id"] == "room-456"
        assert event_data["hand_number"] == 42
        assert event_data["pot_size"] == 1500
        assert event_data["community_cards"] == ["Ah", "Kd", "Qc", "Js", "Th"]
        assert len(event_data["participants"]) == 1
        assert "timestamp" in event_data

    @pytest.mark.asyncio
    async def test_publish_hand_completed_disabled(self):
        """비활성화 상태에서 발행 시도."""
        publisher = FraudEventPublisher(None)

        result = await publisher.publish_hand_completed(
            hand_id="hand-123",
            room_id="room-456",
            hand_number=42,
            pot_size=1500,
            community_cards=[],
            participants=[],
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_publish_hand_completed_redis_error(self):
        """Redis 에러 시 False 반환."""
        mock_redis = AsyncMock()
        mock_redis.publish.side_effect = Exception("Redis connection error")
        publisher = FraudEventPublisher(mock_redis)

        result = await publisher.publish_hand_completed(
            hand_id="hand-123",
            room_id="room-456",
            hand_number=42,
            pot_size=1500,
            community_cards=[],
            participants=[],
        )

        assert result is False


class TestPlayerActionEvent:
    """플레이어 액션 이벤트 테스트."""

    @pytest.mark.asyncio
    async def test_publish_player_action_success(self):
        """플레이어 액션 이벤트 발행 성공."""
        mock_redis = AsyncMock()
        publisher = FraudEventPublisher(mock_redis)

        result = await publisher.publish_player_action(
            user_id="user-123",
            room_id="room-456",
            hand_id="hand-789",
            action_type="raise",
            amount=100,
            response_time_ms=2500,
            turn_start_time="2026-01-16T12:00:00Z",
        )

        assert result is True
        mock_redis.publish.assert_called_once()
        
        call_args = mock_redis.publish.call_args
        assert call_args[0][0] == CHANNEL_PLAYER_ACTION
        
        event_data = json.loads(call_args[0][1])
        assert event_data["event_type"] == "player_action"
        assert event_data["user_id"] == "user-123"
        assert event_data["room_id"] == "room-456"
        assert event_data["hand_id"] == "hand-789"
        assert event_data["action_type"] == "raise"
        assert event_data["amount"] == 100
        assert event_data["response_time_ms"] == 2500
        assert event_data["turn_start_time"] == "2026-01-16T12:00:00Z"
        assert "timestamp" in event_data

    @pytest.mark.asyncio
    async def test_publish_player_action_disabled(self):
        """비활성화 상태에서 발행 시도."""
        publisher = FraudEventPublisher(None)

        result = await publisher.publish_player_action(
            user_id="user-123",
            room_id="room-456",
            hand_id="hand-789",
            action_type="fold",
            amount=0,
            response_time_ms=1000,
            turn_start_time="2026-01-16T12:00:00Z",
        )

        assert result is False


class TestPlayerStatsEvent:
    """플레이어 세션 통계 이벤트 테스트."""

    @pytest.mark.asyncio
    async def test_publish_player_stats_success(self):
        """플레이어 통계 이벤트 발행 성공."""
        mock_redis = AsyncMock()
        publisher = FraudEventPublisher(mock_redis)

        result = await publisher.publish_player_stats(
            user_id="user-123",
            room_id="room-456",
            session_duration_seconds=3600,
            hands_played=45,
            total_bet=15000,
            total_won=18000,
            join_time="2026-01-16T11:00:00Z",
            leave_time="2026-01-16T12:00:00Z",
        )

        assert result is True
        mock_redis.publish.assert_called_once()
        
        call_args = mock_redis.publish.call_args
        assert call_args[0][0] == CHANNEL_PLAYER_STATS
        
        event_data = json.loads(call_args[0][1])
        assert event_data["event_type"] == "player_stats"
        assert event_data["user_id"] == "user-123"
        assert event_data["room_id"] == "room-456"
        assert event_data["session_duration_seconds"] == 3600
        assert event_data["hands_played"] == 45
        assert event_data["total_bet"] == 15000
        assert event_data["total_won"] == 18000
        assert event_data["join_time"] == "2026-01-16T11:00:00Z"
        assert event_data["leave_time"] == "2026-01-16T12:00:00Z"
        assert "timestamp" in event_data

    @pytest.mark.asyncio
    async def test_publish_player_stats_disabled(self):
        """비활성화 상태에서 발행 시도."""
        publisher = FraudEventPublisher(None)

        result = await publisher.publish_player_stats(
            user_id="user-123",
            room_id="room-456",
            session_duration_seconds=3600,
            hands_played=45,
            total_bet=15000,
            total_won=18000,
            join_time="2026-01-16T11:00:00Z",
            leave_time="2026-01-16T12:00:00Z",
        )

        assert result is False


# ============================================================================
# Property-Based Tests
# ============================================================================

class TestHandCompletedEventSchema:
    """Property 1: 핸드 완료 이벤트 발행 및 스키마 검증.
    
    **Validates: Requirements 1.1, 1.2**
    
    For any 완료된 핸드에 대해, Game_Server가 `fraud:hand_completed` 채널로 
    이벤트를 발행하면, 해당 이벤트는 hand_id, room_id, participants, pot_size, 
    community_cards, timestamp 필드를 모두 포함해야 한다.
    """

    @given(
        hand_id=hand_id_strategy,
        room_id=room_id_strategy,
        hand_number=st.integers(min_value=1, max_value=10000),
        pot_size=st.integers(min_value=0, max_value=10000000),
        community_cards=community_cards_strategy,
        participants=st.lists(participant_strategy, min_size=2, max_size=9),
    )
    @settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_hand_completed_event_schema(
        self,
        hand_id: str,
        room_id: str,
        hand_number: int,
        pot_size: int,
        community_cards: list[str],
        participants: list[dict],
    ):
        """핸드 완료 이벤트 스키마 검증."""
        mock_redis = AsyncMock()
        publisher = FraudEventPublisher(mock_redis)

        result = await publisher.publish_hand_completed(
            hand_id=hand_id,
            room_id=room_id,
            hand_number=hand_number,
            pot_size=pot_size,
            community_cards=community_cards,
            participants=participants,
        )

        assert result is True
        
        # 발행된 이벤트 검증
        call_args = mock_redis.publish.call_args
        event_data = json.loads(call_args[0][1])
        
        # 필수 필드 존재 확인
        assert "event_type" in event_data
        assert "timestamp" in event_data
        assert "hand_id" in event_data
        assert "room_id" in event_data
        assert "hand_number" in event_data
        assert "pot_size" in event_data
        assert "community_cards" in event_data
        assert "participants" in event_data
        
        # 값 검증
        assert event_data["event_type"] == "hand_completed"
        assert event_data["hand_id"] == hand_id
        assert event_data["room_id"] == room_id
        assert event_data["hand_number"] == hand_number
        assert event_data["pot_size"] == pot_size
        assert event_data["community_cards"] == community_cards
        assert len(event_data["participants"]) == len(participants)


class TestPlayerActionEventSchema:
    """Property 2: 플레이어 액션 이벤트 발행 및 스키마 검증.
    
    **Validates: Requirements 2.1, 2.2**
    
    For any 인간 플레이어의 액션에 대해, Game_Server가 `fraud:player_action` 채널로 
    이벤트를 발행하면, 해당 이벤트는 user_id, room_id, action_type, amount, 
    response_time_ms, timestamp 필드를 모두 포함해야 한다.
    """

    @given(
        user_id=user_id_strategy,
        room_id=room_id_strategy,
        hand_id=hand_id_strategy,
        action_type=action_type_strategy,
        amount=st.integers(min_value=0, max_value=10000000),
        response_time_ms=st.integers(min_value=0, max_value=300000),
    )
    @settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_player_action_event_schema(
        self,
        user_id: str,
        room_id: str,
        hand_id: str,
        action_type: str,
        amount: int,
        response_time_ms: int,
    ):
        """플레이어 액션 이벤트 스키마 검증."""
        mock_redis = AsyncMock()
        publisher = FraudEventPublisher(mock_redis)

        turn_start_time = datetime.now(timezone.utc).isoformat()

        result = await publisher.publish_player_action(
            user_id=user_id,
            room_id=room_id,
            hand_id=hand_id,
            action_type=action_type,
            amount=amount,
            response_time_ms=response_time_ms,
            turn_start_time=turn_start_time,
        )

        assert result is True
        
        # 발행된 이벤트 검증
        call_args = mock_redis.publish.call_args
        event_data = json.loads(call_args[0][1])
        
        # 필수 필드 존재 확인
        assert "event_type" in event_data
        assert "timestamp" in event_data
        assert "user_id" in event_data
        assert "room_id" in event_data
        assert "hand_id" in event_data
        assert "action_type" in event_data
        assert "amount" in event_data
        assert "response_time_ms" in event_data
        assert "turn_start_time" in event_data
        
        # 값 검증
        assert event_data["event_type"] == "player_action"
        assert event_data["user_id"] == user_id
        assert event_data["room_id"] == room_id
        assert event_data["hand_id"] == hand_id
        assert event_data["action_type"] == action_type
        assert event_data["amount"] == amount
        assert event_data["response_time_ms"] == response_time_ms


class TestPlayerStatsEventSchema:
    """Property 4: 플레이어 통계 이벤트 발행 및 스키마 검증.
    
    **Validates: Requirements 3.1, 3.2**
    
    For any 테이블을 떠나는 플레이어에 대해, Game_Server가 `fraud:player_stats` 채널로 
    이벤트를 발행하면, 해당 이벤트는 user_id, room_id, session_duration_seconds, 
    hands_played, total_bet, total_won, join_time, leave_time 필드를 모두 포함해야 한다.
    """

    @given(
        user_id=user_id_strategy,
        room_id=room_id_strategy,
        session_duration_seconds=st.integers(min_value=0, max_value=86400),
        hands_played=st.integers(min_value=0, max_value=1000),
        total_bet=st.integers(min_value=0, max_value=100000000),
        total_won=st.integers(min_value=0, max_value=100000000),
    )
    @settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_player_stats_event_schema(
        self,
        user_id: str,
        room_id: str,
        session_duration_seconds: int,
        hands_played: int,
        total_bet: int,
        total_won: int,
    ):
        """플레이어 통계 이벤트 스키마 검증."""
        mock_redis = AsyncMock()
        publisher = FraudEventPublisher(mock_redis)

        join_time = "2026-01-16T11:00:00Z"
        leave_time = "2026-01-16T12:00:00Z"

        result = await publisher.publish_player_stats(
            user_id=user_id,
            room_id=room_id,
            session_duration_seconds=session_duration_seconds,
            hands_played=hands_played,
            total_bet=total_bet,
            total_won=total_won,
            join_time=join_time,
            leave_time=leave_time,
        )

        assert result is True
        
        # 발행된 이벤트 검증
        call_args = mock_redis.publish.call_args
        event_data = json.loads(call_args[0][1])
        
        # 필수 필드 존재 확인
        assert "event_type" in event_data
        assert "timestamp" in event_data
        assert "user_id" in event_data
        assert "room_id" in event_data
        assert "session_duration_seconds" in event_data
        assert "hands_played" in event_data
        assert "total_bet" in event_data
        assert "total_won" in event_data
        assert "join_time" in event_data
        assert "leave_time" in event_data
        
        # 값 검증
        assert event_data["event_type"] == "player_stats"
        assert event_data["user_id"] == user_id
        assert event_data["room_id"] == room_id
        assert event_data["session_duration_seconds"] == session_duration_seconds
        assert event_data["hands_played"] == hands_played
        assert event_data["total_bet"] == total_bet
        assert event_data["total_won"] == total_won
