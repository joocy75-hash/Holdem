"""Tests for Telegram notifier service."""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.telegram_notifier import (
    TelegramNotifier,
    get_telegram_notifier,
    notify_deposit_confirmed,
    notify_deposit_expired,
)
from app.models.deposit_request import DepositRequest, DepositRequestStatus


@pytest.fixture
def mock_request():
    """Create a mock deposit request."""
    request = MagicMock(spec=DepositRequest)
    request.id = uuid4()
    request.user_id = "test-user-123"
    request.telegram_id = 123456789
    request.requested_krw = 100000
    request.calculated_usdt = Decimal("68.03")
    request.exchange_rate = Decimal("1470.54")
    request.memo = "user_123_1705401234_ab12"
    request.status = DepositRequestStatus.PENDING
    request.expires_at = datetime.utcnow() + timedelta(minutes=30)
    request.remaining_seconds = 1800
    return request


@pytest.fixture
def mock_request_no_telegram():
    """Create a mock deposit request without telegram_id."""
    request = MagicMock(spec=DepositRequest)
    request.id = uuid4()
    request.user_id = "test-user-456"
    request.telegram_id = None
    request.requested_krw = 50000
    request.calculated_usdt = Decimal("34.01")
    request.exchange_rate = Decimal("1470.54")
    request.memo = "user_456_1705401234_cd34"
    request.status = DepositRequestStatus.PENDING
    return request


class TestTelegramNotifier:
    """Tests for TelegramNotifier class."""
    
    def test_init_default_values(self):
        """Test initialization with default values."""
        with patch('app.services.telegram_notifier.settings') as mock_settings:
            mock_settings.telegram_bot_token = "test_token"
            mock_settings.telegram_admin_chat_id = "123456"
            
            notifier = TelegramNotifier()
            
            assert notifier.bot_token == "test_token"
            assert notifier.admin_chat_id == "123456"
            assert notifier._bot is None
    
    def test_init_custom_values(self):
        """Test initialization with custom values."""
        notifier = TelegramNotifier(
            bot_token="custom_token",
            admin_chat_id="789012",
        )
        
        assert notifier.bot_token == "custom_token"
        assert notifier.admin_chat_id == "789012"
    
    def test_is_configured_true(self):
        """Test is_configured returns True when token is set."""
        notifier = TelegramNotifier(bot_token="test_token")
        assert notifier.is_configured is True
    
    def test_is_configured_false(self):
        """Test is_configured returns False when token is empty."""
        with patch('app.services.telegram_notifier.settings') as mock_settings:
            mock_settings.telegram_bot_token = ""
            mock_settings.telegram_admin_chat_id = ""
            
            notifier = TelegramNotifier(bot_token="")
            assert notifier.is_configured is False
            
            # Also test with placeholder token
            notifier2 = TelegramNotifier(bot_token="your-bot-token")
            assert notifier2.is_configured is False


class TestMessageFormatting:
    """Tests for message formatting methods."""
    
    def test_format_deposit_confirmed_message(self, mock_request):
        """Test deposit confirmed message formatting."""
        notifier = TelegramNotifier(bot_token="test")
        tx_hash = "abc123def456"
        
        message = notifier._format_deposit_confirmed_message(mock_request, tx_hash)
        
        assert "입금이 확인되었습니다" in message
        assert "100,000 KRW" in message
        assert "68.03 USDT" in message
        assert "abc123def456" in message
    
    def test_format_deposit_expired_message(self, mock_request):
        """Test deposit expired message formatting."""
        notifier = TelegramNotifier(bot_token="test")
        
        message = notifier._format_deposit_expired_message(mock_request)
        
        assert "만료되었습니다" in message
        assert "100,000 KRW" in message
        assert mock_request.memo in message
    
    def test_format_deposit_created_message(self, mock_request):
        """Test deposit created message formatting."""
        notifier = TelegramNotifier(bot_token="test")
        
        message = notifier._format_deposit_created_message(mock_request)
        
        assert "입금 요청이 생성되었습니다" in message
        assert "100,000 KRW" in message
        assert "68.03 USDT" in message
        assert mock_request.memo in message
        assert "메모" in message
    
    def test_format_deposit_reminder_message(self, mock_request):
        """Test deposit reminder message formatting."""
        notifier = TelegramNotifier(bot_token="test")
        
        message = notifier._format_deposit_reminder_message(mock_request, 5)
        
        assert "5분 후 만료" in message
        assert "68.03 USDT" in message
    
    def test_format_admin_deposit_confirmed_message(self, mock_request):
        """Test admin deposit confirmed message formatting."""
        notifier = TelegramNotifier(bot_token="test")
        tx_hash = "abc123def456"
        
        message = notifier._format_admin_deposit_confirmed_message(mock_request, tx_hash)
        
        assert "[입금 확인]" in message
        assert mock_request.user_id in message
        assert tx_hash in message
    
    def test_format_admin_large_deposit_message(self, mock_request):
        """Test admin large deposit message formatting."""
        notifier = TelegramNotifier(bot_token="test")
        tx_hash = "abc123def456"
        
        message = notifier._format_admin_large_deposit_message(mock_request, tx_hash)
        
        assert "대량 입금" in message
        assert mock_request.user_id in message
    
    def test_format_admin_manual_review_message(self, mock_request):
        """Test admin manual review message formatting."""
        notifier = TelegramNotifier(bot_token="test")
        
        message = notifier._format_admin_manual_review_message(
            mock_request, "Amount mismatch"
        )
        
        assert "수동 검토 필요" in message
        assert "Amount mismatch" in message


