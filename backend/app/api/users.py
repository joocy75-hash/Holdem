"""User management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.deps import CurrentUser, DbSession, TraceId
from app.schemas import (
    ChangePasswordRequest,
    ErrorResponse,
    SuccessResponse,
    UpdateProfileRequest,
    UserProfileResponse,
    UserStatsResponse,
)
from app.schemas.responses import UserPublicProfileResponse
from app.services.avatar import AvatarService
from app.services.user import UserError, UserService
from app.utils.redis_client import get_redis

router = APIRouter(prefix="/users", tags=["Users"])


# =============================================================================
# Rate Limiting Helper
# =============================================================================


async def check_password_rate_limit(request: Request, user_id: str) -> None:
    """Check rate limit for password-related operations.
    
    Limits: 3 attempts per 5 minutes per user.
    
    Raises:
        HTTPException: If rate limit exceeded
    """
    redis = get_redis()
    if not redis:
        return  # Skip rate limiting if Redis unavailable
    
    key = f"rate_limit:password:{user_id}"
    window = 300  # 5 minutes
    limit = 3
    
    try:
        import time
        now = int(time.time())
        window_start = now - window
        
        pipe = redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, window)
        results = await pipe.execute()
        
        count = results[2]
        if count > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many password change attempts. Please try again later.",
                        "details": {"retry_after_seconds": window},
                    }
                },
                headers={"Retry-After": str(window)},
            )
    except HTTPException:
        raise
    except Exception as e:
        # Log but don't fail the request if rate limiting fails
        import logging
        logging.getLogger(__name__).warning(f"Rate limit check failed: {e}")


# =============================================================================
# Avatar Endpoints
# =============================================================================


@router.get(
    "/avatars",
    response_model=list[dict],
    summary="아바타 목록 조회",
    description="사용 가능한 모든 아바타 목록을 조회합니다.",
)
async def get_avatars():
    """아바타 목록 조회."""
    return AvatarService.get_all_avatars()


@router.get(
    "/avatars/{avatar_id}",
    response_model=dict,
    responses={
        404: {"model": ErrorResponse, "description": "Avatar not found"},
    },
    summary="특정 아바타 조회",
    description="특정 아바타의 상세 정보를 조회합니다.",
)
async def get_avatar(avatar_id: str, trace_id: TraceId):
    """특정 아바타 조회."""
    avatar = AvatarService.get_avatar_by_id(avatar_id)

    if not avatar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "AVATAR_NOT_FOUND",
                    "message": "Avatar not found",
                    "details": {"avatar_id": avatar_id},
                },
                "traceId": trace_id,
            },
        )

    return {
        "id": avatar.id,
        "name": avatar.name,
        "imageUrl": avatar.image_url,
        "category": avatar.category.value,
        "isAvailable": avatar.is_available,
        "description": avatar.description,
    }


# =============================================================================
# User Profile Endpoints
# =============================================================================


@router.get(
    "/me",
    response_model=UserProfileResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
async def get_current_user_profile(
    current_user: CurrentUser,
):
    """Get current user's profile.

    Returns detailed profile information for the authenticated user.
    """
    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        nickname=current_user.nickname,
        avatar_url=current_user.avatar_url,
        status=current_user.status,
        balance=current_user.balance,
        total_hands=current_user.total_hands,
        total_winnings=current_user.total_winnings,
        created_at=current_user.created_at,
    )


@router.patch(
    "/me",
    response_model=UserProfileResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        409: {"model": ErrorResponse, "description": "Nickname already taken"},
    },
)
async def update_profile(
    request_body: UpdateProfileRequest,
    current_user: CurrentUser,
    db: DbSession,
    trace_id: TraceId,
):
    """Update current user's profile.

    Updates the nickname and/or avatar URL for the authenticated user.
    """
    user_service = UserService(db)

    try:
        updated_user = await user_service.update_profile(
            user_id=current_user.id,
            nickname=request_body.nickname,
            avatar_url=request_body.avatar_url,
        )

        return UserProfileResponse(
            id=updated_user.id,
            email=updated_user.email,
            nickname=updated_user.nickname,
            avatar_url=updated_user.avatar_url,
            status=updated_user.status,
            balance=updated_user.balance,
            total_hands=updated_user.total_hands,
            total_winnings=updated_user.total_winnings,
            created_at=updated_user.created_at,
        )

    except UserError as e:
        status_code = status.HTTP_400_BAD_REQUEST
        if "NICKNAME_EXISTS" in e.code:
            status_code = status.HTTP_409_CONFLICT

        raise HTTPException(
            status_code=status_code,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details,
                },
                "traceId": trace_id,
            },
        )


@router.post(
    "/me/password",
    response_model=SuccessResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid current password"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        429: {"model": ErrorResponse, "description": "Too many attempts"},
    },
)
async def change_password(
    request: Request,
    request_body: ChangePasswordRequest,
    current_user: CurrentUser,
    db: DbSession,
    trace_id: TraceId,
):
    """Change current user's password.

    Requires the current password for verification.
    Rate limited: 3 attempts per 5 minutes.
    """
    # Check rate limit before processing
    await check_password_rate_limit(request, current_user.id)
    
    user_service = UserService(db)

    try:
        await user_service.change_password(
            user_id=current_user.id,
            current_password=request_body.current_password,
            new_password=request_body.new_password,
        )

        return SuccessResponse(
            success=True,
            message="Password changed successfully",
        )

    except UserError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details,
                },
                "traceId": trace_id,
            },
        )


@router.get(
    "/me/stats",
    response_model=UserStatsResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
async def get_current_user_stats(
    current_user: CurrentUser,
    db: DbSession,
):
    """Get current user's game statistics.

    Returns detailed statistics including hands played, winnings, and performance metrics.
    """
    user_service = UserService(db)
    stats = await user_service.get_user_stats(current_user.id)

    return UserStatsResponse(
        total_hands=stats["total_hands"],
        total_winnings=stats["total_winnings"],
        hands_won=stats["hands_won"],
        biggest_pot=stats["biggest_pot"],
        vpip=stats["vpip"],
        pfr=stats["pfr"],
    )


@router.get(
    "/me/stats/detailed",
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
    summary="상세 통계 조회",
    description="VPIP, PFR, 3Bet, AF, WTSD, WSD 등 상세 통계와 플레이 스타일 분석을 반환합니다.",
)
async def get_detailed_stats(
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    """상세 통계 조회 (플레이 스타일 분석 포함)."""
    from app.services.statistics import StatisticsService

    stats_service = StatisticsService(db)
    return await stats_service.get_stats_summary(current_user.id)


@router.delete(
    "/me",
    response_model=SuccessResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
async def deactivate_account(
    current_user: CurrentUser,
    db: DbSession,
):
    """Deactivate current user's account.

    This soft-deletes the account. The user will no longer be able to log in.
    """
    user_service = UserService(db)
    await user_service.deactivate_user(current_user.id)

    return SuccessResponse(
        success=True,
        message="Account deactivated successfully",
    )


@router.get(
    "/{user_id}",
    response_model=UserPublicProfileResponse,
    responses={
        404: {"model": ErrorResponse, "description": "User not found"},
    },
)
async def get_user_profile(
    user_id: str,
    db: DbSession,
    trace_id: TraceId,
):
    """Get a user's public profile.

    Returns public profile information for any user.
    Excludes sensitive information (email, balance) for privacy.
    """
    user_service = UserService(db)
    user = await user_service.get_user(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "USER_NOT_FOUND",
                    "message": "User not found",
                    "details": {},
                },
                "traceId": trace_id,
            },
        )

    # Return public-only info (no email, no balance)
    return UserPublicProfileResponse(
        id=user.id,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        status=user.status,
        total_hands=user.total_hands,
        total_winnings=user.total_winnings,
        created_at=user.created_at,
    )
