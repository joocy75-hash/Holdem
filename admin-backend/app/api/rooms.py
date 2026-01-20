"""Room Management API for Admin Dashboard.

Provides endpoints for managing game rooms including:
- Room listing and details (CRUD)
- Force closing rooms with chip refunds
- Sending system messages to rooms

**Phase 3.3**: 방 강제 종료 기능 구현
**Phase X**: 방 CRUD 기능 구현
"""
import logging
from typing import Literal, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

from app.config import get_settings
from app.models.admin_user import AdminUser
from app.utils.dependencies import get_current_user, require_operator, require_supervisor
from app.utils.permissions import Permission, has_permission

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


# ============================================================================
# Request/Response Models
# ============================================================================


class SeatInfo(BaseModel):
    """좌석 정보"""
    model_config = ConfigDict(populate_by_name=True)

    position: int
    user_id: Optional[str] = Field(None, alias="userId")
    nickname: Optional[str] = None
    stack: int = 0
    status: str = "empty"
    is_bot: bool = Field(default=False, alias="isBot")


class RoomResponse(BaseModel):
    """방 정보 응답"""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    description: Optional[str] = None
    player_count: int = Field(..., alias="playerCount")
    max_players: int = Field(..., alias="maxPlayers")
    small_blind: int = Field(..., alias="smallBlind")
    big_blind: int = Field(..., alias="bigBlind")
    buy_in_min: int = Field(..., alias="buyInMin")
    buy_in_max: int = Field(..., alias="buyInMax")
    status: str
    is_private: bool = Field(..., alias="isPrivate")
    room_type: str = Field(..., alias="roomType")
    owner_id: Optional[str] = Field(None, alias="ownerId")
    owner_nickname: Optional[str] = Field(None, alias="ownerNickname")
    created_at: str = Field(..., alias="createdAt")


class RoomDetailResponse(RoomResponse):
    """방 상세 정보 응답"""
    turn_timeout: int = Field(..., alias="turnTimeout")
    seats: list[SeatInfo] = Field(default_factory=list)
    current_hand_id: Optional[str] = Field(None, alias="currentHandId")
    updated_at: str = Field(..., alias="updatedAt")


class PaginatedRooms(BaseModel):
    """방 목록 페이지네이션 응답"""
    model_config = ConfigDict(populate_by_name=True)

    items: list[RoomResponse]
    total: int
    page: int
    page_size: int = Field(..., alias="pageSize")
    total_pages: int = Field(..., alias="totalPages")


class CreateRoomRequest(BaseModel):
    """방 생성 요청"""
    name: str = Field(..., min_length=2, max_length=100, description="방 이름")
    description: Optional[str] = Field(None, max_length=500, description="방 설명")
    room_type: Literal["cash", "tournament"] = Field(default="cash", alias="roomType")
    max_seats: Literal[6, 9] = Field(default=9, alias="maxSeats")
    small_blind: int = Field(default=10, ge=1, alias="smallBlind")
    big_blind: int = Field(default=20, ge=2, alias="bigBlind")
    buy_in_min: int = Field(default=400, ge=1, alias="buyInMin")
    buy_in_max: int = Field(default=2000, ge=1, alias="buyInMax")
    turn_timeout: int = Field(default=30, ge=10, le=120, alias="turnTimeout")
    is_private: bool = Field(default=False, alias="isPrivate")
    password: Optional[str] = Field(None, min_length=4, max_length=20)


class UpdateRoomRequest(BaseModel):
    """방 수정 요청 - 모든 설정 변경 가능"""
    # 기본 정보
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_private: Optional[bool] = Field(None, alias="isPrivate")
    password: Optional[str] = Field(None, min_length=4, max_length=20)
    # 게임 설정
    small_blind: Optional[int] = Field(None, ge=1, alias="smallBlind")
    big_blind: Optional[int] = Field(None, ge=2, alias="bigBlind")
    buy_in_min: Optional[int] = Field(None, ge=1, alias="buyInMin")
    buy_in_max: Optional[int] = Field(None, ge=1, alias="buyInMax")
    turn_timeout: Optional[int] = Field(None, ge=10, le=120, alias="turnTimeout")
    # 테이블 설정 (플레이어 없을 때만)
    max_seats: Optional[Literal[6, 9]] = Field(None, alias="maxSeats")


