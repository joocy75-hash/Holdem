"""
Bans API Tests - 제재 API 엔드포인트 테스트
서비스 레이어를 직접 테스트합니다.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock


class TestBanServiceIntegration:
    """BanService 통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_list_bans_returns_paginated_result(self):
        """제재 목록이 페이지네이션 형식으로 반환되어야 함"""
        from app.services.ban_service import BanService
        
        mock_admin_db = AsyncMock()
        mock_main_db = AsyncMock()
        
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
        mock_row.created_at = None
        mock_row.lifted_at = None
        mock_row.lifted_by = None
        
        list_result = MagicMock()
        list_result.fetchall.return_value = [mock_row]
        
        mock_admin_db.execute.side_effect = [count_result, list_result]
        
        service = BanService(mock_admin_db, mock_main_db)
        result = await service.list_bans()
        
        assert "items" in result
        assert "total" in result
        assert result["total"] == 10
    
    @pytest.mark.asyncio
    async def test_create_ban_permanent(self):
        """영구 제재 생성"""
        from app.services.ban_service import BanService
        
        mock_admin_db = AsyncMock()
        mock_main_db = AsyncMock()
        
        user_result = MagicMock()
        user_row = MagicMock()
        user_row.username = "testuser"
        user_result.fetchone.return_value = user_row
        mock_main_db.execute.return_value = user_result
        
        service = BanService(mock_admin_db, mock_main_db)
        result = await service.create_ban(
            user_id="user-123",
            ban_type="permanent",
            reason="Cheating",
            created_by="admin-1"
        )
        
        assert result["ban_type"] == "permanent"
        assert result["expires_at"] is None
    
    @pytest.mark.asyncio
    async def test_create_ban_temporary(self):
        """임시 제재 생성"""
        from app.services.ban_service import BanService
        
        mock_admin_db = AsyncMock()
        mock_main_db = AsyncMock()
        
        user_result = MagicMock()
        user_row = MagicMock()
        user_row.username = "testuser"
        user_result.fetchone.return_value = user_row
        mock_main_db.execute.return_value = user_result
        
        service = BanService(mock_admin_db, mock_main_db)
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
    async def test_lift_ban_success(self):
        """제재 해제 성공"""
        from app.services.ban_service import BanService
        
        mock_admin_db = AsyncMock()
        mock_main_db = AsyncMock()
        
        ban_result = MagicMock()
        ban_row = MagicMock()
        ban_row.user_id = "user-123"
        ban_row.ban_type = "permanent"
        ban_result.fetchone.return_value = ban_row
        mock_admin_db.execute.return_value = ban_result
        
        service = BanService(mock_admin_db, mock_main_db)
        result = await service.lift_ban("ban-123", "admin-1")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_lift_ban_not_found(self):
        """존재하지 않는 제재 해제 시도"""
        from app.services.ban_service import BanService
        
        mock_admin_db = AsyncMock()
        mock_main_db = AsyncMock()
        
        ban_result = MagicMock()
        ban_result.fetchone.return_value = None
        mock_admin_db.execute.return_value = ban_result
        
        service = BanService(mock_admin_db, mock_main_db)
        result = await service.lift_ban("nonexistent", "admin-1")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_user_bans(self):
        """사용자 제재 기록 조회"""
        from app.services.ban_service import BanService
        
        mock_admin_db = AsyncMock()
        mock_main_db = AsyncMock()
        
        mock_row = MagicMock()
        mock_row.id = "ban-1"
        mock_row.ban_type = "temporary"
        mock_row.reason = "Spam"
        mock_row.expires_at = None
        mock_row.created_by = "admin-1"
        mock_row.created_at = None
        mock_row.lifted_at = None
        
        result = MagicMock()
        result.fetchall.return_value = [mock_row]
        mock_admin_db.execute.return_value = result
        
        service = BanService(mock_admin_db, mock_main_db)
        bans = await service.get_user_bans("user-123")
        
        assert len(bans) == 1
        assert bans[0]["ban_type"] == "temporary"
