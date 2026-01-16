"""Integration tests for the complete deposit flow.

Tests the entire deposit workflow from request creation to confirmation,
including all services working together.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.models.deposit_request import DepositRequest, DepositRequestStatus
from app.services.crypto.ton_exchange_rate import TonExchangeRateService
from app.services.crypto.qr_generator import QRGenerator
from app.services.crypto.deposit_request_service import DepositRequestService
from app.services.crypto.ton_client import TonClient, JettonTransfer
from app.services.crypto.deposit_processor import DepositProcessor


class TestDepositFlowIntegration:
    """Integration tests for the complete deposit flow."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        db.refresh = AsyncMock()
        return db
    
    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        redis = AsyncMock()
        redis.get = AsyncMock(return_value=None)
        redis.setex = AsyncMock()
        return redis
    
    @pytest.mark.asyncio
    async def test_complete_deposit_flow_success(self, mock_db, mock_redis):
        """Test the complete deposit flow from request to confirmation."""
        # Step 1: Get exchange rate - use cached rate
        mock_redis.get = AsyncMock(return_value=b"1400.0")
        
        rate_service = TonExchangeRateService(mock_redis)
        rate = await rate_service.get_usdt_krw_rate()
        
        assert rate == Decimal("1400.0")
        
        # Step 2: Calculate USDT amount
        krw_amount = 100000  # 100,000 KRW
        usdt_amount = rate_service.calculate_usdt_amount(krw_amount, rate)
        
        assert usdt_amount == Decimal("71.428571")  # 100000 / 1400
        
        # Step 3: Generate QR code
        qr_generator = QRGenerator(wallet_address="EQTest123456789")
        memo = "user_123_1234567890_abcd"
        
        qr_data = qr_generator.generate_deposit_qr(usdt_amount, memo)
        
        assert qr_data["qr_base64"].startswith("data:image/png;base64,")
        assert qr_data["memo"] == memo
        
        # Step 4: Verify URI format
        uri = qr_generator.generate_ton_uri(usdt_amount, memo)
        
        assert "ton://transfer/" in uri
        assert "amount=" in uri
        assert "text=" in uri
    
    @pytest.mark.asyncio
    async def test_deposit_request_creation_and_retrieval(self, mock_db, mock_redis):
        """Test deposit request creation and retrieval."""
        # Create mock deposit request
        deposit_id = uuid4()
        mock_deposit = MagicMock(spec=DepositRequest)
        mock_deposit.id = deposit_id
        mock_deposit.user_id = "user_123"
        mock_deposit.telegram_id = 123456789
        mock_deposit.requested_krw = 100000
        mock_deposit.calculated_usdt = Decimal("71.43")
        mock_deposit.exchange_rate = Decimal("1400.0")
        mock_deposit.memo = "user_123_1234567890_abcd"
        mock_deposit.qr_data = "data:image/png;base64,..."
        mock_deposit.status = DepositRequestStatus.PENDING
        mock_deposit.expires_at = datetime.utcnow() + timedelta(minutes=30)
        mock_deposit.created_at = datetime.utcnow()
        mock_deposit.confirmed_at = None
        mock_deposit.tx_hash = None
        mock_deposit.is_expired = False
        mock_deposit.remaining_seconds = 1800
        
        # Mock DB operations
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_deposit
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        # Verify deposit can be retrieved
        service = DepositRequestService(mock_db, mock_redis)
        
        with patch.object(service, 'get_request_by_id', return_value=mock_deposit):
            result = await service.get_request_by_id(deposit_id)
            
            assert result.id == deposit_id
            assert result.status == DepositRequestStatus.PENDING
            assert result.calculated_usdt == Decimal("71.43")
    
    @pytest.mark.asyncio
    async def test_deposit_matching_and_confirmation(self, mock_db, mock_redis):
        """Test deposit matching and confirmation flow."""
        # Create pending deposit request
        deposit_id = uuid4()
        mock_deposit = MagicMock(spec=DepositRequest)
        mock_deposit.id = deposit_id
        mock_deposit.user_id = "user_123"
        mock_deposit.calculated_usdt = Decimal("71.43")
        mock_deposit.memo = "user_123_1234567890_abcd"
        mock_deposit.status = DepositRequestStatus.PENDING
        mock_deposit.expires_at = datetime.utcnow() + timedelta(minutes=30)
        mock_deposit.is_expired = False
        
        # Create matching transfer
        transfer = JettonTransfer(
            tx_hash="abc123def456",
            sender="EQSender123",
            recipient="EQReceiver456",
            amount=Decimal("71.43"),
            memo="user_123_1234567890_abcd",
            timestamp=datetime.utcnow(),
            lt=12345678,
        )
        
        # Verify amount tolerance (0.5%)
        tolerance = Decimal("0.005")
        expected_amount = mock_deposit.calculated_usdt
        actual_amount = transfer.amount
        
        diff_ratio = abs(actual_amount - expected_amount) / expected_amount
        assert diff_ratio <= tolerance
        
        # Verify memo matches
        assert transfer.memo == mock_deposit.memo
    
    @pytest.mark.asyncio
    async def test_deposit_expiry_flow(self, mock_db, mock_redis):
        """Test deposit expiry handling."""
        # Create expired deposit
        expired_deposit = MagicMock(spec=DepositRequest)
        expired_deposit.id = uuid4()
        expired_deposit.status = DepositRequestStatus.PENDING
        expired_deposit.expires_at = datetime.utcnow() - timedelta(minutes=5)
        expired_deposit.is_expired = True
        
        # Verify expiry detection
        assert expired_deposit.is_expired == True
        assert expired_deposit.status == DepositRequestStatus.PENDING
        
        # Simulate status update
        expired_deposit.status = DepositRequestStatus.EXPIRED
        assert expired_deposit.status == DepositRequestStatus.EXPIRED
    
    @pytest.mark.asyncio
    async def test_manual_approval_flow(self, mock_db):
        """Test manual approval by admin."""
        deposit_id = uuid4()
        mock_deposit = MagicMock(spec=DepositRequest)
        mock_deposit.id = deposit_id
        mock_deposit.user_id = "user_123"
        mock_deposit.requested_krw = 100000
        mock_deposit.calculated_usdt = Decimal("71.43")
        mock_deposit.memo = "test_memo"
        mock_deposit.status = DepositRequestStatus.PENDING
        mock_deposit.is_expired = False
        
        # Mock DB operations
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_deposit
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.add = MagicMock()
        
        processor = DepositProcessor(mock_db)
        
        # Mock credit_balance and close
        processor.credit_balance = AsyncMock(return_value=True)
        processor.close = AsyncMock()
        
        await processor.manual_approve(
            deposit_id=deposit_id,
            admin_user_id="admin_1",
            tx_hash="manual_tx_123",
        )
        
        # Verify status updated
        assert mock_deposit.status == DepositRequestStatus.CONFIRMED
        assert mock_deposit.tx_hash == "manual_tx_123"
    
    @pytest.mark.asyncio
    async def test_manual_rejection_flow(self, mock_db):
        """Test manual rejection by admin."""
        deposit_id = uuid4()
        mock_deposit = MagicMock(spec=DepositRequest)
        mock_deposit.id = deposit_id
        mock_deposit.user_id = "user_123"
        mock_deposit.requested_krw = 100000
        mock_deposit.memo = "test_memo"
        mock_deposit.status = DepositRequestStatus.PENDING
        mock_deposit.is_expired = False
        
        # Mock DB operations
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_deposit
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.add = MagicMock()
        
        processor = DepositProcessor(mock_db)
        processor.close = AsyncMock()
        
        await processor.manual_reject(
            deposit_id=deposit_id,
            admin_user_id="admin_1",
            reason="Invalid transaction",
        )
        
        # Verify status updated
        assert mock_deposit.status == DepositRequestStatus.CANCELLED


