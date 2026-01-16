"""API tests for TON deposit endpoints."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from decimal import Decimal
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.models.admin_user import AdminUser, AdminRole


def create_mock_user(user_id: str = "test_user_id") -> AdminUser:
    """Create a mock admin user for testing."""
    user = MagicMock(spec=AdminUser)
    user.id = user_id
    user.username = "test_user"
    user.email = "test@example.com"
    user.role = AdminRole.operator
    user.is_active = True
    user.two_factor_enabled = False
    return user


def mock_get_current_user(user_id: str = "test_user_id"):
    """Create a mock get_current_user dependency."""
    async def _mock_get_current_user():
        return create_mock_user(user_id)
    return _mock_get_current_user


class TestTonDepositAPI:
    """Test cases for TON deposit API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        return create_mock_user()

    def test_get_exchange_rate(self, client):
        """Test GET /api/ton/deposit/rate endpoint (no auth required)."""
        with patch(
            "app.services.crypto.ton_exchange_rate.TonExchangeRateService.get_usdt_krw_rate",
            new_callable=AsyncMock,
            return_value=Decimal("1470.54")
        ):
            with patch(
                "app.services.crypto.ton_exchange_rate.TonExchangeRateService.close",
                new_callable=AsyncMock
            ):
                response = client.get("/api/ton/deposit/rate")
                
                assert response.status_code == 200
                data = response.json()
                assert "usdt_krw" in data
                assert "timestamp" in data

    def test_create_deposit_request_requires_auth(self, client):
        """Test POST /api/ton/deposit/request requires authentication."""
        response = client.post(
            "/api/ton/deposit/request",
            json={"requested_krw": 100000}
        )
        # Should return 403 (no credentials) or 401 (invalid credentials)
        assert response.status_code in [401, 403]

    def test_create_deposit_request_validation(self, client, mock_user):
        """Test POST /api/ton/deposit/request validation with auth."""
        from app.utils.dependencies import get_current_user
        
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        try:
            # Missing required fields
            response = client.post("/api/ton/deposit/request", json={})
            assert response.status_code == 422

            # Invalid amount (too low)
            response = client.post(
                "/api/ton/deposit/request",
                json={"requested_krw": 1000}
            )
            assert response.status_code == 422
            
            # Invalid amount (too high)
            response = client.post(
                "/api/ton/deposit/request",
                json={"requested_krw": 200000000}  # Over 100M limit
            )
            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()

    def test_get_deposit_status_requires_auth(self, client):
        """Test GET /api/ton/deposit/status/{id} requires authentication."""
        fake_id = str(uuid4())
        response = client.get(f"/api/ton/deposit/status/{fake_id}")
        assert response.status_code in [401, 403]

    def test_get_deposit_status_not_found(self, client, mock_user):
        """Test GET /api/ton/deposit/status/{id} with non-existent ID."""
        from app.utils.dependencies import get_current_user
        
        app.dependency_overrides[get_current_user] = lambda: mock_user
        fake_id = str(uuid4())
        
        try:
            with patch(
                "app.api.ton_deposit.DepositRequestService"
            ) as mock_service_class:
                mock_service = MagicMock()
                mock_service.get_request_by_id = AsyncMock(return_value=None)
                mock_service_class.return_value = mock_service

                response = client.get(f"/api/ton/deposit/status/{fake_id}")
                
                assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    def test_get_deposit_status_forbidden_for_other_user(self, client, mock_user):
        """Test GET /api/ton/deposit/status/{id} returns 403 for other user's deposit."""
        from app.utils.dependencies import get_current_user
        
        app.dependency_overrides[get_current_user] = lambda: mock_user
        fake_id = str(uuid4())
        
        try:
            with patch(
                "app.api.ton_deposit.DepositRequestService"
            ) as mock_service_class:
                mock_deposit = MagicMock()
                mock_deposit.user_id = "other_user_id"  # Different user
                mock_deposit.id = fake_id
                mock_deposit.status.value = "pending"
                mock_deposit.remaining_seconds = 1800
                mock_deposit.is_expired = False
                mock_deposit.confirmed_at = None
                mock_deposit.tx_hash = None
                
                mock_service = MagicMock()
                mock_service.get_request_by_id = AsyncMock(return_value=mock_deposit)
                mock_service_class.return_value = mock_service

                response = client.get(f"/api/ton/deposit/status/{fake_id}")
                
                assert response.status_code == 403
        finally:
            app.dependency_overrides.clear()

    def test_get_deposit_request_requires_auth(self, client):
        """Test GET /api/ton/deposit/request/{id} requires authentication."""
        fake_id = str(uuid4())
        response = client.get(f"/api/ton/deposit/request/{fake_id}")
        assert response.status_code in [401, 403]

    def test_get_deposit_request_not_found(self, client, mock_user):
        """Test GET /api/ton/deposit/request/{id} with non-existent ID."""
        from app.utils.dependencies import get_current_user
        
        app.dependency_overrides[get_current_user] = lambda: mock_user
        fake_id = str(uuid4())
        
        try:
            with patch(
                "app.api.ton_deposit.DepositRequestService"
            ) as mock_service_class:
                mock_service = MagicMock()
                mock_service.get_request_by_id = AsyncMock(return_value=None)
                mock_service_class.return_value = mock_service

                response = client.get(f"/api/ton/deposit/request/{fake_id}")
                
                assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    def test_get_deposit_request_forbidden_for_other_user(self, client, mock_user):
        """Test GET /api/ton/deposit/request/{id} returns 403 for other user's deposit."""
        from app.utils.dependencies import get_current_user
        
        app.dependency_overrides[get_current_user] = lambda: mock_user
        fake_id = str(uuid4())
        
        try:
            with patch(
                "app.api.ton_deposit.DepositRequestService"
            ) as mock_service_class:
                mock_deposit = MagicMock()
                mock_deposit.user_id = "other_user_id"  # Different user
                
                mock_service = MagicMock()
                mock_service.get_request_by_id = AsyncMock(return_value=mock_deposit)
                mock_service_class.return_value = mock_service

                response = client.get(f"/api/ton/deposit/request/{fake_id}")
                
                assert response.status_code == 403
        finally:
            app.dependency_overrides.clear()

    def test_exchange_rate_service_unavailable(self, client):
        """Test exchange rate endpoint when service is unavailable."""
        from app.services.crypto.ton_exchange_rate import ExchangeRateError
        
        with patch(
            "app.services.crypto.ton_exchange_rate.TonExchangeRateService.get_usdt_krw_rate",
            new_callable=AsyncMock,
            side_effect=ExchangeRateError("API unavailable")
        ):
            with patch(
                "app.services.crypto.ton_exchange_rate.TonExchangeRateService.close",
                new_callable=AsyncMock
            ):
                response = client.get("/api/ton/deposit/rate")
                
                assert response.status_code == 503


class TestDepositRequestSchemas:
    """Test request/response schemas."""

    def test_deposit_request_create_schema(self):
        """Test DepositRequestCreate schema validation."""
        from app.api.ton_deposit import DepositRequestCreate
        
        # Valid request
        req = DepositRequestCreate(
            requested_krw=100000,
            telegram_id=123456789
        )
        assert req.requested_krw == 100000
        assert req.telegram_id == 123456789

        # Without telegram_id
        req = DepositRequestCreate(
            requested_krw=50000
        )
        assert req.telegram_id is None

    def test_deposit_request_create_min_amount(self):
        """Test minimum amount validation."""
        from app.api.ton_deposit import DepositRequestCreate
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            DepositRequestCreate(
                requested_krw=5000  # Below minimum 10000
            )

    def test_deposit_request_create_max_amount(self):
        """Test maximum amount validation."""
        from app.api.ton_deposit import DepositRequestCreate
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            DepositRequestCreate(
                requested_krw=200000000  # Above maximum 100000000
            )
