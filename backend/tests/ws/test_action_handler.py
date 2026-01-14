"""Unit tests for ActionHandler class.

Tests timeout behavior, cleanup methods, and resource management.
Validates Requirements 10.3 from code-quality-security-upgrade spec.
"""

import asyncio
import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.ws.handlers.action import ActionHandler, is_bot_player
from app.ws.connection import WebSocketConnection
from app.ws.events import EventType
from app.ws.messages import MessageEnvelope
from app.game.poker_table import PokerTable, Player, GamePhase


# =============================================================================
# Fixtures
# =============================================================================


class MockWebSocket:
    """Mock WebSocket for testing."""
    
    def __init__(self):
        self.sent_messages = []
        self.closed = False
    
    async def send_json(self, data):
        self.sent_messages.append(data)
    
    async def close(self):
        self.closed = True


class MockRedis:
    """Mock Redis for testing."""
    
    def __init__(self):
        self.data = {}
    
    async def get(self, key):
        return self.data.get(key)
    
    async def set(self, key, value, ex=None, nx=None):
        if nx and key in self.data:
            return False
        self.data[key] = value
        return True
    
    async def delete(self, key):
        self.data.pop(key, None)


class MockConnectionManager:
    """Mock ConnectionManager for testing."""
    
    def __init__(self):
        self.connections = {}
        self.channels = {}
        self.broadcast_messages = []
        self.user_messages = {}
    
    async def broadcast_to_channel(self, channel: str, message: dict):
        self.broadcast_messages.append((channel, message))
    
    async def send_to_user(self, user_id: str, message: dict):
        if user_id not in self.user_messages:
            self.user_messages[user_id] = []
        self.user_messages[user_id].append(message)


@pytest.fixture
def mock_manager():
    """Create mock connection manager."""
    return MockConnectionManager()


@pytest.fixture
def mock_redis():
    """Create mock Redis."""
    return MockRedis()


@pytest_asyncio.fixture
async def action_handler(mock_manager, mock_redis):
    """Create ActionHandler with mocks."""
    handler = ActionHandler(mock_manager, mock_redis)
    yield handler
    # Cleanup
    await handler.cleanup_all_resources()


@pytest.fixture
def mock_connection():
    """Create mock WebSocket connection."""
    return WebSocketConnection(
        websocket=MockWebSocket(),
        user_id="user1",
        session_id="session1",
        connection_id=str(uuid4()),
        connected_at=datetime.utcnow(),
    )


@pytest.fixture
def mock_table():
    """Create mock PokerTable."""
    table = PokerTable(
        room_id="test-room",
        name="Test Table",
        small_blind=10,
        big_blind=20,
        min_buy_in=400,
        max_buy_in=2000,
    )
    
    player1 = Player(user_id="user1", username="Player1", seat=0, stack=1000)
    player2 = Player(user_id="user2", username="Player2", seat=1, stack=1000)
    
    table.seat_player(0, player1)
    table.seat_player(1, player2)
    
    return table


# =============================================================================
# is_bot_player Tests
# =============================================================================


class TestIsBotPlayer:
    """Tests for is_bot_player utility function."""

    def test_bot_with_is_bot_field(self):
        """Test bot detection using is_bot field."""
        player = Player(user_id="user1", username="Bot1", seat=0, stack=1000, is_bot=True)
        assert is_bot_player(player) is True

    def test_human_with_is_bot_field(self):
        """Test human detection using is_bot field."""
        player = Player(user_id="user1", username="Human1", seat=0, stack=1000, is_bot=False)
        assert is_bot_player(player) is False

    def test_bot_by_user_id_prefix(self):
        """Test bot detection by user_id prefix when is_bot not set."""
        # Create a mock object without is_bot attribute
        class MockPlayer:
            def __init__(self, user_id):
                self.user_id = user_id
        
        player = MockPlayer("bot_123")
        assert is_bot_player(player) is True

    def test_test_player_prefix(self):
        """Test bot detection by test_player prefix when is_bot not set."""
        class MockPlayer:
            def __init__(self, user_id):
                self.user_id = user_id
        
        player = MockPlayer("test_player_1")
        assert is_bot_player(player) is True

    def test_none_player(self):
        """Test None player returns False."""
        assert is_bot_player(None) is False


