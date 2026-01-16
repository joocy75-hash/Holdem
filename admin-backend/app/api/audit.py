"""
Audit API - 감사 로그 조회 엔드포인트
"""
from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_admin_db
from app.utils.dependencies import require_admin
from app.models.admin_user import AdminUser
from app.services.audit_service import AuditService


router = APIRouter()


class AuditLogResponse(BaseModel):
    id: str
    admin_user_id: str
    admin_username: str
    action: str
    target_type: str
    target_id: str
    details: dict
    ip_address: str | None
    created_at: str


class PaginatedAuditLogs(BaseModel):
    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


@router.get("", response_model=PaginatedAuditLogs)
async def list_audit_logs(
    action: str | None = Query(None, description="Filter by action type"),
    admin_user_id: str | None = Query(None, description="Filter by admin user"),
    target_type: str | None = Query(None, description="Filter by target type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: AdminUser = Depends(require_admin),
    db: AsyncSession = Depends(get_admin_db),
):
    """List audit logs (admin only)"""
    service = AuditService(db)
    result = await service.list_logs(
        action=action,
        admin_user_id=admin_user_id,
        target_type=target_type,
        page=page,
        page_size=page_size
    )
    return PaginatedAuditLogs(**result)


@router.get("/my-activity")
async def get_my_activity(
    limit: int = Query(50, ge=1, le=100),
    current_user: AdminUser = Depends(require_admin),
    db: AsyncSession = Depends(get_admin_db),
):
    """Get current admin's recent activity"""
    service = AuditService(db)
    items = await service.get_user_activity(
        admin_user_id=str(current_user.id),
        limit=limit
    )
    return {"items": items, "total": len(items)}


@router.get("/actions")
async def list_action_types(
    current_user: AdminUser = Depends(require_admin),
):
    """List available action types for filtering"""
    return {
        "actions": [
            {"value": "create_ban", "label": "제재 생성"},
            {"value": "lift_ban", "label": "제재 해제"},
            {"value": "update_user", "label": "사용자 수정"},
            {"value": "approve_deposit", "label": "입금 승인"},
            {"value": "reject_deposit", "label": "입금 거부"},
            {"value": "create_room", "label": "방 생성"},
            {"value": "close_room", "label": "방 종료"},
            {"value": "login", "label": "로그인"},
            {"value": "logout", "label": "로그아웃"},
        ]
    }
