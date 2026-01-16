"""Tests for deposit bot."""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.bot.deposit_bot import (
    DepositBot,
    DepositStates,
    get_deposit_bot,
    cmd_start,
    cmd_help,
    cmd_rate,
    cmd_deposit,
    cmd_cancel,
    cmd_status,
    process_deposit_amount,
)


class TestDepositBot:
    """Tests for DepositBot class."""
    
    def test_init_default_values(self):
        """Test initialization with default values."""
        with patch('app.bot.deposit_bot.settings') as mock_settings:
            mock_settings.telegram_bot_token = "test_token"
            
            bot = DepositBot()
            
            assert bot.bot_token == "test_token"
            assert bot._bot is None
            assert bot._dp is None
    
    def test_init_custom_token(self):
        """Test initialization with custom token."""
        bot = DepositBot(bot_token="custom_token")
        
        assert bot.bot_token == "custom_token"
    
    def test_is_configured_true(self):
        """Test is_configured returns True when token is set."""
        bot = DepositBot(bot_token="valid_token")
        assert bot.is_configured is True
    
    def test_is_configured_false_empty(self):
        """Test is_configured returns False when token is empty."""
        with patch('app.bot.deposit_bot.settings') as mock_settings:
            mock_settings.telegram_bot_token = ""
            
            bot = DepositBot(bot_token="")
            assert bot.is_configured is False
    
    def test_is_configured_false_placeholder(self):
        """Test is_configured returns False for placeholder token."""
        bot = DepositBot(bot_token="your-bot-token")
        assert bot.is_configured is False
    
    def test_setup_raises_without_token(self):
        """Test setup raises error without token."""
        with patch('app.bot.deposit_bot.settings') as mock_settings:
            mock_settings.telegram_bot_token = ""
            
            bot = DepositBot(bot_token="")
            
            with pytest.raises(ValueError, match="not configured"):
                bot.setup()
    
    def test_setup_creates_bot_and_dispatcher(self):
        """Test setup creates bot and dispatcher."""
        # Use a valid token format: number:alphanumeric
        bot = DepositBot(bot_token="123456789:ABCdefGHIjklMNOpqrSTUvwxYZ")
        
        result_bot, result_dp = bot.setup()
        
        assert result_bot is not None
        assert result_dp is not None
        assert bot._bot is result_bot
        assert bot._dp is result_dp


class TestCommandHandlers:
    """Tests for command handlers."""
    
    @pytest.fixture
    def mock_message(self):
        """Create a mock message."""
        message = AsyncMock()
        message.from_user = MagicMock()
        message.from_user.id = 123456789
        message.text = ""
        return message
    
    @pytest.fixture
    def mock_state(self):
        """Create a mock FSM state."""
        state = AsyncMock()
        state.get_state.return_value = None
        return state
    
    @pytest.mark.asyncio
    async def test_cmd_start(self, mock_message):
        """Test /start command."""
        await cmd_start(mock_message)
        
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args
        assert "안녕하세요" in call_args[0][0]
        assert "/deposit" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_cmd_help(self, mock_message):
        """Test /help command."""
        await cmd_help(mock_message)
        
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args
        assert "도움말" in call_args[0][0]
        assert "명령어" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_cmd_rate_success(self, mock_message):
        """Test /rate command success."""
        with patch('app.bot.deposit_bot.TonExchangeRateService') as mock_service:
            mock_instance = AsyncMock()
            mock_instance.get_usdt_krw_rate.return_value = Decimal("1470.54")
            mock_service.return_value = mock_instance
            
            await cmd_rate(mock_message)
            
            mock_message.answer.assert_called_once()
            call_args = mock_message.answer.call_args
            assert "환율" in call_args[0][0]
            assert "1,470.54" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_cmd_rate_error(self, mock_message):
        """Test /rate command error handling."""
        with patch('app.bot.deposit_bot.TonExchangeRateService') as mock_service:
            mock_instance = AsyncMock()
            mock_instance.get_usdt_krw_rate.side_effect = Exception("API error")
            mock_service.return_value = mock_instance
            
            await cmd_rate(mock_message)
            
            mock_message.answer.assert_called_once()
            call_args = mock_message.answer.call_args
            assert "오류" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_cmd_deposit(self, mock_message, mock_state):
        """Test /deposit command."""
        await cmd_deposit(mock_message, mock_state)
        
        mock_state.set_state.assert_called_once_with(DepositStates.waiting_for_amount)
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args
        assert "입금 요청" in call_args[0][0]
        assert "KRW" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_cmd_cancel_no_state(self, mock_message, mock_state):
        """Test /cancel command with no active state."""
        mock_state.get_state.return_value = None
        
        await cmd_cancel(mock_message, mock_state)
        
        mock_message.answer.assert_called_once()
        assert "취소할 작업이 없습니다" in mock_message.answer.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_cmd_cancel_with_state(self, mock_message, mock_state):
        """Test /cancel command with active state."""
        mock_state.get_state.return_value = DepositStates.waiting_for_amount
        
        await cmd_cancel(mock_message, mock_state)
        
        mock_state.clear.assert_called_once()
        mock_message.answer.assert_called_once()
        assert "취소되었습니다" in mock_message.answer.call_args[0][0]


class TestProcessDepositAmount:
    """Tests for deposit amount processing."""
    
    @pytest.fixture
    def mock_message(self):
        """Create a mock message."""
        message = AsyncMock()
        message.from_user = MagicMock()
        message.from_user.id = 123456789
        return message
    
    @pytest.fixture
    def mock_state(self):
        """Create a mock FSM state."""
        return AsyncMock()
    
    @pytest.mark.asyncio
    async def test_invalid_amount_text(self, mock_message, mock_state):
        """Test invalid amount input."""
        mock_message.text = "abc"
        
        await process_deposit_amount(mock_message, mock_state)
        
        mock_message.answer.assert_called_once()
        assert "올바른 금액" in mock_message.answer.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_amount_below_minimum(self, mock_message, mock_state):
        """Test amount below minimum."""
        mock_message.text = "5000"
        
        await process_deposit_amount(mock_message, mock_state)
        
        mock_message.answer.assert_called_once()
        assert "최소 입금액" in mock_message.answer.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_amount_above_maximum(self, mock_message, mock_state):
        """Test amount above maximum."""
        mock_message.text = "50000000"
        
        await process_deposit_amount(mock_message, mock_state)
        
        mock_message.answer.assert_called_once()
        assert "최대 입금액" in mock_message.answer.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_amount_with_commas(self, mock_message, mock_state):
        """Test amount with comma separators."""
        mock_message.text = "100,000"
        
        # Should parse correctly (100000 is valid)
        # Will fail at DB step but amount parsing should work
        with patch('app.bot.deposit_bot.get_admin_db') as mock_db:
            mock_db.return_value.__aiter__ = AsyncMock(
                side_effect=Exception("DB error")
            )
            
            await process_deposit_amount(mock_message, mock_state)
            
            # State should be cleared before DB call
            mock_state.clear.assert_called_once()


class TestGetDepositBot:
    """Tests for get_deposit_bot function."""
    
    def test_singleton_pattern(self):
        """Test singleton pattern."""
        with patch('app.bot.deposit_bot._bot_instance', None):
            bot1 = get_deposit_bot()
            bot2 = get_deposit_bot()
            
            assert bot1 is bot2