# =============================================================================
# Handler Events Tests
# =============================================================================


class TestHandlerEvents:
    """Tests for handler event types."""

    def test_handled_events(self, action_handler):
        """Test handler handles correct events."""
        assert EventType.ACTION_REQUEST in action_handler.handled_events
        assert EventType.START_GAME in action_handler.handled_events

    def test_can_handle_action_request(self, action_handler):
        """Test can_handle returns True for ACTION_REQUEST."""
        assert action_handler.can_handle(EventType.ACTION_REQUEST) is True

    def test_can_handle_start_game(self, action_handler):
        """Test can_handle returns True for START_GAME."""
        assert action_handler.can_handle(EventType.START_GAME) is True

    def test_cannot_handle_other_events(self, action_handler):
        """Test can_handle returns False for other events."""
        assert action_handler.can_handle(EventType.PING) is False
        assert action_handler.can_handle(EventType.CHAT_MESSAGE) is False


# =============================================================================
# Table Lock Tests
# =============================================================================


class TestTableLocks:
    """Tests for table lock management."""

    def test_get_table_lock_creates_new(self, action_handler):
        """Test getting lock creates new lock if not exists."""
        lock = action_handler._get_table_lock("room1")
        
        assert lock is not None
        assert isinstance(lock, asyncio.Lock)
        assert "room1" in action_handler._table_locks

    def test_get_table_lock_returns_existing(self, action_handler):
        """Test getting lock returns existing lock."""
        lock1 = action_handler._get_table_lock("room1")
        lock2 = action_handler._get_table_lock("room1")
        
        assert lock1 is lock2

    def test_different_rooms_different_locks(self, action_handler):
        """Test different rooms have different locks."""
        lock1 = action_handler._get_table_lock("room1")
        lock2 = action_handler._get_table_lock("room2")
        
        assert lock1 is not lock2


# =============================================================================
# Timeout Tests
# =============================================================================


class TestTimeoutManagement:
    """Tests for turn timeout management."""

    @pytest.mark.asyncio
    async def test_cancel_turn_timeout_no_task(self, action_handler):
        """Test cancelling timeout when no task exists."""
        # Should not raise
        await action_handler._cancel_turn_timeout("nonexistent-room")

    @pytest.mark.asyncio
    async def test_cancel_turn_timeout_with_task(self, action_handler):
        """Test cancelling existing timeout task."""
        # Create a dummy task
        async def dummy_task():
            await asyncio.sleep(100)
        
        task = asyncio.create_task(dummy_task())
        action_handler._timeout_tasks["room1"] = task
        
        await action_handler._cancel_turn_timeout("room1")
        
        assert "room1" not in action_handler._timeout_tasks
        assert task.cancelled()


# =============================================================================
# Cleanup Tests
# =============================================================================


class TestCleanup:
    """Tests for resource cleanup methods."""

    @pytest.mark.asyncio
    async def test_cleanup_table_resources(self, action_handler):
        """Test cleanup_table_resources removes all resources."""
        # Setup resources
        action_handler._table_locks["room1"] = asyncio.Lock()
        
        async def dummy_task():
            await asyncio.sleep(100)
        
        task = asyncio.create_task(dummy_task())
        action_handler._timeout_tasks["room1"] = task
        
        # Cleanup
        await action_handler.cleanup_table_resources("room1")
        
        assert "room1" not in action_handler._table_locks
        assert "room1" not in action_handler._timeout_tasks

    @pytest.mark.asyncio
    async def test_cleanup_all_resources(self, action_handler):
        """Test cleanup_all_resources clears everything."""
        # Setup multiple resources
        action_handler._table_locks["room1"] = asyncio.Lock()
        action_handler._table_locks["room2"] = asyncio.Lock()
        
        async def dummy_task():
            await asyncio.sleep(100)
        
        task1 = asyncio.create_task(dummy_task())
        task2 = asyncio.create_task(dummy_task())
        action_handler._timeout_tasks["room1"] = task1
        action_handler._timeout_tasks["room2"] = task2
        
        # Cleanup all
        await action_handler.cleanup_all_resources()
        
        assert len(action_handler._table_locks) == 0
        assert len(action_handler._timeout_tasks) == 0

    @pytest.mark.asyncio
    async def test_cleanup_idempotent(self, action_handler):
        """Test cleanup can be called multiple times safely."""
        await action_handler.cleanup_all_resources()
        await action_handler.cleanup_all_resources()
        # Should not raise


