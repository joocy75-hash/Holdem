"""Unit tests for DepositProcessor."""

import pytest
from decimal import Decimal
from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.crypto.deposit_processor import (
    DepositProcessor,
    DepositProcessorError,
)
from app.models.deposit_request import DepositRequest, DepositRequestStatus


class TestDepositProcessor:
    """Test cases for DepositProcessor."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        return db

    @pytest.fixture
    def processor(self, mock_db):
        """Create processor instance."""
        return DepositProcessor(
            admin_db=mock_db,
            main_api_url="http://localhost:8000",
            main_api_key="test-key",
        )

    @pytest.fixture
    def mock_request(self):
        """Create mock deposit request."""
        request = MagicMock(spec=DepositRequest)
        request.id = uuid4()
        request.user_id = "user_123"
        request.memo = "user_123_test"
        request.requested_krw = 100000
        request.calculated_usdt = Decimal("68.027")
        request.exchange_rate = Decimal("1470.54")
        request.status = DepositRequestStatus.PENDING
        return request

    def test_init(self, processor):
        """Test processor initialization."""
        assert processor.main_api_url == "http://localhost:8000"
        assert processor.main_api_key == "test-key"

    @pytest.mark.asyncio
    async def test_close(self, processor):
        """Test closing HTTP client."""
        processor._http_client = AsyncMock()
        processor._http_client.is_closed = False
        
        await processor.close()
        
        processor._http_client.aclose.assert_called_once()


class TestProcessDeposit:
    """Test process_deposit method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        return db

    @pytest.fixture
    def processor(self, mock_db):
        """Create processor instance."""
        return DepositProcessor(admin_db=mock_db)

    @pytest.fixture
    def mock_request(self):
        """Create mock deposit request."""
        request = MagicMock(spec=DepositRequest)
        request.id = uuid4()
        request.user_id = "user_123"
        request.memo = "user_123_test"
        request.requested_krw = 100000
        request.calculated_usdt = Decimal("68.027")
        request.exchange_rate = Decimal("1470.54")
        request.status = DepositRequestStatus.PENDING
        return request

    @pytest.mark.asyncio
    async def test_process_already_confirmed(self, processor, mock_request):
        """Test processing already confirmed deposit."""
        mock_request.status = DepositRequestStatus.CONFIRMED
        
        result = await processor.process_deposit(mock_request, "tx123")
        
        assert result == mock_request
        processor.admin_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_expired_raises_error(self, processor, mock_request):
        """Test processing expired deposit raises error."""
        mock_request.status = DepositRequestStatus.EXPIRED
        
        with pytest.raises(DepositProcessorError) as exc_info:
            await processor.process_deposit(mock_request, "tx123")
        
        assert "expired" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_process_success(self, processor, mock_request, mock_db):
        """Test successful deposit processing."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        with patch.object(processor, "credit_balance", new_callable=AsyncMock) as mock_credit:
            mock_credit.return_value = True
            
            with patch("app.services.crypto.deposit_processor.AuditLog"):
                result = await processor.process_deposit(mock_request, "tx123")
                
                mock_credit.assert_called_once()
                assert mock_request.status == DepositRequestStatus.CONFIRMED
                assert mock_request.tx_hash == "tx123"
                mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_rollback_on_error(self, processor, mock_request, mock_db):
        """Test rollback on processing error."""
        with patch.object(
            processor, "credit_balance", new_callable=AsyncMock
        ) as mock_credit:
            mock_credit.side_effect = Exception("API error")
            
            with pytest.raises(DepositProcessorError):
                await processor.process_deposit(mock_request, "tx123")
            
            mock_db.rollback.assert_called_once()


class TestCreditBalance:
    """Test credit_balance method."""

    @pytest.fixture
    def processor(self):
        """Create processor instance."""
        return DepositProcessor(
            admin_db=AsyncMock(),
            main_api_url="http://localhost:8000",
        )

    @pytest.mark.asyncio
    async def test_credit_success(self, processor):
        """Test successful balance credit."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        with patch.object(processor, "_get_http_client") as mock_get_client:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_http
            
            result = await processor.credit_balance(
                user_id="user_123",
                amount_krw=100000,
                memo="test_memo",
                tx_hash="tx123",
            )
            
            assert result is True
            mock_http.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_credit_api_error(self, processor):
        """Test balance credit with API error."""
        from app.services.crypto.deposit_processor import BalanceCreditError
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"detail": "Internal error"}
        
        with patch.object(processor, "_get_http_client") as mock_get_client:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_http
            
            with pytest.raises(BalanceCreditError):
                await processor.credit_balance(
                    user_id="user_123",
                    amount_krw=100000,
                    memo="test_memo",
                    tx_hash="tx123",
                )


