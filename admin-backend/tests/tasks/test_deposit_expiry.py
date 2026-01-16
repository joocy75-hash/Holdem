"""Tests for deposit expiry task."""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.tasks.deposit_expiry import (
    DepositExpiryTask,
    check_expired_deposits,
    get_expiring_soon_deposits,
)
from app.models.deposit_request import DepositRequest, DepositRequestStatus


class TestDepositExpiryTask:
    """Tests for DepositExpiryTask class."""
    
    def test_init_default_values(self):
        """Test initialization with default values."""
        db_factory = MagicMock()
        task = DepositExpiryTask(db_factory)
        
        assert task.db_session_factory == db_factory
        assert task.check_interval == 60
        assert task._on_expired is None
        assert task._running is False
    
    def test_init_custom_values(self):
        """Test initialization with custom values."""
        db_factory = MagicMock()
        callback = AsyncMock()
        
        task = DepositExpiryTask(
            db_factory,
            check_interval=30,
            on_expired=callback,
        )
        
        assert task.check_interval == 30
        assert task._on_expired == callback
    
    def test_set_expired_callback(self):
        """Test setting expired callback."""
        db_factory = MagicMock()
        task = DepositExpiryTask(db_factory)
        
        callback = AsyncMock()
        task.set_expired_callback(callback)
        
        assert task._on_expired == callback
    
    def test_stop(self):
        """Test stop method."""
        db_factory = MagicMock()
        task = DepositExpiryTask(db_factory)
        task._running = True
        
        task.stop()
        
        assert task._running is False


class TestCheckExpiredDeposits:
    """Tests for check_expired_deposits function."""
    
    @pytest.mark.asyncio
    async def test_no_expired_requests(self):
        """Test when there are no expired requests."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result
        
        count = await check_expired_deposits(mock_db)
        
        assert count == 0
        mock_db.commit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_marks_expired_requests(self):
        """Test marking expired requests."""
        # Create mock expired request
        expired_request = MagicMock(spec=DepositRequest)
        expired_request.memo = "test_memo"
        expired_request.requested_krw = 100000
        expired_request.calculated_usdt = Decimal("68.03")
        expired_request.status = DepositRequestStatus.PENDING
        
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [expired_request]
        mock_db.execute.return_value = mock_result
        
        count = await check_expired_deposits(mock_db)
        
        assert count == 1
        assert expired_request.status == DepositRequestStatus.EXPIRED
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_calls_callback_for_each_expired(self):
        """Test callback is called for each expired request."""
        # Create mock expired requests
        expired1 = MagicMock(spec=DepositRequest)
        expired1.memo = "memo1"
        expired1.requested_krw = 100000
        expired1.calculated_usdt = Decimal("68.03")
        
        expired2 = MagicMock(spec=DepositRequest)
        expired2.memo = "memo2"
        expired2.requested_krw = 200000
        expired2.calculated_usdt = Decimal("136.06")
        
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [expired1, expired2]
        mock_db.execute.return_value = mock_result
        
        callback = AsyncMock()
        
        count = await check_expired_deposits(mock_db, on_expired=callback)
        
        assert count == 2
        assert callback.call_count == 2
        callback.assert_any_call(expired1)
        callback.assert_any_call(expired2)
    
    @pytest.mark.asyncio
    async def test_callback_error_does_not_stop_processing(self):
        """Test that callback errors don't stop processing."""
        expired1 = MagicMock(spec=DepositRequest)
        expired1.memo = "memo1"
        expired1.requested_krw = 100000
        expired1.calculated_usdt = Decimal("68.03")
        
        expired2 = MagicMock(spec=DepositRequest)
        expired2.memo = "memo2"
        expired2.requested_krw = 200000
        expired2.calculated_usdt = Decimal("136.06")
        
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [expired1, expired2]
        mock_db.execute.return_value = mock_result
        
        # Callback raises error on first call
        callback = AsyncMock(side_effect=[Exception("Test error"), None])
        
        count = await check_expired_deposits(mock_db, on_expired=callback)
        
        # Both should still be marked as expired
        assert count == 2
        assert expired1.status == DepositRequestStatus.EXPIRED
        assert expired2.status == DepositRequestStatus.EXPIRED


class TestGetExpiringSoonDeposits:
    """Tests for get_expiring_soon_deposits function."""
    
    @pytest.mark.asyncio
    async def test_returns_expiring_soon_requests(self):
        """Test returning requests expiring soon."""
        expiring_request = MagicMock(spec=DepositRequest)
        expiring_request.memo = "expiring_memo"
        
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [expiring_request]
        mock_db.execute.return_value = mock_result
        
        result = await get_expiring_soon_deposits(mock_db, minutes_threshold=5)
        
        assert len(result) == 1
        assert result[0] == expiring_request
    
    @pytest.mark.asyncio
    async def test_empty_when_no_expiring_requests(self):
        """Test empty result when no requests expiring soon."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result
        
        result = await get_expiring_soon_deposits(mock_db)
        
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_custom_threshold(self):
        """Test with custom minutes threshold."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result
        
        await get_expiring_soon_deposits(mock_db, minutes_threshold=10)
        
        # Verify execute was called (query was made)
        mock_db.execute.assert_called_once()
