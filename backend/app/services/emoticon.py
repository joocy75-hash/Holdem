"""이모티콘 서비스.

게임 내 이모티콘 시스템 관리.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class EmoticonCategory(str, Enum):
    """이모티콘 카테고리."""
    
    BASIC = "basic"         # 기본 이모티콘
    POKER = "poker"         # 포커 관련
    EMOTION = "emotion"     # 감정 표현
    CELEBRATION = "celebration"  # 축하/승리
    TAUNT = "taunt"         # 도발


@dataclass(frozen=True)
class Emoticon:
    """이모티콘 정보."""
    
    id: str
    name: str
    emoji: str  # 유니코드 이모지
    image_url: str | None  # 커스텀 이미지 (선택적)
    category: EmoticonCategory
    sound_url: str | None = None  # 사운드 효과 (선택적)
    is_premium: bool = False  # 프리미엄 전용


# =============================================================================
# 기본 이모티콘 정의
# =============================================================================

DEFAULT_EMOTICONS: list[Emoticon] = [
    # 기본 감정
    Emoticon(
        id="thumbs_up",
        name="좋아요",
        emoji="👍",
        image_url="/assets/emoticons/thumbs_up.png",
        category=EmoticonCategory.BASIC,
    ),
    Emoticon(
        id="thumbs_down",
        name="별로",
        emoji="👎",
        image_url="/assets/emoticons/thumbs_down.png",
        category=EmoticonCategory.BASIC,
    ),
    Emoticon(
        id="clap",
        name="박수",
        emoji="👏",
        image_url="/assets/emoticons/clap.png",
        category=EmoticonCategory.BASIC,
        sound_url="/sounds/clap.webm",
    ),
    Emoticon(
        id="wave",
        name="인사",
        emoji="👋",
        image_url="/assets/emoticons/wave.png",
        category=EmoticonCategory.BASIC,
    ),
    
    # 포커 관련
    Emoticon(
        id="good_game",
        name="GG",
        emoji="🎰",
        image_url="/assets/emoticons/good_game.png",
        category=EmoticonCategory.POKER,
    ),
    Emoticon(
        id="nice_hand",
        name="나이스 핸드",
        emoji="🃏",
        image_url="/assets/emoticons/nice_hand.png",
        category=EmoticonCategory.POKER,
    ),
    Emoticon(
        id="all_in",
        name="올인!",
        emoji="💰",
        image_url="/assets/emoticons/all_in.png",
        category=EmoticonCategory.POKER,
        sound_url="/sounds/all_in.webm",
    ),
    Emoticon(
        id="bluff",
        name="블러프",
        emoji="🎭",
        image_url="/assets/emoticons/bluff.png",
        category=EmoticonCategory.POKER,
    ),
    
    # 감정 표현
    Emoticon(
        id="smile",
        name="웃음",
        emoji="😊",
        image_url="/assets/emoticons/smile.png",
        category=EmoticonCategory.EMOTION,
    ),
    Emoticon(
        id="cry",
        name="울음",
        emoji="😢",
        image_url="/assets/emoticons/cry.png",
        category=EmoticonCategory.EMOTION,
    ),
    Emoticon(
        id="angry",
        name="화남",
        emoji="😠",
        image_url="/assets/emoticons/angry.png",
        category=EmoticonCategory.EMOTION,
    ),
    Emoticon(
        id="shocked",
        name="놀람",
        emoji="😱",
        image_url="/assets/emoticons/shocked.png",
        category=EmoticonCategory.EMOTION,
    ),
    Emoticon(
        id="thinking",
        name="생각중",
        emoji="🤔",
        image_url="/assets/emoticons/thinking.png",
        category=EmoticonCategory.EMOTION,
    ),
    Emoticon(
        id="cool",
        name="쿨",
        emoji="😎",
        image_url="/assets/emoticons/cool.png",
        category=EmoticonCategory.EMOTION,
    ),
    
    # 축하/승리
    Emoticon(
        id="trophy",
        name="트로피",
        emoji="🏆",
        image_url="/assets/emoticons/trophy.png",
        category=EmoticonCategory.CELEBRATION,
        sound_url="/sounds/winner.webm",
    ),
    Emoticon(
        id="party",
        name="파티",
        emoji="🎉",
        image_url="/assets/emoticons/party.png",
        category=EmoticonCategory.CELEBRATION,
    ),
    Emoticon(
        id="fire",
        name="불꽃",
        emoji="🔥",
        image_url="/assets/emoticons/fire.png",
        category=EmoticonCategory.CELEBRATION,
    ),
    Emoticon(
        id="money_bag",
        name="돈주머니",
        emoji="💵",
        image_url="/assets/emoticons/money_bag.png",
        category=EmoticonCategory.CELEBRATION,
    ),
    
    # 도발 (쿨다운 적용 권장)
    Emoticon(
        id="laugh",
        name="웃김",
        emoji="🤣",
        image_url="/assets/emoticons/laugh.png",
        category=EmoticonCategory.TAUNT,
    ),
    Emoticon(
        id="slow",
        name="빨리빨리",
        emoji="🐢",
        image_url="/assets/emoticons/slow.png",
        category=EmoticonCategory.TAUNT,
    ),
]

# 이모티콘 ID로 빠른 조회
EMOTICON_MAP: dict[str, Emoticon] = {e.id: e for e in DEFAULT_EMOTICONS}


class EmoticonService:
    """이모티콘 서비스."""

    @staticmethod
    def get_all_emoticons(
        category: EmoticonCategory | None = None,
        include_premium: bool = True,
    ) -> list[dict[str, Any]]:
        """모든 이모티콘 목록 조회.

        Args:
            category: 필터링할 카테고리
            include_premium: 프리미엄 포함 여부

        Returns:
            이모티콘 목록
        """
        emoticons = DEFAULT_EMOTICONS
        
        if category:
            emoticons = [e for e in emoticons if e.category == category]
        
        if not include_premium:
            emoticons = [e for e in emoticons if not e.is_premium]

        return [
            {
                "id": e.id,
                "name": e.name,
                "emoji": e.emoji,
                "imageUrl": e.image_url,
                "category": e.category.value,
                "soundUrl": e.sound_url,
                "isPremium": e.is_premium,
            }
            for e in emoticons
        ]

    @staticmethod
    def get_emoticon_by_id(emoticon_id: str) -> Emoticon | None:
        """이모티콘 ID로 조회.

        Args:
            emoticon_id: 이모티콘 ID

        Returns:
            이모티콘 정보 또는 None
        """
        return EMOTICON_MAP.get(emoticon_id)

    @staticmethod
    def is_valid_emoticon_id(emoticon_id: str) -> bool:
        """유효한 이모티콘 ID 여부.

        Args:
            emoticon_id: 이모티콘 ID

        Returns:
            유효 여부
        """
        return emoticon_id in EMOTICON_MAP

    @staticmethod
    def get_emoticons_by_category(category: EmoticonCategory) -> list[dict[str, Any]]:
        """카테고리별 이모티콘 목록.

        Args:
            category: 카테고리

        Returns:
            해당 카테고리 이모티콘 목록
        """
        return EmoticonService.get_all_emoticons(category=category)

    @staticmethod
    def get_available_categories() -> list[dict[str, str]]:
        """사용 가능한 카테고리 목록."""
        return [
            {"id": c.value, "name": c.name}
            for c in EmoticonCategory
        ]
