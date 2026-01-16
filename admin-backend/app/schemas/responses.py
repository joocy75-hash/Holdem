"""Pydantic response schemas for API endpoints.

Provides structured response types for better type safety and documentation.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Generic, TypeVar
from pydantic import BaseModel, Field


# Generic type for paginated responses
T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    items: List[T]
    total: int = Field(ge=0, description="Total number of items")
    page: int = Field(ge=1, description="Current page number")
    page_size: int = Field(ge=1, le=100, description="Items per page")
    total_pages: int = Field(ge=0, description="Total number of pages")

    class Config:
        from_attributes = True


class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = True
    message: str = "Operation completed successfully"


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    code: Optional[str] = None
    errors: Optional[dict] = None


# ============== User Schemas ==============

class UserSummary(BaseModel):
    """Brief user information."""
    id: str
    username: str
    email: Optional[str] = None
    telegram_id: Optional[int] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class UserDetail(UserSummary):
    """Detailed user information."""
    balance: Decimal = Decimal("0")
    total_hands: int = 0
    total_rake: Decimal = Decimal("0")
    created_at: datetime
    last_login: Optional[datetime] = None
    is_banned: bool = False
    ban_reason: Optional[str] = None


# ============== Deposit Schemas ==============

class DepositSummary(BaseModel):
    """Brief deposit request information."""
    id: str
    user_id: str
    requested_krw: int
    calculated_usdt: Decimal
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class DepositDetail(DepositSummary):
    """Detailed deposit request information."""
    telegram_id: Optional[int] = None
    exchange_rate: Decimal
    memo: str
    qr_data: str
    expires_at: datetime
    confirmed_at: Optional[datetime] = None
    tx_hash: Optional[str] = None
    is_expired: bool = False
    remaining_seconds: int = 0


class DepositStats(BaseModel):
    """Deposit statistics."""
    total_pending: int = 0
    total_confirmed: int = 0
    total_expired: int = 0
    total_cancelled: int = 0
    total_usdt_confirmed: Decimal = Decimal("0")
    total_krw_confirmed: int = 0
    today_confirmed_count: int = 0
    today_confirmed_usdt: Decimal = Decimal("0")


# ============== Ban Schemas ==============

class BanSummary(BaseModel):
    """Brief ban information."""
    id: str
    user_id: str
    ban_type: str
    reason: str
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class BanDetail(BanSummary):
    """Detailed ban information."""
    banned_by: str
    expires_at: Optional[datetime] = None
    lifted_at: Optional[datetime] = None
    lifted_by: Optional[str] = None


# ============== Statistics Schemas ==============

class DashboardSummary(BaseModel):
    """Dashboard summary statistics."""
    total_users: int = 0
    active_users_today: int = 0
    total_hands_today: int = 0
    total_rake_today: Decimal = Decimal("0")
    pending_deposits: int = 0
    active_bans: int = 0


class RakeStatistics(BaseModel):
    """Rake statistics for a period."""
    total_rake: Decimal = Decimal("0")
    total_hands: int = 0
    unique_rooms: int = 0
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class PlayerActivity(BaseModel):
    """Player activity statistics."""
    user_id: str
    total_hands: int = 0
    total_rake: Decimal = Decimal("0")
    win_rate: Optional[float] = None
    last_active: Optional[datetime] = None


# ============== Audit Schemas ==============

class AuditLogEntry(BaseModel):
    """Audit log entry."""
    id: str
    admin_id: str
    admin_username: str
    action: str
    target_type: str
    target_id: Optional[str] = None
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
