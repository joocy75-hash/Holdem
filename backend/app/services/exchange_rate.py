"""Exchange Rate Service for cryptocurrency to KRW conversion.

Phase 5.5: Real-time exchange rate API integration.
- Primary: jsdelivr CDN (fawazahmed0/currency-api)
- Fallback: Cloudflare Pages
- Redis caching with 60-second TTL

지원 코인:
- USDT: USD/KRW 환율 사용 (1:1 페깅)

Note: XRP, TRX, SOL은 더 이상 지원하지 않습니다.
"""

import logging
from decimal import Decimal

import httpx

from app.models.wallet import CryptoType
from app.utils.redis_client import get_redis

logger = logging.getLogger(__name__)

# API URLs
PRIMARY_API_URL = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.min.json"
FALLBACK_API_URL = "https://latest.currency-api.pages.dev/v1/currencies/usd.min.json"


class ExchangeRateError(Exception):
    """Exchange rate fetch error."""

    pass


class ExchangeRateService:
    """Real-time cryptocurrency exchange rate service.

    Features:
    - Real-time rate fetching from fawazahmed0/currency-api
    - Redis caching with 60-second TTL
    - Fallback to cached rate on API failure
    - Support for USDT only (uses USD/KRW rate with 1:1 peg assumption)
    """

    CACHE_TTL = 60  # 1 minute cache
    CACHE_KEY_PREFIX = "exchange_rate:"

    def __init__(self) -> None:
        """Initialize exchange rate service."""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0),
            limits=httpx.Limits(max_connections=20),
        )

    async def close(self) -> None:
        """Close HTTP client."""
        await self._client.aclose()

    async def get_rate_to_krw(self, crypto_type: CryptoType) -> int:
        """Get exchange rate: 1 crypto = X KRW.

        Args:
            crypto_type: Cryptocurrency type (only USDT supported)

        Returns:
            Exchange rate in KRW (integer)

        Raises:
            ExchangeRateError: If rate cannot be fetched or crypto_type not supported
        """
        # USDT만 지원
        if crypto_type != CryptoType.USDT:
            raise ExchangeRateError(
                f"{crypto_type.value}는 더 이상 지원하지 않습니다. USDT만 사용 가능합니다."
            )

        cache_key = f"{self.CACHE_KEY_PREFIX}{crypto_type.value}"

        # Try cache first
        redis = get_redis()
        cached_rate = await redis.get(cache_key)
        if cached_rate:
            logger.debug(f"Cache hit for {crypto_type.value} rate: {cached_rate}")
            return int(cached_rate)

        # Fetch from API
        rate = await self._fetch_rate_jsdelivr()
        if rate is None:
            rate = await self._fetch_rate_cloudflare()

        if rate is None:
            # Try to return stale cache
            stale_key = f"{cache_key}:stale"
            stale_rate = await redis.get(stale_key)
            if stale_rate:
                logger.warning(
                    f"Using stale rate for {crypto_type.value}: {stale_rate}"
                )
                return int(stale_rate)
            raise ExchangeRateError(f"Could not fetch rate for {crypto_type.value}")

        # Cache the rate
        await redis.setex(cache_key, self.CACHE_TTL, str(rate))
        # Also keep a stale copy for 24 hours as fallback
        await redis.setex(f"{cache_key}:stale", 86400, str(rate))

        logger.info(f"Fetched {crypto_type.value} rate: {rate:,} KRW")
        return rate

    async def _fetch_rate_jsdelivr(self) -> int | None:
        """Fetch USD/KRW rate from jsdelivr CDN (primary)."""
        try:
            response = await self._client.get(PRIMARY_API_URL)
            response.raise_for_status()
            data = response.json()
            # 응답 형식: {"date": "2026-01-19", "usd": {"krw": 1474.99, ...}}
            rate = int(float(data["usd"]["krw"]))
            logger.info(f"jsdelivr USD/KRW: {rate}")
            return rate
        except Exception as e:
            logger.warning(f"jsdelivr API error: {e}")
            return None

    async def _fetch_rate_cloudflare(self) -> int | None:
        """Fetch USD/KRW rate from Cloudflare Pages (fallback)."""
        try:
            response = await self._client.get(FALLBACK_API_URL)
            response.raise_for_status()
            data = response.json()
            # 응답 형식: {"date": "2026-01-19", "usd": {"krw": 1474.99, ...}}
            rate = int(float(data["usd"]["krw"]))
            logger.info(f"Cloudflare USD/KRW: {rate}")
            return rate
        except Exception as e:
            logger.warning(f"Cloudflare API error: {e}")
            return None

    async def convert_crypto_to_krw(
        self,
        crypto_type: CryptoType,
        crypto_amount: str | Decimal,
    ) -> tuple[int, int]:
        """Convert cryptocurrency amount to KRW.

        Args:
            crypto_type: Cryptocurrency type
            crypto_amount: Amount in crypto (string/Decimal for precision)

        Returns:
            Tuple of (krw_amount, exchange_rate)
        """
        if isinstance(crypto_amount, str):
            crypto_amount = Decimal(crypto_amount)

        rate = await self.get_rate_to_krw(crypto_type)
        krw_amount = int(crypto_amount * rate)

        return krw_amount, rate

    async def convert_krw_to_crypto(
        self,
        crypto_type: CryptoType,
        krw_amount: int,
    ) -> tuple[Decimal, int]:
        """Convert KRW amount to cryptocurrency.

        Args:
            crypto_type: Cryptocurrency type
            krw_amount: Amount in KRW

        Returns:
            Tuple of (crypto_amount as Decimal, exchange_rate)
        """
        rate = await self.get_rate_to_krw(crypto_type)
        crypto_amount = Decimal(krw_amount) / Decimal(rate)

        return crypto_amount, rate

    async def get_all_rates(self) -> dict[CryptoType, int]:
        """Get all supported crypto rates.

        Returns:
            Dict mapping CryptoType to KRW rate (USDT only)
        """
        result = {}
        try:
            rate = await self.get_rate_to_krw(CryptoType.USDT)
            result[CryptoType.USDT] = rate
        except ExchangeRateError as e:
            logger.error(f"Failed to get USDT rate: {e}")
        return result


# Singleton instance
_exchange_rate_service: ExchangeRateService | None = None


def get_exchange_rate_service() -> ExchangeRateService:
    """Get exchange rate service singleton."""
    global _exchange_rate_service
    if _exchange_rate_service is None:
        _exchange_rate_service = ExchangeRateService()
    return _exchange_rate_service


async def close_exchange_rate_service() -> None:
    """Close exchange rate service."""
    global _exchange_rate_service
    if _exchange_rate_service:
        await _exchange_rate_service.close()
        _exchange_rate_service = None
