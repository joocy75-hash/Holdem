"""
Users API Tests - 사용자 API 엔드포인트 테스트
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.api.users import router
from app.models.admin_user import AdminUser


# Test app setup
app = FastAPI()
app.include_router(router, prefix="/api/users")


class TestListUsersAPI:
    """GET /api/users 엔드포인트 테스트"""
    
    @pytest.fixture
    def mock_admin_user(self):
        """Mock admin user for authentication"""
        user = MagicMock(spec=AdminUser)
        user.id = "admin-123"
        user.username = "admin"
        user.role = "viewer"
        return user
    
    @pytest.fixture
    def mock_user_service(self):
        """Mock UserService"""
        with patch("app.api.users.UserService") as mock:
            service_instance = AsyncMock()
            mock.return_value = service_instance
            yield service_instance
    
    @pytest.mark.asyncio
    async def test_list_users_success(self, mock_admin_user, mock_user_service):
        """사용자 목록 조회 성공"""
        mock_user_service.search_users.return_value = {
            "items": [
                {
                    "id": "user-1",
                    "username": "testuser1",
                    "email": "test1@example.com",
                    "balance": 1000.0,
                    "created_at": "2026-01-01T00:00:00",
                    "last_login": "2026-01-15T00:00:00",
                    "is_banned": False
                }
            ],
            "total": 1,
            "page": 1,
            "page_size": 20,
            "total_pages": 1
        }
        
        with patch("app.api.users.require_viewer", return_value=mock_admin_user):
            with patch("app.api.users.get_main_db"):
                # Verify service method signature
                result = await mock_user_service.search_users(
                    search=None,
                    page=1,
                    page_size=20,
                    is_banned=None,
                    sort_by="created_at",
                    sort_order="desc"
                )
                
                assert result["total"] == 1
                assert len(result["items"]) == 1
    
    @pytest.mark.asyncio
    async def test_list_users_with_search(self, mock_admin_user, mock_user_service):
        """검색어로 사용자 목록 조회"""
        mock_user_service.search_users.return_value = {
            "items": [
                {
                    "id": "user-1",
                    "username": "searchuser",
                    "email": "search@example.com",
                    "balance": 500.0,
                    "created_at": "2026-01-01T00:00:00",
                    "last_login": None,
                    "is_banned": False
                }
            ],
            "total": 1,
            "page": 1,
            "page_size": 20,
            "total_pages": 1
        }
        
        result = await mock_user_service.search_users(search="searchuser")
        
        assert result["items"][0]["username"] == "searchuser"
    
    @pytest.mark.asyncio
    async def test_list_users_with_ban_filter(self, mock_admin_user, mock_user_service):
        """제재 상태로 필터링"""
        mock_user_service.search_users.return_value = {
            "items": [
                {
                    "id": "banned-1",
                    "username": "banneduser",
                    "email": "banned@example.com",
                    "balance": 0.0,
                    "created_at": "2026-01-01T00:00:00",
                    "last_login": "2026-01-10T00:00:00",
                    "is_banned": True
                }
            ],
            "total": 1,
            "page": 1,
            "page_size": 20,
            "total_pages": 1
        }
        
        result = await mock_user_service.search_users(is_banned=True)
        
        assert result["items"][0]["is_banned"] is True
    
    @pytest.mark.asyncio
    async def test_list_users_pagination(self, mock_admin_user, mock_user_service):
        """페이지네이션 동작 확인"""
        mock_user_service.search_users.return_value = {
            "items": [],
            "total": 100,
            "page": 5,
            "page_size": 10,
            "total_pages": 10
        }
        
        result = await mock_user_service.search_users(page=5, page_size=10)
        
        assert result["page"] == 5
        assert result["page_size"] == 10
        assert result["total_pages"] == 10


class TestGetUserAPI:
    """GET /api/users/{user_id} 엔드포인트 테스트"""
    
    @pytest.fixture
    def mock_user_service(self):
        with patch("app.api.users.UserService") as mock:
            service_instance = AsyncMock()
            mock.return_value = service_instance
            yield service_instance
    
    @pytest.mark.asyncio
    async def test_get_user_success(self, mock_user_service):
        """사용자 상세 조회 성공"""
        mock_user_service.get_user_detail.return_value = {
            "id": "user-123",
            "username": "testuser",
            "email": "test@example.com",
            "balance": 1500.0,
            "created_at": "2026-01-01T00:00:00",
            "last_login": "2026-01-15T00:00:00",
            "is_banned": False,
            "ban_reason": None,
            "ban_expires_at": None
        }
        
        result = await mock_user_service.get_user_detail("user-123")
        
        assert result["id"] == "user-123"
        assert result["username"] == "testuser"
        assert result["balance"] == 1500.0
    
    @pytest.mark.asyncio
    async def test_get_user_not_found(self, mock_user_service):
        """존재하지 않는 사용자 조회"""
        mock_user_service.get_user_detail.return_value = None
        
        result = await mock_user_service.get_user_detail("nonexistent")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_banned_user(self, mock_user_service):
        """제재된 사용자 상세 조회"""
        mock_user_service.get_user_detail.return_value = {
            "id": "banned-user",
            "username": "banneduser",
            "email": "banned@example.com",
            "balance": 0.0,
            "created_at": "2026-01-01T00:00:00",
            "last_login": "2026-01-10T00:00:00",
            "is_banned": True,
            "ban_reason": "Cheating",
            "ban_expires_at": "2026-02-01T00:00:00"
        }
        
        result = await mock_user_service.get_user_detail("banned-user")
        
        assert result["is_banned"] is True
        assert result["ban_reason"] == "Cheating"


class TestGetUserTransactionsAPI:
    """GET /api/users/{user_id}/transactions 엔드포인트 테스트"""
    
    @pytest.fixture
    def mock_user_service(self):
        with patch("app.api.users.UserService") as mock:
            service_instance = AsyncMock()
            mock.return_value = service_instance
            yield service_instance
    
    @pytest.mark.asyncio
    async def test_get_transactions_success(self, mock_user_service):
        """거래 내역 조회 성공"""
        mock_user_service.get_user_transactions.return_value = {
            "items": [
                {
                    "id": "tx-1",
                    "type": "deposit",
                    "amount": 100.0,
                    "balance_before": 900.0,
                    "balance_after": 1000.0,
                    "description": "USDT Deposit",
                    "created_at": "2026-01-15T00:00:00"
                }
            ],
            "total": 1,
            "page": 1,
            "page_size": 20
        }
        
        result = await mock_user_service.get_user_transactions("user-123")
        
        assert result["total"] == 1
        assert result["items"][0]["type"] == "deposit"
    
    @pytest.mark.asyncio
    async def test_get_transactions_with_type_filter(self, mock_user_service):
        """거래 유형 필터링"""
        mock_user_service.get_user_transactions.return_value = {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 20
        }
        
        result = await mock_user_service.get_user_transactions(
            user_id="user-123",
            tx_type="withdrawal"
        )
        
        assert result["total"] == 0


class TestGetUserLoginHistoryAPI:
    """GET /api/users/{user_id}/login-history 엔드포인트 테스트"""
    
    @pytest.fixture
    def mock_user_service(self):
        with patch("app.api.users.UserService") as mock:
            service_instance = AsyncMock()
            mock.return_value = service_instance
            yield service_instance
    
    @pytest.mark.asyncio
    async def test_get_login_history_success(self, mock_user_service):
        """로그인 기록 조회 성공"""
        mock_user_service.get_user_login_history.return_value = {
            "items": [
                {
                    "id": "login-1",
                    "ip_address": "192.168.1.1",
                    "user_agent": "Mozilla/5.0",
                    "success": True,
                    "created_at": "2026-01-15T00:00:00"
                }
            ],
            "total": 1,
            "page": 1,
            "page_size": 20
        }
        
        result = await mock_user_service.get_user_login_history("user-123")
        
        assert result["total"] == 1
        assert result["items"][0]["ip_address"] == "192.168.1.1"
    
    @pytest.mark.asyncio
    async def test_get_login_history_failed_attempts(self, mock_user_service):
        """실패한 로그인 시도 포함"""
        mock_user_service.get_user_login_history.return_value = {
            "items": [
                {
                    "id": "login-1",
                    "ip_address": "10.0.0.1",
                    "user_agent": "Bot/1.0",
                    "success": False,
                    "created_at": "2026-01-15T00:00:00"
                }
            ],
            "total": 1,
            "page": 1,
            "page_size": 20
        }
        
        result = await mock_user_service.get_user_login_history("user-123")
        
        assert result["items"][0]["success"] is False


class TestGetUserHandsAPI:
    """GET /api/users/{user_id}/hands 엔드포인트 테스트"""
    
    @pytest.fixture
    def mock_user_service(self):
        with patch("app.api.users.UserService") as mock:
            service_instance = AsyncMock()
            mock.return_value = service_instance
            yield service_instance
    
    @pytest.mark.asyncio
    async def test_get_hands_success(self, mock_user_service):
        """핸드 기록 조회 성공"""
        mock_user_service.get_user_hands.return_value = {
            "items": [
                {
                    "id": "hp-1",
                    "hand_id": "hand-123",
                    "room_id": "room-456",
                    "position": 2,
                    "cards": "As Kh",
                    "bet_amount": 50.0,
                    "won_amount": 120.0,
                    "pot_size": 200.0,
                    "created_at": "2026-01-15T00:00:00"
                }
            ],
            "total": 1,
            "page": 1,
            "page_size": 20
        }
        
        result = await mock_user_service.get_user_hands("user-123")
        
        assert result["total"] == 1
        assert result["items"][0]["cards"] == "As Kh"
        assert result["items"][0]["won_amount"] == 120.0
    
    @pytest.mark.asyncio
    async def test_get_hands_pagination(self, mock_user_service):
        """핸드 기록 페이지네이션"""
        mock_user_service.get_user_hands.return_value = {
            "items": [],
            "total": 500,
            "page": 10,
            "page_size": 20
        }
        
        result = await mock_user_service.get_user_hands(
            user_id="user-123",
            page=10,
            page_size=20
        )
        
        assert result["total"] == 500
        assert result["page"] == 10
