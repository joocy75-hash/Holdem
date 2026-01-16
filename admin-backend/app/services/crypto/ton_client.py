"""TON Blockchain Client for USDT Jetton operations.

Provides methods to interact with TON blockchain for monitoring
USDT (Jetton) transfers and wallet operations.
"""

import logging
from decimal import Decimal, ROUND_DOWN
from typing import Optional, List
from dataclasses import dataclass, field
from datetime import datetime

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# USDT Jetton Master Address (Official)
USDT_JETTON_MASTER = "EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs"
USDT_DECIMALS = 6

# Decimal precision for USDT amounts (6 decimal places)
USDT_PRECISION = Decimal("0.000001")


def _mask_sensitive(value: str, visible_chars: int = 4) -> str:
    """Mask sensitive values for logging.
    
    Args:
        value: The sensitive value to mask
        visible_chars: Number of characters to show at start and end
        
    Returns:
        Masked string like "abc...xyz"
    """
    if not value or len(value) <= visible_chars * 2:
        return "***"
    return f"{value[:visible_chars]}...{value[-visible_chars:]}"


@dataclass(frozen=True)
class JettonTransfer:
    """Represents a Jetton (USDT) transfer on TON blockchain.
    
    Immutable dataclass to prevent accidental modification.
    """
    tx_hash: str
    sender: str
    recipient: str
    amount: Decimal  # In USDT (not nano)
    memo: Optional[str]
    timestamp: datetime
    lt: int  # Logical time for ordering
    
    def __post_init__(self):
        """Validate transfer data."""
        if self.amount < 0:
            raise ValueError("Transfer amount cannot be negative")


class TonClientError(Exception):
    """Exception raised for TON client errors."""
    pass


class TonClientConfigError(TonClientError):
    """Exception raised for configuration errors."""
    pass