class TestNotifications:
    """Tests for notification methods."""
    
    @pytest.mark.asyncio
    async def test_notify_deposit_confirmed_no_telegram_id(self, mock_request_no_telegram):
        """Test notification skipped when no telegram_id."""
        notifier = TelegramNotifier(bot_token="test")
        
        result = await notifier.notify_deposit_confirmed(
            mock_request_no_telegram, "tx_hash"
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_notify_deposit_expired_no_telegram_id(self, mock_request_no_telegram):
        """Test notification skipped when no telegram_id."""
        notifier = TelegramNotifier(bot_token="test")
        
        result = await notifier.notify_deposit_expired(mock_request_no_telegram)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_send_message_not_configured(self):
        """Test message not sent when not configured."""
        notifier = TelegramNotifier(bot_token="")
        
        result = await notifier._send_message(123456, "Test message")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_notify_admin_no_chat_id(self, mock_request):
        """Test admin notification skipped when no chat_id."""
        with patch('app.services.telegram_notifier.settings') as mock_settings:
            mock_settings.telegram_bot_token = "test"
            mock_settings.telegram_admin_chat_id = ""
            
            notifier = TelegramNotifier(bot_token="test", admin_chat_id="")
            
            result = await notifier.notify_admin_deposit_confirmed(
                mock_request, "tx_hash"
            )
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_notify_admin_large_deposit_below_threshold(self, mock_request):
        """Test large deposit notification skipped when below threshold."""
        notifier = TelegramNotifier(bot_token="test", admin_chat_id="123")
        mock_request.calculated_usdt = Decimal("50")  # Below 1000 threshold
        
        result = await notifier.notify_admin_large_deposit(
            mock_request, "tx_hash", threshold=Decimal("1000")
        )
        
        assert result is False


class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_get_telegram_notifier_singleton(self):
        """Test singleton pattern for notifier."""
        with patch('app.services.telegram_notifier._notifier', None):
            notifier1 = get_telegram_notifier()
            notifier2 = get_telegram_notifier()
            
            # Should return same instance
            assert notifier1 is notifier2
    
    @pytest.mark.asyncio
    async def test_notify_deposit_confirmed_convenience(self, mock_request):
        """Test convenience function for deposit confirmed."""
        with patch('app.services.telegram_notifier.get_telegram_notifier') as mock_get:
            mock_notifier = AsyncMock()
            mock_notifier.notify_deposit_confirmed.return_value = True
            mock_notifier.notify_admin_deposit_confirmed.return_value = True
            mock_notifier.notify_admin_large_deposit.return_value = False
            mock_get.return_value = mock_notifier
            
            result = await notify_deposit_confirmed(mock_request, "tx_hash")
            
            assert result is True
            mock_notifier.notify_deposit_confirmed.assert_called_once()
            mock_notifier.notify_admin_deposit_confirmed.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_notify_deposit_expired_convenience(self, mock_request):
        """Test convenience function for deposit expired."""
        with patch('app.services.telegram_notifier.get_telegram_notifier') as mock_get:
            mock_notifier = AsyncMock()
            mock_notifier.notify_deposit_expired.return_value = True
            mock_get.return_value = mock_notifier
            
            result = await notify_deposit_expired(mock_request)
            
            assert result is True
            mock_notifier.notify_deposit_expired.assert_called_once_with(mock_request)
