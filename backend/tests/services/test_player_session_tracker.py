"""Tests for PlayerSessionTracker service.

Property 4: 플레이어 통계 이벤트 발행 및 스키마 검증
Property 5: 세션 통계 정확성

**Validates: Requirements 3.1, 3.2, 3.3**
"""

import json
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hypothesis import given, settings, strategies as st

from app.services.player_session_tracker import (
    PlayerSession,
    PlayerSessionTracker,
    get_session_tracker,
    init_session_tracker,
)


class TestPlayerSessionTrackerInit:
    """PlayerSessionTracker 초기화 테스트."""

    def test_init_with_publisher(self):
        """FraudEventPublisher가 있으면 설정됨."""
        mock_publisher = MagicMock()
        tracker = PlayerSessionTracker(mock_publisher)
        assert tracker._fraud_publisher is mock_publisher

    def test_init_without_publisher(self):
        """FraudEventPublisher 없이도 동작."""
        tracker = PlayerSessionTracker(None)
        assert tracker._fraud_publisher is None

    def test_global_instance(self):
        """글로벌 인스턴스 초기화 테스트."""
        mock_publisher = MagicMock()
        tracker = init_session_tracker(mock_publisher)
        assert get_session_tracker() is tracker


class TestSessionLifecycle:
    """세션 생명주기 테스트."""

    @pytest.fixture
    def tracker(self):
        return PlayerSessionTracker(None)

    def test_start_session(self, tracker):
        """세션 시작."""
        session = tracker.start_session("user-123", "room-456")
        
        assert session.user_id == "user-123"
        assert session.room_id == "room-456"
        assert session.hands_played == 0
        assert session.total_bet == 0
        assert session.total_won == 0
        assert isinstance(session.join_time, datetime)

    def test_start_session_duplicate(self, tracker):
        """중복 세션 시작 시 기존 세션 반환."""
        session1 = tracker.start_session("user-123", "room-456")
        session2 = tracker.start_session("user-123", "room-456")
        
        assert session1 is session2

    def test_get_session(self, tracker):
        """세션 조회."""
        tracker.start_session("user-123", "room-456")
        
        session = tracker.get_session("user-123", "room-456")
        assert session is not None
        assert session.user_id == "user-123"

    def test_get_session_not_found(self, tracker):
        """존재하지 않는 세션 조회."""
        session = tracker.get_session("user-123", "room-456")
        assert session is None

    @pytest.mark.asyncio
    async def test_end_session(self, tracker):
        """세션 종료."""
        tracker.start_session("user-123", "room-456")
        
        session = await tracker.end_session("user-123", "room-456")
        
        assert session is not None
        assert session.user_id == "user-123"
        
        # 세션이 제거되었는지 확인
        assert tracker.get_session("user-123", "room-456") is None

    @pytest.mark.asyncio
    async def test_end_session_not_found(self, tracker):
        """존재하지 않는 세션 종료."""
        session = await tracker.end_session("user-123", "room-456")
        assert session is None


class TestHandStatsUpdate:
    """핸드 통계 업데이트 테스트."""

    @pytest.fixture
    def tracker(self):
        return PlayerSessionTracker(None)

    def test_update_hand_stats(self, tracker):
        """핸드 통계 업데이트."""
        tracker.start_session("user-123", "room-456")
        
        tracker.update_hand_stats("user-123", "room-456", bet_amount=100, won_amount=200)
        
        session = tracker.get_session("user-123", "room-456")
        assert session.hands_played == 1
        assert session.total_bet == 100
        assert session.total_won == 200

    def test_update_hand_stats_multiple(self, tracker):
        """여러 핸드 통계 누적."""
        tracker.start_session("user-123", "room-456")
        
        tracker.update_hand_stats("user-123", "room-456", bet_amount=100, won_amount=0)
        tracker.update_hand_stats("user-123", "room-456", bet_amount=200, won_amount=500)
        tracker.update_hand_stats("user-123", "room-456", bet_amount=150, won_amount=0)
        
        session = tracker.get_session("user-123", "room-456")
        assert session.hands_played == 3
        assert session.total_bet == 450  # 100 + 200 + 150
        assert session.total_won == 500  # 0 + 500 + 0

    def test_update_hand_stats_no_session(self, tracker):
        """세션 없이 통계 업데이트 시도."""
        # 에러 없이 무시되어야 함
        tracker.update_hand_stats("user-123", "room-456", bet_amount=100, won_amount=200)


