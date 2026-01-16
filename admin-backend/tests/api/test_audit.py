"""
Audit API Tests - 감사 로그 API 엔드포인트 테스트
서비스 레이어를 직접 테스트합니다.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
import json


class TestAuditServiceIntegration:
    """AuditService 통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_log_action_success(self):
        """액션 로그 기록 성공"""
        from app.services.audit_service import AuditService
        
        mock_db = AsyncMock()
        
        service = AuditService(mock_db)
        result = await service.log_action(
            admin_user_id="admin-1",
            admin_username="admin",
            action="create_ban",
            target_type="user",
            target_id="user-123",
            details={"reason": "Cheating"},
            ip_address="192.168.1.1"
        )
        
        assert result["admin_user_id"] == "admin-1"
        assert result["action"] == "create_ban"
        assert mock_db.commit.called
    
    @pytest.mark.asyncio
    async def test_list_logs_returns_paginated_result(self):
        """로그 목록이 페이지네이션 형식으로 반환되어야 함"""
        from app.services.audit_service import AuditService
        
        mock_db = AsyncMock()
        
        count_result = MagicMock()
        count_result.scalar.return_value = 100
        
        mock_row = MagicMock()
        mock_row.id = "log-1"
        mock_row.admin_user_id = "admin-1"
        mock_row.admin_username = "admin"
        mock_row.action = "create_ban"
        mock_row.target_type = "user"
        mock_row.target_id = "user-123"
        mock_row.details = json.dumps({"reason": "Cheating"})
        mock_row.ip_address = "192.168.1.1"
        mock_row.created_at = datetime(2026, 1, 15)
        
        list_result = MagicMock()
        list_result.fetchall.return_value = [mock_row]
        
        mock_db.execute.side_effect = [count_result, list_result]
        
        service = AuditService(mock_db)
        result = await service.list_logs()
        
        assert "items" in result
        assert "total" in result
        assert result["total"] == 100
    
    @pytest.mark.asyncio
    async def test_list_logs_with_action_filter(self):
        """액션 유형으로 필터링"""
        from app.services.audit_service import AuditService
        
        mock_db = AsyncMock()
        
        count_result = MagicMock()
        count_result.scalar.return_value = 10
        
        list_result = MagicMock()
        list_result.fetchall.return_value = []
        
        mock_db.execute.side_effect = [count_result, list_result]
        
        service = AuditService(mock_db)
        result = await service.list_logs(action="create_ban")
        
        assert result["total"] == 10
    
    @pytest.mark.asyncio
    async def test_list_logs_with_admin_filter(self):
        """관리자 ID로 필터링"""
        from app.services.audit_service import AuditService
        
        mock_db = AsyncMock()
        
        count_result = MagicMock()
        count_result.scalar.return_value = 25
        
        list_result = MagicMock()
        list_result.fetchall.return_value = []
        
        mock_db.execute.side_effect = [count_result, list_result]
        
        service = AuditService(mock_db)
        result = await service.list_logs(admin_user_id="admin-1")
        
        assert result["total"] == 25
    
    @pytest.mark.asyncio
    async def test_get_user_activity(self):
        """관리자의 최근 활동 조회"""
        from app.services.audit_service import AuditService
        
        mock_db = AsyncMock()
        
        mock_row = MagicMock()
        mock_row.id = "log-1"
        mock_row.action = "create_ban"
        mock_row.target_type = "user"
        mock_row.target_id = "user-123"
        mock_row.details = json.dumps({"reason": "Spam"})
        mock_row.ip_address = "192.168.1.1"
        mock_row.created_at = datetime(2026, 1, 15)
        
        result = MagicMock()
        result.fetchall.return_value = [mock_row]
        mock_db.execute.return_value = result
        
        service = AuditService(mock_db)
        items = await service.get_user_activity("admin-1")
        
        assert len(items) == 1
        assert items[0]["action"] == "create_ban"
    
    @pytest.mark.asyncio
    async def test_log_action_handles_exception(self):
        """예외 발생 시에도 결과 반환"""
        from app.services.audit_service import AuditService
        
        mock_db = AsyncMock()
        mock_db.execute.side_effect = Exception("Database error")
        
        service = AuditService(mock_db)
        result = await service.log_action(
            admin_user_id="admin-1",
            admin_username="admin",
            action="create_ban",
            target_type="user",
            target_id="user-123",
            details={}
        )
        
        assert "error" in result