class ForceCloseRequest(BaseModel):
    """방 강제 종료 요청"""
    reason: str = Field(..., min_length=1, max_length=500, description="강제 종료 사유")


class RefundInfo(BaseModel):
    """환불 정보"""
    user_id: str
    nickname: str
    amount: int
    seat: int


class ForceCloseResponse(BaseModel):
    """방 강제 종료 응답"""
    model_config = ConfigDict(populate_by_name=True)

    success: bool
    room_id: str = Field(..., alias="roomId")
    room_name: str = Field(..., alias="roomName")
    reason: str
    refunds: list[RefundInfo]
    total_refunded: int = Field(..., alias="totalRefunded")
    players_affected: int = Field(..., alias="playersAffected")


class CloseRoomResponse(BaseModel):
    """방 종료 응답"""
    model_config = ConfigDict(populate_by_name=True)

    success: bool
    message: str
    room_id: str = Field(..., alias="roomId")


class SystemMessageRequest(BaseModel):
    """시스템 메시지 요청"""
    message: str = Field(..., min_length=1, max_length=1000)


class SystemMessageResponse(BaseModel):
    """시스템 메시지 응답"""
    model_config = ConfigDict(populate_by_name=True)

    success: bool
    room_id: str = Field(..., alias="roomId")
    message: str


# ============================================================================
# Helper Functions
# ============================================================================


async def _call_game_backend(
    method: str,
    path: str,
    data: Optional[dict] = None,
    params: Optional[dict] = None,
) -> dict:
    """Game Backend API 호출.

    Args:
        method: HTTP 메서드 (GET, POST, PATCH, DELETE)
        path: API 경로 (/internal/admin/...)
        data: 요청 데이터 (POST/PATCH에서 사용)
        params: 쿼리 파라미터 (GET에서 사용)

    Returns:
        API 응답 데이터

    Raises:
        HTTPException: API 호출 실패 시
    """
    url = f"{settings.main_api_url}{path}"
    headers = {"X-API-Key": settings.main_api_key}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            method_upper = method.upper()

            if method_upper == "GET":
                response = await client.get(url, headers=headers, params=params)
            elif method_upper == "POST":
                response = await client.post(url, json=data, headers=headers)
            elif method_upper == "PATCH":
                response = await client.patch(url, json=data, headers=headers)
            elif method_upper == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            if response.status_code in (200, 201):
                return response.json()
            elif response.status_code == 401:
                logger.error("Game Backend API key authentication failed")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Game server authentication failed",
                )
            elif response.status_code == 404:
                error_detail = response.json().get("detail", "리소스를 찾을 수 없습니다")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=error_detail,
                )
            elif response.status_code == 400:
                error_detail = response.json().get("detail", "잘못된 요청입니다")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_detail,
                )
            else:
                logger.error(f"Game Backend API error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Game server error",
                )

    except httpx.TimeoutException:
        logger.error(f"Game Backend API timeout: {url}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Game server timeout",
        )
    except httpx.RequestError as e:
        logger.error(f"Game Backend API connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Game server connection failed",
        )


# ============================================================================
# API Endpoints - List & Detail
# ============================================================================


