"""
Audit Service Tests - 감사 로그 서비스 테스트
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import json

from app.services.audit_service import AuditService, AuditServiceError


class TestAuditServiceLogAction:
    """log_action 메서드 테스트"""
    
    @pytest.fixture
    def mock_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def service(self, mock_db):
        return AuditService(mock_db)
    
    @pytest.mark.asyncio
    async def test_log_action_success(self, service, mock_db):
        """액션 로그 기록 성공"""
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
        assert result["target_type"] == "user"
        assert result["target_id"] == "user-123"
        assert result["details"] == {"reason": "Cheating"}
        assert mock_db.commit.called
    
    @pytest.mark.asyncio
    async def test_log_action_without_ip(self, service, mock_db):
        """IP 주소 없이 로그 기록"""
        result = await service.log_action(
            admin_user_id="admin-1",
            admin_username="admin",
            action="lift_ban",
            target_type="ban",
            target_id="ban-123",
            details={}
        )
        
        assert result["ip_address"] is None
    
    @pytest.mark.asyncio
    async def test_log_action_handles_exception(self, service, mock_db):
        """예외 발생 시에도 결과 반환 (주요 작업 중단 방지)"""
        mock_db.execute.side_effect = Exception("Database error")
        
        result = await service.log_action(
            admin_user_id="admin-1",
            admin_username="admin",
            action="create_ban",
            target_type="user",
            target_id="user-123",
            details={}
        )
        
        assert "error" in result
        assert result["admin_user_id"] == "admin-1"


class TestAuditServiceListLogs:
    """list_logs 메서드 테스트"""
    
    @pytest.fixture
    def mock_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def service(self, mock_db):
        return AuditService(mock_db)
    
    @pytest.mark.asyncio
    async def test_list_logs_returns_paginated_result(self, service, mock_db):
        """로그 목록이 페이지네이션 형식으로 반환되어야 함"""
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
        
        result = await service.list_logs()
        
        assert "items" in result
        assert "total" in result
        assert result["total"] == 100
        assert len(result["items"]) == 1
        assert result["items"][0]["action"] == "create_ban"
    
    @pytest.mark.asyncio
    async def test_list_logs_with_action_filter(self, service, mock_db):
        """액션 유형으로 필터링"""
        count_result = MagicMock()
        count_result.scalar.return_value = 10
        
        list_result = MagicMock()
        list_result.fetchall.return_value = []
        
        mock_db.execute.side_effect = [count_result, list_result]
        
        result = await service.list_logs(action="create_ban")
        
        assert result["total"] == 10
    
    @pytest.mark.asyncio
    async def test_list_logs_with_admin_filter(self, service, mock_db):
        """관리자 ID로 필터링"""
        count_result = MagicMock()
        count_result.scalar.return_value = 25
        
        list_result = MagicMock()
        list_result.fetchall.return_value = []
        
        mock_db.execute.side_effect = [count_result, list_result]
        
        result = await service.list_logs(admin_user_id="admin-1")
        
        assert result["total"] == 25
    
    @pytest.mark.asyncio
    async def test_list_logs_with_target_type_filter(self, service, mock_db):
        """대상 유형으로 필터링"""
        count_result = MagicMock()
        count_result.scalar.return_value = 15
        
        list_result = MagicMock()
        list_result.fetchall.return_value = []
        
        mock_db.execute.side_effect = [count_result, list_result]
        
        result = await service.list_logs(target_type="user")
        
        assert result["total"] == 15
    
    @pytest.mark.asyncio
    async def test_list_logs_raises_on_exception(self, service, mock_db):
        """예외 발생 시 AuditServiceError 발생"""
        mock_db.execute.side_effect = Exception("Database error")
        
        with pytest.raises(AuditServiceError, match="Failed to list audit logs"):
            await service.list_logs()
    
    @pytest.mark.asyncio
    async def test_list_logs_parses_json_details(self, service, mock_db):
        """JSON 문자열 details를 파싱해야 함"""
        count_result = MagicMock()
        count_result.scalar.return_value = 1
        
        mock_row = MagicMock()
        mock_row.id = "log-1"
        mock_row.admin_user_id = "admin-1"
        mock_row.admin_username = "admin"
        mock_row.action = "create_ban"
        mock_row.target_type = "user"
        mock_row.target_id = "user-123"
        mock_row.details = '{"ban_type": "permanent", "reason": "Cheating"}'
        mock_row.ip_address = "192.168.1.1"
        mock_row.created_at = datetime(2026, 1, 15)
        
        list_result = MagicMock()
        list_result.fetchall.return_value = [mock_row]
        
        mock_db.execute.side_effect = [count_result, list_result]
        
        result = await service.list_logs()
        
        assert result["items"][0]["details"]["ban_type"] == "permanent"


class TestAuditServiceGetUserActivity:
    """get_user_activity 메서드 테스트"""
    
    @pytest.fixture
    def mock_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def service(self, mock_db):
        return AuditService(mock_db)
    
    @pytest.mark.asyncio
    async def test_get_user_activity_returns_list(self, service, mock_db):
        """관리자의 최근 활동 목록 반환"""
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
        
        items = await service.get_user_activity("admin-1")
        
        assert len(items) == 1
        assert items[0]["action"] == "create_ban"
    
    @pytest.mark.asyncio
    async def test_get_user_activity_with_limit(self, service, mock_db):
        """제한된 개수의 활동 조회"""
        result = MagicMock()
        result.fetchall.return_value = []
        mock_db.execute.return_value = result
        
        items = await service.get_user_activity("admin-1", limit=10)
        
        assert items == []
    
    @pytest.mark.asyncio
    async def test_get_user_activity_raises_on_exception(self, service, mock_db):
        """예외 발생 시 AuditServiceError 발생"""
        mock_db.execute.side_effect = Exception("Database error")
        
        with pytest.raises(AuditServiceError, match="Failed to get user activity"):
            await service.get_user_activity("admin-1")
