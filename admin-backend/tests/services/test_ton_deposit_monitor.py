"""Unit tests for TonDepositMonitor."""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.crypto.ton_deposit_monitor import TonDepositMonitor
from app.services.crypto.ton_client import JettonTransfer
from app.models.deposit_request import DepositRequest, DepositRequestStatus


class TestTonDepositMonitor:
    """Test cases for TonDepositMonitor."""

    @pytest.fixture
    def mock_db_factory(self):
        """Create mock DB session factory."""
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        return lambda: mock_session

    @pytest.fixture
    def mock_ton_client(self):
        """Create mock TON client."""
        client = AsyncMock()
        client.get_jetton_transfers = AsyncMock(return_value=[])
        client.close = AsyncMock()
        return client

    @pytest.fixture
    def monitor(self, mock_db_factory, mock_ton_client):
        """Create monitor instance."""
        return TonDepositMonitor(
            db_session_factory=mock_db_factory,
            ton_client=mock_ton_client,
            polling_interval=1,
            amount_tolerance=0.005,
        )

    def test_init(self, monitor):
        """Test monitor initialization."""
        assert monitor.polling_interval == 1
        assert monitor.amount_tolerance == 0.005
        assert monitor._running is False

    def test_set_callbacks(self, monitor):
        """Test setting callbacks."""
        on_confirmed = AsyncMock()
        on_expired = AsyncMock()
        
        monitor.set_callbacks(on_confirmed=on_confirmed, on_expired=on_expired)
        
        assert monitor._on_deposit_confirmed == on_confirmed
        assert monitor._on_deposit_expired == on_expired

    def test_stop_polling(self, monitor):
        """Test stop_polling sets flag."""
        monitor._running = True
        monitor.stop_polling()
        assert monitor._running is False


class TestMatchDeposit:
    """Test match_deposit method."""

    @pytest.fixture
    def monitor(self):
        """Create monitor for matching tests."""
        monitor = TonDepositMonitor.__new__(TonDepositMonitor)
        monitor.amount_tolerance = 0.005
        return monitor

    @pytest.fixture
    def mock_request(self):
        """Create mock deposit request."""
        request = MagicMock()
        request.memo = "user_123_test"
        request.calculated_usdt = Decimal("68.027")
        request.is_expired = False
        return request

    @pytest.fixture
    def mock_transfer(self):
        """Create mock Jetton transfer."""
        return JettonTransfer(
            tx_hash="tx123",
            sender="EQSender",
            recipient="EQRecipient",
            amount=Decimal("68.027"),
            memo="user_123_test",
            timestamp=datetime.now(),
            lt=12345,
        )

    def test_match_exact_amount(self, monitor, mock_request, mock_transfer):
        """Test matching with exact amount."""
        result = monitor.match_deposit(mock_request, mock_transfer)
        
        assert result["matched"] is True
        assert result["reason"] == "ok"

    def test_match_with_tolerance(self, monitor, mock_request):
        """Test matching within tolerance."""
        transfer = JettonTransfer(
            tx_hash="tx123",
            sender="EQSender",
            recipient="EQRecipient",
            amount=Decimal("67.8"),  # Slightly less but within 0.5%
            memo="user_123_test",
            timestamp=datetime.now(),
            lt=12345,
        )
        
        result = monitor.match_deposit(mock_request, transfer)
        
        assert result["matched"] is True

    def test_match_amount_too_low(self, monitor, mock_request):
        """Test rejection when amount too low."""
        transfer = JettonTransfer(
            tx_hash="tx123",
            sender="EQSender",
            recipient="EQRecipient",
            amount=Decimal("60.0"),  # Too low
            memo="user_123_test",
            timestamp=datetime.now(),
            lt=12345,
        )
        
        result = monitor.match_deposit(mock_request, transfer)
        
        assert result["matched"] is False
        assert "amount_too_low" in result["reason"]

    def test_match_expired_request(self, monitor, mock_transfer):
        """Test rejection when request expired."""
        request = MagicMock()
        request.memo = "user_123_test"
        request.calculated_usdt = Decimal("68.027")
        request.is_expired = True
        
        result = monitor.match_deposit(request, mock_transfer)
        
        assert result["matched"] is False
        assert result["reason"] == "request_expired"

    def test_match_memo_mismatch(self, monitor, mock_request):
        """Test rejection when memo doesn't match."""
        transfer = JettonTransfer(
            tx_hash="tx123",
            sender="EQSender",
            recipient="EQRecipient",
            amount=Decimal("68.027"),
            memo="different_memo",
            timestamp=datetime.now(),
            lt=12345,
        )
        
        result = monitor.match_deposit(mock_request, transfer)
        
        assert result["matched"] is False
        assert result["reason"] == "memo_mismatch"

    def test_match_overpayment_accepted(self, monitor, mock_request):
        """Test that overpayment is accepted."""
        transfer = JettonTransfer(
            tx_hash="tx123",
            sender="EQSender",
            recipient="EQRecipient",
            amount=Decimal("100.0"),  # More than expected
            memo="user_123_test",
            timestamp=datetime.now(),
            lt=12345,
        )
        
        result = monitor.match_deposit(mock_request, transfer)
        
        assert result["matched"] is True


