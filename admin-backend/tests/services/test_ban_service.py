"""
Ban Service Tests - 제재 서비스 테스트
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from app.services.ban_service import BanService, BanServiceError


class TestBanServiceCreateBan:
    """create_ban 메서드 테스트"""
    
    @pytest.fixture
    def mock_admin_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_main_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def service(self, mock_admin_db, mock_main_db):
        return BanService(mock_admin_db, mock_main_db)
    
    @pytest.mark.asyncio
    async def test_create_permanent_ban(self, service, mock_admin_db, mock_main_db):
        """영구 제재 생성"""
        # Mock user query
        user_result = MagicMock()
        user_row = MagicMock()
        user_row.username = "testuser"
        user_result.fetchone.return_value = user_row
        mock_main_db.execute.return_value = user_result
        
        result = await service.create_ban(
            user_id="user-123",
            ban_type="permanent",
            reason="Cheating",
            created_by="admin-1"
        )
        
        assert result["user_id"] == "user-123"
        assert result["ban_type"] == "permanent"
        assert result["reason"] == "Cheating"
        assert result["expires_at"] is None
        assert mock_main_db.commit.called
        assert mock_admin_db.commit.called
    
    @pytest.mark.asyncio
    async def test_create_temporary_ban(self, service, mock_admin_db, mock_main_db):
        """임시 제재 생성"""
        user_result = MagicMock()
        user_row = MagicMock()
        user_row.username = "testuser"
        user_result.fetchone.return_value = user_row
        mock_main_db.execute.return_value = user_result
        
        result = await service.create_ban(
            user_id="user-123",
            ban_type="temporary",
            reason="Spam",
            created_by="admin-1",
            duration_hours=24
        )
        
        assert result["ban_type"] == "temporary"
        assert result["expires_at"] is not None
    
    @pytest.mark.asyncio
    async def test_create_chat_only_ban(self, service, mock_admin_db, mock_main_db):
        """채팅 금지 생성 (메인 DB 업데이트 없음)"""
        user_result = MagicMock()
        user_row = MagicMock()
        user_row.username = "testuser"
        user_result.fetchone.return_value = user_row
        mock_main_db.execute.return_value = user_result
        
        result = await service.create_ban(
            user_id="user-123",
            ban_type="chat_only",
            reason="Inappropriate language",
            created_by="admin-1"
        )
        
        assert result["ban_type"] == "chat_only"
        # chat_only는 메인 DB 업데이트 없이 admin DB에만 기록
        assert mock_admin_db.commit.called


class TestBanServiceLiftBan:
    """lift_ban 메서드 테스트"""
    
    @pytest.fixture
    def mock_admin_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_main_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def service(self, mock_admin_db, mock_main_db):
        return BanService(mock_admin_db, mock_main_db)
    
    @pytest.mark.asyncio
    async def test_lift_ban_success(self, service, mock_admin_db, mock_main_db):
        """제재 해제 성공"""
        ban_result = MagicMock()
        ban_row = MagicMock()
        ban_row.user_id = "user-123"
        ban_row.ban_type = "permanent"
        ban_result.fetchone.return_value = ban_row
        mock_admin_db.execute.return_value = ban_result
        
        result = await service.lift_ban("ban-123", "admin-1")
        
        assert result is True
        assert mock_main_db.commit.called
        assert mock_admin_db.commit.called
    
    @pytest.mark.asyncio
    async def test_lift_ban_not_found(self, service, mock_admin_db, mock_main_db):
        """존재하지 않는 제재 해제 시도"""
        ban_result = MagicMock()
        ban_result.fetchone.return_value = None
        mock_admin_db.execute.return_value = ban_result
        
        result = await service.lift_ban("nonexistent", "admin-1")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_lift_chat_only_ban(self, service, mock_admin_db, mock_main_db):
        """채팅 금지 해제 (메인 DB 업데이트 없음)"""
        ban_result = MagicMock()
        ban_row = MagicMock()
        ban_row.user_id = "user-123"
        ban_row.ban_type = "chat_only"
        ban_result.fetchone.return_value = ban_row
        mock_admin_db.execute.return_value = ban_result
        
        result = await service.lift_ban("ban-123", "admin-1")
        
        assert result is True


class TestBanServiceListBans:
    """list_bans 메서드 테스트"""
    
    @pytest.fixture
    def mock_admin_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_main_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def service(self, mock_admin_db, mock_main_db):
        return BanService(mock_admin_db, mock_main_db)
    
    @pytest.mark.asyncio
    async def test_list_bans_returns_paginated_result(self, service, mock_admin_db):
        """제재 목록이 페이지네이션 형식으로 반환되어야 함"""
        count_result = MagicMock()
        count_result.scalar.return_value = 10
        
        mock_row = MagicMock()
        mock_row.id = "ban-1"
        mock_row.user_id = "user-123"
        mock_row.username = "testuser"
        mock_row.ban_type = "permanent"
        mock_row.reason = "Cheating"
        mock_row.expires_at = None
        mock_row.created_by = "admin-1"
        mock_row.created_at = datetime(2026, 1, 15)
        mock_row.lifted_at = None
        mock_row.lifted_by = None
        
        list_result = MagicMock()
        list_result.fetchall.return_value = [mock_row]
        
        mock_admin_db.execute.side_effect = [count_result, list_result]
        
        result = await service.list_bans()
        
        assert "items" in result
        assert "total" in result
        assert result["total"] == 10
        assert len(result["items"]) == 1
    
    @pytest.mark.asyncio
    async def test_list_bans_with_active_filter(self, service, mock_admin_db):
        """활성 제재만 필터링"""
        count_result = MagicMock()
        count_result.scalar.return_value = 5
        
        list_result = MagicMock()
        list_result.fetchall.return_value = []
        
        mock_admin_db.execute.side_effect = [count_result, list_result]
        
        result = await service.list_bans(status="active")
        
        assert result["total"] == 5
    
    @pytest.mark.asyncio
    async def test_list_bans_raises_on_exception(self, service, mock_admin_db):
        """예외 발생 시 BanServiceError 발생"""
        mock_admin_db.execute.side_effect = Exception("Database error")
        
        with pytest.raises(BanServiceError, match="Failed to list bans"):
            await service.list_bans()


class TestBanServiceGetUserBans:
    """get_user_bans 메서드 테스트"""
    
    @pytest.fixture
    def mock_admin_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_main_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def service(self, mock_admin_db, mock_main_db):
        return BanService(mock_admin_db, mock_main_db)
    
    @pytest.mark.asyncio
    async def test_get_user_bans_returns_list(self, service, mock_admin_db):
        """사용자의 제재 기록 목록 반환"""
        mock_row = MagicMock()
        mock_row.id = "ban-1"
        mock_row.ban_type = "temporary"
        mock_row.reason = "Spam"
        mock_row.expires_at = datetime(2026, 1, 20)
        mock_row.created_by = "admin-1"
        mock_row.created_at = datetime(2026, 1, 15)
        mock_row.lifted_at = None
        
        result = MagicMock()
        result.fetchall.return_value = [mock_row]
        mock_admin_db.execute.return_value = result
        
        bans = await service.get_user_bans("user-123")
        
        assert len(bans) == 1
        assert bans[0]["ban_type"] == "temporary"
    
    @pytest.mark.asyncio
    async def test_get_user_bans_raises_on_exception(self, service, mock_admin_db):
        """예외 발생 시 BanServiceError 발생"""
        mock_admin_db.execute.side_effect = Exception("Database error")
        
        with pytest.raises(BanServiceError, match="Failed to get user bans"):
            await service.get_user_bans("user-123")
