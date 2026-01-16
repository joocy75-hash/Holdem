"""Tests for admin TON deposit API."""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.api.admin_ton_deposit import (
    DepositListItem,
    DepositListResponse,
    DepositDetailResponse,
    DepositStatsResponse,
    ManualApproveRequest,
    ManualRejectRequest,
)
from app.models.deposit_request import DepositRequestStatus


class TestSchemas:
    """Tests for API schemas."""
    
    def test_deposit_list_item_schema(self):
        """Test DepositListItem schema."""
        item = DepositListItem(
            id=uuid4(),
            user_id="test-user",
            telegram_id=123456789,
            requested_krw=100000,
            calculated_usdt=Decimal("68.03"),
            exchange_rate=Decimal("1470.54"),
            memo="test_memo",
            status="pending",
            expires_at=datetime.utcnow() + timedelta(minutes=30),
            created_at=datetime.utcnow(),
            confirmed_at=None,
            tx_hash=None,
        )
        
        assert item.user_id == "test-user"
        assert item.requested_krw == 100000
        assert item.status == "pending"
    
    def test_deposit_list_response_schema(self):
        """Test DepositListResponse schema."""
        response = DepositListResponse(
            items=[],
            total=0,
            page=1,
            page_size=20,
            total_pages=0,
        )
        
        assert response.total == 0
        assert response.page == 1
    
    def test_deposit_stats_response_schema(self):
        """Test DepositStatsResponse schema."""
        stats = DepositStatsResponse(
            total_pending=5,
            total_confirmed=100,
            total_expired=10,
            total_cancelled=2,
            total_usdt_confirmed=Decimal("5000.00"),
            total_krw_confirmed=7500000,
            today_confirmed_count=3,
            today_confirmed_usdt=Decimal("200.00"),
        )
        
        assert stats.total_pending == 5
        assert stats.total_confirmed == 100
        assert stats.total_usdt_confirmed == Decimal("5000.00")
    
    def test_manual_approve_request_schema(self):
        """Test ManualApproveRequest schema."""
        request = ManualApproveRequest(
            tx_hash="abc123def456",
            note="Manual approval",
        )
        
        assert request.tx_hash == "abc123def456"
        assert request.note == "Manual approval"
    
    def test_manual_reject_request_schema(self):
        """Test ManualRejectRequest schema."""
        request = ManualRejectRequest(
            reason="Suspicious activity",
        )
        
        assert request.reason == "Suspicious activity"


class TestDepositDetailResponse:
    """Tests for DepositDetailResponse schema."""
    
    def test_deposit_detail_response_schema(self):
        """Test DepositDetailResponse schema."""
        response = DepositDetailResponse(
            id=uuid4(),
            user_id="test-user",
            telegram_id=123456789,
            requested_krw=100000,
            calculated_usdt=Decimal("68.03"),
            exchange_rate=Decimal("1470.54"),
            memo="test_memo",
            qr_data="data:image/png;base64,abc123",
            status="pending",
            expires_at=datetime.utcnow() + timedelta(minutes=30),
            created_at=datetime.utcnow(),
            confirmed_at=None,
            tx_hash=None,
            is_expired=False,
            remaining_seconds=1800,
        )
        
        assert response.user_id == "test-user"
        assert response.is_expired is False
        assert response.remaining_seconds == 1800
    
    def test_deposit_detail_response_expired(self):
        """Test DepositDetailResponse for expired deposit."""
        response = DepositDetailResponse(
            id=uuid4(),
            user_id="test-user",
            telegram_id=None,
            requested_krw=50000,
            calculated_usdt=Decimal("34.01"),
            exchange_rate=Decimal("1470.54"),
            memo="expired_memo",
            qr_data="data:image/png;base64,xyz789",
            status="expired",
            expires_at=datetime.utcnow() - timedelta(minutes=30),
            created_at=datetime.utcnow() - timedelta(hours=1),
            confirmed_at=None,
            tx_hash=None,
            is_expired=True,
            remaining_seconds=0,
        )
        
        assert response.status == "expired"
        assert response.is_expired is True
        assert response.remaining_seconds == 0


class TestStatusEnum:
    """Tests for status enum handling."""
    
    def test_valid_status_values(self):
        """Test valid status enum values."""
        valid_statuses = ["pending", "confirmed", "expired", "cancelled"]
        
        for status in valid_statuses:
            enum_value = DepositRequestStatus(status)
            assert enum_value.value == status
    
    def test_invalid_status_raises_error(self):
        """Test invalid status raises ValueError."""
        with pytest.raises(ValueError):
            DepositRequestStatus("invalid_status")
