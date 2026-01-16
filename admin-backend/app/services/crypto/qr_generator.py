"""QR Code Generator for TON/USDT deposits.

Generates QR codes with ton:// transfer URIs for easy wallet scanning.
"""

import base64
import io
import logging
from decimal import Decimal
from typing import Optional

import qrcode
from qrcode.image.pil import PilImage
from PIL import Image

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class QRGenerator:
    """Generator for TON transfer QR codes.
    
    Creates QR codes containing ton:// URIs that can be scanned
    by Tonkeeper, @wallet, and other TON wallets.
    """
    
    # USDT has 6 decimal places (1 USDT = 1,000,000 nano units)
    USDT_DECIMALS = 6
    
    def __init__(self, wallet_address: Optional[str] = None):
        """Initialize QR generator.
        
        Args:
            wallet_address: TON wallet address for receiving deposits.
                          Defaults to config hot wallet address.
        """
        self.wallet_address = wallet_address or settings.ton_hot_wallet_address
    
    def generate_ton_uri(
        self,
        amount_usdt: Decimal,
        memo: str,
        jetton_master: Optional[str] = None,
    ) -> str:
        """Generate ton:// transfer URI.
        
        Args:
            amount_usdt: Amount in USDT (e.g., 68.027)
            memo: Unique memo/comment for transaction matching
            jetton_master: USDT Jetton master address (defaults to config)
            
        Returns:
            str: ton:// URI for wallet scanning
            
        Example:
            ton://transfer/EQxxx?amount=68027000&text=user_123_1705123456_abcd
        """
        jetton = jetton_master or settings.ton_usdt_master_address
        
        # Convert USDT to nano units (× 10^6)
        nano_amount = int(amount_usdt * (10 ** self.USDT_DECIMALS))
        
        # Build URI
        # For Jetton transfers, we use the jetton parameter
        uri = (
            f"ton://transfer/{self.wallet_address}"
            f"?amount={nano_amount}"
            f"&text={memo}"
        )
        
        # Add jetton master for USDT transfers
        if jetton:
            uri += f"&jetton={jetton}"
        
        logger.debug(f"Generated TON URI: {uri}")
        return uri
    
    def generate_qr_image(
        self,
        uri: str,
        size: int = 256,
        border: int = 4,
    ) -> bytes:
        """Generate QR code image as PNG bytes.
        
        Args:
            uri: The ton:// URI to encode
            size: Image size in pixels (default 256)
            border: Border size in modules (default 4)
            
        Returns:
            bytes: PNG image data
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=border,
        )
        qr.add_data(uri)
        qr.make(fit=True)
        
        img: PilImage = qr.make_image(fill_color="black", back_color="white")
        
        # Resize to target size
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        
        # Convert to bytes
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        return buffer.getvalue()
    
    def generate_qr_base64(
        self,
        uri: str,
        size: int = 256,
        border: int = 4,
    ) -> str:
        """Generate QR code as base64-encoded PNG.
        
        Args:
            uri: The ton:// URI to encode
            size: Image size in pixels
            border: Border size in modules
            
        Returns:
            str: Base64-encoded PNG image (data URI format)
        """
        png_bytes = self.generate_qr_image(uri, size, border)
        b64 = base64.b64encode(png_bytes).decode("utf-8")
        return f"data:image/png;base64,{b64}"
    
    def generate_deposit_qr(
        self,
        amount_usdt: Decimal,
        memo: str,
        size: int = 256,
    ) -> dict:
        """Generate complete deposit QR data.
        
        Convenience method that generates URI and QR image together.
        
        Args:
            amount_usdt: Amount in USDT
            memo: Unique memo for matching
            size: QR image size
            
        Returns:
            dict: {
                "uri": "ton://...",
                "qr_base64": "data:image/png;base64,...",
                "amount_usdt": "68.027000",
                "memo": "user_123_...",
                "wallet_address": "EQxxx"
            }
        """
        uri = self.generate_ton_uri(amount_usdt, memo)
        qr_base64 = self.generate_qr_base64(uri, size)
        
        return {
            "uri": uri,
            "qr_base64": qr_base64,
            "amount_usdt": str(amount_usdt),
            "memo": memo,
            "wallet_address": self.wallet_address,
        }
