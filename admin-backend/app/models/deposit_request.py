"""Deposit Request model for TON/USDT deposits.

This model tracks deposit requests with unique memos for matching
incoming blockchain transactions.
"""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional
from sqlalchemy import String, DateTime, Numeric, BigInteger, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class DepositRequestStatus(str, Enum):
    """Status of a deposit request."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class InvalidStateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


# Valid state transitions
VALID_TRANSITIONS = {
    DepositRequestStatus.PENDING: {
        DepositRequestStatus.CONFIRMED,
        DepositRequestStatus.EXPIRED,
        DepositRequestStatus.CANCELLED,
    },
    DepositRequestStatus.CONFIRMED: set(),  # Terminal state
    DepositRequestStatus.EXPIRED: set(),    # Terminal state
    DepositRequestStatus.CANCELLED: set(),  # Terminal state
}


class DepositRequest(Base, UUIDMixin):
    """TON/USDT deposit request record.
    
    Each request generates a unique memo for matching incoming
    blockchain transactions. Requests expire after 30 minutes.
    
    State Transitions:
        PENDING -> CONFIRMED (via confirm())
        PENDING -> EXPIRED (via expire())
        PENDING -> CANCELLED (via cancel())
    """
    __tablename__ = "deposit_requests"

    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    requested_krw: Mapped[int] = mapped_column(BigInteger, nullable=False)
    calculated_usdt: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    memo: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    qr_data: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[DepositRequestStatus] = mapped_column(
        SQLEnum(DepositRequestStatus),
        default=DepositRequestStatus.PENDING,
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tx_hash: Mapped[str | None] = mapped_column(String(66), nullable=True)

    def __repr__(self) -> str:
        return f"<DepositRequest {self.memo} {self.requested_krw} KRW -> {self.calculated_usdt} USDT>"

    def _can_transition_to(self, new_status: DepositRequestStatus) -> bool:
        """Check if transition to new status is valid.
        
        Args:
            new_status: Target status
            
        Returns:
            bool: True if transition is valid
        """
        return new_status in VALID_TRANSITIONS.get(self.status, set())

    def _transition_to(self, new_status: DepositRequestStatus) -> None:
        """Transition to a new status with validation.
        
        Args:
            new_status: Target status
            
        Raises:
            InvalidStateTransitionError: If transition is not allowed
        """
        if not self._can_transition_to(new_status):
            raise InvalidStateTransitionError(
                f"Cannot transition from {self.status.value} to {new_status.value}"
            )
        self.status = new_status

    def confirm(self, tx_hash: str) -> None:
        """Confirm the deposit request.
        
        Args:
            tx_hash: Transaction hash from blockchain
            
        Raises:
            InvalidStateTransitionError: If not in PENDING status
            ValueError: If tx_hash is empty
        """
        if not tx_hash or not tx_hash.strip():
            raise ValueError("tx_hash is required for confirmation")
        
        self._transition_to(DepositRequestStatus.CONFIRMED)
        self.tx_hash = tx_hash.strip()
        self.confirmed_at = datetime.now(timezone.utc)

    def expire(self) -> None:
        """Mark the deposit request as expired.
        
        Raises:
            InvalidStateTransitionError: If not in PENDING status
        """
        self._transition_to(DepositRequestStatus.EXPIRED)

    def cancel(self, reason: Optional[str] = None) -> None:
        """Cancel the deposit request.
        
        Args:
            reason: Optional cancellation reason (for logging)
            
        Raises:
            InvalidStateTransitionError: If not in PENDING status
        """
        self._transition_to(DepositRequestStatus.CANCELLED)

    @property
    def is_pending(self) -> bool:
        """Check if the request is still pending."""
        return self.status == DepositRequestStatus.PENDING

    @property
    def is_confirmed(self) -> bool:
        """Check if the request has been confirmed."""
        return self.status == DepositRequestStatus.CONFIRMED

    @property
    def is_terminal(self) -> bool:
        """Check if the request is in a terminal state."""
        return self.status in (
            DepositRequestStatus.CONFIRMED,
            DepositRequestStatus.EXPIRED,
            DepositRequestStatus.CANCELLED,
        )

    @property
    def is_expired(self) -> bool:
        """Check if the request has expired (by time or status)."""
        if self.status == DepositRequestStatus.EXPIRED:
            return True
        now = datetime.now(timezone.utc)
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return now > expires_at

    @property
    def remaining_seconds(self) -> int:
        """Get remaining seconds until expiry."""
        if self.is_expired:
            return 0
        now = datetime.now(timezone.utc)
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        delta = expires_at - now
        return max(0, int(delta.total_seconds()))