class TonClient:
    """Client for interacting with TON blockchain.
    
    Uses TON Center API or TonAPI for blockchain queries.
    Supports both testnet and mainnet.
    
    Security Notes:
    - Hot wallet address and API keys should be stored securely
    - Consider using AWS Secrets Manager or HashiCorp Vault for production
    - API keys are masked in logs to prevent exposure
    """
    
    # API endpoints
    TONCENTER_MAINNET = "https://toncenter.com/api/v2"
    TONCENTER_TESTNET = "https://testnet.toncenter.com/api/v2"
    TONAPI_MAINNET = "https://tonapi.io/v2"
    TONAPI_TESTNET = "https://testnet.tonapi.io/v2"
    
    def __init__(
        self,
        wallet_address: Optional[str] = None,
        network: str = "testnet",
        api_key: Optional[str] = None,
    ):
        """Initialize TON client.
        
        Args:
            wallet_address: Hot wallet address to monitor
            network: "mainnet" or "testnet"
            api_key: TON Center or TonAPI key
            
        Raises:
            TonClientConfigError: If required configuration is missing
        """
        self.wallet_address = wallet_address or settings.ton_hot_wallet_address
        self.network = network or settings.ton_network
        self.api_key = api_key or settings.ton_center_api_key
        
        # Validate configuration
        self._validate_config()
        
        # Set API base URL based on network
        if self.network == "mainnet":
            self.toncenter_url = self.TONCENTER_MAINNET
            self.tonapi_url = self.TONAPI_MAINNET
        else:
            self.toncenter_url = self.TONCENTER_TESTNET
            self.tonapi_url = self.TONAPI_TESTNET
        
        self._http_client: Optional[httpx.AsyncClient] = None
        
        # Log initialization with masked sensitive data
        logger.info(
            f"TonClient initialized for {self.network} network, "
            f"wallet: {_mask_sensitive(self.wallet_address) if self.wallet_address else 'not configured'}, "
            f"api_key: {'configured' if self.api_key else 'not configured'}"
        )
    
    def _validate_config(self):
        """Validate client configuration.
        
        Raises:
            TonClientConfigError: If configuration is invalid
        """
        # Validate network
        if self.network not in ("mainnet", "testnet"):
            raise TonClientConfigError(
                f"Invalid network: {self.network}. Must be 'mainnet' or 'testnet'"
            )
        
        # Warn if hot wallet is not configured (but don't fail)
        if not self.wallet_address:
            logger.warning(
                "TON hot wallet address not configured. "
                "Set TON_HOT_WALLET_ADDRESS environment variable."
            )
        
        # Warn if API key is not configured
        if not self.api_key:
            logger.warning(
                "TON API key not configured. API rate limits may apply. "
                "Set TON_CENTER_API_KEY environment variable."
            )
        
        # Validate wallet address format (basic check)
        if self.wallet_address and not self._is_valid_ton_address(self.wallet_address):
            raise TonClientConfigError(
                f"Invalid TON wallet address format: {_mask_sensitive(self.wallet_address)}"
            )
    
    def _is_valid_ton_address(self, address: str) -> bool:
        """Basic validation of TON address format.
        
        Args:
            address: TON address to validate
            
        Returns:
            bool: True if address appears valid
        """
        # TON addresses are typically 48 characters (base64) or start with EQ/UQ
        if not address:
            return False
        
        # Check for common TON address formats
        if address.startswith(("EQ", "UQ", "0:", "-1:")):
            return len(address) >= 48
        
        # Base64 encoded address
        if len(address) == 48:
            return True
        
        return False
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            headers = {}
            if self.api_key:
                headers["X-API-Key"] = self.api_key
            self._http_client = httpx.AsyncClient(
                timeout=30.0,
                headers=headers,
            )
        return self._http_client
    
    async def close(self):
        """Close HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
    
    async def get_jetton_wallet_address(
        self,
        owner_address: str,
        jetton_master: str = USDT_JETTON_MASTER,
    ) -> Optional[str]:
        """Get Jetton wallet address for an owner.
        
        Each user has a unique Jetton wallet address derived from
        their main wallet and the Jetton master contract.
        
        Args:
            owner_address: Owner's main TON wallet address
            jetton_master: Jetton master contract address
            
        Returns:
            str: Jetton wallet address or None if not found
        """
        try:
            client = await self._get_http_client()
            
            # Use TonAPI for Jetton wallet lookup
            url = f"{self.tonapi_url}/jettons/{jetton_master}/holders"
            params = {"owner_address": owner_address}
            
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                # Extract wallet address from response
                if "addresses" in data and len(data["addresses"]) > 0:
                    return data["addresses"][0].get("address")
            
            # Fallback: Use TON Center runGetMethod
            url = f"{self.toncenter_url}/runGetMethod"
            params = {
                "address": jetton_master,
                "method": "get_wallet_address",
                "stack": [["tvm.Slice", owner_address]],
            }
            
            response = await client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get("ok") and "result" in data:
                    # Parse result stack
                    stack = data["result"].get("stack", [])
                    if stack:
                        return stack[0][1].get("object", {}).get("data", {}).get("b64")
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting Jetton wallet address: {e}")
            return None
    
    async def get_jetton_transfers(
        self,
        wallet_address: Optional[str] = None,
        limit: int = 100,
        after_lt: Optional[int] = None,
    ) -> List[JettonTransfer]:
        """Get recent Jetton transfers to a wallet.
        
        Args:
            wallet_address: Wallet address to check (defaults to hot wallet)
            limit: Maximum number of transfers to return
            after_lt: Only return transfers after this logical time
            
        Returns:
            List of JettonTransfer objects
        """
        address = wallet_address or self.wallet_address
        if not address:
            raise TonClientError("No wallet address configured")
        
        transfers = []
        
        try:
            client = await self._get_http_client()
            
            # Use TonAPI for Jetton events
            url = f"{self.tonapi_url}/accounts/{address}/jettons/history"
            params = {
                "limit": limit,
                "jetton_id": USDT_JETTON_MASTER,
            }
            if after_lt:
                params["before_lt"] = after_lt
            
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                events = data.get("events", [])
                
                for event in events:
                    transfer = self._parse_jetton_event(event)
                    if transfer:
                        transfers.append(transfer)
            else:
                # Fallback to TON Center
                transfers = await self._get_transfers_toncenter(address, limit, after_lt)
            
        except Exception as e:
            logger.error(f"Error getting Jetton transfers: {e}")
            # Try fallback
            try:
                transfers = await self._get_transfers_toncenter(address, limit, after_lt)
            except Exception as e2:
                logger.error(f"Fallback also failed: {e2}")
        
        return transfers
    
    async def _get_transfers_toncenter(
        self,
        address: str,
        limit: int,
        after_lt: Optional[int],
    ) -> List[JettonTransfer]:
        """Get transfers using TON Center API."""
        transfers = []
        
        try:
            client = await self._get_http_client()
            
            url = f"{self.toncenter_url}/getTransactions"
            params = {
                "address": address,
                "limit": limit,
            }
            if after_lt:
                params["lt"] = after_lt
            
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    for tx in data.get("result", []):
                        transfer = self._parse_toncenter_tx(tx)
                        if transfer:
                            transfers.append(transfer)
        
        except Exception as e:
            logger.error(f"TON Center API error: {e}")
        
        return transfers
    
    def _parse_jetton_event(self, event: dict) -> Optional[JettonTransfer]:
        """Parse TonAPI Jetton event into JettonTransfer."""
        try:
            actions = event.get("actions", [])
            for action in actions:
                if action.get("type") == "JettonTransfer":
                    jetton = action.get("JettonTransfer", {})
                    
                    # Convert nano to USDT with explicit rounding policy
                    # ROUND_DOWN ensures we never credit more than received
                    amount_nano = int(jetton.get("amount", 0))
                    amount = (Decimal(amount_nano) / Decimal(10 ** USDT_DECIMALS)).quantize(
                        USDT_PRECISION, rounding=ROUND_DOWN
                    )
                    
                    return JettonTransfer(
                        tx_hash=event.get("event_id", ""),
                        sender=jetton.get("sender", {}).get("address", ""),
                        recipient=jetton.get("recipient", {}).get("address", ""),
                        amount=amount,
                        memo=jetton.get("comment"),
                        timestamp=datetime.fromtimestamp(event.get("timestamp", 0)),
                        lt=event.get("lt", 0),
                    )
        except Exception as e:
            logger.warning(f"Error parsing Jetton event: {e}")
        
        return None
    
    def _parse_toncenter_tx(self, tx: dict) -> Optional[JettonTransfer]:
        """Parse TON Center transaction into JettonTransfer."""
        try:
            in_msg = tx.get("in_msg", {})
            
            # Check if this is a Jetton transfer
            msg_data = in_msg.get("msg_data", {})
            if msg_data.get("@type") != "msg.dataText":
                return None
            
            # Extract memo from message
            memo = msg_data.get("text", "")
            
            # Get amount (this is simplified - real implementation needs Jetton parsing)
            # ROUND_DOWN ensures we never credit more than received
            value = int(in_msg.get("value", 0))
            amount = (Decimal(value) / Decimal(10 ** USDT_DECIMALS)).quantize(
                USDT_PRECISION, rounding=ROUND_DOWN
            )
            
            return JettonTransfer(
                tx_hash=tx.get("transaction_id", {}).get("hash", ""),
                sender=in_msg.get("source", ""),
                recipient=in_msg.get("destination", ""),
                amount=amount,
                memo=memo if memo else None,
                timestamp=datetime.fromtimestamp(tx.get("utime", 0)),
                lt=tx.get("transaction_id", {}).get("lt", 0),
            )
        except Exception as e:
            logger.warning(f"Error parsing TON Center tx: {e}")
        
        return None
    
    async def verify_transaction(self, tx_hash: str) -> bool:
        """Verify a transaction exists and is confirmed.
        
        Args:
            tx_hash: Transaction hash to verify
            
        Returns:
            bool: True if transaction is confirmed
        """
        try:
            client = await self._get_http_client()
            
            url = f"{self.tonapi_url}/blockchain/transactions/{tx_hash}"
            response = await client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                # Check if transaction is successful
                return data.get("success", False)
            
            return False
            
        except Exception as e:
            logger.error(f"Error verifying transaction: {e}")
            return False
    
    async def get_wallet_balance(
        self,
        wallet_address: Optional[str] = None,
    ) -> Decimal:
        """Get USDT balance of a wallet.
        
        Args:
            wallet_address: Wallet to check (defaults to hot wallet)
            
        Returns:
            Decimal: USDT balance with 6 decimal places
            
        Raises:
            TonClientError: If balance cannot be retrieved
        """
        address = wallet_address or self.wallet_address
        if not address:
            raise TonClientError("No wallet address configured")
        
        try:
            client = await self._get_http_client()
            
            url = f"{self.tonapi_url}/accounts/{address}/jettons"
            response = await client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                balances = data.get("balances", [])
                
                for balance in balances:
                    jetton = balance.get("jetton", {})
                    if jetton.get("address") == USDT_JETTON_MASTER:
                        amount_nano = int(balance.get("balance", 0))
                        # ROUND_DOWN for balance to be conservative
                        return (Decimal(amount_nano) / Decimal(10 ** USDT_DECIMALS)).quantize(
                            USDT_PRECISION, rounding=ROUND_DOWN
                        )
            
            return Decimal("0")
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting wallet balance: {e}")
            raise TonClientError(f"Failed to get wallet balance: {e}")
        except Exception as e:
            logger.error(f"Error getting wallet balance: {e}", exc_info=True)
            raise TonClientError(f"Failed to get wallet balance: {e}")