# =============================================================================
# Error Result Tests
# =============================================================================


class TestErrorResult:
    """Tests for error result creation."""

    def test_create_error_result(self, action_handler):
        """Test creating error result message."""
        result = action_handler._create_error_result(
            table_id="room1",
            error_code="TEST_ERROR",
            error_message="Test error message",
            request_id="req-1",
            trace_id="trace-1",
        )
        
        assert result.type == EventType.ACTION_RESULT
        assert result.payload["success"] is False
        assert result.payload["errorCode"] == "TEST_ERROR"
        assert result.payload["errorMessage"] == "Test error message"
        assert result.request_id == "req-1"

    def test_create_error_result_with_refresh(self, action_handler):
        """Test creating error result with shouldRefresh flag."""
        result = action_handler._create_error_result(
            table_id="room1",
            error_code="STATE_MISMATCH",
            error_message="State mismatch",
            request_id="req-1",
            trace_id="trace-1",
            should_refresh=True,
        )
        
        assert result.payload["shouldRefresh"] is True


# =============================================================================
# Bot Decision Tests
# =============================================================================


class TestBotDecision:
    """Tests for bot decision logic."""

    def test_decide_bot_action_strong_hand(self, action_handler):
        """Test bot raises with strong hand."""
        action, amount = action_handler._decide_bot_action(
            actions=["fold", "call", "raise"],
            call_amount=20,
            stack=1000,
            available={"min_raise": 40, "max_raise": 1000},
            hole_cards=["As", "Ah"],
            community_cards=["Ad", "Ks", "Qh"],
            pot=100,
        )
        
        # Strong hand should raise or call
        assert action in ["raise", "call", "bet"]

    def test_decide_bot_action_weak_hand_check(self, action_handler):
        """Test bot checks or bets with weak hand when possible."""
        action, amount = action_handler._decide_bot_action(
            actions=["check", "bet"],
            call_amount=0,
            stack=1000,
            available={"min_raise": 20, "max_raise": 1000},
            hole_cards=["7h", "2c"],
            community_cards=["Ad", "Ks", "Qh"],
            pot=100,
        )
        
        # Weak hand should check or occasionally bluff bet
        assert action in ["check", "bet"]

    def test_decide_bot_action_weak_hand_fold(self, action_handler):
        """Test bot folds with weak hand when facing bet."""
        action, amount = action_handler._decide_bot_action(
            actions=["fold", "call", "raise"],
            call_amount=100,
            stack=1000,
            available={"min_raise": 200, "max_raise": 1000},
            hole_cards=["7h", "2c"],
            community_cards=["Ad", "Ks", "Qh"],
            pot=100,
        )
        
        # Weak hand facing big bet should fold
        assert action == "fold"

    def test_decide_bot_action_fallback(self, action_handler):
        """Test bot fallback when no actions available."""
        action, amount = action_handler._decide_bot_action(
            actions=[],
            call_amount=0,
            stack=1000,
            available={},
            hole_cards=["As", "Kh"],
            community_cards=[],
            pot=30,
        )
        
        # Should return fold as fallback
        assert action == "fold"


# =============================================================================
# Handle Action Tests
# =============================================================================


class TestHandleAction:
    """Tests for action handling."""

    @pytest.mark.asyncio
    async def test_handle_action_table_not_found(self, action_handler, mock_connection):
        """Test action fails when table not found."""
        event = MessageEnvelope.create(
            event_type=EventType.ACTION_REQUEST,
            payload={
                "tableId": "nonexistent-room",
                "actionType": "fold",
                "amount": 0,
            },
            request_id="req-1",
            trace_id="trace-1",
        )
        
        with patch("app.ws.handlers.action.game_manager") as mock_gm:
            mock_gm.get_table.return_value = None
            
            result = await action_handler._handle_action(mock_connection, event)
            
            assert result.payload["success"] is False
            assert result.payload["errorCode"] == "TABLE_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_handle_action_invalid_payload(self, action_handler, mock_connection):
        """Test action fails with invalid payload."""
        event = MessageEnvelope.create(
            event_type=EventType.ACTION_REQUEST,
            payload={
                # Missing required fields
                "tableId": "room1",
            },
            request_id="req-1",
            trace_id="trace-1",
        )
        
        result = await action_handler._handle_action(mock_connection, event)
        
        assert result.payload["success"] is False
        assert result.payload["errorCode"] == "INVALID_PAYLOAD"