class TestCheckNewDeposits:
    """Test check_new_deposits method."""

    @pytest.fixture
    def mock_db_factory(self):
        """Create mock DB session factory."""
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        return lambda: mock_session

    @pytest.mark.asyncio
    async def test_check_new_deposits_no_transfers(self, mock_db_factory):
        """Test when no new transfers."""
        mock_client = AsyncMock()
        mock_client.get_jetton_transfers = AsyncMock(return_value=[])
        
        monitor = TonDepositMonitor(
            db_session_factory=mock_db_factory,
            ton_client=mock_client,
        )
        
        await monitor.check_new_deposits()
        
        mock_client.get_jetton_transfers.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_new_deposits_updates_last_lt(self, mock_db_factory):
        """Test that last_lt is updated."""
        transfers = [
            JettonTransfer(
                tx_hash="tx1",
                sender="S",
                recipient="R",
                amount=Decimal("10"),
                memo=None,
                timestamp=datetime.now(),
                lt=100,
            ),
            JettonTransfer(
                tx_hash="tx2",
                sender="S",
                recipient="R",
                amount=Decimal("20"),
                memo=None,
                timestamp=datetime.now(),
                lt=200,
            ),
        ]
        
        mock_client = AsyncMock()
        mock_client.get_jetton_transfers = AsyncMock(return_value=transfers)
        
        monitor = TonDepositMonitor(
            db_session_factory=mock_db_factory,
            ton_client=mock_client,
        )
        
        await monitor.check_new_deposits()
        
        assert monitor._last_lt == 200


class TestClose:
    """Test close method."""

    @pytest.mark.asyncio
    async def test_close_stops_and_closes_client(self):
        """Test close stops polling and closes client."""
        mock_client = AsyncMock()
        mock_client.close = AsyncMock()
        
        monitor = TonDepositMonitor(
            db_session_factory=lambda: AsyncMock(),
            ton_client=mock_client,
        )
        monitor._running = True
        
        await monitor.close()
        
        assert monitor._running is False
        mock_client.close.assert_called_once()


