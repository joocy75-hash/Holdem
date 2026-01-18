"""관리자 알림 API.

실시간 알림 조회, 읽음 처리 등.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_admin_db
from app.models.admin_user import AdminUser
from app.services.notification_service import NotificationService
from app.utils.dependencies import require_operator
from app.utils.redis_client import get_redis

router = APIRouter()


class NotificationResponse(BaseModel):
    """알림 응답."""
    id: str
    type: str
    priority: str
    title: str
    message: str
    data: dict
    created_at: str = Field(alias="createdAt")
    read: bool
    read_by: str | None = Field(None, alias="readBy")
    read_at: str | None = Field(None, alias="readAt")

    class Config:
        populate_by_name = True


class NotificationListResponse(BaseModel):
    """알림 목록 응답."""
    items: list[dict]
    unread_count: int = Field(alias="unreadCount")
    total: int

    class Config:
        populate_by_name = True


class MarkReadRequest(BaseModel):
    """읽음 처리 요청."""
    notification_id: str = Field(alias="notificationId")

    class Config:
        populate_by_name = True


@router.get("", response_model=NotificationListResponse)
async def get_notifications(
    limit: int = 50,
    include_read: bool = False,
    current_user: AdminUser = Depends(require_operator),
):
    """알림 목록 조회."""
    redis = await get_redis()
    service = NotificationService(redis)

    notifications = await service.get_notifications(
        limit=limit,
        include_read=include_read,
    )
    unread_count = await service.get_unread_count()
    total_count = await service.get_total_count()

    return NotificationListResponse(
        items=notifications,
        unread_count=unread_count,
        total=total_count,
    )


@router.get("/unread-count")
async def get_unread_count(
    current_user: AdminUser = Depends(require_operator),
):
    """읽지 않은 알림 개수."""
    redis = await get_redis()
    service = NotificationService(redis)
    count = await service.get_unread_count()

    return {"unreadCount": count}


@router.post("/{notification_id}/read")
async def mark_as_read(
    notification_id: str,
    current_user: AdminUser = Depends(require_operator),
):
    """알림 읽음 처리."""
    redis = await get_redis()
    service = NotificationService(redis)

    success = await service.mark_as_read(
        notification_id=notification_id,
        admin_id=str(current_user.id),
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    return {"success": True, "message": "Marked as read"}


@router.post("/read-all")
async def mark_all_as_read(
    current_user: AdminUser = Depends(require_operator),
):
    """모든 알림 읽음 처리."""
    redis = await get_redis()
    service = NotificationService(redis)

    count = await service.mark_all_as_read(admin_id=str(current_user.id))

    return {"success": True, "count": count, "message": f"{count} notifications marked as read"}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: AdminUser = Depends(require_operator),
):
    """알림 삭제."""
    redis = await get_redis()
    service = NotificationService(redis)

    success = await service.delete_notification(notification_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    return {"success": True, "message": "Notification deleted"}


# =============================================================================
# 테스트용 (개발 환경에서만)
# =============================================================================


@router.post("/test", include_in_schema=False)
async def create_test_notification(
    current_user: AdminUser = Depends(require_operator),
):
    """테스트 알림 생성 (개발용)."""
    from app.services.notification_service import (
        NotificationPriority,
        NotificationType,
    )

    redis = await get_redis()
    service = NotificationService(redis)

    notification = await service.create_notification(
        notification_type=NotificationType.SYSTEM_ERROR,
        priority=NotificationPriority.MEDIUM,
        title="🔔 테스트 알림",
        message="이것은 테스트 알림입니다.",
        data={"test": True},
    )

    return notification.to_dict()