class TestManualApprove:
    """Test manual_approve method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        return db

    @pytest.fixture
    def processor(self, mock_db):
        """Create processor instance."""
        return DepositProcessor(admin_db=mock_db)

    @pytest.fixture
    def mock_request(self):
        """Create mock deposit request."""
        request = MagicMock(spec=DepositRequest)
        request.id = uuid4()
        request.user_id = "user_123"
        request.memo = "user_123_test"
        request.requested_krw = 100000
        request.status = DepositRequestStatus.PENDING
        return request

    @pytest.mark.asyncio
    async def test_manual_approve_not_found(self, processor):
        """Test manual approve with non-existent deposit."""
        with patch.object(
            processor, "get_deposit_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = None
            
            with pytest.raises(DepositProcessorError) as exc_info:
                await processor.manual_approve(uuid4(), "admin_1")
            
            assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_manual_approve_wrong_status(self, processor, mock_request):
        """Test manual approve with wrong status."""
        mock_request.status = DepositRequestStatus.CONFIRMED
        
        with patch.object(
            processor, "get_deposit_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_request
            
            with pytest.raises(DepositProcessorError) as exc_info:
                await processor.manual_approve(mock_request.id, "admin_1")
            
            assert "status" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_manual_approve_success(self, processor, mock_request, mock_db):
        """Test successful manual approval with tx_hash."""
        with patch.object(
            processor, "get_deposit_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_request
            
            with patch.object(
                processor, "credit_balance", new_callable=AsyncMock
            ) as mock_credit:
                mock_credit.return_value = True
                
                with patch("app.services.crypto.deposit_processor.AuditLog"):
                    result = await processor.manual_approve(
                        mock_request.id, "admin_1", 
                        tx_hash="0x123abc456def",
                        notes="Manual approval"
                    )
                    
                    assert result.status == DepositRequestStatus.CONFIRMED
                    mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_manual_approve_requires_tx_hash(self, processor, mock_request, mock_db):
        """Test manual approval requires tx_hash by default."""
        with patch.object(
            processor, "get_deposit_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_request
            
            with pytest.raises(DepositProcessorError, match="tx_hash.*required"):
                await processor.manual_approve(
                    mock_request.id, "admin_1", notes="Manual approval"
                )
    
    @pytest.mark.asyncio
    async def test_manual_approve_skip_tx_verification(self, processor, mock_request, mock_db):
        """Test manual approval with skip_tx_verification flag."""
        with patch.object(
            processor, "get_deposit_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_request
            
            with patch.object(
                processor, "credit_balance", new_callable=AsyncMock
            ) as mock_credit:
                mock_credit.return_value = True
                
                with patch("app.services.crypto.deposit_processor.AuditLog"):
                    result = await processor.manual_approve(
                        mock_request.id, "admin_1",
                        skip_tx_verification=True,
                        notes="Emergency approval"
                    )
                    
                    assert result.status == DepositRequestStatus.CONFIRMED
                    assert "manual_no_tx" in result.tx_hash


class TestManualReject:
    """Test manual_reject method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        return db

    @pytest.fixture
    def processor(self, mock_db):
        """Create processor instance."""
        return DepositProcessor(admin_db=mock_db)

    @pytest.fixture
    def mock_request(self):
        """Create mock deposit request."""
        request = MagicMock(spec=DepositRequest)
        request.id = uuid4()
        request.user_id = "user_123"
        request.memo = "user_123_test"
        request.requested_krw = 100000
        request.status = DepositRequestStatus.PENDING
        return request

    @pytest.mark.asyncio
    async def test_manual_reject_success(self, processor, mock_request, mock_db):
        """Test successful manual rejection."""
        with patch.object(
            processor, "get_deposit_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_request
            
            with patch("app.services.crypto.deposit_processor.AuditLog"):
                result = await processor.manual_reject(
                    mock_request.id, "admin_1", "Invalid deposit"
                )
                
                assert result.status == DepositRequestStatus.CANCELLED
                mock_db.commit.assert_called_once()