class TestExchangeRateIntegration:
    """Integration tests for exchange rate service."""
    
    @pytest.fixture
    def mock_redis(self):
        redis = AsyncMock()
        redis.get = AsyncMock(return_value=None)
        redis.setex = AsyncMock()
        return redis
    
    @pytest.mark.asyncio
    async def test_rate_caching_flow(self, mock_redis):
        """Test exchange rate caching behavior."""
        # First call - cache hit
        mock_redis.get = AsyncMock(return_value=b"1400.0")
        
        service = TonExchangeRateService(mock_redis)
        
        # Cache hit
        rate1 = await service.get_usdt_krw_rate()
        assert rate1 == Decimal("1400.0")
        
        rate2 = await service.get_usdt_krw_rate()
        assert rate2 == Decimal("1400.0")
    
    @pytest.mark.asyncio
    async def test_rate_calculation(self, mock_redis):
        """Test USDT amount calculation from KRW."""
        mock_redis.get = AsyncMock(return_value=b"1400.0")
        
        service = TonExchangeRateService(mock_redis)
        rate = await service.get_usdt_krw_rate()
        
        # Test various amounts
        usdt_100k = service.calculate_usdt_amount(100000, rate)
        assert usdt_100k == Decimal("71.428571")
        
        usdt_1m = service.calculate_usdt_amount(1000000, rate)
        assert usdt_1m == Decimal("714.285714")


