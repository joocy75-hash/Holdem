"""Admin API 전용 스키마.

어드민 백엔드와 통신하는 내부 API용 요청/응답 스키마입니다.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# Request Models
# =============================================================================


class AdminCreateRoomRequest(BaseModel):
    """어드민 방 생성 요청."""

    name: str = Field(..., min_length=2, max_length=100, description="방 이름")
    description: str | None = Field(None, max_length=500, description="방 설명")
    room_type: Literal["cash", "tournament"] = Field(default="cash", description="방 타입")
    max_seats: Literal[6, 9] = Field(default=9, description="최대 좌석 수")
    small_blind: int = Field(default=10, ge=1, description="스몰 블라인드")
    big_blind: int = Field(default=20, ge=2, description="빅 블라인드")
    buy_in_min: int = Field(default=400, ge=1, description="최소 바이인")
    buy_in_max: int = Field(default=2000, ge=1, description="최대 바이인")
    turn_timeout: int = Field(default=30, ge=10, le=120, description="턴 타임아웃(초)")
    is_private: bool = Field(default=False, description="비공개 여부")
    password: str | None = Field(None, min_length=4, max_length=20, description="비공개 방 비밀번호")


class AdminUpdateRoomRequest(BaseModel):
    """어드민 방 수정 요청.

    모든 설정을 수정할 수 있습니다.
    max_seats는 플레이어가 없을 때만 변경 가능합니다.
    """

    # 기본 정보
    name: str | None = Field(None, min_length=2, max_length=100, description="방 이름")
    description: str | None = Field(None, max_length=500, description="방 설명")
    is_private: bool | None = Field(None, description="비공개 여부")
    password: str | None = Field(None, min_length=4, max_length=20, description="비공개 방 비밀번호")

    # 게임 설정
    small_blind: int | None = Field(None, ge=1, description="스몰 블라인드")
    big_blind: int | None = Field(None, ge=2, description="빅 블라인드")
    buy_in_min: int | None = Field(None, ge=1, description="최소 바이인")
    buy_in_max: int | None = Field(None, ge=1, description="최대 바이인")
    turn_timeout: int | None = Field(None, ge=10, le=120, description="턴 타임아웃(초)")

    # 테이블 설정 (플레이어 없을 때만)
    max_seats: Literal[6, 9] | None = Field(None, description="최대 좌석 수 (플레이어 없을 때만)")


# =============================================================================
# Response Models
# =============================================================================


class AdminSeatInfo(BaseModel):
    """좌석 정보."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    position: int
    user_id: str | None = Field(None, alias="userId")
    nickname: str | None = None
    stack: int = 0
    status: str = "empty"
    is_bot: bool = Field(default=False, alias="isBot")


class AdminRoomResponse(BaseModel):
    """어드민 방 목록용 응답."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: str
    name: str
    description: str | None = None
    player_count: int = Field(..., alias="playerCount")
    max_players: int = Field(..., alias="maxPlayers")
    small_blind: int = Field(..., alias="smallBlind")
    big_blind: int = Field(..., alias="bigBlind")
    buy_in_min: int = Field(..., alias="buyInMin")
    buy_in_max: int = Field(..., alias="buyInMax")
    status: str
    is_private: bool = Field(..., alias="isPrivate")
    room_type: str = Field(..., alias="roomType")
    owner_id: str | None = Field(None, alias="ownerId")
    owner_nickname: str | None = Field(None, alias="ownerNickname")
    created_at: datetime = Field(..., alias="createdAt")


class AdminRoomDetailResponse(AdminRoomResponse):
    """어드민 방 상세 응답."""

    turn_timeout: int = Field(..., alias="turnTimeout")
    seats: list[AdminSeatInfo] = Field(default_factory=list)
    current_hand_id: str | None = Field(None, alias="currentHandId")
    updated_at: datetime = Field(..., alias="updatedAt")


class AdminRoomListResponse(BaseModel):
    """어드민 방 목록 응답."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    items: list[AdminRoomResponse]
    total: int
    page: int
    page_size: int = Field(..., alias="pageSize")
    total_pages: int = Field(..., alias="totalPages")


class AdminCloseRoomResponse(BaseModel):
    """방 종료 응답."""

    success: bool
    message: str
    room_id: str = Field(..., alias="roomId")


# =============================================================================
# Rake Config Models (P1-1)
# =============================================================================


class RakeConfigCreate(BaseModel):
    """레이크 설정 생성 요청."""

    small_blind: int = Field(..., ge=1, alias="smallBlind", description="스몰 블라인드 (KRW)")
    big_blind: int = Field(..., ge=2, alias="bigBlind", description="빅 블라인드 (KRW)")
    percentage: float = Field(
        ..., ge=0.0, le=1.0, description="레이크 퍼센트 (0.05 = 5%)"
    )
    cap_bb: int = Field(..., ge=1, le=20, alias="capBb", description="레이크 캡 (BB 단위)")
    is_active: bool = Field(default=True, alias="isActive", description="활성화 여부")

    model_config = ConfigDict(populate_by_name=True)


class RakeConfigUpdate(BaseModel):
    """레이크 설정 수정 요청."""

    percentage: float | None = Field(
        None, ge=0.0, le=1.0, description="레이크 퍼센트 (0.05 = 5%)"
    )
    cap_bb: int | None = Field(None, ge=1, le=20, alias="capBb", description="레이크 캡 (BB 단위)")
    is_active: bool | None = Field(None, alias="isActive", description="활성화 여부")

    model_config = ConfigDict(populate_by_name=True)


class RakeConfigResponse(BaseModel):
    """레이크 설정 응답."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: str
    small_blind: int = Field(..., alias="smallBlind")
    big_blind: int = Field(..., alias="bigBlind")
    percentage: float
    cap_bb: int = Field(..., alias="capBb")
    is_active: bool = Field(..., alias="isActive")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")


class RakeConfigListResponse(BaseModel):
    """레이크 설정 목록 응답."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    items: list[RakeConfigResponse]
    total: int