class TestFraudEventPublishing:
    """Fraud 이벤트 발행 테스트."""

    @pytest.fixture
    def mock_publisher(self):
        publisher = MagicMock()
        publisher.enabled = True
        publisher.publish_player_stats = AsyncMock(return_value=True)
        return publisher

    @pytest.fixture
    def tracker(self, mock_publisher):
        return PlayerSessionTracker(mock_publisher)

    @pytest.mark.asyncio
    async def test_end_session_publishes_event(self, tracker, mock_publisher):
        """세션 종료 시 fraud 이벤트 발행."""
        tracker.start_session("user-123", "room-456")
        tracker.update_hand_stats("user-123", "room-456", bet_amount=500, won_amount=1000)
        
        await tracker.end_session("user-123", "room-456")
        
        mock_publisher.publish_player_stats.assert_called_once()
        
        call_kwargs = mock_publisher.publish_player_stats.call_args.kwargs
        assert call_kwargs["user_id"] == "user-123"
        assert call_kwargs["room_id"] == "room-456"
        assert call_kwargs["hands_played"] == 1
        assert call_kwargs["total_bet"] == 500
        assert call_kwargs["total_won"] == 1000
        assert "session_duration_seconds" in call_kwargs
        assert "join_time" in call_kwargs
        assert "leave_time" in call_kwargs

    @pytest.mark.asyncio
    async def test_end_session_no_publish_when_disabled(self):
        """Publisher 비활성화 시 이벤트 발행 안 함."""
        mock_publisher = MagicMock()
        mock_publisher.enabled = False
        mock_publisher.publish_player_stats = AsyncMock()
        
        tracker = PlayerSessionTracker(mock_publisher)
        tracker.start_session("user-123", "room-456")
        
        await tracker.end_session("user-123", "room-456")
        
        mock_publisher.publish_player_stats.assert_not_called()


class TestRoomSessionCleanup:
    """방 세션 정리 테스트."""

    @pytest.fixture
    def tracker(self):
        return PlayerSessionTracker(None)

    def test_clear_room_sessions(self, tracker):
        """방의 모든 세션 정리."""
        tracker.start_session("user-1", "room-A")
        tracker.start_session("user-2", "room-A")
        tracker.start_session("user-3", "room-B")
        
        cleared = tracker.clear_room_sessions("room-A")
        
        assert cleared == 2
        assert tracker.get_session("user-1", "room-A") is None
        assert tracker.get_session("user-2", "room-A") is None
        assert tracker.get_session("user-3", "room-B") is not None

    def test_clear_room_sessions_empty(self, tracker):
        """빈 방 세션 정리."""
        cleared = tracker.clear_room_sessions("room-A")
        assert cleared == 0


# ============================================================================
# Property-Based Tests
# ============================================================================

