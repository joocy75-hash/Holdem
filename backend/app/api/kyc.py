"""KYC (성인 인증) API 엔드포인트.

본인인증 및 성인 확인 관련 API.
"""

from datetime import date

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, DbSession, TraceId
from app.models.kyc import KYCProvider, KYCStatus
from app.schemas import ErrorResponse
from app.services.kyc import KYCError, KYCService

router = APIRouter(prefix="/kyc", tags=["KYC"])


# ============================================================
# Request Schemas
# ============================================================


class KYCRequestBody(BaseModel):
    """본인인증 요청."""
    
    provider: str = Field(
        default="nice",
        description="인증 제공자 (nice, pass, kakao, toss)",
    )


class KYCCompleteBody(BaseModel):
    """본인인증 완료 (콜백용)."""
    
    real_name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="실명",
        alias="realName",
    )
    birth_date: date = Field(
        ...,
        description="생년월일 (YYYY-MM-DD)",
        alias="birthDate",
    )
    phone_number: str = Field(
        ...,
        min_length=10,
        max_length=15,
        description="휴대폰 번호 (숫자만)",
        alias="phoneNumber",
    )
    ci: str | None = Field(
        None,
        description="연계정보 (CI)",
    )
    di: str | None = Field(
        None,
        description="본인확인정보 (DI)",
    )

    class Config:
        populate_by_name = True


# ============================================================
# Response Schemas
# ============================================================


class KYCStatusResponse(BaseModel):
    """KYC 상태 응답."""
    
    status: str = Field(..., description="인증 상태")
    is_verified: bool = Field(..., alias="isVerified", description="인증 완료 여부")
    is_adult: bool = Field(..., alias="isAdult", description="성인 여부")
    can_withdraw: bool = Field(..., alias="canWithdraw", description="출금 가능 여부")
    verified_at: str | None = Field(None, alias="verifiedAt", description="인증 완료 일시")
    expires_at: str | None = Field(None, alias="expiresAt", description="인증 만료 일시")
    rejection_reason: str | None = Field(None, alias="rejectionReason", description="거부 사유")
    message: str = Field(..., description="상태 메시지")

    class Config:
        populate_by_name = True


class KYCRequestResponse(BaseModel):
    """본인인증 요청 응답."""
    
    request_id: str = Field(..., alias="requestId", description="인증 요청 ID")
    provider: str = Field(..., description="인증 제공자")
    status: str = Field(..., description="요청 상태")
    redirect_url: str = Field(..., alias="redirectUrl", description="인증 페이지 URL")
    message: str = Field(..., description="안내 메시지")

    class Config:
        populate_by_name = True


# ============================================================
# API Endpoints
# ============================================================


@router.get(
    "/status",
    response_model=KYCStatusResponse,
    responses={
        401: {"model": ErrorResponse, "description": "인증되지 않음"},
    },
    summary="KYC 상태 조회",
    description="현재 사용자의 본인인증 상태를 조회합니다.",
)
async def get_kyc_status(
    current_user: CurrentUser,
    db: DbSession,
):
    """본인인증 상태 조회."""
    kyc_service = KYCService(db)
    result = await kyc_service.get_kyc_status(current_user.id)

    return KYCStatusResponse(
        status=result["status"],
        is_verified=result["is_verified"],
        is_adult=result["is_adult"],
        can_withdraw=result["can_withdraw"],
        verified_at=result.get("verified_at"),
        expires_at=result.get("expires_at"),
        rejection_reason=result.get("rejection_reason"),
        message=result["message"],
    )


@router.post(
    "/request",
    response_model=KYCRequestResponse,
    responses={
        400: {"model": ErrorResponse, "description": "인증 요청 불가"},
        401: {"model": ErrorResponse, "description": "인증되지 않음"},
        409: {"model": ErrorResponse, "description": "이미 인증 완료"},
        429: {"model": ErrorResponse, "description": "시도 횟수 초과"},
    },
    summary="본인인증 요청",
    description="본인인증을 시작합니다. 인증 페이지 URL을 반환합니다.",
)
async def request_kyc_verification(
    request_body: KYCRequestBody,
    current_user: CurrentUser,
    db: DbSession,
    trace_id: TraceId,
):
    """본인인증 요청 시작."""
    kyc_service = KYCService(db)

    # 제공자 검증
    try:
        provider = KYCProvider(request_body.provider)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_PROVIDER",
                    "message": f"지원하지 않는 인증 제공자입니다: {request_body.provider}",
                    "details": {"valid_providers": [p.value for p in KYCProvider]},
                },
                "traceId": trace_id,
            },
        )

    try:
        result = await kyc_service.request_verification(
            user_id=current_user.id,
            provider=provider,
        )
        await db.commit()

        return KYCRequestResponse(
            request_id=result["request_id"],
            provider=result["provider"],
            status=result["status"],
            redirect_url=result["redirect_url"],
            message=result["message"],
        )

    except KYCError as e:
        status_code = status.HTTP_400_BAD_REQUEST
        if e.code == "KYC_ALREADY_VERIFIED":
            status_code = status.HTTP_409_CONFLICT
        elif e.code == "KYC_TOO_MANY_ATTEMPTS":
            status_code = status.HTTP_429_TOO_MANY_REQUESTS

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
    "/complete",
    response_model=KYCStatusResponse,
    responses={
        400: {"model": ErrorResponse, "description": "인증 실패"},
        401: {"model": ErrorResponse, "description": "인증되지 않음"},
        403: {"model": ErrorResponse, "description": "미성년자"},
        409: {"model": ErrorResponse, "description": "중복 계정"},
    },
    summary="본인인증 완료",
    description="본인인증을 완료합니다. 외부 인증 서비스 콜백 후 호출됩니다.",
)
async def complete_kyc_verification(
    request_body: KYCCompleteBody,
    current_user: CurrentUser,
    db: DbSession,
    trace_id: TraceId,
):
    """본인인증 완료 처리."""
    kyc_service = KYCService(db)

    try:
        result = await kyc_service.complete_verification(
            user_id=current_user.id,
            real_name=request_body.real_name,
            birth_date=request_body.birth_date,
            phone_number=request_body.phone_number,
            ci=request_body.ci,
            di=request_body.di,
        )
        await db.commit()

        return KYCStatusResponse(
            status=result["status"],
            is_verified=result["is_verified"],
            is_adult=result["is_adult"],
            can_withdraw=result["can_withdraw"],
            verified_at=result.get("verified_at"),
            expires_at=result.get("expires_at"),
            rejection_reason=None,
            message=result["message"],
        )

    except KYCError as e:
        await db.rollback()

        status_code = status.HTTP_400_BAD_REQUEST
        if e.code == "KYC_NOT_ADULT":
            status_code = status.HTTP_403_FORBIDDEN
        elif e.code == "KYC_DUPLICATE_CI":
            status_code = status.HTTP_409_CONFLICT
        elif e.code == "KYC_ALREADY_VERIFIED":
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


@router.get(
    "/can-withdraw",
    responses={
        401: {"model": ErrorResponse, "description": "인증되지 않음"},
    },
    summary="출금 가능 여부 확인",
    description="KYC 인증 상태 기반으로 출금 가능 여부를 확인합니다.",
)
async def check_can_withdraw(
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    """출금 가능 여부 확인."""
    kyc_service = KYCService(db)
    result = await kyc_service.get_kyc_status(current_user.id)

    return {
        "canWithdraw": result["can_withdraw"],
        "reason": None if result["can_withdraw"] else result["message"],
    }
