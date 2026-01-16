"""
Bans API - 사용자 제재 관리 엔드포인트
"""
from enum import Enum
from fastapi import APIRouter, Query, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_admin_db, get_main_db
from app.utils.dependencies import require_operator
from app.models.admin_user import AdminUser
from app.services.ban_service import BanService
from app.services.audit_service import AuditService


router = APIRouter()


class BanType(str, Enum):
    """Valid ban types."""
    TEMPORARY = "temporary"
    PERMANENT = "permanent"
    CHAT_ONLY = "chat_only"


class BanResponse(BaseModel):
    id: str
    user_id: str
    username: str
    ban_type: str
    reason: str
    expires_at: str | None
    created_by: str
    created_at: str


class BanDetailResponse(BanResponse):
    lifted_at: str | None = None
    lifted_by: str | None = None


class PaginatedBans(BaseModel):
    items: list[BanDetailResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CreateBanRequest(BaseModel):
    """Request body for creating a ban."""
    user_id: str = Field(..., min_length=1, max_length=100, description="User ID to ban")
    ban_type: BanType = Field(..., description="Type of ban: temporary, permanent, or chat_only")
    reason: str = Field(..., min_length=1, max_length=500, description="Reason for the ban")
    duration_hours: Optional[int] = Field(None, ge=1, le=8760, description="Duration in hours for temporary bans (max 1 year)")
    
    @field_validator('duration_hours')
    @classmethod
    def validate_duration_for_temporary(cls, v, info):
        """Validate duration is provided for temporary bans."""
        # Note: This validation happens after field parsing, 
        # so we can't access ban_type here. API-level validation handles this.
        return v


@router.get("", response_model=PaginatedBans)
async def list_bans(
    status: str | None = Query(None, description="active, expired, or lifted"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: AdminUser = Depends(require_operator),
    admin_db: AsyncSession = Depends(get_admin_db),
    main_db: AsyncSession = Depends(get_main_db),
):
    """List bans with optional status filter"""
    service = BanService(admin_db, main_db)
    result = await service.list_bans(
        status=status,
        page=page,
        page_size=page_size
    )
    return PaginatedBans(**result)


@router.post("", response_model=BanResponse)
async def create_ban(
    request: CreateBanRequest,
    req: Request,
    current_user: AdminUser = Depends(require_operator),
    admin_db: AsyncSession = Depends(get_admin_db),
    main_db: AsyncSession = Depends(get_main_db),
):
    """Create a new ban"""
    # Validate duration for temporary bans
    if request.ban_type == BanType.TEMPORARY and not request.duration_hours:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="duration_hours is required for temporary bans"
        )
    
    service = BanService(admin_db, main_db)
    result = await service.create_ban(
        user_id=request.user_id,
        ban_type=request.ban_type.value,
        reason=request.reason,
        created_by=str(current_user.id),
        duration_hours=request.duration_hours
    )
    
    # Log audit
    audit_service = AuditService(admin_db)
    await audit_service.log_action(
        admin_user_id=str(current_user.id),
        admin_username=current_user.username,
        action="create_ban",
        target_type="user",
        target_id=request.user_id,
        details={
            "ban_id": result["id"],
            "ban_type": request.ban_type.value,
            "reason": request.reason,
            "duration_hours": request.duration_hours
        },
        ip_address=req.client.host if req.client else None
    )
    
    return BanResponse(**result)


@router.delete("/{ban_id}")
async def lift_ban(
    ban_id: str,
    req: Request,
    current_user: AdminUser = Depends(require_operator),
    admin_db: AsyncSession = Depends(get_admin_db),
    main_db: AsyncSession = Depends(get_main_db),
):
    """Lift a ban"""
    service = BanService(admin_db, main_db)
    success = await service.lift_ban(
        ban_id=ban_id,
        lifted_by=str(current_user.id)
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ban not found"
        )
    
    # Log audit
    audit_service = AuditService(admin_db)
    await audit_service.log_action(
        admin_user_id=str(current_user.id),
        admin_username=current_user.username,
        action="lift_ban",
        target_type="ban",
        target_id=ban_id,
        details={},
        ip_address=req.client.host if req.client else None
    )
    
    return {"message": f"Ban {ban_id} lifted successfully"}


@router.get("/user/{user_id}")
async def get_user_bans(
    user_id: str,
    current_user: AdminUser = Depends(require_operator),
    admin_db: AsyncSession = Depends(get_admin_db),
    main_db: AsyncSession = Depends(get_main_db),
):
    """Get all bans for a specific user"""
    service = BanService(admin_db, main_db)
    bans = await service.get_user_bans(user_id)
    return {"items": bans, "total": len(bans)}
