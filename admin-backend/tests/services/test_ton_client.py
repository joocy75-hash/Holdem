"""Unit tests for TonClient."""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.crypto.ton_client import (
    TonClient,
    JettonTransfer,
    TonClientError,
    TonClientConfigError,
    USDT_JETTON_MASTER,
    USDT_DECIMALS,
)

# Valid test wallet address (48 chars, starts with EQ)
TEST_WALLET_ADDRESS = "EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs"


class TestTonClientConstants:
    """Test TON client constants."""

    def test_usdt_jetton_master_address(self):
        """Test USDT Jetton master address is correct."""
        assert USDT_JETTON_MASTER == "EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs"

    def test_usdt_decimals(self):
        """Test USDT decimals is 6."""
        assert USDT_DECIMALS == 6


class TestJettonTransfer:
    """Test JettonTransfer dataclass."""

    def test_create_jetton_transfer(self):
        """Test creating a JettonTransfer."""
        transfer = JettonTransfer(
            tx_hash="abc123",
            sender="EQSender",
            recipient="EQRecipient",
            amount=Decimal("68.027"),
            memo="user_123_test",
            timestamp=datetime(2026, 1, 16, 12, 0, 0),
            lt=12345678,
        )
        
        assert transfer.tx_hash == "abc123"
        assert transfer.sender == "EQSender"
        assert transfer.recipient == "EQRecipient"
        assert transfer.amount == Decimal("68.027")
        assert transfer.memo == "user_123_test"
        assert transfer.lt == 12345678

    def test_jetton_transfer_optional_memo(self):
        """Test JettonTransfer with None memo."""
        transfer = JettonTransfer(
            tx_hash="abc123",
            sender="EQSender",
            recipient="EQRecipient",
            amount=Decimal("100.0"),
            memo=None,
            timestamp=datetime.now(),
            lt=0,
        )
        
        assert transfer.memo is None
    
    def test_jetton_transfer_negative_amount_raises(self):
        """Test JettonTransfer raises error for negative amount."""
        with pytest.raises(ValueError, match="cannot be negative"):
            JettonTransfer(
                tx_hash="abc123",
                sender="EQSender",
                recipient="EQRecipient",
                amount=Decimal("-10.0"),
                memo=None,
                timestamp=datetime.now(),
                lt=0,
            )
    
    def test_jetton_transfer_is_immutable(self):
        """Test JettonTransfer is frozen (immutable)."""
        transfer = JettonTransfer(
            tx_hash="abc123",
            sender="EQSender",
            recipient="EQRecipient",
            amount=Decimal("100.0"),
            memo=None,
            timestamp=datetime.now(),
            lt=0,
        )
        
        with pytest.raises(Exception):  # FrozenInstanceError
            transfer.amount = Decimal("200.0")


