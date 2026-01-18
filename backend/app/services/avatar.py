"""아바타 서비스.

사용자 아바타 관리 및 제공.
"""

import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AvatarCategory(str, Enum):
    """아바타 카테고리."""
    
    DEFAULT = "default"     # 기본 제공 아바타
    PREMIUM = "premium"     # 프리미엄 아바타 (유료)
    EVENT = "event"         # 이벤트 아바타


@dataclass(frozen=True)
class Avatar:
    """아바타 정보."""
    
    id: str
    name: str
    image_url: str
    category: AvatarCategory
    is_available: bool = True
    required_level: int = 0
    description: str | None = None


# =============================================================================
# 기본 아바타 정의
# =============================================================================

DEFAULT_AVATARS: list[Avatar] = [
    Avatar(
        id="1",
        name="에이스",
        image_url="/assets/avatars/avatar_01.png",
        category=AvatarCategory.DEFAULT,
        description="기본 아바타",
    ),
    Avatar(
        id="2",
        name="킹",
        image_url="/assets/avatars/avatar_02.png",
        category=AvatarCategory.DEFAULT,
        description="기본 아바타",
    ),
    Avatar(
        id="3",
        name="퀸",
        image_url="/assets/avatars/avatar_03.png",
        category=AvatarCategory.DEFAULT,
        description="기본 아바타",
    ),
    Avatar(
        id="4",
        name="잭",
        image_url="/assets/avatars/avatar_04.png",
        category=AvatarCategory.DEFAULT,
        description="기본 아바타",
    ),
    Avatar(
        id="5",
        name="조커",
        image_url="/assets/avatars/avatar_05.png",
        category=AvatarCategory.DEFAULT,
        description="기본 아바타",
    ),
    Avatar(
        id="6",
        name="스페이드",
        image_url="/assets/avatars/avatar_06.png",
        category=AvatarCategory.DEFAULT,
        description="기본 아바타",
    ),
    Avatar(
        id="7",
        name="하트",
        image_url="/assets/avatars/avatar_07.png",
        category=AvatarCategory.DEFAULT,
        description="기본 아바타",
    ),
    Avatar(
        id="8",
        name="다이아",
        image_url="/assets/avatars/avatar_08.png",
        category=AvatarCategory.DEFAULT,
        description="기본 아바타",
    ),
    Avatar(
        id="9",
        name="클로버",
        image_url="/assets/avatars/avatar_09.png",
        category=AvatarCategory.DEFAULT,
        description="기본 아바타",
    ),
    Avatar(
        id="10",
        name="칩스",
        image_url="/assets/avatars/avatar_10.png",
        category=AvatarCategory.DEFAULT,
        description="기본 아바타",
    ),
]

# 아바타 ID로 빠른 조회를 위한 딕셔너리
AVATAR_MAP: dict[str, Avatar] = {avatar.id: avatar for avatar in DEFAULT_AVATARS}


class AvatarService:
    """아바타 서비스."""

    @staticmethod
    def get_all_avatars(include_unavailable: bool = False) -> list[dict]:
        """모든 아바타 목록 조회.

        Args:
            include_unavailable: 이용 불가 아바타 포함 여부

        Returns:
            아바타 목록
        """
        avatars = DEFAULT_AVATARS
        
        if not include_unavailable:
            avatars = [a for a in avatars if a.is_available]

        return [
            {
                "id": a.id,
                "name": a.name,
                "imageUrl": a.image_url,
                "category": a.category.value,
                "isAvailable": a.is_available,
                "requiredLevel": a.required_level,
                "description": a.description,
            }
            for a in avatars
        ]

    @staticmethod
    def get_avatar_by_id(avatar_id: str) -> Avatar | None:
        """아바타 ID로 조회.

        Args:
            avatar_id: 아바타 ID

        Returns:
            아바타 정보 또는 None
        """
        return AVATAR_MAP.get(avatar_id)

    @staticmethod
    def is_valid_avatar_id(avatar_id: str) -> bool:
        """유효한 아바타 ID 여부.

        Args:
            avatar_id: 아바타 ID

        Returns:
            유효 여부
        """
        return avatar_id in AVATAR_MAP

    @staticmethod
    def get_avatar_url(avatar_id: str | None) -> str:
        """아바타 ID로 이미지 URL 반환.

        Args:
            avatar_id: 아바타 ID (None이면 기본 아바타)

        Returns:
            아바타 이미지 URL
        """
        if avatar_id is None:
            avatar_id = "1"  # 기본 아바타
        
        avatar = AVATAR_MAP.get(avatar_id)
        if avatar:
            return avatar.image_url
        
        # 유효하지 않은 ID면 기본 아바타 반환
        return DEFAULT_AVATARS[0].image_url

    @staticmethod
    def get_available_avatars_for_user(user_level: int = 0) -> list[dict]:
        """사용자가 이용 가능한 아바타 목록.

        Args:
            user_level: 사용자 레벨

        Returns:
            이용 가능한 아바타 목록
        """
        available = [
            a for a in DEFAULT_AVATARS 
            if a.is_available and a.required_level <= user_level
        ]

        return [
            {
                "id": a.id,
                "name": a.name,
                "imageUrl": a.image_url,
                "category": a.category.value,
            }
            for a in available
        ]

    @staticmethod
    def get_default_avatar_id() -> str:
        """기본 아바타 ID 반환."""
        return "1"