class TestSessionStatsAccuracy:
    """Property 5: 세션 통계 정확성.
    
    **Validates: Requirements 3.3**
    
    For any 플레이어 세션에 대해, 발행된 통계 이벤트의 hands_played, 
    total_bet, total_won 값은 해당 세션 동안 실제로 플레이한 핸드들의 
    합계와 일치해야 한다.
    """

    @given(
        hand_bets=st.lists(
            st.integers(min_value=0, max_value=100000),
            min_size=0,
            max_size=100,
        ),
        hand_wins=st.lists(
            st.integers(min_value=0, max_value=100000),
            min_size=0,
            max_size=100,
        ),
    )
    @settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_session_stats_accuracy(
        self,
        hand_bets: list[int],
        hand_wins: list[int],
    ):
        """세션 통계가 실제 핸드 합계와 일치."""
        # 리스트 길이 맞추기
        min_len = min(len(hand_bets), len(hand_wins))
        hand_bets = hand_bets[:min_len]
        hand_wins = hand_wins[:min_len]
        
        mock_publisher = MagicMock()
        mock_publisher.enabled = True
        mock_publisher.publish_player_stats = AsyncMock(return_value=True)
        
        tracker = PlayerSessionTracker(mock_publisher)
        tracker.start_session("user-123", "room-456")
        
        # 핸드 통계 업데이트
        for bet, won in zip(hand_bets, hand_wins):
            tracker.update_hand_stats("user-123", "room-456", bet_amount=bet, won_amount=won)
        
        # 세션 종료
        await tracker.end_session("user-123", "room-456")
        
        # 발행된 이벤트 검증
        if min_len > 0 or mock_publisher.publish_player_stats.called:
            call_kwargs = mock_publisher.publish_player_stats.call_args.kwargs
            
            # 통계 정확성 검증
            assert call_kwargs["hands_played"] == min_len
            assert call_kwargs["total_bet"] == sum(hand_bets)
            assert call_kwargs["total_won"] == sum(hand_wins)


class TestPlayerStatsEventSchema:
    """Property 4: 플레이어 통계 이벤트 발행 및 스키마 검증.
    
    **Validates: Requirements 3.1, 3.2**
    
    For any 테이블을 떠나는 플레이어에 대해, Game_Server가 
    `fraud:player_stats` 채널로 이벤트를 발행하면, 해당 이벤트는 
    user_id, room_id, session_duration_seconds, hands_played, 
    total_bet, total_won, join_time, leave_time 필드를 모두 포함해야 한다.
    """

    @given(
        user_id=st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-"),
            min_size=1,
            max_size=36,
        ),
        room_id=st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-"),
            min_size=1,
            max_size=36,
        ),
        hands_played=st.integers(min_value=0, max_value=1000),
        total_bet=st.integers(min_value=0, max_value=10000000),
        total_won=st.integers(min_value=0, max_value=10000000),
    )
    @settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_player_stats_event_schema(
        self,
        user_id: str,
        room_id: str,
        hands_played: int,
        total_bet: int,
        total_won: int,
    ):
        """플레이어 통계 이벤트 스키마 검증."""
        mock_publisher = MagicMock()
        mock_publisher.enabled = True
        mock_publisher.publish_player_stats = AsyncMock(return_value=True)
        
        tracker = PlayerSessionTracker(mock_publisher)
        tracker.start_session(user_id, room_id)
        
        # 통계 설정 (직접 세션 수정)
        session = tracker.get_session(user_id, room_id)
        session.hands_played = hands_played
        session.total_bet = total_bet
        session.total_won = total_won
        
        # 세션 종료
        await tracker.end_session(user_id, room_id)
        
        # 발행된 이벤트 검증
        mock_publisher.publish_player_stats.assert_called_once()
        
        call_kwargs = mock_publisher.publish_player_stats.call_args.kwargs
        
        # 필수 필드 존재 확인
        assert "user_id" in call_kwargs
        assert "room_id" in call_kwargs
        assert "session_duration_seconds" in call_kwargs
        assert "hands_played" in call_kwargs
        assert "total_bet" in call_kwargs
        assert "total_won" in call_kwargs
        assert "join_time" in call_kwargs
        assert "leave_time" in call_kwargs
        
        # 값 검증
        assert call_kwargs["user_id"] == user_id
        assert call_kwargs["room_id"] == room_id
        assert call_kwargs["hands_played"] == hands_played
        assert call_kwargs["total_bet"] == total_bet
        assert call_kwargs["total_won"] == total_won
        assert call_kwargs["session_duration_seconds"] >= 0
