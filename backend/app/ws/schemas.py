"""Pydantic schemas for WebSocket message validation.

Provides type-safe validation for incoming WebSocket messages.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ActionRequestPayload(BaseModel):
    """Payload for ACTION_REQUEST event."""

    tableId: str = Field(..., min_length=1, description="Table/Room ID")
    actionType: Literal["fold", "check", "call", "bet", "raise", "all_in"] = Field(
        ..., description="Action type"
    )
    amount: int = Field(default=0, ge=0, description="Bet/raise amount")

    @field_validator("actionType", mode="before")
    @classmethod
    def normalize_action_type(cls, v: str) -> str:
        """Normalize action type to lowercase."""
        if isinstance(v, str):
            return v.lower()
        return v


class SeatRequestPayload(BaseModel):
    """Payload for SEAT_REQUEST event."""

    tableId: str = Field(..., min_length=1, description="Table/Room ID")
    buyInAmount: int = Field(..., gt=0, description="Buy-in amount")
    preferredSeat: int | None = Field(default=None, ge=0, le=8, description="Preferred seat")


class LeaveRequestPayload(BaseModel):
    """Payload for LEAVE_REQUEST event."""

    tableId: str = Field(..., min_length=1, description="Table/Room ID")


class StartGamePayload(BaseModel):
    """Payload for START_GAME event."""

    tableId: str = Field(..., min_length=1, description="Table/Room ID")


class SubscribeTablePayload(BaseModel):
    """Payload for SUBSCRIBE_TABLE event."""

    tableId: str = Field(..., min_length=1, description="Table/Room ID")


class UnsubscribeTablePayload(BaseModel):
    """Payload for UNSUBSCRIBE_TABLE event."""

    tableId: str = Field(..., min_length=1, description="Table/Room ID")


class AddBotRequestPayload(BaseModel):
    """Payload for ADD_BOT_REQUEST event."""

    tableId: str = Field(..., min_length=1, description="Table/Room ID")
    buyIn: int = Field(..., gt=0, description="Bot buy-in amount")


class StartBotLoopRequestPayload(BaseModel):
    """Payload for START_BOT_LOOP_REQUEST event."""

    tableId: str = Field(..., min_length=1, description="Table/Room ID")
    botCount: int = Field(default=4, ge=1, le=8, description="Number of bots to add")
    buyIn: int | None = Field(default=None, gt=0, description="Bot buy-in amount")


class ChatMessagePayload(BaseModel):
    """Payload for CHAT_MESSAGE event."""

    tableId: str | None = Field(default=None, description="Table ID for table chat")
    message: str = Field(..., min_length=1, max_length=500, description="Chat message")


class RoomCreateRequestPayload(BaseModel):
    """Payload for ROOM_CREATE_REQUEST event."""

    name: str = Field(..., min_length=1, max_length=50, description="Room name")
    smallBlind: int = Field(default=10, gt=0, description="Small blind amount")
    bigBlind: int = Field(default=20, gt=0, description="Big blind amount")
    minBuyIn: int = Field(default=1000, gt=0, description="Minimum buy-in")
    maxBuyIn: int = Field(default=10000, gt=0, description="Maximum buy-in")
    maxSeats: int = Field(default=9, ge=2, le=9, description="Maximum seats")
    isPrivate: bool = Field(default=False, description="Private room flag")


class RoomJoinRequestPayload(BaseModel):
    """Payload for ROOM_JOIN_REQUEST event."""

    roomId: str = Field(..., min_length=1, description="Room ID")
    buyIn: int = Field(..., gt=0, description="Buy-in amount")
