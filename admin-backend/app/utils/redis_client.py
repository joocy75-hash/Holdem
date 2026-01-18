"""Redis 클라이언트 유틸리티."""

from redis.asyncio import Redis

from app.config import get_settings

_redis_instance: Redis | None = None


async def get_redis() -> Redis:
    """Redis 클라이언트 인스턴스를 반환합니다.
    
    싱글톤 패턴으로 하나의 연결을 재사용합니다.
    """
    global _redis_instance
    
    if _redis_instance is None:
        settings = get_settings()
        _redis_instance = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
    
    return _redis_instance


async def close_redis() -> None:
    """Redis 연결을 닫습니다."""
    global _redis_instance
    
    if _redis_instance is not None:
        await _redis_instance.close()
        _redis_instance = None
