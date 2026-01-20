"""USDT/KRW Exchange Rate Service.

Fetches real-time USD/KRW exchange rates from fawazahmed0 currency-api.
USDT is pegged to USD, so we use USD/KRW rate as USDT/KRW rate (1:1).

Primary: jsdelivr CDN
Fallback: Cloudflare Pages
"""

import logging
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# API URLs
PRIMARY_API_URL = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.min.json"
FALLBACK_API_URL = "https://latest.currency-api.pages.dev/v1/currencies/usd.min.json"


class TonExchangeRateService:
    """Service for fetching and caching USDT/KRW exchange rates.

    Primary source: jsdelivr CDN (fawazahmed0/currency-api)
    Fallback source: Cloudflare Pages
    Cache: Redis with configurable TTL

    Note: Uses USD/KRW rate as USDT/KRW (1:1 peg assumption)

    Can be used as async context manager for automatic cleanup:
        async with TonExchangeRateService() as service:
            rate = await service.get_usdt_krw_rate()
    """

    CACHE_KEY = "exchange_rate:usdt_krw"

    def __init__(self, redis_client=None):
        """Initialize the exchange rate service.

        Args:
            redis_client: Optional Redis client for caching
        """
        self.redis = redis_client
        self.cache_ttl = settings.exchange_rate_cache_ttl
        self._http_client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - ensures cleanup."""
        await self.close()
        return False

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=10.0)
        return self._http_client

    async def close(self):
        """Close HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None

    async def get_usdt_krw_rate(self) -> Decimal:
        """Get current USDT/KRW exchange rate.

        Tries cache first, then primary API (jsdelivr), then fallback (Cloudflare).

        Returns:
            Decimal: Current USDT/KRW rate (e.g., 1474.99)

        Raises:
            ExchangeRateError: If unable to fetch rate from any source
        """
        # Try cache first
        cached_rate = await self._get_cached_rate()
        if cached_rate is not None:
            logger.debug(f"Cache hit: USDT/KRW = {cached_rate}")
            return cached_rate

        # Try primary API (jsdelivr CDN)
        rate = await self._fetch_from_jsdelivr()
        if rate is not None:
            await self._cache_rate(rate)
            await self._save_rate_history(rate, "jsdelivr")
            return rate

        # Fallback to Cloudflare Pages
        rate = await self._fetch_from_cloudflare()
        if rate is not None:
            await self._cache_rate(rate)
            await self._save_rate_history(rate, "cloudflare")
            return rate

        raise ExchangeRateError("Failed to fetch USDT/KRW rate from all sources")

    async def _get_cached_rate(self) -> Optional[Decimal]:
        """Get rate from Redis cache."""
        if self.redis is None:
            return None
        try:
            cached = await self.redis.get(self.CACHE_KEY)
            if cached:
                return Decimal(cached.decode() if isinstance(cached, bytes) else cached)
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
        return None

    async def _cache_rate(self, rate: Decimal):
        """Store rate in Redis cache."""
        if self.redis is None:
            return
        try:
            await self.redis.setex(self.CACHE_KEY, self.cache_ttl, str(rate))
            logger.debug(f"Cached USDT/KRW rate: {rate}")
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

    async def _fetch_from_jsdelivr(self) -> Optional[Decimal]:
        """Fetch USD/KRW rate from jsdelivr CDN (primary)."""
        try:
            client = await self._get_http_client()
            response = await client.get(PRIMARY_API_URL)
            response.raise_for_status()

            data = response.json()
            # 응답 형식: {"date": "2026-01-19", "usd": {"krw": 1474.99, ...}}
            rate = Decimal(str(data["usd"]["krw"]))
            logger.info(f"jsdelivr USD/KRW: {rate}")
            return rate
        except Exception as e:
            logger.warning(f"jsdelivr API error: {e}")
            return None

    async def _fetch_from_cloudflare(self) -> Optional[Decimal]:
        """Fetch USD/KRW rate from Cloudflare Pages (fallback)."""
        try:
            client = await self._get_http_client()
            response = await client.get(FALLBACK_API_URL)
            response.raise_for_status()

            data = response.json()
            # 응답 형식: {"date": "2026-01-19", "usd": {"krw": 1474.99, ...}}
            rate = Decimal(str(data["usd"]["krw"]))
            logger.info(f"Cloudflare USD/KRW: {rate}")
            return rate
        except Exception as e:
            logger.warning(f"Cloudflare API error: {e}")
            return None

    async def _save_rate_history(self, rate: Decimal, source: str):
        """Save rate to history for analytics.

        Args:
            rate: The exchange rate
            source: Source of the rate (jsdelivr, cloudflare)
        """
        # TODO: Implement rate history storage in DB
        logger.debug(f"Rate history: {rate} from {source} at {datetime.now(timezone.utc)}")

    def calculate_usdt_amount(self, krw_amount: int, rate: Decimal) -> Decimal:
        """Calculate USDT amount from KRW.

        Args:
            krw_amount: Amount in KRW (e.g., 100000)
            rate: USDT/KRW exchange rate

        Returns:
            Decimal: USDT amount with 6 decimal places
        """
        usdt = Decimal(krw_amount) / rate
        return usdt.quantize(Decimal("0.000001"))


class ExchangeRateError(Exception):
    """Exception raised when exchange rate cannot be fetched."""
    pass
