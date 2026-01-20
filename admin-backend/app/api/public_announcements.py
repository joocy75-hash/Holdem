"""
공지사항 Public API - 인증 없이 접근 가능한 활성 공지 조회
"""
from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_admin_db

router = APIRouter()


# ============================================================================
# Response Models
# ============================================================================


class PublicAnnouncementResponse(BaseModel):
    """공지사항 응답 (Public)"""
    id: str
    title: str
    content: str
    announcement_type: str
    priority: str
    target: str
    target_room_id: str | None
    start_time: str | None
    end_time: str | None
    created_at: str | None


class PublicAnnouncementListResponse(BaseModel):
    """공지사항 목록 응답"""
    items: list[PublicAnnouncementResponse]
    total: int


# ============================================================================
# API Endpoints
# ============================================================================


@router.get("/active", response_model=PublicAnnouncementListResponse)
async def get_active_announcements(
    announcement_type: str | None = Query(None, description="유형 필터"),
    limit: int = Query(10, ge=1, le=50, description="조회 개수"),
    db: AsyncSession = Depends(get_admin_db),
):
    """
    현재 활성화된 공지사항 목록 조회 (인증 불필요)

    - start_time이 없거나 현재 시간 이전
    - end_time이 없거나 현재 시간 이후
    - target이 'all'인 공지만 조회
    - 우선순위 높은 순 → 생성일 최신순 정렬
    """
    # Raw SQL로 직접 조회 - PostgreSQL NOW() 사용
    query = """
        SELECT
            id,
            title,
            content,
            announcement_type,
            priority,
            target,
            target_room_id,
            start_time,
            end_time,
            created_at
        FROM announcements
        WHERE
            (start_time IS NULL OR start_time <= NOW())
            AND (end_time IS NULL OR end_time >= NOW())
            AND target = 'all'
    """

    params = {}

    if announcement_type:
        query += " AND announcement_type = :announcement_type"
        params["announcement_type"] = announcement_type

    # 우선순위 정렬 (critical > high > normal > low)
    query += """
        ORDER BY
            CASE priority
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                WHEN 'normal' THEN 3
                WHEN 'low' THEN 4
                ELSE 5
            END,
            created_at DESC
        LIMIT :limit
    """
    params["limit"] = limit

    result = await db.execute(text(query), params)
    rows = result.fetchall()

    items = []
    for row in rows:
        items.append(PublicAnnouncementResponse(
            id=str(row.id),
            title=row.title,
            content=row.content,
            announcement_type=row.announcement_type,
            priority=row.priority,
            target=row.target,
            target_room_id=row.target_room_id,
            start_time=row.start_time.isoformat() if row.start_time else None,
            end_time=row.end_time.isoformat() if row.end_time else None,
            created_at=row.created_at.isoformat() if row.created_at else None,
        ))

    return PublicAnnouncementListResponse(
        items=items,
        total=len(items),
    )
