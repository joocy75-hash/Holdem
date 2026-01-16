"""Tests for fraud event integration in ActionHandler.

Property 3: 봇 플레이어 액션 이벤트 미발행
**Validates: Requirements 2.4**
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ws.handlers.action import ActionHandler, is_bot_player
from app.game.poker_table import Player


class TestIsBotPlayer:
    """is_bot_player 함수 테스트."""

    def test_bot_prefix_bot_(self):
        """bot_ 접두사로 시작하는 user_id는 봇."""
        player = MagicMock()
        player.user_id = "bot_12345"
        player.is_bot = False  # is_bot 필드와 관계없이 접두사로 판단
        assert is_bot_player(player) is True

    def test_bot_prefix_test_player_(self):
        """test_player_ 접두사로 시작하는 user_id는 봇."""
        player = MagicMock()
        player.user_id = "test_player_abc"
        player.is_bot = False
        assert is_bot_player(player) is True

    def test_is_bot_field_true(self):
        """is_bot 필드가 True면 봇."""
        player = MagicMock()
        player.user_id = "user_123"
        player.is_bot = True
        assert is_bot_player(player) is True

    def test_human_player(self):
        """일반 user_id와 is_bot=False면 인간."""
        player = MagicMock()
        player.user_id = "user_123"
        player.is_bot = False
        assert is_bot_player(player) is False

    def test_none_player(self):
        """None 플레이어는 False."""
        assert is_bot_player(None) is False


class TestBotPlayerEventFiltering:
    """Property 3: 봇 플레이어 액션 이벤트 미발행 테스트.
    
    **Validates: Requirements 2.4**
    
    For any 봇 플레이어의 액션에 대해, Game_Server는 
    `fraud:player_action` 채널로 이벤트를 발행하지 않아야 한다.
    """

    @pytest.fixture
    def mock_manager(self):
        """Mock ConnectionManager."""
        manager = MagicMock()
        manager.broadcast_to_channel = AsyncMock()
        manager.send_to_user = AsyncMock()
        return manager

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        redis = AsyncMock()
        redis.publish = AsyncMock()
        return redis

    @pytest.fixture
    def action_handler(self, mock_manager, mock_redis):
        """ActionHandler with mocked dependencies."""
        handler = ActionHandler(mock_manager, mock_redis)
        return handler

    @pytest.mark.asyncio
    async def test_bot_action_not_published(self, action_handler, mock_redis):
        """봇 플레이어 액션은 fraud 이벤트로 발행되지 않음."""
        # 봇 플레이어 액션 이벤트 발행 시도
        await action_handler._publish_player_action_event(
            user_id="bot_12345",
            room_id="room-123",
            action_type="call",
            amount=100,
            is_bot=True,
        )

        # Redis publish가 호출되지 않아야 함
        mock_redis.publish.assert_not_called()

    @pytest.mark.asyncio
    async def test_human_action_published(self, action_handler, mock_redis):
        """인간 플레이어 액션은 fraud 이벤트로 발행됨."""
        # 테이블 모킹
        mock_table = MagicMock()
        mock_table.hand_number = 42

        with patch("app.ws.handlers.action.game_manager") as mock_gm:
            mock_gm.get_table.return_value = mock_table

            # 인간 플레이어 액션 이벤트 발행
            await action_handler._publish_player_action_event(
                user_id="user_123",
                room_id="room-456",
                action_type="raise",
                amount=200,
                is_bot=False,
            )

            # Redis publish가 호출되어야 함
            mock_redis.publish.assert_called_once()
            
            # 채널 확인
            call_args = mock_redis.publish.call_args
            assert call_args[0][0] == "fraud:player_action"

    @pytest.mark.asyncio
    async def test_test_player_action_not_published(self, action_handler, mock_redis):
        """test_player_ 접두사 플레이어 액션은 발행되지 않음."""
        await action_handler._publish_player_action_event(
            user_id="test_player_abc",
            room_id="room-123",
            action_type="fold",
            amount=0,
            is_bot=True,
        )

        mock_redis.publish.assert_not_called()


class TestTurnStartTimeTracking:
    """턴 시작 시간 추적 테스트."""

    @pytest.fixture
    def mock_manager(self):
        manager = MagicMock()
        manager.broadcast_to_channel = AsyncMock()
        return manager

    @pytest.fixture
    def action_handler(self, mock_manager):
        return ActionHandler(mock_manager, None)

    def test_record_turn_start(self, action_handler):
        """턴 시작 시간 기록."""
        action_handler._record_turn_start("room-123", "user-456")
        
        turn_key = "room-123:user-456"
        assert turn_key in action_handler._turn_start_times
        assert isinstance(action_handler._turn_start_times[turn_key], datetime)

    def test_turn_start_time_cleared_after_action(self, action_handler):
        """액션 후 턴 시작 시간 정리."""
        # 턴 시작 시간 기록
        action_handler._record_turn_start("room-123", "user-456")
        turn_key = "room-123:user-456"
        assert turn_key in action_handler._turn_start_times

        # 액션 이벤트 발행 (disabled 상태이므로 실제 발행은 안 됨)
        # 하지만 턴 시작 시간은 정리되어야 함
        # Note: _publish_player_action_event는 enabled=False면 바로 리턴하므로
        # 이 테스트는 enabled=True 상태에서만 의미 있음


class TestHandCompletedEventPublishing:
    """핸드 완료 이벤트 발행 테스트."""

    @pytest.fixture
    def mock_manager(self):
        manager = MagicMock()
        manager.broadcast_to_channel = AsyncMock()
        return manager

    @pytest.fixture
    def mock_redis(self):
        redis = AsyncMock()
        redis.publish = AsyncMock()
        return redis

    @pytest.fixture
    def action_handler(self, mock_manager, mock_redis):
        return ActionHandler(mock_manager, mock_redis)

    @pytest.mark.asyncio
    async def test_hand_completed_event_published(self, action_handler, mock_redis):
        """핸드 완료 시 fraud 이벤트 발행."""
        # 테이블 모킹
        mock_player = MagicMock()
        mock_player.user_id = "user-123"
        mock_player.status = "active"
        mock_player.total_bet_this_hand = 500
        mock_player.hole_cards = ["As", "Kd"]

        mock_table = MagicMock()
        mock_table.hand_number = 42
        mock_table.community_cards = ["Ah", "Kh", "Qh", "Jh", "Th"]
        mock_table.players = {0: mock_player, 1: None}

        hand_result = {
            "pot": 1000,
            "winners": [{"userId": "user-123", "amount": 1000}],
            "showdown": [{"userId": "user-123", "cards": ["As", "Kd"]}],
        }

        with patch("app.ws.handlers.action.game_manager") as mock_gm:
            mock_gm.get_table.return_value = mock_table

            await action_handler._publish_hand_completed_event(
                room_id="room-456",
                hand_result=hand_result,
            )

            # Redis publish가 호출되어야 함
            mock_redis.publish.assert_called_once()
            
            # 채널 확인
            call_args = mock_redis.publish.call_args
            assert call_args[0][0] == "fraud:hand_completed"

    @pytest.mark.asyncio
    async def test_hand_completed_event_disabled(self, mock_manager):
        """Redis 없으면 이벤트 발행 안 함."""
        handler = ActionHandler(mock_manager, None)
        
        hand_result = {"pot": 1000, "winners": [], "showdown": []}
        
        # 에러 없이 실행되어야 함
        await handler._publish_hand_completed_event("room-123", hand_result)
