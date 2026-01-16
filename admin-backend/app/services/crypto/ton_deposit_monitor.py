"""TON Deposit Monitor for automatic deposit detection.

Polls the TON blockchain for incoming USDT transfers and matches
them against pending deposit requests using memo matching.
"""

import asyncio
import logging
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional, Callable, Awaitable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.deposit_request import DepositRequest, DepositRequestStatus
from app.services.crypto.ton_client import TonClient, JettonTransfer

logger = logging.getLogger(__name__)
settings = get_settings()


class TonDepositMonitor:
    """Monitor for incoming TON/USDT deposits.
    
    Polls the blockchain at regular intervals and matches incoming
    transfers against pending deposit requests using memo matching.
    """
    
    # Default threshold for consecutive errors before alerting
    DEFAULT_CONSECUTIVE_ERROR_THRESHOLD = 5
    
    def __init__(
        self,
        db_session_factory: Callable[[], AsyncSession],
        ton_client: Optional[TonClient] = None,
        polling_interval: int = None,
        amount_tolerance: float = None,
        consecutive_error_threshold: int = None,
    ):
        """Initialize deposit monitor.
        
        Args:
            db_session_factory: Factory function to create DB sessions
            ton_client: TON client instance (created if not provided)
            polling_interval: Seconds between polls (default from config)
            amount_tolerance: Allowed amount variance (default 0.5%)
            consecutive_error_threshold: Number of consecutive errors before alerting admin
        """
        self.db_session_factory = db_session_factory
        self.ton_client = ton_client or TonClient()
        self.polling_interval = polling_interval or settings.deposit_polling_interval
        self.amount_tolerance = amount_tolerance or settings.deposit_amount_tolerance
        self.consecutive_error_threshold = (
            consecutive_error_threshold or self.DEFAULT_CONSECUTIVE_ERROR_THRESHOLD
        )
        
        self._running = False
        self._last_lt: Optional[int] = None  # Last processed logical time
        self._consecutive_errors = 0  # Counter for consecutive polling errors
        self._alert_sent = False  # Flag to prevent duplicate alerts
        self._on_deposit_confirmed: Optional[Callable[[DepositRequest, str], Awaitable[None]]] = None
        self._on_deposit_expired: Optional[Callable[[DepositRequest], Awaitable[None]]] = None
        self._on_polling_error_alert: Optional[Callable[[int, str], Awaitable[None]]] = None
    
    def set_callbacks(
        self,
        on_confirmed: Optional[Callable[[DepositRequest, str], Awaitable[None]]] = None,
        on_expired: Optional[Callable[[DepositRequest], Awaitable[None]]] = None,
        on_polling_error_alert: Optional[Callable[[int, str], Awaitable[None]]] = None,
    ):
        """Set callback functions for deposit events.
        
        Args:
            on_confirmed: Called when deposit is confirmed (request, tx_hash)
            on_expired: Called when deposit request expires
            on_polling_error_alert: Called when consecutive polling errors exceed threshold (error_count, last_error)
        """
        self._on_deposit_confirmed = on_confirmed
        self._on_deposit_expired = on_expired
        self._on_polling_error_alert = on_polling_error_alert
    
    async def start_polling(self):
        """Start the polling loop.
        
        Runs continuously until stop_polling() is called.
        """
        self._running = True
        logger.info(f"Starting deposit monitor (interval: {self.polling_interval}s)")
        
        while self._running:
            try:
                await self.check_new_deposits()
                await self.check_expired_requests()
                # Reset error counter on successful poll
                self._reset_error_counter()
            except Exception as e:
                await self._handle_polling_error(e)
            
            await asyncio.sleep(self.polling_interval)
        
        logger.info("Deposit monitor stopped")
    
    async def _handle_polling_error(self, error: Exception):
        """Handle polling errors and trigger alerts if threshold exceeded.
        
        Args:
            error: The exception that occurred during polling
        """
        self._consecutive_errors += 1
        error_msg = str(error)
        
        logger.error(
            f"Error in polling loop (consecutive: {self._consecutive_errors}): {error_msg}"
        )
        
        # Check if we should alert
        if self._consecutive_errors >= self.consecutive_error_threshold and not self._alert_sent:
            self._alert_sent = True
            logger.critical(
                f"ALERT: {self._consecutive_errors} consecutive polling errors! "
                f"Last error: {error_msg}"
            )
            
            # Call alert callback if set
            if self._on_polling_error_alert:
                try:
                    await self._on_polling_error_alert(self._consecutive_errors, error_msg)
                except Exception as callback_error:
                    logger.error(f"Error in polling error alert callback: {callback_error}")
    
    def _reset_error_counter(self):
        """Reset the consecutive error counter after successful poll."""
        if self._consecutive_errors > 0:
            logger.info(
                f"Polling recovered after {self._consecutive_errors} consecutive errors"
            )
        self._consecutive_errors = 0
        self._alert_sent = False
    
    def stop_polling(self):
        """Stop the polling loop."""
        self._running = False
    
    @property
    def consecutive_errors(self) -> int:
        """Get current consecutive error count."""
        return self._consecutive_errors
    
    @property
    def is_healthy(self) -> bool:
        """Check if monitor is healthy (no consecutive errors)."""
        return self._consecutive_errors < self.consecutive_error_threshold
    
    async def check_new_deposits(self):
        """Check for new deposits and match against pending requests."""
        try:
            # Get recent transfers
            transfers = await self.ton_client.get_jetton_transfers(
                limit=50,
                after_lt=self._last_lt,
            )
            
            if not transfers:
                return
            
            # Update last processed LT
            max_lt = max(t.lt for t in transfers)
            if self._last_lt is None or max_lt > self._last_lt:
                self._last_lt = max_lt
            
            # Process each transfer
            for transfer in transfers:
                await self._process_transfer(transfer)
                
        except Exception as e:
            logger.error(f"Error checking new deposits: {e}")
    
    async def _process_transfer(self, transfer: JettonTransfer):
        """Process a single transfer and try to match it.
        
        Args:
            transfer: The Jetton transfer to process
        """
        if not transfer.memo:
            logger.debug(f"Transfer {transfer.tx_hash} has no memo, skipping")
            return
        
        async with self.db_session_factory() as db:
            # Find matching deposit request by memo
            request = await self._find_request_by_memo(db, transfer.memo)
            
            if not request:
                logger.debug(f"No matching request for memo: {transfer.memo}")
                return
            
            # Validate the transfer
            match_result = self.match_deposit(request, transfer)
            
            if match_result["matched"]:
                await self._confirm_deposit(db, request, transfer)
            else:
                logger.warning(
                    f"Transfer {transfer.tx_hash} did not match request {request.memo}: "
                    f"{match_result['reason']}"
                )
    
    async def _find_request_by_memo(
        self,
        db: AsyncSession,
        memo: str,
    ) -> Optional[DepositRequest]:
        """Find a pending deposit request by memo.
        
        Args:
            db: Database session
            memo: Memo to search for
            
        Returns:
            DepositRequest or None
        """
        result = await db.execute(
            select(DepositRequest)
            .where(DepositRequest.memo == memo)
            .where(DepositRequest.status == DepositRequestStatus.PENDING)
        )
        return result.scalar_one_or_none()
    
    def match_deposit(
        self,
        request: DepositRequest,
        transfer: JettonTransfer,
    ) -> dict:
        """Check if a transfer matches a deposit request.
        
        Validates:
        1. Memo matches exactly
        2. Amount is within tolerance
        3. Request has not expired
        
        Args:
            request: The deposit request
            transfer: The incoming transfer
            
        Returns:
            dict: {"matched": bool, "reason": str}
        """
        # Check memo match (already matched if we got here)
        if transfer.memo != request.memo:
            return {"matched": False, "reason": "memo_mismatch"}
        
        # Check expiry
        if request.is_expired:
            return {"matched": False, "reason": "request_expired"}
        
        # Check amount with tolerance
        expected = request.calculated_usdt
        actual = transfer.amount
        min_amount = expected * Decimal(1 - self.amount_tolerance)
        
        if actual < min_amount:
            return {
                "matched": False,
                "reason": f"amount_too_low: expected >= {min_amount}, got {actual}"
            }
        
        return {"matched": True, "reason": "ok"}
    
    async def _confirm_deposit(
        self,
        db: AsyncSession,
        request: DepositRequest,
        transfer: JettonTransfer,
    ):
        """Confirm a matched deposit.
        
        Args:
            db: Database session
            request: The deposit request
            transfer: The matching transfer
        """
        request.status = DepositRequestStatus.CONFIRMED
        request.tx_hash = transfer.tx_hash
        request.confirmed_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(request)
        
        logger.info(
            f"Deposit confirmed: {request.memo} - "
            f"{request.requested_krw} KRW ({transfer.amount} USDT) - "
            f"tx: {transfer.tx_hash}"
        )
        
        # Call callback if set
        if self._on_deposit_confirmed:
            try:
                await self._on_deposit_confirmed(request, transfer.tx_hash)
            except Exception as e:
                logger.error(f"Error in deposit confirmed callback: {e}")
    
    async def check_expired_requests(self):
        """Check for and mark expired deposit requests."""
        try:
            async with self.db_session_factory() as db:
                # Find expired pending requests
                result = await db.execute(
                    select(DepositRequest)
                    .where(DepositRequest.status == DepositRequestStatus.PENDING)
                    .where(DepositRequest.expires_at < datetime.now(timezone.utc))
                )
                expired_requests = result.scalars().all()
                
                for request in expired_requests:
                    request.status = DepositRequestStatus.EXPIRED
                    
                    logger.info(f"Deposit request expired: {request.memo}")
                    
                    # Call callback if set
                    if self._on_deposit_expired:
                        try:
                            await self._on_deposit_expired(request)
                        except Exception as e:
                            logger.error(f"Error in deposit expired callback: {e}")
                
                if expired_requests:
                    await db.commit()
                    
        except Exception as e:
            logger.error(f"Error checking expired requests: {e}")
    
    async def close(self):
        """Clean up resources."""
        self.stop_polling()
        await self.ton_client.close()