# =============================================================================
# Handle Start Game Tests
# =============================================================================


class TestHandleStartGame:
    """Tests for start game handling."""

    @pytest.mark.asyncio
    async def test_start_game_table_not_found(self, action_handler, mock_connection):
        """Test start game fails when table not found."""
        event = MessageEnvelope.create(
            event_type=EventType.START_GAME,
            payload={"tableId": "nonexistent-room"},
            request_id="req-1",
            trace_id="trace-1",
        )
        
        with patch("app.ws.handlers.action.game_manager") as mock_gm:
            mock_gm.get_table.return_value = None
            
            result = await action_handler._handle_start_game(mock_connection, event)
            
            assert result.payload["success"] is False
            assert result.payload["errorCode"] == "TABLE_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_start_game_already_in_progress(self, action_handler, mock_connection, mock_table):
        """Test start game fails when game already in progress."""
        mock_table.phase = GamePhase.PREFLOP
        
        event = MessageEnvelope.create(
            event_type=EventType.START_GAME,
            payload={"tableId": "test-room"},
            request_id="req-1",
            trace_id="trace-1",
        )
        
        with patch("app.ws.handlers.action.game_manager") as mock_gm:
            mock_gm.get_table.return_value = mock_table
            
            result = await action_handler._handle_start_game(mock_connection, event)
            
            assert result.payload["success"] is False
            assert result.payload["errorCode"] == "GAME_ALREADY_IN_PROGRESS"

    @pytest.mark.asyncio
    async def test_start_game_not_enough_players(self, action_handler, mock_connection):
        """Test start game fails with insufficient players."""
        table = PokerTable(
            room_id="test-room",
            name="Test Table",
            small_blind=10,
            big_blind=20,
            min_buy_in=400,
            max_buy_in=2000,
        )
        # Only one player
        player1 = Player(user_id="user1", username="Player1", seat=0, stack=1000)
        table.seat_player(0, player1)
        
        event = MessageEnvelope.create(
            event_type=EventType.START_GAME,
            payload={"tableId": "test-room"},
            request_id="req-1",
            trace_id="trace-1",
        )
        
        with patch("app.ws.handlers.action.game_manager") as mock_gm:
            mock_gm.get_table.return_value = table
            
            result = await action_handler._handle_start_game(mock_connection, event)
            
            assert result.payload["success"] is False
            assert result.payload["errorCode"] == "NOT_ENOUGH_PLAYERS"


# =============================================================================
# Integration-like Tests
# =============================================================================


class TestActionHandlerIntegration:
    """Integration-like tests for ActionHandler."""

    @pytest.mark.asyncio
    async def test_concurrent_lock_acquisition(self, action_handler):
        """Test concurrent lock acquisition for same room."""
        lock = action_handler._get_table_lock("room1")
        
        acquired_count = 0
        
        async def try_acquire():
            nonlocal acquired_count
            async with lock:
                acquired_count += 1
                await asyncio.sleep(0.01)
        
        # Run multiple concurrent acquisitions
        await asyncio.gather(
            try_acquire(),
            try_acquire(),
            try_acquire(),
        )
        
        # All should have acquired the lock sequentially
        assert acquired_count == 3

    @pytest.mark.asyncio
    async def test_cleanup_during_active_timeout(self, action_handler):
        """Test cleanup properly cancels active timeout."""
        timeout_executed = False
        
        async def timeout_handler():
            nonlocal timeout_executed
            await asyncio.sleep(0.5)
            timeout_executed = True
        
        task = asyncio.create_task(timeout_handler())
        action_handler._timeout_tasks["room1"] = task
        
        # Cleanup immediately
        await action_handler.cleanup_table_resources("room1")
        
        # Wait a bit to ensure timeout didn't execute
        await asyncio.sleep(0.1)
        
        assert timeout_executed is False
        assert task.cancelled()