class TestTonClient:
    """Test TonClient class."""

    @pytest.fixture
    def client(self):
        """Create TonClient for testing."""
        return TonClient(
            wallet_address=TEST_WALLET_ADDRESS,
            network="testnet",
        )

    def test_init_testnet(self):
        """Test client initialization for testnet."""
        client = TonClient(
            wallet_address=TEST_WALLET_ADDRESS,
            network="testnet"
        )
        
        assert client.network == "testnet"
        assert "testnet" in client.toncenter_url
        assert "testnet" in client.tonapi_url

    def test_init_mainnet(self):
        """Test client initialization for mainnet."""
        client = TonClient(
            wallet_address=TEST_WALLET_ADDRESS,
            network="mainnet"
        )
        
        assert client.network == "mainnet"
        assert "testnet" not in client.toncenter_url
        assert "testnet" not in client.tonapi_url
    
    def test_init_invalid_network_raises(self):
        """Test client raises error for invalid network."""
        with pytest.raises(TonClientConfigError, match="Invalid network"):
            TonClient(
                wallet_address=TEST_WALLET_ADDRESS,
                network="invalid"
            )
    
    def test_init_invalid_wallet_address_raises(self):
        """Test client raises error for invalid wallet address."""
        with pytest.raises(TonClientConfigError, match="Invalid TON wallet address"):
            TonClient(
                wallet_address="invalid_short_address",
                network="testnet"
            )

    @pytest.mark.asyncio
    async def test_close_client(self, client):
        """Test closing HTTP client."""
        # Create a mock HTTP client
        client._http_client = AsyncMock()
        client._http_client.is_closed = False
        
        await client.close()
        
        client._http_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_jetton_transfers_no_wallet(self):
        """Test get_jetton_transfers raises error without wallet."""
        client = TonClient(wallet_address=TEST_WALLET_ADDRESS, network="testnet")
        client.wallet_address = ""  # Force empty after init
        
        with pytest.raises(TonClientError):
            await client.get_jetton_transfers(wallet_address="")

    @pytest.mark.asyncio
    async def test_get_jetton_transfers_success(self, client):
        """Test successful Jetton transfer retrieval."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "events": [
                {
                    "event_id": "tx123",
                    "timestamp": 1705401600,
                    "lt": 12345,
                    "actions": [
                        {
                            "type": "JettonTransfer",
                            "JettonTransfer": {
                                "sender": {"address": "EQSender"},
                                "recipient": {"address": "EQRecipient"},
                                "amount": "68027000",  # 68.027 USDT
                                "comment": "user_123_test",
                            }
                        }
                    ]
                }
            ]
        }
        
        with patch.object(client, "_get_http_client") as mock_get_client:
            mock_http = AsyncMock()
            mock_http.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_http
            
            transfers = await client.get_jetton_transfers()
            
            assert len(transfers) == 1
            assert transfers[0].tx_hash == "tx123"
            assert transfers[0].amount == Decimal("68.027")
            assert transfers[0].memo == "user_123_test"

    @pytest.mark.asyncio
    async def test_verify_transaction_success(self, client):
        """Test successful transaction verification."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        
        with patch.object(client, "_get_http_client") as mock_get_client:
            mock_http = AsyncMock()
            mock_http.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_http
            
            result = await client.verify_transaction("tx123")
            
            assert result is True

    @pytest.mark.asyncio
    async def test_verify_transaction_not_found(self, client):
        """Test transaction verification when not found."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        
        with patch.object(client, "_get_http_client") as mock_get_client:
            mock_http = AsyncMock()
            mock_http.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_http
            
            result = await client.verify_transaction("nonexistent")
            
            assert result is False

    @pytest.mark.asyncio
    async def test_get_wallet_balance_success(self, client):
        """Test successful wallet balance retrieval."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "balances": [
                {
                    "jetton": {"address": USDT_JETTON_MASTER},
                    "balance": "100000000",  # 100 USDT
                }
            ]
        }
        
        with patch.object(client, "_get_http_client") as mock_get_client:
            mock_http = AsyncMock()
            mock_http.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_http
            
            balance = await client.get_wallet_balance()
            
            assert balance == Decimal("100")

    @pytest.mark.asyncio
    async def test_get_wallet_balance_no_usdt(self, client):
        """Test wallet balance when no USDT."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"balances": []}
        
        with patch.object(client, "_get_http_client") as mock_get_client:
            mock_http = AsyncMock()
            mock_http.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_http
            
            balance = await client.get_wallet_balance()
            
            assert balance == Decimal("0")
    
    @pytest.mark.asyncio
    async def test_get_wallet_balance_error_raises(self, client):
        """Test wallet balance raises error on HTTP failure."""
        import httpx
        
        with patch.object(client, "_get_http_client") as mock_get_client:
            mock_http = AsyncMock()
            mock_http.get = AsyncMock(side_effect=httpx.HTTPError("Connection failed"))
            mock_get_client.return_value = mock_http
            
            with pytest.raises(TonClientError, match="Failed to get wallet balance"):
                await client.get_wallet_balance()

    def test_parse_jetton_event_valid(self, client):
        """Test parsing valid Jetton event."""
        event = {
            "event_id": "tx123",
            "timestamp": 1705401600,
            "lt": 12345,
            "actions": [
                {
                    "type": "JettonTransfer",
                    "JettonTransfer": {
                        "sender": {"address": "EQSender"},
                        "recipient": {"address": "EQRecipient"},
                        "amount": "50000000",  # 50 USDT
                        "comment": "test_memo",
                    }
                }
            ]
        }
        
        transfer = client._parse_jetton_event(event)
        
        assert transfer is not None
        assert transfer.amount == Decimal("50")
        assert transfer.memo == "test_memo"

    def test_parse_jetton_event_invalid(self, client):
        """Test parsing invalid Jetton event."""
        event = {"invalid": "data"}
        
        transfer = client._parse_jetton_event(event)
        
        assert transfer is None
