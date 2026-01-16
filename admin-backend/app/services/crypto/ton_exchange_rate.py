"""TON/USDT Exchange Rate Service.

Fetches real-time USDT/KRW exchange rates from CoinGecko and Binance APIs
with Redis caching for performance.
"""

import logging
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TonExchangeRateService:
    """Service for fetching and caching USDT/KRW exchange rates.
    
    Primary source: CoinGecko API
    Fallback source: Binance API
    Cache: Redis with configurable TTL
    
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
        
        Tries cache first, then CoinGecko, then Binance as fallback.
        
        Returns:
            Decimal: Current USDT/KRW rate (e.g., 1468.50)
            
        Raises:
            ExchangeRateError: If unable to fetch rate from any source
        """
        # Try cache first
        cached_rate = await self._get_cached_rate()
        if cached_rate is not None:
            logger.debug(f"Cache hit: USDT/KRW = {cached_rate}")
            return cached_rate
        
        # Try CoinGecko
        rate = await self._fetch_from_coingecko()
        if rate is not None:
            await self._cache_rate(rate)
            await self._save_rate_history(rate, "coingecko")
            return rate
        
        # Fallback to Binance
        rate = await self._fetch_from_binance()
        if rate is not None:
            await self._cache_rate(rate)
            await self._save_rate_history(rate, "binance")
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
    
    async def _fetch_from_coingecko(self) -> Optional[Decimal]:
        """Fetch USDT/KRW rate from CoinGecko API."""
        try:
            client = await self._get_http_client()
            url = f"{settings.coingecko_api_url}/simple/price"
            params = {"ids": "tether", "vs_currencies": "krw"}
            
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            rate = Decimal(str(data["tether"]["krw"]))
            logger.info(f"CoinGecko USDT/KRW: {rate}")
            return rate
        except Exception as e:
            logger.warning(f"CoinGecko API error: {e}")
            return None
    
    async def _fetch_from_binance(self) -> Optional[Decimal]:
        """Fetch USDT/KRW rate from Binance API (via USDT/BUSD proxy)."""
        try:
            client = await self._get_http_client()
            # Binance doesn't have direct KRW pair, use approximation
            # USDT is pegged to USD, get USD/KRW from other source or use fixed rate
            url = f"{settings.binance_api_url}/ticker/price"
            params = {"symbol": "USDTKRW"}
            
            response = await client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                rate = Decimal(data["price"])
                logger.info(f"Binance USDT/KRW: {rate}")
                return rate
            
            # If USDTKRW not available, return None
            logger.warning("Binance USDTKRW pair not available")
            return None
        except Exception as e:
            logger.warning(f"Binance API error: {e}")
            return None
    
    async def _save_rate_history(self, rate: Decimal, source: str):
        """Save rate to history for analytics.
        
        Args:
            rate: The exchange rate
            source: Source of the rate (coingecko, binance)
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
