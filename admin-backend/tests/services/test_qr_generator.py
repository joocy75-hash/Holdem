"""Unit tests for QRGenerator."""

import pytest
from decimal import Decimal

from app.services.crypto.qr_generator import QRGenerator


class TestQRGenerator:
    """Test cases for QRGenerator."""

    @pytest.fixture
    def generator(self):
        """Create generator with test wallet address."""
        return QRGenerator(wallet_address="EQTestWallet123")

    def test_generate_ton_uri_basic(self, generator):
        """Test basic URI generation."""
        uri = generator.generate_ton_uri(
            amount_usdt=Decimal("68.027"),
            memo="test_memo_123"
        )
        
        assert "ton://transfer/EQTestWallet123" in uri
        assert "amount=68027000" in uri  # 68.027 * 10^6
        assert "text=test_memo_123" in uri

    def test_generate_ton_uri_with_jetton(self, generator):
        """Test URI includes jetton master address."""
        uri = generator.generate_ton_uri(
            amount_usdt=Decimal("100.0"),
            memo="test"
        )
        
        assert "jetton=" in uri

    def test_generate_ton_uri_amount_conversion(self, generator):
        """Test USDT to nano conversion."""
        # 1 USDT = 1,000,000 nano
        uri = generator.generate_ton_uri(Decimal("1.0"), "test")
        assert "amount=1000000" in uri
        
        # 0.5 USDT = 500,000 nano
        uri = generator.generate_ton_uri(Decimal("0.5"), "test")
        assert "amount=500000" in uri
        
        # 100 USDT = 100,000,000 nano
        uri = generator.generate_ton_uri(Decimal("100.0"), "test")
        assert "amount=100000000" in uri

    def test_generate_qr_image_returns_png(self, generator):
        """Test QR image is valid PNG."""
        uri = generator.generate_ton_uri(Decimal("68.0"), "test")
        png_bytes = generator.generate_qr_image(uri)
        
        # Check PNG signature
        assert png_bytes[:4] == b'\x89PNG'
        assert len(png_bytes) > 100

    def test_generate_qr_image_custom_size(self, generator):
        """Test QR image with custom size."""
        uri = generator.generate_ton_uri(Decimal("68.0"), "test")
        
        small = generator.generate_qr_image(uri, size=128)
        large = generator.generate_qr_image(uri, size=512)
        
        # Larger image should have more bytes
        assert len(large) > len(small)

    def test_generate_qr_base64_format(self, generator):
        """Test base64 output format."""
        uri = generator.generate_ton_uri(Decimal("68.0"), "test")
        b64 = generator.generate_qr_base64(uri)
        
        assert b64.startswith("data:image/png;base64,")
        # Should be valid base64
        import base64
        data_part = b64.split(",")[1]
        decoded = base64.b64decode(data_part)
        assert decoded[:4] == b'\x89PNG'

    def test_generate_deposit_qr_complete(self, generator):
        """Test complete deposit QR generation."""
        result = generator.generate_deposit_qr(
            amount_usdt=Decimal("68.027"),
            memo="user_123_test"
        )
        
        assert "uri" in result
        assert "qr_base64" in result
        assert "amount_usdt" in result
        assert "memo" in result
        assert "wallet_address" in result
        
        assert result["memo"] == "user_123_test"
        assert result["amount_usdt"] == "68.027"
        assert result["wallet_address"] == "EQTestWallet123"

    def test_usdt_decimals_constant(self, generator):
        """Test USDT decimals is 6."""
        assert generator.USDT_DECIMALS == 6

    def test_default_wallet_from_config(self):
        """Test default wallet address from config."""
        gen = QRGenerator()
        # Should use config value (may be empty in test)
        assert gen.wallet_address is not None
