"""Admin API for TON/USDT deposit management.

Provides endpoints for administrators to view, approve, and reject
deposit requests.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_admin_db
from app.models.deposit_request import DepositRequest, DepositRequestStatus
from app.services.crypto.deposit_processor import DepositProcessor
from app.services.telegram_notifier import TelegramNotifier
from app.utils.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/deposits", tags=["admin-deposits"])


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request.
    
    Handles X-Forwarded-For header for proxied requests.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Client IP address string
    """
    # Check X-Forwarded-For header (for reverse proxy setups)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first one (original client)
        return forwarded_for.split(",")[0].strip()
    
    # Check X-Real-IP header (nginx)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # Fall back to direct client IP
    if request.client:
        return request.client.host
    
    return "unknown"


# ==================== Schemas ====================

class DepositListItem(BaseModel):
    """Deposit list item schema."""
    id: UUID
    user_id: str
    telegram_id: Optional[int]
    requested_krw: int
    calculated_usdt: Decimal
    exchange_rate: Decimal
    memo: str
    status: str
    expires_at: datetime
    created_at: datetime
    confirmed_at: Optional[datetime]
    tx_hash: Optional[str]
    
    class Config:
        from_attributes = True


class DepositListResponse(BaseModel):
    """Deposit list response schema."""
    items: list[DepositListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class DepositDetailResponse(BaseModel):
    """Deposit detail response schema."""
    id: UUID
    user_id: str
    telegram_id: Optional[int]
    requested_krw: int
    calculated_usdt: Decimal
    exchange_rate: Decimal
    memo: str
    qr_data: str
    status: str
    expires_at: datetime
    created_at: datetime
    confirmed_at: Optional[datetime]
    tx_hash: Optional[str]
    is_expired: bool
    remaining_seconds: int
    
    class Config:
        from_attributes = True


class ManualApproveRequest(BaseModel):
    """Manual approve request schema."""
    tx_hash: str
    note: Optional[str] = None


class ManualRejectRequest(BaseModel):
    """Manual reject request schema."""
    reason: str


class DepositStatsResponse(BaseModel):
    """Deposit statistics response schema."""
    total_pending: int
    total_confirmed: int
    total_expired: int
    total_cancelled: int
    total_usdt_confirmed: Decimal
    total_krw_confirmed: int
    today_confirmed_count: int
    today_confirmed_usdt: Decimal


# ==================== Endpoints ====================

@router.get("", response_model=DepositListResponse)
async def list_deposits(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_admin_db),
    current_user = Depends(get_current_user),
):
    """List all deposit requests with pagination and filtering."""
    # Build query
    query = select(DepositRequest)
    count_query = select(func.count(DepositRequest.id))
    
    # Apply filters
    if status:
        try:
            status_enum = DepositRequestStatus(status)
            query = query.where(DepositRequest.status == status_enum)
            count_query = count_query.where(DepositRequest.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    if user_id:
        query = query.where(DepositRequest.user_id == user_id)
        count_query = count_query.where(DepositRequest.user_id == user_id)
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(desc(DepositRequest.created_at)).offset(offset).limit(page_size)
    
    # Execute query
    result = await db.execute(query)
    deposits = result.scalars().all()
    
    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size
    
    return DepositListResponse(
        items=[DepositListItem.model_validate(d) for d in deposits],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/stats", response_model=DepositStatsResponse)
async def get_deposit_stats(
    db: AsyncSession = Depends(get_admin_db),
    current_user = Depends(get_current_user),
):
    """Get deposit statistics."""
    # Count by status
    status_counts = {}
    for status in DepositRequestStatus:
        result = await db.execute(
            select(func.count(DepositRequest.id))
            .where(DepositRequest.status == status)
        )
        status_counts[status.value] = result.scalar() or 0
    
    # Total confirmed amounts
    confirmed_result = await db.execute(
        select(
            func.sum(DepositRequest.calculated_usdt),
            func.sum(DepositRequest.requested_krw),
        )
        .where(DepositRequest.status == DepositRequestStatus.CONFIRMED)
    )
    confirmed_row = confirmed_result.one()
    total_usdt = confirmed_row[0] or Decimal("0")
    total_krw = confirmed_row[1] or 0
    
    # Today's confirmed
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_result = await db.execute(
        select(
            func.count(DepositRequest.id),
            func.sum(DepositRequest.calculated_usdt),
        )
        .where(DepositRequest.status == DepositRequestStatus.CONFIRMED)
        .where(DepositRequest.confirmed_at >= today_start)
    )
    today_row = today_result.one()
    today_count = today_row[0] or 0
    today_usdt = today_row[1] or Decimal("0")
    
    return DepositStatsResponse(
        total_pending=status_counts.get("pending", 0),
        total_confirmed=status_counts.get("confirmed", 0),
        total_expired=status_counts.get("expired", 0),
        total_cancelled=status_counts.get("cancelled", 0),
        total_usdt_confirmed=total_usdt,
        total_krw_confirmed=total_krw,
        today_confirmed_count=today_count,
        today_confirmed_usdt=today_usdt,
    )


@router.get("/{deposit_id}", response_model=DepositDetailResponse)
async def get_deposit_detail(
    deposit_id: UUID,
    db: AsyncSession = Depends(get_admin_db),
    current_user = Depends(get_current_user),
):
    """Get deposit request details."""
    result = await db.execute(
        select(DepositRequest).where(DepositRequest.id == deposit_id)
    )
    deposit = result.scalar_one_or_none()
    
    if not deposit:
        raise HTTPException(status_code=404, detail="Deposit not found")
    
    return DepositDetailResponse(
        id=deposit.id,
        user_id=deposit.user_id,
        telegram_id=deposit.telegram_id,
        requested_krw=deposit.requested_krw,
        calculated_usdt=deposit.calculated_usdt,
        exchange_rate=deposit.exchange_rate,
        memo=deposit.memo,
        qr_data=deposit.qr_data,
        status=deposit.status.value,
        expires_at=deposit.expires_at,
        created_at=deposit.created_at,
        confirmed_at=deposit.confirmed_at,
        tx_hash=deposit.tx_hash,
        is_expired=deposit.is_expired,
        remaining_seconds=deposit.remaining_seconds,
    )


@router.post("/{deposit_id}/approve")
async def manual_approve_deposit(
    deposit_id: UUID,
    request: ManualApproveRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_admin_db),
    current_user = Depends(get_current_user),
):
    """Manually approve a deposit request."""
    # Get client IP address
    client_ip = get_client_ip(http_request)
    
    # Get deposit
    result = await db.execute(
        select(DepositRequest).where(DepositRequest.id == deposit_id)
    )
    deposit = result.scalar_one_or_none()
    
    if not deposit:
        raise HTTPException(status_code=404, detail="Deposit not found")
    
    if deposit.status != DepositRequestStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve deposit with status: {deposit.status.value}"
        )
    
    # Process approval
    processor = DepositProcessor(db)
    
    try:
        await processor.manual_approve(
            deposit_id=deposit_id,
            tx_hash=request.tx_hash,
            admin_user_id=str(current_user.id),
            notes=request.note,
            ip_address=client_ip,
        )
        
        # Send notification
        notifier = TelegramNotifier()
        await notifier.notify_deposit_confirmed(deposit, request.tx_hash)
        await notifier.close()
        
        logger.info(
            f"Deposit {deposit_id} manually approved by admin {current_user.id} from IP {client_ip}"
        )
        
        return {"status": "approved", "deposit_id": str(deposit_id)}
        
    except Exception as e:
        logger.error(f"Error approving deposit {deposit_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await processor.close()


@router.post("/{deposit_id}/reject")
async def manual_reject_deposit(
    deposit_id: UUID,
    request: ManualRejectRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_admin_db),
    current_user = Depends(get_current_user),
):
    """Manually reject a deposit request."""
    # Get client IP address
    client_ip = get_client_ip(http_request)
    
    # Get deposit
    result = await db.execute(
        select(DepositRequest).where(DepositRequest.id == deposit_id)
    )
    deposit = result.scalar_one_or_none()
    
    if not deposit:
        raise HTTPException(status_code=404, detail="Deposit not found")
    
    if deposit.status != DepositRequestStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reject deposit with status: {deposit.status.value}"
        )
    
    # Process rejection
    processor = DepositProcessor(db)
    
    try:
        await processor.manual_reject(
            deposit_id=deposit_id,
            reason=request.reason,
            admin_user_id=str(current_user.id),
            ip_address=client_ip,
        )
        
        logger.info(
            f"Deposit {deposit_id} rejected by admin {current_user.id} from IP {client_ip}: {request.reason}"
        )
        
        return {"status": "rejected", "deposit_id": str(deposit_id)}
        
    except Exception as e:
        logger.error(f"Error rejecting deposit {deposit_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await processor.close()


@router.get("/pending/count")
async def get_pending_count(
    db: AsyncSession = Depends(get_admin_db),
    current_user = Depends(get_current_user),
):
    """Get count of pending deposits (for dashboard badge)."""
    result = await db.execute(
        select(func.count(DepositRequest.id))
        .where(DepositRequest.status == DepositRequestStatus.PENDING)
    )
    count = result.scalar() or 0
    
    return {"pending_count": count}
