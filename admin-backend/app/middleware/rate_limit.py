"""
Rate Limiting Middleware - API 요청 속도 제한

보안 기능:
- Brute-force 공격 방지
- DoS 공격 완화
- API 남용 방지

Rate Limit 정책:
- 인증 엔드포인트: 5req/분 (로그인 시도 제한)
- 일반 조회 API: 60req/분
- 쓰기 API (POST/PUT/DELETE): 30req/분
- 관리자 전용 API: 120req/분 (신뢰할 수 있는 사용자)
"""
import logging
from typing import Callable

from fastapi import FastAPI, Request, Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


def get_real_ip(request: Request) -> str:
    """실제 클라이언트 IP 주소 추출 (프록시 고려)"""
    # X-Forwarded-For 헤더 확인 (리버스 프록시 뒤에 있을 때)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # 첫 번째 IP가 실제 클라이언트 IP
        return forwarded.split(",")[0].strip()
    
    # X-Real-IP 헤더 확인 (Nginx 등)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # 기본값: 직접 연결 IP
    return get_remote_address(request)


def get_user_identifier(request: Request) -> str:
    """사용자 식별자 추출 (IP + 인증 토큰 조합)
    
    인증된 사용자는 토큰 기반으로 제한하고,
    비인증 사용자는 IP 기반으로 제한합니다.
    """
    # Authorization 헤더에서 토큰 추출
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        # 토큰의 일부만 사용 (프라이버시 보호)
        token = auth_header[7:]
        if len(token) > 20:
            return f"token:{token[:20]}"
    
    # 비인증 요청은 IP 기반
    return f"ip:{get_real_ip(request)}"


# Limiter 인스턴스 생성
limiter = Limiter(
    key_func=get_user_identifier,
    default_limits=["60/minute"],  # 기본 제한: 분당 60회
    storage_uri=settings.redis_url,  # Redis 백엔드 사용
    strategy="fixed-window",  # 고정 윈도우 전략
)


# Rate Limit 설정 상수
class RateLimits:
    """API 엔드포인트별 Rate Limit 정의"""
    
    # 인증 관련 (가장 엄격)
    AUTH_LOGIN = "5/minute"  # 로그인 시도
    AUTH_2FA = "10/minute"  # 2FA 인증
    AUTH_REFRESH = "30/minute"  # 토큰 갱신
    
    # 조회 API
    READ_DEFAULT = "60/minute"  # 일반 조회
    READ_LIST = "30/minute"  # 목록 조회 (더 무거운 쿼리)
    READ_DETAIL = "120/minute"  # 상세 조회
    READ_DASHBOARD = "30/minute"  # 대시보드 메트릭
    
    # 쓰기 API
    WRITE_DEFAULT = "30/minute"  # 일반 쓰기
    WRITE_BAN = "20/minute"  # 제재 생성/해제
    WRITE_CHIPS = "10/minute"  # 칩 지급/회수 (민감)
    
    # 관리자 전용
    ADMIN_DEFAULT = "120/minute"  # 관리자 기본
    ADMIN_EXPORT = "5/minute"  # 데이터 내보내기 (리소스 많이 사용)
    
    # 보안 관련
    SECURITY_CRITICAL = "3/minute"  # 매우 민감한 작업


def setup_rate_limiting(app: FastAPI) -> None:
    """Rate Limiting 미들웨어 설정"""
    # 에러 핸들러 등록
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _custom_rate_limit_handler)
    app.add_middleware(SlowAPIMiddleware)
    
    logger.info("Rate Limiting middleware enabled")


async def _custom_rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """Rate Limit 초과 시 커스텀 응답"""
    logger.warning(
        f"Rate limit exceeded: {get_user_identifier(request)}, "
        f"path={request.url.path}, limit={exc.detail}"
    )
    
    # Retry-After 헤더 포함
    response = Response(
        content='{"detail": "요청이 너무 많습니다. 잠시 후 다시 시도해주세요.", "code": "RATE_LIMIT_EXCEEDED"}',
        status_code=429,
        media_type="application/json",
        headers={
            "Retry-After": "60",  # 1분 후 재시도
            "X-RateLimit-Limit": str(exc.detail).split("/")[0] if "/" in str(exc.detail) else "60",
        }
    )
    return response


# 데코레이터 헬퍼 함수
def rate_limit(limit: str) -> Callable:
    """Rate Limit 데코레이터
    
    Usage:
        @router.get("/users")
        @rate_limit(RateLimits.READ_LIST)
        async def list_users(...):
            ...
    """
    return limiter.limit(limit)


# 동적 Rate Limit (역할 기반)
def get_role_based_limit(request: Request) -> str:
    """사용자 역할에 따른 동적 Rate Limit
    
    Admin 역할은 더 높은 제한을 받습니다.
    """
    # JWT에서 역할 추출 (간단한 구현)
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        # 실제로는 JWT 디코딩 필요
        # 여기서는 기본값 반환
        return RateLimits.ADMIN_DEFAULT
    
    return RateLimits.READ_DEFAULT
