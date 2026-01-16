"""Deposit expiry task for handling expired deposit requests.

This module provides background task functionality to check and mark
expired deposit requests, with optional notification callbacks.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Callable, Awaitable

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.deposit_request import DepositRequest, DepositRequestStatus

logger = logging.getLogger(__name__)
settings = get_settings()


class DepositExpiryTask:
    """Background task for handling expired deposit requests.
    
    Periodically checks for expired pending requests and marks them
    as expired, optionally triggering notification callbacks.
    """
    
    def __init__(
        self,
        db_session_factory: Callable[[], AsyncSession],
        check_interval: int = 60,  # Check every minute
        on_expired: Optional[Callable[[DepositRequest], Awaitable[None]]] = None,
    ):
        """Initialize expiry task.
        
        Args:
            db_session_factory: Factory function to create DB sessions
            check_interval: Seconds between expiry checks
            on_expired: Callback when a request expires
        """
        self.db_session_factory = db_session_factory
        self.check_interval = check_interval
        self._on_expired = on_expired
        self._running = False
    
    def set_expired_callback(
        self,
        callback: Callable[[DepositRequest], Awaitable[None]],
    ):
        """Set callback for expired requests.
        
        Args:
            callback: Async function called with expired request
        """
        self._on_expired = callback
    
    async def start(self):
        """Start the expiry check loop.
        
        Runs continuously until stop() is called.
        """
        self._running = True
        logger.info(f"Starting deposit expiry task (interval: {self.check_interval}s)")
        
        while self._running:
            try:
                expired_count = await self.check_expired_deposits()
                if expired_count > 0:
                    logger.info(f"Marked {expired_count} deposit requests as expired")
            except Exception as e:
                logger.error(f"Error in expiry check loop: {e}")
            
            await asyncio.sleep(self.check_interval)
        
        logger.info("Deposit expiry task stopped")
    
    def stop(self):
        """Stop the expiry check loop."""
        self._running = False
    
    async def check_expired_deposits(self) -> int:
        """Check for and mark expired deposit requests.
        
        Returns:
            int: Number of requests marked as expired
        """
        expired_count = 0
        
        async with self.db_session_factory() as db:
            # Find expired pending requests
            result = await db.execute(
                select(DepositRequest)
                .where(DepositRequest.status == DepositRequestStatus.PENDING)
                .where(DepositRequest.expires_at < datetime.now(timezone.utc))
            )
            expired_requests = list(result.scalars().all())
            
            for request in expired_requests:
                request.status = DepositRequestStatus.EXPIRED
                expired_count += 1
                
                logger.info(
                    f"Deposit request expired: {request.memo} - "
                    f"{request.requested_krw} KRW ({request.calculated_usdt} USDT)"
                )
                
                # Call callback if set
                if self._on_expired:
                    try:
                        await self._on_expired(request)
                    except Exception as e:
                        logger.error(f"Error in expired callback for {request.memo}: {e}")
            
            if expired_requests:
                await db.commit()
        
        return expired_count


async def check_expired_deposits(
    db: AsyncSession,
    on_expired: Optional[Callable[[DepositRequest], Awaitable[None]]] = None,
) -> int:
    """One-shot function to check and mark expired deposits.
    
    Can be called from API endpoints or scheduled tasks.
    
    Args:
        db: Database session
        on_expired: Optional callback for each expired request
        
    Returns:
        int: Number of requests marked as expired
    """
    expired_count = 0
    
    # Find expired pending requests
    result = await db.execute(
        select(DepositRequest)
        .where(DepositRequest.status == DepositRequestStatus.PENDING)
        .where(DepositRequest.expires_at < datetime.now(timezone.utc))
    )
    expired_requests = list(result.scalars().all())
    
    for request in expired_requests:
        request.status = DepositRequestStatus.EXPIRED
        expired_count += 1
        
        logger.info(
            f"Deposit request expired: {request.memo} - "
            f"{request.requested_krw} KRW ({request.calculated_usdt} USDT)"
        )
        
        # Call callback if set
        if on_expired:
            try:
                await on_expired(request)
            except Exception as e:
                logger.error(f"Error in expired callback for {request.memo}: {e}")
    
    if expired_requests:
        await db.commit()
    
    return expired_count


async def get_expiring_soon_deposits(
    db: AsyncSession,
    minutes_threshold: int = 5,
) -> list[DepositRequest]:
    """Get deposits that will expire soon.
    
    Useful for sending reminder notifications.
    
    Args:
        db: Database session
        minutes_threshold: Minutes until expiry to consider "soon"
        
    Returns:
        List of deposit requests expiring soon
    """
    from datetime import timedelta
    
    now = datetime.now(timezone.utc)
    threshold = now + timedelta(minutes=minutes_threshold)
    
    result = await db.execute(
        select(DepositRequest)
        .where(DepositRequest.status == DepositRequestStatus.PENDING)
        .where(DepositRequest.expires_at > now)
        .where(DepositRequest.expires_at <= threshold)
    )
    
    return list(result.scalars().all())