@router.get("", response_model=PaginatedRooms)
async def list_rooms(
    status_filter: Optional[str] = Query(None, alias="status", description="상태 필터 (waiting, playing, closed)"),
    search: Optional[str] = Query(None, description="방 이름 검색"),
    include_closed: bool = Query(False, alias="includeClosed", description="종료된 방 포함"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    current_user: AdminUser = Depends(get_current_user),
):
    """방 목록 조회.

    - 필터링: 상태, 검색어
    - 페이지네이션 지원
    - 종료된 방 포함 옵션

    **권한**: 모든 관리자
    """
    if not has_permission(current_user.role, Permission.VIEW_ROOMS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="VIEW_ROOMS 권한이 필요합니다",
        )

    params = {
        "page": page,
        "page_size": page_size,
        "include_closed": include_closed,
    }
    if status_filter:
        params["status"] = status_filter
    if search:
        params["search"] = search

    result = await _call_game_backend(
        method="GET",
        path="/api/v1/internal/admin/rooms",
        params=params,
    )

    return PaginatedRooms(**result)


@router.get("/{room_id}", response_model=RoomDetailResponse)
async def get_room(
    room_id: str,
    current_user: AdminUser = Depends(get_current_user),
):
    """방 상세 조회.

    - 현재 착석자 정보 포함
    - 진행 중인 핸드 ID 포함 (있는 경우)

    **권한**: 모든 관리자
    """
    if not has_permission(current_user.role, Permission.VIEW_ROOMS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="VIEW_ROOMS 권한이 필요합니다",
        )

    result = await _call_game_backend(
        method="GET",
        path=f"/api/v1/internal/admin/rooms/{room_id}",
    )

    return RoomDetailResponse(**result)


# ============================================================================
# API Endpoints - Create, Update, Delete
# ============================================================================


@router.post("", response_model=RoomDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    request: CreateRoomRequest,
    current_user: AdminUser = Depends(require_operator),
):
    """방 생성.

    - owner_id는 None (시스템 소유)
    - 모든 설정 가능

    **권한**: operator 이상
    """
    if not has_permission(current_user.role, Permission.CREATE_ROOM):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CREATE_ROOM 권한이 필요합니다",
        )

    logger.info(
        f"Admin {current_user.username} ({current_user.id}) creating room: {request.name}"
    )

    # snake_case로 변환하여 전송
    data = {
        "name": request.name,
        "description": request.description,
        "room_type": request.room_type,
        "max_seats": request.max_seats,
        "small_blind": request.small_blind,
        "big_blind": request.big_blind,
        "buy_in_min": request.buy_in_min,
        "buy_in_max": request.buy_in_max,
        "turn_timeout": request.turn_timeout,
        "is_private": request.is_private,
        "password": request.password,
    }

    result = await _call_game_backend(
        method="POST",
        path="/api/v1/internal/admin/rooms",
        data=data,
    )

    logger.info(f"Room created by admin {current_user.username}: {result.get('id')}")

    return RoomDetailResponse(**result)


@router.patch("/{room_id}", response_model=RoomDetailResponse)
async def update_room(
    room_id: str,
    request: UpdateRoomRequest,
    current_user: AdminUser = Depends(require_operator),
):
    """방 설정 수정.

    - owner 권한 체크 없음
    - 모든 설정 변경 가능 (좌석 수는 플레이어 없을 때만)

    **권한**: operator 이상
    """
    if not has_permission(current_user.role, Permission.UPDATE_ROOM):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="UPDATE_ROOM 권한이 필요합니다",
        )

    logger.info(
        f"Admin {current_user.username} ({current_user.id}) updating room {room_id}"
    )

    # None이 아닌 필드만 전송 (snake_case로 변환)
    data = {}
    if request.name is not None:
        data["name"] = request.name
    if request.description is not None:
        data["description"] = request.description
    if request.is_private is not None:
        data["is_private"] = request.is_private
    if request.password is not None:
        data["password"] = request.password
    if request.small_blind is not None:
        data["small_blind"] = request.small_blind
    if request.big_blind is not None:
        data["big_blind"] = request.big_blind
    if request.buy_in_min is not None:
        data["buy_in_min"] = request.buy_in_min
    if request.buy_in_max is not None:
        data["buy_in_max"] = request.buy_in_max
    if request.turn_timeout is not None:
        data["turn_timeout"] = request.turn_timeout
    if request.max_seats is not None:
        data["max_seats"] = request.max_seats

    result = await _call_game_backend(
        method="PATCH",
        path=f"/api/v1/internal/admin/rooms/{room_id}",
        data=data,
    )

    logger.info(f"Room {room_id} updated by admin {current_user.username}")

    return RoomDetailResponse(**result)


