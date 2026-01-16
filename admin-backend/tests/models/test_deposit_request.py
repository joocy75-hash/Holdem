"""Tests for DepositRequest model state transitions."""

import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from app.models.deposit_request import (
    DepositRequest,
    DepositRequestStatus,
    InvalidStateTransitionError,
)


class TestDepositRequestStateTransitions:
    """Test state transition methods."""

    def _create_pending_request(self) -> DepositRequest:
        """Create a pending deposit request for testing."""
        return DepositRequest(
            user_id="test-user-123",
            requested_krw=10000,
            calculated_usdt=Decimal("7.50"),
            exchange_rate=Decimal("1333.33"),
            memo="TEST123",
            qr_data="ton://transfer/...",
            status=DepositRequestStatus.PENDING,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        )

    def test_confirm_from_pending(self):
        """Test confirming a pending request."""
        request = self._create_pending_request()
        
        request.confirm(tx_hash="abc123def456")
        
        assert request.status == DepositRequestStatus.CONFIRMED
        assert request.tx_hash == "abc123def456"
        assert request.confirmed_at is not None
        assert request.is_confirmed is True
        assert request.is_terminal is True

    def test_confirm_requires_tx_hash(self):
        """Test that confirm requires a tx_hash."""
        request = self._create_pending_request()
        
        with pytest.raises(ValueError, match="tx_hash is required"):
            request.confirm(tx_hash="")
        
        with pytest.raises(ValueError, match="tx_hash is required"):
            request.confirm(tx_hash="   ")

    def test_confirm_strips_tx_hash(self):
        """Test that tx_hash is stripped of whitespace."""
        request = self._create_pending_request()
        
        request.confirm(tx_hash="  abc123  ")
        
        assert request.tx_hash == "abc123"

    def test_expire_from_pending(self):
        """Test expiring a pending request."""
        request = self._create_pending_request()
        
        request.expire()
        
        assert request.status == DepositRequestStatus.EXPIRED
        assert request.is_terminal is True

    def test_cancel_from_pending(self):
        """Test cancelling a pending request."""
        request = self._create_pending_request()
        
        request.cancel()
        
        assert request.status == DepositRequestStatus.CANCELLED
        assert request.is_terminal is True

    def test_cannot_confirm_confirmed(self):
        """Test that confirmed requests cannot be confirmed again."""
        request = self._create_pending_request()
        request.confirm(tx_hash="abc123")
        
        with pytest.raises(InvalidStateTransitionError):
            request.confirm(tx_hash="def456")

    def test_cannot_expire_confirmed(self):
        """Test that confirmed requests cannot be expired."""
        request = self._create_pending_request()
        request.confirm(tx_hash="abc123")
        
        with pytest.raises(InvalidStateTransitionError):
            request.expire()

    def test_cannot_cancel_confirmed(self):
        """Test that confirmed requests cannot be cancelled."""
        request = self._create_pending_request()
        request.confirm(tx_hash="abc123")
        
        with pytest.raises(InvalidStateTransitionError):
            request.cancel()

    def test_cannot_confirm_expired(self):
        """Test that expired requests cannot be confirmed."""
        request = self._create_pending_request()
        request.expire()
        
        with pytest.raises(InvalidStateTransitionError):
            request.confirm(tx_hash="abc123")

    def test_cannot_confirm_cancelled(self):
        """Test that cancelled requests cannot be confirmed."""
        request = self._create_pending_request()
        request.cancel()
        
        with pytest.raises(InvalidStateTransitionError):
            request.confirm(tx_hash="abc123")


class TestDepositRequestProperties:
    """Test property methods."""

    def _create_request(
        self,
        status: DepositRequestStatus = DepositRequestStatus.PENDING,
        expires_at: datetime = None,
    ) -> DepositRequest:
        """Create a deposit request for testing."""
        if expires_at is None:
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
        
        return DepositRequest(
            user_id="test-user-123",
            requested_krw=10000,
            calculated_usdt=Decimal("7.50"),
            exchange_rate=Decimal("1333.33"),
            memo="TEST123",
            qr_data="ton://transfer/...",
            status=status,
            expires_at=expires_at,
        )

    def test_is_pending(self):
        """Test is_pending property."""
        request = self._create_request(status=DepositRequestStatus.PENDING)
        assert request.is_pending is True
        
        request.expire()
        assert request.is_pending is False

    def test_is_confirmed(self):
        """Test is_confirmed property."""
        request = self._create_request(status=DepositRequestStatus.PENDING)
        assert request.is_confirmed is False
        
        request.confirm(tx_hash="abc123")
        assert request.is_confirmed is True

    def test_is_terminal(self):
        """Test is_terminal property."""
        request = self._create_request(status=DepositRequestStatus.PENDING)
        assert request.is_terminal is False
        
        # Test all terminal states
        for status in [
            DepositRequestStatus.CONFIRMED,
            DepositRequestStatus.EXPIRED,
            DepositRequestStatus.CANCELLED,
        ]:
            request = self._create_request(status=status)
            assert request.is_terminal is True

    def test_is_expired_by_status(self):
        """Test is_expired returns True for EXPIRED status."""
        request = self._create_request(status=DepositRequestStatus.EXPIRED)
        assert request.is_expired is True

    def test_is_expired_by_time(self):
        """Test is_expired returns True when time has passed."""
        past_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        request = self._create_request(expires_at=past_time)
        assert request.is_expired is True

    def test_is_not_expired(self):
        """Test is_expired returns False when not expired."""
        future_time = datetime.now(timezone.utc) + timedelta(minutes=30)
        request = self._create_request(expires_at=future_time)
        assert request.is_expired is False

    def test_remaining_seconds_positive(self):
        """Test remaining_seconds returns positive value."""
        future_time = datetime.now(timezone.utc) + timedelta(minutes=5)
        request = self._create_request(expires_at=future_time)
        
        remaining = request.remaining_seconds
        assert 290 <= remaining <= 300  # ~5 minutes

    def test_remaining_seconds_zero_when_expired(self):
        """Test remaining_seconds returns 0 when expired."""
        past_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        request = self._create_request(expires_at=past_time)
        
        assert request.remaining_seconds == 0

    def test_remaining_seconds_handles_naive_datetime(self):
        """Test remaining_seconds handles naive datetime in expires_at."""
        # Create with naive datetime (no timezone)
        naive_future = datetime.utcnow() + timedelta(minutes=5)
        request = self._create_request()
        request.expires_at = naive_future
        
        # Should not raise and should return reasonable value
        remaining = request.remaining_seconds
        assert remaining >= 0
