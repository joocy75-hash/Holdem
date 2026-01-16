"""Deposit Request Service for TON/USDT deposits.

Handles creation and management of deposit requests with unique memos.
"""

import logging
import secrets
import string
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.deposit_request import DepositRequest, DepositRequestStatus
from app.services.crypto.ton_exchange_rate import TonExchangeRateService
from app.services.crypto.qr_generator import QRGenerator

logger = logging.getLogger(__name__)
settings = get_settings()


class DepositRequestService:
    """Service for managing deposit requests.
    
    Creates deposit requests with unique memos, calculates USDT amounts
    based on real-time exchange rates, and generates QR codes.
    """
    
    def __init__(
        self,
        db: AsyncSession,
        exchange_service: Optional[TonExchangeRateService] = None,
        qr_generator: Optional[QRGenerator] = None,
    ):
        """Initialize deposit request service.
        
        Args:
            db: Database session
            exchange_service: Exchange rate service (created if not provided)
            qr_generator: QR generator (created if not provided)
        """
        self.db = db
        self.exchange_service = exchange_service or TonExchangeRateService()
        self.qr_generator = qr_generator or QRGenerator()
    
    def _generate_memo(self, user_id: str, telegram_id: Optional[int] = None) -> str:
        """Generate unique memo for deposit matching.
        
        Format: user_{user_id}_{timestamp}_{random4}
        
        Args:
            user_id: User's ID
            telegram_id: Optional Telegram ID
            
        Returns:
            str: Unique memo string
        """
        timestamp = int(datetime.utcnow().timestamp())
        random_suffix = ''.join(
            secrets.choice(string.ascii_lowercase + string.digits)
            for _ in range(4)
        )
        
        # Use telegram_id if available, otherwise user_id
        identifier = telegram_id if telegram_id else user_id[:8]
        
        return f"user_{identifier}_{timestamp}_{random_suffix}"
    
    async def create_request(
        self,
        user_id: str,
        requested_krw: int,
        telegram_id: Optional[int] = None,
    ) -> DepositRequest:
        """Create a new deposit request.
        
        Args:
            user_id: User's ID
            requested_krw: Amount in KRW (e.g., 100000)
            telegram_id: Optional Telegram ID
            
        Returns:
            DepositRequest: Created deposit request with QR data
            
        Raises:
            ExchangeRateError: If unable to fetch exchange rate
        """
        # Get current exchange rate
        rate = await self.exchange_service.get_usdt_krw_rate()
        
        # Calculate USDT amount
        calculated_usdt = self.exchange_service.calculate_usdt_amount(
            requested_krw, rate
        )
        
        # Generate unique memo
        memo = self._generate_memo(user_id, telegram_id)
        
        # Generate QR data
        qr_data = self.qr_generator.generate_deposit_qr(calculated_usdt, memo)
        
        # Calculate expiry time
        expires_at = datetime.utcnow() + timedelta(
            minutes=settings.deposit_expiry_minutes
        )
        
        # Create deposit request
        deposit_request = DepositRequest(
            user_id=user_id,
            telegram_id=telegram_id,
            requested_krw=requested_krw,
            calculated_usdt=calculated_usdt,
            exchange_rate=rate,
            memo=memo,
            qr_data=qr_data["qr_base64"],
            status=DepositRequestStatus.PENDING,
            expires_at=expires_at,
        )
        
        self.db.add(deposit_request)
        await self.db.commit()
        await self.db.refresh(deposit_request)
        
        logger.info(
            f"Created deposit request: {memo} - "
            f"{requested_krw} KRW -> {calculated_usdt} USDT @ {rate}"
        )
        
        return deposit_request
    
    async def get_request_by_id(self, request_id: UUID) -> Optional[DepositRequest]:
        """Get deposit request by ID.
        
        Args:
            request_id: Deposit request UUID
            
        Returns:
            DepositRequest or None
        """
        result = await self.db.execute(
            select(DepositRequest).where(DepositRequest.id == request_id)
        )
        return result.scalar_one_or_none()
    
    async def get_request_by_memo(self, memo: str) -> Optional[DepositRequest]:
        """Get deposit request by memo.
        
        Args:
            memo: Unique memo string
            
        Returns:
            DepositRequest or None
        """
        result = await self.db.execute(
            select(DepositRequest).where(DepositRequest.memo == memo)
        )
        return result.scalar_one_or_none()
    
    async def get_pending_requests(self) -> list[DepositRequest]:
        """Get all pending deposit requests.
        
        Returns:
            List of pending deposit requests
        """
        result = await self.db.execute(
            select(DepositRequest)
            .where(DepositRequest.status == DepositRequestStatus.PENDING)
            .where(DepositRequest.expires_at > datetime.utcnow())
        )
        return list(result.scalars().all())
    
    async def mark_expired(self, request: DepositRequest) -> DepositRequest:
        """Mark a deposit request as expired.
        
        Args:
            request: Deposit request to expire
            
        Returns:
            Updated deposit request
        """
        request.status = DepositRequestStatus.EXPIRED
        await self.db.commit()
        await self.db.refresh(request)
        
        logger.info(f"Marked deposit request as expired: {request.memo}")
        return request
    
    async def confirm_deposit(
        self,
        request: DepositRequest,
        tx_hash: str,
    ) -> DepositRequest:
        """Confirm a deposit request.
        
        Args:
            request: Deposit request to confirm
            tx_hash: Transaction hash from blockchain
            
        Returns:
            Updated deposit request
        """
        request.status = DepositRequestStatus.CONFIRMED
        request.tx_hash = tx_hash
        request.confirmed_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(request)
        
        logger.info(f"Confirmed deposit request: {request.memo} - tx: {tx_hash}")
        return request