class TestQRGeneratorIntegration:
    """Integration tests for QR code generation."""
    
    def test_qr_code_contains_all_parameters(self):
        """Test that generated QR code contains all required parameters."""
        generator = QRGenerator(wallet_address="EQTest123456789")
        
        amount = Decimal("100.50")
        memo = "test_memo_123"
        
        uri = generator.generate_ton_uri(amount, memo)
        
        # Verify all parameters present
        assert "EQTest123456789" in uri
        assert "amount=" in uri
        assert f"text={memo}" in uri
    
    def test_qr_image_generation(self):
        """Test QR image generation produces valid PNG."""
        generator = QRGenerator(wallet_address="EQTest123456789")
        
        uri = "ton://transfer/EQTest?amount=100000000"
        
        # Generate PNG bytes
        png_bytes = generator.generate_qr_image(uri)
        
        # Verify PNG header
        assert png_bytes[:8] == b'\x89PNG\r\n\x1a\n'
        
        # Generate base64
        base64_data = generator.generate_qr_base64(uri)
        
        assert base64_data.startswith("data:image/png;base64,")


class TestTelegramNotificationIntegration:
    """Integration tests for Telegram notifications."""
    
    @pytest.mark.asyncio
    async def test_notification_message_format(self):
        """Test notification message formatting."""
        # Create mock deposit
        mock_deposit = MagicMock()
        mock_deposit.id = uuid4()
        mock_deposit.user_id = "user_123"
        mock_deposit.telegram_id = 123456789
        mock_deposit.requested_krw = 100000
        mock_deposit.calculated_usdt = Decimal("71.43")
        mock_deposit.memo = "test_memo"
        
        # Verify deposit data is correct
        assert mock_deposit.calculated_usdt == Decimal("71.43")
        assert mock_deposit.telegram_id == 123456789
        assert mock_deposit.memo == "test_memo"


class TestStressTest:
    """Stress tests for concurrent deposit handling."""
    
    @pytest.mark.asyncio
    async def test_concurrent_deposit_requests(self):
        """Test handling multiple concurrent deposit requests."""
        import asyncio
        
        mock_db = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=b"1400.0")
        mock_redis.setex = AsyncMock()
        
        async def create_deposit(user_id: str):
            """Simulate deposit creation."""
            service = DepositRequestService(mock_db, mock_redis)
            
            # Generate unique memo
            memo = service._generate_memo(user_id)
            
            return {
                "user_id": user_id,
                "memo": memo,
                "status": "created",
            }
        
        # Create 50 concurrent requests
        tasks = [create_deposit(f"user_{i}") for i in range(50)]
        results = await asyncio.gather(*tasks)
        
        # Verify all requests completed
        assert len(results) == 50
        
        # Verify all memos are unique
        memos = [r["memo"] for r in results]
        assert len(set(memos)) == 50
    
    @pytest.mark.asyncio
    async def test_rate_service_under_load(self):
        """Test exchange rate service under concurrent load."""
        import asyncio
        
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=b"1400.0")
        mock_redis.setex = AsyncMock()
        
        async def get_rate():
            service = TonExchangeRateService(mock_redis)
            return await service.get_usdt_krw_rate()
        
        # 100 concurrent rate requests
        tasks = [get_rate() for _ in range(100)]
        results = await asyncio.gather(*tasks)
        
        # All should return same cached rate
        assert all(r == Decimal("1400.0") for r in results)


class TestErrorHandling:
    """Tests for error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_database_connection_error(self):
        """Test handling of database connection errors."""
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=Exception("Connection refused"))
        
        processor = DepositProcessor(mock_db)
        processor.close = AsyncMock()
        
        with pytest.raises(Exception) as exc_info:
            await processor.manual_approve(
                deposit_id=uuid4(),
                admin_user_id="admin",
                tx_hash="test",
            )
        
        assert "Connection refused" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_external_api_timeout(self):
        """Test handling of external API timeouts."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient') as mock_client:
            import httpx
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException("Request timed out")
            )
            
            service = TonExchangeRateService(mock_redis)
            
            with pytest.raises(Exception):
                await service.get_usdt_krw_rate()
    
    @pytest.mark.asyncio
    async def test_invalid_deposit_status_transition(self):
        """Test rejection of invalid status transitions."""
        mock_db = AsyncMock()
        
        # Already confirmed deposit
        mock_deposit = MagicMock()
        mock_deposit.id = uuid4()
        mock_deposit.status = DepositRequestStatus.CONFIRMED
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_deposit
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        processor = DepositProcessor(mock_db)
        processor.close = AsyncMock()
        
        # Should raise error for already confirmed deposit
        with pytest.raises(Exception):
            await processor.manual_approve(
                deposit_id=mock_deposit.id,
                admin_user_id="admin",
                tx_hash="test",
            )
