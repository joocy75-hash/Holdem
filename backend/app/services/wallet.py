"""Wallet Service for KRW balance operations.

Phase 5.7: Core wallet service for balance management.

Features:
- Atomic KRW transfers (buy-in, cash-out)
- Distributed locking for concurrent safety
- Full transaction logging with integrity hash
- Redis caching for balance lookups
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.wallet import (
    TransactionStatus,
    TransactionType,
    WalletTransaction,
)

if TYPE_CHECKING:
    from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class WalletError(Exception):
    """Wallet operation error with error code."""

    def __init__(self, message: str, code: str = "WALLET_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class InsufficientBalanceError(WalletError):
    """Insufficient balance error with details."""

    def __init__(self, current: int, required: int):
        super().__init__(
            f"Insufficient balance: {current} < {required}",
            code="INSUFFICIENT_BALANCE",
        )
        self.current = current
        self.required = required


class WalletService:
    """Wallet service for KRW balance operations.

    Features:
    - Thread-safe balance operations using Redis distributed locks
    - Transaction logging with SHA-256 integrity hashes
    - Automatic cache invalidation on balance changes
    """

    LOCK_TTL = 10  # Lock timeout in seconds
    BALANCE_CACHE_TTL = 300  # 5 minute cache for balances
    BALANCE_KEY_PREFIX = "wallet:balance:"
    LOCK_KEY_PREFIX = "wallet:lock:"

    # Load Lua script
    LUA_SCRIPT: str | None = None

    @classmethod
    def _load_lua_script(cls) -> str:
        """Load Lua script from file."""
        if cls.LUA_SCRIPT is None:
            script_path = Path(__file__).parent.parent / "utils" / "lua_scripts" / "krw_transfer.lua"
            with open(script_path) as f:
                cls.LUA_SCRIPT = f.read()
        return cls.LUA_SCRIPT

    def __init__(self, session: AsyncSession) -> None:
        """Initialize wallet service."""
        self.session = session
        self._redis: Redis | None = None

    async def _get_redis(self) -> Redis:
        """Get Redis client, initializing if needed.
        
        Returns:
            Redis client instance
            
        Raises:
            WalletError: If Redis is unavailable
        """
        if self._redis is not None:
            return self._redis
        
        from app.utils.redis_client import get_redis_client
        
        try:
            self._redis = await get_redis_client()
            return self._redis
        except Exception as e:
            logger.error(f"Failed to get Redis client: {e}")
            raise WalletError(
                "Wallet service temporarily unavailable",
                code="REDIS_UNAVAILABLE",
            ) from e

    async def get_balance(self, user_id: str) -> int:
        """Get user's KRW balance with caching.

        Args:
            user_id: User ID

        Returns:
            Current KRW balance
            
        Raises:
            WalletError: If user not found
        """
        # Early validation
        if not user_id:
            raise WalletError("User ID is required", code="INVALID_USER_ID")
        
        redis = await self._get_redis()
        cache_key = f"{self.BALANCE_KEY_PREFIX}{user_id}"
        
        # Try cache first
        try:
            cached = await redis.get(cache_key)
            if cached is not None:
                return int(cached)
        except Exception as e:
            logger.warning(f"Cache read failed for user {user_id[:8]}...: {e}")

        # Fetch from database
        user = await self.session.get(User, user_id)
        if not user:
            raise WalletError(f"User not found: {user_id}", code="USER_NOT_FOUND")

        # Cache the balance (fire-and-forget with error handling)
        try:
            await redis.setex(
                cache_key,
                self.BALANCE_CACHE_TTL,
                str(user.krw_balance),
            )
        except Exception as e:
            logger.warning(f"Cache write failed for user {user_id[:8]}...: {e}")

        return user.krw_balance

    async def transfer_krw(
        self,
        user_id: str,
        amount: int,
        tx_type: TransactionType,
        *,
        table_id: str | None = None,
        hand_id: str | None = None,
        description: str | None = None,
    ) -> WalletTransaction:
        """Transfer KRW (debit or credit) with distributed locking.

        Args:
            user_id: User ID
            amount: Amount to transfer (positive = credit, negative = debit)
            tx_type: Transaction type for logging
            table_id: Optional table reference
            hand_id: Optional hand reference
            description: Optional description

        Returns:
            WalletTransaction record

        Raises:
            InsufficientBalanceError: If debit exceeds balance
            WalletError: For other errors
        """
        # Early validation
        if not user_id:
            raise WalletError("User ID is required", code="INVALID_USER_ID")
        if amount == 0:
            raise WalletError("Amount cannot be zero", code="INVALID_AMOUNT")

        redis = await self._get_redis()
        lock_key = f"{self.LOCK_KEY_PREFIX}{user_id}"
        lock_token = str(uuid4())

        try:
            # Acquire distributed lock
            lock_acquired = await redis.set(
                lock_key,
                lock_token,
                nx=True,
                ex=self.LOCK_TTL,
            )
            if not lock_acquired:
                logger.warning(f"Lock contention for user {user_id[:8]}...")
                raise WalletError(
                    "Could not acquire wallet lock, try again",
                    code="LOCK_CONTENTION",
                )

            # Get current balance
            user = await self.session.get(User, user_id)
            if not user:
                raise WalletError(f"User not found: {user_id}", code="USER_NOT_FOUND")

            balance_before = user.krw_balance

            # Validate for debit (early return pattern)
            if amount < 0 and user.krw_balance < abs(amount):
                raise InsufficientBalanceError(
                    current=user.krw_balance,
                    required=abs(amount),
                )

            # Update balance
            balance_after = balance_before + amount
            user.krw_balance = balance_after

            # Create transaction record
            tx = WalletTransaction(
                id=str(uuid4()),
                user_id=user_id,
                tx_type=tx_type,
                status=TransactionStatus.COMPLETED,
                krw_amount=amount,
                krw_balance_before=balance_before,
                krw_balance_after=balance_after,
                table_id=table_id,
                hand_id=hand_id,
                description=description,
                integrity_hash=self._compute_integrity_hash(
                    user_id=user_id,
                    tx_type=tx_type,
                    amount=amount,
                    balance_before=balance_before,
                    balance_after=balance_after,
                ),
            )

            self.session.add(tx)
            await self.session.flush()

            # Invalidate cache (with error handling)
            cache_key = f"{self.BALANCE_KEY_PREFIX}{user_id}"
            try:
                await redis.delete(cache_key)
            except Exception as e:
                logger.warning(f"Cache invalidation failed for user {user_id[:8]}...: {e}")

            logger.info(
                "wallet_transfer",
                extra={
                    "user_id": user_id[:8],
                    "tx_type": tx_type.value,
                    "amount": amount,
                    "balance_before": balance_before,
                    "balance_after": balance_after,
                },
            )

            return tx

        finally:
            # Release lock - verify ownership before deletion
            try:
                current_token = await redis.get(lock_key)
                # Handle both string and bytes response
                if current_token:
                    token_str = (
                        current_token.decode()
                        if isinstance(current_token, bytes)
                        else current_token
                    )
                    if token_str == lock_token:
                        await redis.delete(lock_key)
            except Exception as e:
                logger.error(f"Lock release failed for user {user_id[:8]}...: {e}")

    async def buy_in(
        self,
        user_id: str,
        amount: int,
        table_id: str,
    ) -> WalletTransaction:
        """Table buy-in (transfer from balance to table chips).

        Args:
            user_id: User ID
            amount: Buy-in amount (positive)
            table_id: Table ID

        Returns:
            WalletTransaction record
        """
        if amount <= 0:
            raise WalletError("Buy-in amount must be positive")

        return await self.transfer_krw(
            user_id=user_id,
            amount=-amount,  # Debit
            tx_type=TransactionType.BUY_IN,
            table_id=table_id,
            description=f"Table buy-in: {amount:,} KRW",
        )

    async def cash_out(
        self,
        user_id: str,
        amount: int,
        table_id: str,
    ) -> WalletTransaction:
        """Table cash-out (transfer from table chips to balance).

        Args:
            user_id: User ID
            amount: Cash-out amount (positive)
            table_id: Table ID

        Returns:
            WalletTransaction record
        """
        if amount <= 0:
            raise WalletError("Cash-out amount must be positive")

        return await self.transfer_krw(
            user_id=user_id,
            amount=amount,  # Credit
            tx_type=TransactionType.CASH_OUT,
            table_id=table_id,
            description=f"Table cash-out: {amount:,} KRW",
        )

    async def record_win(
        self,
        user_id: str,
        amount: int,
        table_id: str,
        hand_id: str,
    ) -> WalletTransaction:
        """Record pot winnings.

        Args:
            user_id: User ID
            amount: Win amount (positive)
            table_id: Table ID
            hand_id: Hand ID

        Returns:
            WalletTransaction record
        """
        return await self.transfer_krw(
            user_id=user_id,
            amount=amount,
            tx_type=TransactionType.WIN,
            table_id=table_id,
            hand_id=hand_id,
            description=f"Pot won: {amount:,} KRW",
        )

    async def deduct_rake(
        self,
        user_id: str,
        amount: int,
        table_id: str,
        hand_id: str,
    ) -> WalletTransaction:
        """Deduct rake from player.

        Args:
            user_id: User ID
            amount: Rake amount (positive, will be debited)
            table_id: Table ID
            hand_id: Hand ID

        Returns:
            WalletTransaction record
        """
        if amount <= 0:
            return None  # No rake to deduct

        # Also update total_rake_paid for VIP calculation
        user = await self.session.get(User, user_id)
        if user:
            user.total_rake_paid_krw += amount

        return await self.transfer_krw(
            user_id=user_id,
            amount=-amount,  # Debit
            tx_type=TransactionType.RAKE,
            table_id=table_id,
            hand_id=hand_id,
            description=f"Rake deducted: {amount:,} KRW",
        )

    async def get_transactions(
        self,
        user_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
        tx_type: TransactionType | None = None,
    ) -> list[WalletTransaction]:
        """Get user's transaction history.

        Args:
            user_id: User ID
            limit: Max transactions to return
            offset: Pagination offset
            tx_type: Optional filter by transaction type

        Returns:
            List of transactions
        """
        query = (
            select(WalletTransaction)
            .where(WalletTransaction.user_id == user_id)
            .order_by(WalletTransaction.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        if tx_type:
            query = query.where(WalletTransaction.tx_type == tx_type)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    def _compute_integrity_hash(
        user_id: str,
        tx_type: TransactionType,
        amount: int,
        balance_before: int,
        balance_after: int,
    ) -> str:
        """Compute SHA-256 integrity hash for transaction.

        This hash can be verified later to detect tampering.
        """
        data = f"{user_id}:{tx_type.value}:{amount}:{balance_before}:{balance_after}"
        return hashlib.sha256(data.encode()).hexdigest()

    @staticmethod
    def verify_integrity(tx: WalletTransaction) -> bool:
        """Verify transaction integrity hash."""
        expected = WalletService._compute_integrity_hash(
            user_id=tx.user_id,
            tx_type=tx.tx_type,
            amount=tx.krw_amount,
            balance_before=tx.krw_balance_before,
            balance_after=tx.krw_balance_after,
        )
        return tx.integrity_hash == expected
