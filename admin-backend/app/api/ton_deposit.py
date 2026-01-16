"""TON/USDT Deposit API endpoints.

Provides endpoints for creating and managing deposit requests.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_admin_db
from app.models.admin_user import AdminUser
from app.models.deposit_request import DepositRequestStatus
from app.services.crypto.deposit_request_service import DepositRequestService
from app.services.crypto.ton_exchange_rate import ExchangeRateError
from app.utils.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/deposit", tags=["TON Deposit"])


# Request/Response schemas
class DepositRequestCreate(BaseModel):
    """Request body for creating a deposit request."""
    requested_krw: int = Field(..., ge=10000, le=100000000, description="Amount in KRW (min 10,000, max 100,000,000)")
    telegram_id: Optional[int] = Field(None, description="Telegram user ID")


class DepositRequestResponse(BaseModel):
    """Response for deposit request."""
    id: UUID
    user_id: str
    telegram_id: Optional[int]
    requested_krw: int
    calculated_usdt: str
    exchange_rate: str
    memo: str
    qr_data: str
    status: str
    expires_at: datetime
    remaining_seconds: int
    created_at: datetime
    confirmed_at: Optional[datetime]
    tx_hash: Optional[str]

    class Config:
        from_attributes = True


class DepositStatusResponse(BaseModel):
    """Response for deposit status check."""
    id: UUID
    status: str
    remaining_seconds: int
    is_expired: bool
    confirmed_at: Optional[datetime]
    tx_hash: Optional[str]


class ExchangeRateResponse(BaseModel):
    """Response for exchange rate."""
    usdt_krw: str
    timestamp: datetime


@router.post(
    "/request",
    response_model=DepositRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create deposit request",
    description="Create a new TON/USDT deposit request with QR code",
)
async def create_deposit_request(
    request: DepositRequestCreate,
    current_user: AdminUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_admin_db),
):
    """Create a new deposit request.
    
    Generates a unique memo and QR code for the deposit.
    The request expires after 30 minutes.
    User ID is automatically set from the authenticated user.
    """
    service = DepositRequestService(db)
    
    try:
        deposit = await service.create_request(
            user_id=current_user.id,
            requested_krw=request.requested_krw,
            telegram_id=request.telegram_id,
        )
        
        return DepositRequestResponse(
            id=deposit.id,
            user_id=deposit.user_id,
            telegram_id=deposit.telegram_id,
            requested_krw=deposit.requested_krw,
            calculated_usdt=str(deposit.calculated_usdt),
            exchange_rate=str(deposit.exchange_rate),
            memo=deposit.memo,
            qr_data=deposit.qr_data,
            status=deposit.status.value,
            expires_at=deposit.expires_at,
            remaining_seconds=deposit.remaining_seconds,
            created_at=deposit.created_at,
            confirmed_at=deposit.confirmed_at,
            tx_hash=deposit.tx_hash,
        )
    except ExchangeRateError as e:
        logger.error(f"Exchange rate error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to fetch exchange rate. Please try again later.",
        )
    except Exception as e:
        logger.error(f"Error creating deposit request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create deposit request",
        )


@router.get(
    "/status/{request_id}",
    response_model=DepositStatusResponse,
    summary="Get deposit status",
    description="Check the status of a deposit request",
)
async def get_deposit_status(
    request_id: UUID,
    current_user: AdminUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_admin_db),
):
    """Get the status of a deposit request.
    
    Only the owner of the deposit request can check its status.
    """
    service = DepositRequestService(db)
    
    deposit = await service.get_request_by_id(request_id)
    if not deposit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deposit request not found",
        )
    
    # 소유자 검증
    if deposit.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only view your own deposit requests",
        )
    
    return DepositStatusResponse(
        id=deposit.id,
        status=deposit.status.value,
        remaining_seconds=deposit.remaining_seconds,
        is_expired=deposit.is_expired,
        confirmed_at=deposit.confirmed_at,
        tx_hash=deposit.tx_hash,
    )


@router.get(
    "/request/{request_id}",
    response_model=DepositRequestResponse,
    summary="Get deposit request details",
    description="Get full details of a deposit request including QR code",
)
async def get_deposit_request(
    request_id: UUID,
    current_user: AdminUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_admin_db),
):
    """Get full details of a deposit request.
    
    Only the owner of the deposit request can view its details.
    """
    service = DepositRequestService(db)
    
    deposit = await service.get_request_by_id(request_id)
    if not deposit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deposit request not found",
        )
    
    # 소유자 검증
    if deposit.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only view your own deposit requests",
        )
    
    return DepositRequestResponse(
        id=deposit.id,
        user_id=deposit.user_id,
        telegram_id=deposit.telegram_id,
        requested_krw=deposit.requested_krw,
        calculated_usdt=str(deposit.calculated_usdt),
        exchange_rate=str(deposit.exchange_rate),
        memo=deposit.memo,
        qr_data=deposit.qr_data,
        status=deposit.status.value,
        expires_at=deposit.expires_at,
        remaining_seconds=deposit.remaining_seconds,
        created_at=deposit.created_at,
        confirmed_at=deposit.confirmed_at,
        tx_hash=deposit.tx_hash,
    )


@router.get(
    "/rate",
    response_model=ExchangeRateResponse,
    summary="Get current exchange rate",
    description="Get current USDT/KRW exchange rate",
)
async def get_exchange_rate():
    """Get current USDT/KRW exchange rate."""
    from app.services.crypto.ton_exchange_rate import TonExchangeRateService
    
    service = TonExchangeRateService()
    try:
        rate = await service.get_usdt_krw_rate()
        return ExchangeRateResponse(
            usdt_krw=str(rate),
            timestamp=datetime.utcnow(),
        )
    except ExchangeRateError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to fetch exchange rate",
        )
    finally:
        await service.close()
