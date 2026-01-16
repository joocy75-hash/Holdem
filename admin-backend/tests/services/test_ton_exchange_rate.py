"""Unit tests for TonExchangeRateService."""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.services.crypto.ton_exchange_rate import (
    TonExchangeRateService,
    ExchangeRateError,
)


class TestTonExchangeRateService:
    """Test cases for TonExchangeRateService."""

    @pytest.fixture
    def service(self):
        """Create service instance without Redis."""
        return TonExchangeRateService(redis_client=None)

    @pytest.fixture
    def service_with_redis(self):
        """Create service instance with mock Redis."""
        mock_redis = AsyncMock()
        return TonExchangeRateService(redis_client=mock_redis)

    @pytest.mark.asyncio
    async def test_calculate_usdt_amount(self, service):
        """Test KRW to USDT conversion."""
        rate = Decimal("1470.54")
        krw_amount = 100000
        
        usdt = service.calculate_usdt_amount(krw_amount, rate)
        
        # 100000 / 1470.54 ≈ 68.00
        assert usdt > Decimal("67")
        assert usdt < Decimal("69")
        # Check 6 decimal places
        assert str(usdt).split(".")[-1].__len__() <= 6

    @pytest.mark.asyncio
    async def test_cache_miss_returns_none(self, service):
        """Test cache miss when no Redis client."""
        result = await service._get_cached_rate()
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_hit_returns_rate(self, service_with_redis):
        """Test cache hit returns cached rate."""
        service_with_redis.redis.get = AsyncMock(return_value=b"1470.54")
        
        result = await service_with_redis._get_cached_rate()
        
        assert result == Decimal("1470.54")

    @pytest.mark.asyncio
    async def test_cache_write(self, service_with_redis):
        """Test rate is cached correctly."""
        service_with_redis.redis.setex = AsyncMock()
        
        await service_with_redis._cache_rate(Decimal("1470.54"))
        
        service_with_redis.redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_from_coingecko_success(self, service):
        """Test successful CoinGecko API call."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"tether": {"krw": 1470.54}}
        mock_response.raise_for_status = MagicMock()
        
        with patch.object(service, "_get_http_client") as mock_client:
            mock_http = AsyncMock()
            mock_http.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_http
            
            rate = await service._fetch_from_coingecko()
            
            assert rate == Decimal("1470.54")

    @pytest.mark.asyncio
    async def test_fetch_from_coingecko_failure(self, service):
        """Test CoinGecko API failure returns None."""
        with patch.object(service, "_get_http_client") as mock_client:
            mock_http = AsyncMock()
            mock_http.get = AsyncMock(side_effect=httpx.HTTPError("API Error"))
            mock_client.return_value = mock_http
            
            rate = await service._fetch_from_coingecko()
            
            assert rate is None

    @pytest.mark.asyncio
    async def test_get_usdt_krw_rate_with_cache(self, service_with_redis):
        """Test get_usdt_krw_rate returns cached value."""
        service_with_redis.redis.get = AsyncMock(return_value=b"1470.54")
        
        rate = await service_with_redis.get_usdt_krw_rate()
        
        assert rate == Decimal("1470.54")

    @pytest.mark.asyncio
    async def test_get_usdt_krw_rate_fallback_to_api(self, service_with_redis):
        """Test get_usdt_krw_rate fetches from API on cache miss."""
        service_with_redis.redis.get = AsyncMock(return_value=None)
        service_with_redis.redis.setex = AsyncMock()
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"tether": {"krw": 1470.54}}
        mock_response.raise_for_status = MagicMock()
        
        with patch.object(service_with_redis, "_get_http_client") as mock_client:
            mock_http = AsyncMock()
            mock_http.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_http
            
            rate = await service_with_redis.get_usdt_krw_rate()
            
            assert rate == Decimal("1470.54")
            service_with_redis.redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_usdt_krw_rate_all_sources_fail(self, service):
        """Test ExchangeRateError when all sources fail."""
        with patch.object(service, "_fetch_from_coingecko", return_value=None):
            with patch.object(service, "_fetch_from_binance", return_value=None):
                with pytest.raises(ExchangeRateError):
                    await service.get_usdt_krw_rate()

    @pytest.mark.asyncio
    async def test_close_http_client(self, service):
        """Test HTTP client is closed properly."""
        mock_client = AsyncMock()
        mock_client.is_closed = False
        service._http_client = mock_client
        
        await service.close()
        
        mock_client.aclose.assert_called_once()
        # Client should be set to None after close
        assert service._http_client is None
