"""Deposit Processor for automatic deposit approval.

Handles the complete deposit processing flow including balance updates,
transaction logging, and notification triggers.
"""

import logging
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from app.config import get_settings
from app.models.deposit_request import DepositRequest, DepositRequestStatus
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)
settings = get_settings()


class DepositProcessorError(Exception):
    """Exception raised for deposit processing errors."""
    pass


class BalanceCreditError(Exception):
    """Exception raised when balance credit fails."""
    pass


class BalanceRollbackError(Exception):
    """Exception raised when balance rollback fails."""
    pass


class DepositProcessor:
    """Processor for handling confirmed deposits.
    
    Responsible for:
    1. Updating user balance in main DB
    2. Recording audit logs
    3. Triggering notifications
    
    Implements Saga pattern for distributed transaction handling:
    - Idempotency keys prevent duplicate credits
    - Compensating transactions (debit) for rollback
    - Retry logic with exponential backoff
    """
    
    def __init__(
        self,
        admin_db: AsyncSession,
        main_api_url: Optional[str] = None,
        main_api_key: Optional[str] = None,
    ):
        """Initialize deposit processor.
        
        Args:
            admin_db: Admin database session
            main_api_url: Main backend API URL for balance updates
            main_api_key: API key for main backend
        """
        self.admin_db = admin_db
        self.main_api_url = main_api_url or settings.main_api_url
        self.main_api_key = main_api_key or settings.main_api_key
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=30.0,
                headers={"X-API-Key": self.main_api_key},
            )
        return self._http_client
    
    async def close(self):
        """Close HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
    
    async def process_deposit(
        self,
        request: DepositRequest,
        tx_hash: str,
        actual_amount: Optional[Decimal] = None,
    ) -> DepositRequest:
        """Process a confirmed deposit.
        
        This is the main entry point for deposit processing.
        Implements Saga pattern for distributed transaction handling:
        1. Credit balance with idempotency key
        2. Update local DB status
        3. If step 2 fails, attempt compensating transaction (debit)
        
        Args:
            request: The deposit request to process
            tx_hash: Blockchain transaction hash
            actual_amount: Actual USDT amount received (if different from calculated)
            
        Returns:
            Updated DepositRequest
            
        Raises:
            DepositProcessorError: If processing fails
        """
        if request.status == DepositRequestStatus.CONFIRMED:
            logger.warning(f"Deposit {request.memo} already confirmed")
            return request
        
        if request.status == DepositRequestStatus.EXPIRED:
            raise DepositProcessorError(f"Cannot process expired deposit: {request.memo}")
        
        # Generate idempotency key to prevent duplicate credits
        idempotency_key = f"deposit_{request.id}_{tx_hash}"
        balance_credited = False
        
        try:
            # Step 1: Update user balance in main DB (with retry)
            await self._credit_balance_with_retry(
                user_id=request.user_id,
                amount_krw=request.requested_krw,
                memo=request.memo,
                tx_hash=tx_hash,
                idempotency_key=idempotency_key,
            )
            balance_credited = True
            
            # Step 2: Update deposit request status
            request.status = DepositRequestStatus.CONFIRMED
            request.tx_hash = tx_hash
            request.confirmed_at = datetime.now(timezone.utc)
            
            # Step 3: Create audit log
            await self._create_audit_log(request, tx_hash, actual_amount)
            
            # Commit all changes
            await self.admin_db.commit()
            await self.admin_db.refresh(request)
            
            logger.info(
                f"Deposit processed successfully: {request.memo} - "
                f"{request.requested_krw} KRW - tx: {tx_hash}"
            )
            
            return request
            
        except Exception as e:
            await self.admin_db.rollback()
            
            # If balance was credited but DB update failed, attempt rollback
            if balance_credited:
                logger.error(
                    f"DB update failed after balance credit for {request.memo}. "
                    f"Attempting compensating transaction..."
                )
                try:
                    await self._debit_balance_rollback(
                        user_id=request.user_id,
                        amount_krw=request.requested_krw,
                        memo=request.memo,
                        original_tx_hash=tx_hash,
                        reason="deposit_processing_failed",
                    )
                    logger.info(f"Compensating transaction successful for {request.memo}")
                except BalanceRollbackError as rollback_error:
                    # Critical: Balance credited but rollback failed
                    # This requires manual intervention
                    logger.critical(
                        f"CRITICAL: Balance rollback failed for {request.memo}! "
                        f"User {request.user_id} may have incorrect balance. "
                        f"Amount: {request.requested_krw} KRW. "
                        f"Original error: {e}. Rollback error: {rollback_error}"
                    )
                    # Mark request for manual review
                    await self._mark_for_manual_review(request, str(e), str(rollback_error))
            
            logger.error(f"Error processing deposit {request.memo}: {e}")
            raise DepositProcessorError(f"Failed to process deposit: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def _credit_balance_with_retry(
        self,
        user_id: str,
        amount_krw: int,
        memo: str,
        tx_hash: str,
        idempotency_key: str,
    ) -> bool:
        """Credit user balance with retry logic.
        
        Uses idempotency key to prevent duplicate credits on retry.
        """
        return await self.credit_balance(
            user_id=user_id,
            amount_krw=amount_krw,
            memo=memo,
            tx_hash=tx_hash,
            idempotency_key=idempotency_key,
        )
    
    async def credit_balance(
        self,
        user_id: str,
        amount_krw: int,
        memo: str,
        tx_hash: str,
        idempotency_key: Optional[str] = None,
    ) -> bool:
        """Credit user balance in main database.
        
        Calls the main backend API to update user balance.
        
        Args:
            user_id: User ID to credit
            amount_krw: Amount in KRW to add
            memo: Deposit memo for reference
            tx_hash: Transaction hash for reference
            idempotency_key: Optional key to prevent duplicate credits
            
        Returns:
            bool: True if successful
            
        Raises:
            BalanceCreditError: If balance update fails
        """
        try:
            client = await self._get_http_client()
            
            # Call main backend API to credit balance
            request_data = {
                "user_id": user_id,
                "amount": amount_krw,
                "transaction_type": "deposit",
                "reference": memo,
                "tx_hash": tx_hash,
            }
            
            # Add idempotency key if provided
            if idempotency_key:
                request_data["idempotency_key"] = idempotency_key
            
            response = await client.post(
                f"{self.main_api_url}/api/wallet/credit",
                json=request_data,
            )
            
            if response.status_code == 200:
                logger.info(f"Balance credited: {user_id} +{amount_krw} KRW")
                return True
            elif response.status_code == 409:
                # Idempotency conflict - already processed
                logger.info(f"Balance already credited (idempotent): {user_id} +{amount_krw} KRW")
                return True
            else:
                error_detail = response.json().get("detail", "Unknown error")
                raise BalanceCreditError(
                    f"Main API returned {response.status_code}: {error_detail}"
                )
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error crediting balance: {e}")
            raise BalanceCreditError(f"Failed to credit balance: {e}")
    
    async def _debit_balance_rollback(
        self,
        user_id: str,
        amount_krw: int,
        memo: str,
        original_tx_hash: str,
        reason: str,
    ) -> bool:
        """Debit user balance as compensating transaction.
        
        Used to rollback a credit when subsequent operations fail.
        
        Args:
            user_id: User ID to debit
            amount_krw: Amount in KRW to remove
            memo: Original deposit memo
            original_tx_hash: Original transaction hash
            reason: Reason for rollback
            
        Returns:
            bool: True if successful
            
        Raises:
            BalanceRollbackError: If rollback fails
        """
        try:
            client = await self._get_http_client()
            
            response = await client.post(
                f"{self.main_api_url}/api/wallet/debit",
                json={
                    "user_id": user_id,
                    "amount": amount_krw,
                    "transaction_type": "deposit_rollback",
                    "reference": f"rollback_{memo}",
                    "original_tx_hash": original_tx_hash,
                    "reason": reason,
                },
            )
            
            if response.status_code == 200:
                logger.info(f"Balance rollback successful: {user_id} -{amount_krw} KRW")
                return True
            else:
                error_detail = response.json().get("detail", "Unknown error")
                raise BalanceRollbackError(
                    f"Rollback API returned {response.status_code}: {error_detail}"
                )
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during balance rollback: {e}")
            raise BalanceRollbackError(f"Failed to rollback balance: {e}")
    
    async def _mark_for_manual_review(
        self,
        request: DepositRequest,
        error: str,
        rollback_error: str,
    ):
        """Mark a deposit request for manual review.
        
        Called when automatic processing and rollback both fail.
        """
        try:
            # Create critical audit log
            # Note: System-initiated actions use "system" as IP since there's no HTTP request
            audit_log = AuditLog(
                action="deposit_requires_manual_review",
                target_type="deposit_request",
                target_id=str(request.id),
                admin_user_id="system",
                ip_address="system",
                details={
                    "memo": request.memo,
                    "user_id": request.user_id,
                    "requested_krw": request.requested_krw,
                    "error": error,
                    "rollback_error": rollback_error,
                    "status": "CRITICAL_MANUAL_REVIEW_REQUIRED",
                },
            )
            self.admin_db.add(audit_log)
            await self.admin_db.commit()
        except Exception as e:
            logger.critical(f"Failed to create manual review audit log: {e}")
    
    async def _create_audit_log(
        self,
        request: DepositRequest,
        tx_hash: str,
        actual_amount: Optional[Decimal] = None,
        ip_address: str = "system",
        admin_user_id: str = "system",
    ):
        """Create audit log entry for the deposit.
        
        Args:
            request: The deposit request
            tx_hash: Transaction hash
            actual_amount: Actual amount received
            ip_address: IP address of the requester (default "system" for automated actions)
            admin_user_id: Admin user ID (default "system" for automated actions)
        """
        audit_log = AuditLog(
            action="deposit_confirmed",
            target_type="deposit_request",
            target_id=str(request.id),
            admin_user_id=admin_user_id,
            ip_address=ip_address,
            details={
                "memo": request.memo,
                "requested_krw": request.requested_krw,
                "calculated_usdt": str(request.calculated_usdt),
                "actual_usdt": str(actual_amount) if actual_amount else None,
                "exchange_rate": str(request.exchange_rate),
                "tx_hash": tx_hash,
                "user_id": request.user_id,
            },
        )
        self.admin_db.add(audit_log)
    
    async def get_deposit_by_id(self, deposit_id: UUID) -> Optional[DepositRequest]:
        """Get deposit request by ID.
        
        Args:
            deposit_id: Deposit request UUID
            
        Returns:
            DepositRequest or None
        """
        result = await self.admin_db.execute(
            select(DepositRequest).where(DepositRequest.id == deposit_id)
        )
        return result.scalar_one_or_none()
    
    async def get_pending_deposits(self) -> list[DepositRequest]:
        """Get all pending deposit requests.
        
        Returns:
            List of pending deposits
        """
        result = await self.admin_db.execute(
            select(DepositRequest)
            .where(DepositRequest.status == DepositRequestStatus.PENDING)
            .order_by(DepositRequest.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def manual_approve(
        self,
        deposit_id: UUID,
        admin_user_id: str,
        tx_hash: Optional[str] = None,
        notes: Optional[str] = None,
        skip_tx_verification: bool = False,
        ip_address: str = "unknown",
    ) -> DepositRequest:
        """Manually approve a deposit request.
        
        Used by admins to approve deposits that couldn't be auto-matched.
        
        Args:
            deposit_id: Deposit request ID
            admin_user_id: Admin user performing the action
            tx_hash: Transaction hash (required unless skip_tx_verification=True)
            notes: Optional admin notes
            skip_tx_verification: If True, allows approval without tx_hash (requires elevated permissions)
            ip_address: IP address of the admin making the request
            
        Returns:
            Updated DepositRequest
            
        Raises:
            DepositProcessorError: If tx_hash is missing and skip_tx_verification is False
        """
        request = await self.get_deposit_by_id(deposit_id)
        if not request:
            raise DepositProcessorError(f"Deposit not found: {deposit_id}")
        
        if request.status != DepositRequestStatus.PENDING:
            raise DepositProcessorError(
                f"Cannot approve deposit with status: {request.status}"
            )
        
        # Require tx_hash unless explicitly skipped (elevated permission)
        if not tx_hash and not skip_tx_verification:
            raise DepositProcessorError(
                "Transaction hash (tx_hash) is required for manual approval. "
                "Use skip_tx_verification=True only with elevated permissions."
            )
        
        # Generate synthetic tx_hash only when explicitly skipping verification
        if not tx_hash:
            tx_hash = f"manual_no_tx_{admin_user_id}_{datetime.now(timezone.utc).timestamp()}"
            logger.warning(
                f"Manual approval without tx_hash for deposit {deposit_id} "
                f"by admin {admin_user_id}. This should be audited."
            )
        
        try:
            await self.credit_balance(
                user_id=request.user_id,
                amount_krw=request.requested_krw,
                memo=request.memo,
                tx_hash=tx_hash,
            )
            
            request.status = DepositRequestStatus.CONFIRMED
            request.tx_hash = tx_hash
            request.confirmed_at = datetime.now(timezone.utc)
            
            # Create audit log with admin info and real IP address
            audit_log = AuditLog(
                action="deposit_manual_approved",
                target_type="deposit_request",
                target_id=str(request.id),
                admin_user_id=admin_user_id,
                ip_address=ip_address,
                details={
                    "memo": request.memo,
                    "requested_krw": request.requested_krw,
                    "tx_hash": tx_hash,
                    "notes": notes,
                    "target_user_id": request.user_id,
                },
            )
            self.admin_db.add(audit_log)
            
            await self.admin_db.commit()
            await self.admin_db.refresh(request)
            
            logger.info(
                f"Deposit manually approved: {request.memo} by admin {admin_user_id} from IP {ip_address}"
            )
            
            return request
            
        except Exception as e:
            await self.admin_db.rollback()
            raise DepositProcessorError(f"Manual approval failed: {e}")
    
    async def manual_reject(
        self,
        deposit_id: UUID,
        admin_user_id: str,
        reason: str,
        ip_address: str = "unknown",
    ) -> DepositRequest:
        """Manually reject a deposit request.
        
        Args:
            deposit_id: Deposit request ID
            admin_user_id: Admin user performing the action
            reason: Rejection reason
            ip_address: IP address of the admin making the request
            
        Returns:
            Updated DepositRequest
        """
        request = await self.get_deposit_by_id(deposit_id)
        if not request:
            raise DepositProcessorError(f"Deposit not found: {deposit_id}")
        
        if request.status != DepositRequestStatus.PENDING:
            raise DepositProcessorError(
                f"Cannot reject deposit with status: {request.status}"
            )
        
        try:
            request.status = DepositRequestStatus.CANCELLED
            
            # Create audit log with real IP address
            audit_log = AuditLog(
                action="deposit_manual_rejected",
                target_type="deposit_request",
                target_id=str(request.id),
                admin_user_id=admin_user_id,
                ip_address=ip_address,
                details={
                    "memo": request.memo,
                    "requested_krw": request.requested_krw,
                    "reason": reason,
                    "target_user_id": request.user_id,
                },
            )
            self.admin_db.add(audit_log)
            
            await self.admin_db.commit()
            await self.admin_db.refresh(request)
            
            logger.info(
                f"Deposit manually rejected: {request.memo} by admin {admin_user_id} from IP {ip_address}"
            )
            
            return request
            
        except Exception as e:
            await self.admin_db.rollback()
            raise DepositProcessorError(f"Manual rejection failed: {e}")
