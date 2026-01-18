"""
Cache Service - Redis 기반 캐싱 서비스

성능 최적화를 위한 캐싱 전략:
- TTL 기반 자동 만료
- 키 프리픽스로 네임스페이스 분리
- JSON 직렬화/역직렬화
"""
import json
import logging
from typing import Optional, Any, Callable, TypeVar
from functools import wraps

from redis.asyncio import Redis

from app.config import get_settings
from app.utils.redis_client import get_redis

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CacheService:
    """Redis 기반 캐싱 서비스"""
    
    # 캐시 키 프리픽스
    PREFIX = "admin:cache:"
    
    # 기본 TTL (초)
    DEFAULT_TTL = 300  # 5분
    
    # 기능별 TTL
    TTL_USER_ACTIVITY = 60  # 1분 (자주 변경됨)
    TTL_USER_LIST = 120  # 2분
    TTL_DASHBOARD_METRICS = 30  # 30초
    TTL_AUDIT_LOGS = 180  # 3분
    
    def __init__(self, redis: Redis):
        self.redis = redis
        self.settings = get_settings()
    
    def _make_key(self, namespace: str, *args: Any) -> str:
        """캐시 키 생성"""
        key_parts = [self.PREFIX, namespace]
        for arg in args:
            if arg is not None:
                key_parts.append(str(arg))
        return ":".join(key_parts)
    
    async def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 조회"""
        try:
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.warning(f"캐시 조회 실패: key={key}, error={e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: int = DEFAULT_TTL
    ) -> bool:
        """캐시에 값 저장"""
        try:
            data = json.dumps(value, default=str)
            await self.redis.setex(key, ttl, data)
            return True
        except Exception as e:
            logger.warning(f"캐시 저장 실패: key={key}, error={e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """캐시에서 값 삭제"""
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.warning(f"캐시 삭제 실패: key={key}, error={e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """패턴 매칭하는 모든 키 삭제"""
        try:
            full_pattern = f"{self.PREFIX}{pattern}"
            keys = []
            async for key in self.redis.scan_iter(match=full_pattern):
                keys.append(key)
            
            if keys:
                await self.redis.delete(*keys)
            return len(keys)
        except Exception as e:
            logger.warning(f"패턴 삭제 실패: pattern={pattern}, error={e}")
            return 0
    
    # =========================================================================
    # 사용자 활동 캐싱
    # =========================================================================
    
    async def get_user_activity(
        self,
        user_id: str,
        page: int,
        page_size: int,
        activity_type: Optional[str] = None
    ) -> Optional[dict]:
        """사용자 활동 로그 캐시 조회"""
        key = self._make_key("user_activity", user_id, page, page_size, activity_type)
        return await self.get(key)
    
    async def set_user_activity(
        self,
        user_id: str,
        page: int,
        page_size: int,
        activity_type: Optional[str],
        data: dict
    ) -> bool:
        """사용자 활동 로그 캐시 저장"""
        key = self._make_key("user_activity", user_id, page, page_size, activity_type)
        return await self.set(key, data, self.TTL_USER_ACTIVITY)
    
    async def invalidate_user_activity(self, user_id: str) -> int:
        """사용자 활동 캐시 무효화"""
        return await self.delete_pattern(f"user_activity:{user_id}:*")
    
    # =========================================================================
    # 사용자 목록 캐싱
    # =========================================================================
    
    async def get_user_list(
        self,
        search: Optional[str],
        page: int,
        page_size: int,
        is_banned: Optional[bool]
    ) -> Optional[dict]:
        """사용자 목록 캐시 조회"""
        key = self._make_key("user_list", search or "_all_", page, page_size, is_banned)
        return await self.get(key)
    
    async def set_user_list(
        self,
        search: Optional[str],
        page: int,
        page_size: int,
        is_banned: Optional[bool],
        data: dict
    ) -> bool:
        """사용자 목록 캐시 저장"""
        key = self._make_key("user_list", search or "_all_", page, page_size, is_banned)
        return await self.set(key, data, self.TTL_USER_LIST)
    
    async def invalidate_user_list(self) -> int:
        """사용자 목록 캐시 무효화"""
        return await self.delete_pattern("user_list:*")
    
    # =========================================================================
    # 활동 카운트 캐싱 (UNION ALL 최적화)
    # =========================================================================
    
    async def get_activity_count(
        self,
        user_id: str,
        activity_type: Optional[str] = None
    ) -> Optional[int]:
        """활동 카운트 캐시 조회"""
        key = self._make_key("activity_count", user_id, activity_type or "_all_")
        result = await self.get(key)
        return result.get("count") if result else None
    
    async def set_activity_count(
        self,
        user_id: str,
        activity_type: Optional[str],
        count: int
    ) -> bool:
        """활동 카운트 캐시 저장"""
        key = self._make_key("activity_count", user_id, activity_type or "_all_")
        return await self.set(key, {"count": count}, self.TTL_USER_ACTIVITY)


# 싱글톤 인스턴스
_cache_instance: Optional[CacheService] = None


async def get_cache_service() -> CacheService:
    """CacheService 싱글톤 인스턴스 반환"""
    global _cache_instance
    
    if _cache_instance is None:
        redis = await get_redis()
        _cache_instance = CacheService(redis)
    
    return _cache_instance