class TestConsecutiveErrors:
    """Test consecutive error handling and alerts."""

    @pytest.fixture
    def mock_db_factory(self):
        """Create mock DB session factory."""
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        return lambda: mock_session

    @pytest.fixture
    def mock_ton_client(self):
        """Create mock TON client."""
        client = AsyncMock()
        client.get_jetton_transfers = AsyncMock(return_value=[])
        client.close = AsyncMock()
        return client

    def test_initial_error_count_is_zero(self, mock_db_factory, mock_ton_client):
        """Test that initial consecutive error count is zero."""
        monitor = TonDepositMonitor(
            db_session_factory=mock_db_factory,
            ton_client=mock_ton_client,
        )
        
        assert monitor.consecutive_errors == 0
        assert monitor.is_healthy is True

    def test_custom_error_threshold(self, mock_db_factory, mock_ton_client):
        """Test custom consecutive error threshold."""
        monitor = TonDepositMonitor(
            db_session_factory=mock_db_factory,
            ton_client=mock_ton_client,
            consecutive_error_threshold=3,
        )
        
        assert monitor.consecutive_error_threshold == 3

    @pytest.mark.asyncio
    async def test_error_counter_increments(self, mock_db_factory, mock_ton_client):
        """Test that error counter increments on polling error."""
        monitor = TonDepositMonitor(
            db_session_factory=mock_db_factory,
            ton_client=mock_ton_client,
            consecutive_error_threshold=5,
        )
        
        # Simulate error handling
        await monitor._handle_polling_error(Exception("Test error"))
        
        assert monitor.consecutive_errors == 1
        assert monitor.is_healthy is True

    @pytest.mark.asyncio
    async def test_error_counter_resets_on_success(self, mock_db_factory, mock_ton_client):
        """Test that error counter resets after successful poll."""
        monitor = TonDepositMonitor(
            db_session_factory=mock_db_factory,
            ton_client=mock_ton_client,
        )
        
        # Simulate some errors
        monitor._consecutive_errors = 3
        
        # Reset on success
        monitor._reset_error_counter()
        
        assert monitor.consecutive_errors == 0
        assert monitor._alert_sent is False

    @pytest.mark.asyncio
    async def test_alert_triggered_at_threshold(self, mock_db_factory, mock_ton_client):
        """Test that alert is triggered when threshold is reached."""
        alert_callback = AsyncMock()
        
        monitor = TonDepositMonitor(
            db_session_factory=mock_db_factory,
            ton_client=mock_ton_client,
            consecutive_error_threshold=3,
        )
        monitor.set_callbacks(on_polling_error_alert=alert_callback)
        
        # Simulate errors up to threshold
        for i in range(3):
            await monitor._handle_polling_error(Exception(f"Error {i+1}"))
        
        # Alert should be called once
        alert_callback.assert_called_once()
        assert monitor._alert_sent is True

    @pytest.mark.asyncio
    async def test_alert_not_duplicated(self, mock_db_factory, mock_ton_client):
        """Test that alert is not sent multiple times."""
        alert_callback = AsyncMock()
        
        monitor = TonDepositMonitor(
            db_session_factory=mock_db_factory,
            ton_client=mock_ton_client,
            consecutive_error_threshold=2,
        )
        monitor.set_callbacks(on_polling_error_alert=alert_callback)
        
        # Simulate many errors
        for i in range(5):
            await monitor._handle_polling_error(Exception(f"Error {i+1}"))
        
        # Alert should only be called once
        assert alert_callback.call_count == 1

    @pytest.mark.asyncio
    async def test_alert_callback_error_handled(self, mock_db_factory, mock_ton_client):
        """Test that errors in alert callback are handled gracefully."""
        alert_callback = AsyncMock(side_effect=Exception("Callback error"))
        
        monitor = TonDepositMonitor(
            db_session_factory=mock_db_factory,
            ton_client=mock_ton_client,
            consecutive_error_threshold=1,
        )
        monitor.set_callbacks(on_polling_error_alert=alert_callback)
        
        # Should not raise even if callback fails
        await monitor._handle_polling_error(Exception("Test error"))
        
        assert monitor._consecutive_errors == 1

    def test_is_healthy_false_at_threshold(self, mock_db_factory, mock_ton_client):
        """Test is_healthy returns False when at or above threshold."""
        monitor = TonDepositMonitor(
            db_session_factory=mock_db_factory,
            ton_client=mock_ton_client,
            consecutive_error_threshold=3,
        )
        
        monitor._consecutive_errors = 3
        assert monitor.is_healthy is False
        
        monitor._consecutive_errors = 5
        assert monitor.is_healthy is False

    def test_set_polling_error_callback(self, mock_db_factory, mock_ton_client):
        """Test setting polling error alert callback."""
        monitor = TonDepositMonitor(
            db_session_factory=mock_db_factory,
            ton_client=mock_ton_client,
        )
        
        callback = AsyncMock()
        monitor.set_callbacks(on_polling_error_alert=callback)
        
        assert monitor._on_polling_error_alert == callback
