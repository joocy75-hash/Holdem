"""
Audit API - 감사 로그 조회 엔드포인트

RBAC 정책:
- 기본 로그 조회 (/api/audit): operator 이상
- 자신의 활동 조회 (/api/audit/my-activity): operator 이상
- 관리자 활동 대시보드 (/api/audit/dashboard): admin만
"""
from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_admin_db
from app.utils.dependencies import require_admin, require_operator
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
    current_user: AdminUser = Depends(require_operator),
    db: AsyncSession = Depends(get_admin_db),
):
    """List audit logs (operator and above)"""
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
    current_user: AdminUser = Depends(require_operator),
    db: AsyncSession = Depends(get_admin_db),
):
    """Get current admin's recent activity (operator and above)"""
    service = AuditService(db)
    items = await service.get_user_activity(
        admin_user_id=str(current_user.id),
        limit=limit
    )
    return {"items": items, "total": len(items)}


@router.get("/actions")
async def list_action_types(
    current_user: AdminUser = Depends(require_operator),
):
    """List available action types for filtering"""
    return {
        "actions": [
            {"value": "create_ban", "label": "제재 생성"},
            {"value": "lift_ban", "label": "제재 해제"},
            {"value": "mute_user", "label": "채팅 금지"},
            {"value": "update_user", "label": "사용자 수정"},
            {"value": "approve_deposit", "label": "입금 승인"},
            {"value": "reject_deposit", "label": "입금 거부"},
            {"value": "approve_withdrawal", "label": "출금 승인"},
            {"value": "reject_withdrawal", "label": "출금 거부"},
            {"value": "create_room", "label": "방 생성"},
            {"value": "close_room", "label": "방 종료"},
            {"value": "send_announcement", "label": "공지 발송"},
            {"value": "login", "label": "로그인"},
            {"value": "logout", "label": "로그아웃"},
        ]
    }


# =============================================================================
# 관리자 활동 대시보드
# =============================================================================


class AdminActivitySummary(BaseModel):
    """관리자 활동 요약."""
    admin_id: str
    admin_username: str
    total_actions: int
    actions_today: int
    actions_this_week: int
    last_action_at: str | None
    top_actions: list[dict]


class AdminActivityDashboard(BaseModel):
    """관리자 활동 대시보드 응답."""
    total_admins: int
    active_admins_today: int
    total_actions_today: int
    total_actions_this_week: int
    admins: list[AdminActivitySummary]
    recent_actions: list[AuditLogResponse]
    action_breakdown: list[dict]


@router.get("/dashboard", response_model=AdminActivityDashboard)
async def get_admin_activity_dashboard(
    current_user: AdminUser = Depends(require_admin),
    db: AsyncSession = Depends(get_admin_db),
):
    """관리자 활동 대시보드.
    
    모든 관리자의 활동 통계와 최근 활동을 요약합니다.
    """
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import text

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)

    # 전체 관리자 수
    admin_count_query = text("SELECT COUNT(*) FROM admin_users WHERE is_active = true")
    admin_count_result = await db.execute(admin_count_query)
    total_admins = admin_count_result.scalar() or 0

    # 오늘 활동한 관리자 수
    active_today_query = text("""
        SELECT COUNT(DISTINCT admin_user_id) 
        FROM audit_logs 
        WHERE created_at >= :today_start
    """)
    active_today_result = await db.execute(active_today_query, {"today_start": today_start})
    active_admins_today = active_today_result.scalar() or 0

    # 오늘 전체 액션 수
    actions_today_query = text("""
        SELECT COUNT(*) 
        FROM audit_logs 
        WHERE created_at >= :today_start
    """)
    actions_today_result = await db.execute(actions_today_query, {"today_start": today_start})
    total_actions_today = actions_today_result.scalar() or 0

    # 이번 주 전체 액션 수
    actions_week_query = text("""
        SELECT COUNT(*) 
        FROM audit_logs 
        WHERE created_at >= :week_start
    """)
    actions_week_result = await db.execute(actions_week_query, {"week_start": week_start})
    total_actions_this_week = actions_week_result.scalar() or 0

    # 관리자별 활동 요약
    admin_summary_query = text("""
        SELECT 
            au.id as admin_id,
            au.username as admin_username,
            COUNT(al.id) as total_actions,
            COUNT(CASE WHEN al.created_at >= :today_start THEN 1 END) as actions_today,
            COUNT(CASE WHEN al.created_at >= :week_start THEN 1 END) as actions_this_week,
            MAX(al.created_at) as last_action_at
        FROM admin_users au
        LEFT JOIN audit_logs al ON au.id::text = al.admin_user_id
        WHERE au.is_active = true
        GROUP BY au.id, au.username
        ORDER BY actions_this_week DESC
        LIMIT 10
    """)
    admin_summary_result = await db.execute(admin_summary_query, {
        "today_start": today_start,
        "week_start": week_start
    })
    admin_rows = admin_summary_result.fetchall()

    admins = []
    for row in admin_rows:
        # 관리자별 top 액션 조회
        top_actions_query = text("""
            SELECT action, COUNT(*) as count
            FROM audit_logs
            WHERE admin_user_id = :admin_id
              AND created_at >= :week_start
            GROUP BY action
            ORDER BY count DESC
            LIMIT 3
        """)
        top_actions_result = await db.execute(top_actions_query, {
            "admin_id": row.admin_id,
            "week_start": week_start
        })
        top_actions = [{"action": r.action, "count": r.count} for r in top_actions_result.fetchall()]

        admins.append(AdminActivitySummary(
            admin_id=str(row.admin_id),
            admin_username=row.admin_username,
            total_actions=row.total_actions or 0,
            actions_today=row.actions_today or 0,
            actions_this_week=row.actions_this_week or 0,
            last_action_at=row.last_action_at.isoformat() if row.last_action_at else None,
            top_actions=top_actions,
        ))

    # 최근 활동 (전체)
    recent_query = text("""
        SELECT id, admin_user_id, admin_username, action, target_type, target_id, 
               details, ip_address, created_at
        FROM audit_logs
        ORDER BY created_at DESC
        LIMIT 20
    """)
    recent_result = await db.execute(recent_query)
    recent_actions = [
        AuditLogResponse(
            id=str(r.id),
            admin_user_id=r.admin_user_id,
            admin_username=r.admin_username,
            action=r.action,
            target_type=r.target_type,
            target_id=r.target_id,
            details=r.details or {},
            ip_address=r.ip_address,
            created_at=r.created_at.isoformat(),
        )
        for r in recent_result.fetchall()
    ]

    # 액션 유형별 통계 (이번 주)
    breakdown_query = text("""
        SELECT action, COUNT(*) as count
        FROM audit_logs
        WHERE created_at >= :week_start
        GROUP BY action
        ORDER BY count DESC
    """)
    breakdown_result = await db.execute(breakdown_query, {"week_start": week_start})
    action_breakdown = [{"action": r.action, "count": r.count} for r in breakdown_result.fetchall()]

    return AdminActivityDashboard(
        total_admins=total_admins,
        active_admins_today=active_admins_today,
        total_actions_today=total_actions_today,
        total_actions_this_week=total_actions_this_week,
        admins=admins,
        recent_actions=recent_actions,
        action_breakdown=action_breakdown,
    )