@router.delete("/{room_id}", response_model=CloseRoomResponse)
async def delete_room(
    room_id: str,
    current_user: AdminUser = Depends(require_operator),
):
    """방 종료.

    - 플레이어가 없는 방만 종료 가능
    - 플레이어가 있으면 force-close 사용 필요

    **권한**: operator 이상
    """
    if not has_permission(current_user.role, Permission.DELETE_ROOM):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="DELETE_ROOM 권한이 필요합니다",
        )

    logger.info(
        f"Admin {current_user.username} ({current_user.id}) deleting room {room_id}"
    )

    result = await _call_game_backend(
        method="DELETE",
        path=f"/api/v1/internal/admin/rooms/{room_id}",
    )

    logger.info(f"Room {room_id} deleted by admin {current_user.username}")

    return CloseRoomResponse(**result)


# ============================================================================
# API Endpoints - Force Close & System Message
# ============================================================================


@router.post("/{room_id}/force-close", response_model=ForceCloseResponse)
async def force_close_room(
    room_id: str,
    request: ForceCloseRequest,
    current_user: AdminUser = Depends(require_supervisor),
):
    """방 강제 종료.

    - 진행 중인 게임이 있어도 강제로 종료합니다.
    - 모든 플레이어의 칩을 환불합니다.
    - WebSocket으로 플레이어에게 알림을 보냅니다.

    **권한**: supervisor 이상
    """
    if not has_permission(current_user.role, Permission.FORCE_CLOSE_ROOM):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="FORCE_CLOSE_ROOM 권한이 필요합니다",
        )

    logger.info(
        f"Admin {current_user.username} ({current_user.id}) "
        f"requesting force close for room {room_id}: {request.reason}"
    )

    result = await _call_game_backend(
        method="POST",
        path=f"/api/v1/internal/admin/rooms/{room_id}/force-close",
        data={
            "reason": request.reason,
            "admin_user_id": str(current_user.id),
        },
    )

    logger.info(
        f"Room {room_id} force closed by admin {current_user.username}: "
        f"{result.get('players_affected', 0)} players refunded "
        f"{result.get('total_refunded', 0)} chips"
    )

    return ForceCloseResponse(
        success=result.get("success", True),
        room_id=result.get("room_id", room_id),
        room_name=result.get("room_name", "Unknown"),
        reason=result.get("reason", request.reason),
        refunds=[RefundInfo(**r) for r in result.get("refunds", [])],
        total_refunded=result.get("total_refunded", 0),
        players_affected=result.get("players_affected", 0),
    )


@router.post("/{room_id}/message", response_model=SystemMessageResponse)
async def send_system_message(
    room_id: str,
    request: SystemMessageRequest,
    current_user: AdminUser = Depends(require_operator),
):
    """방에 시스템 메시지 전송.

    **권한**: operator 이상

    **Note**: 2차 구현으로 미룸
    """
    if not has_permission(current_user.role, Permission.SEND_ROOM_MESSAGE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SEND_ROOM_MESSAGE 권한이 필요합니다",
        )

    # TODO: Game Backend에 시스템 메시지 전송 API 호출 구현 (2차)
    logger.info(
        f"Admin {current_user.username} sending message to room {room_id}: {request.message}"
    )

    return SystemMessageResponse(
        success=True,
        room_id=room_id,
        message=request.message,
    )
