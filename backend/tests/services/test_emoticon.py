"""이모티콘 서비스 테스트."""

import pytest

from app.services.emoticon import (
    DEFAULT_EMOTICONS,
    EMOTICON_MAP,
    Emoticon,
    EmoticonCategory,
    EmoticonService,
)


class TestEmoticonService:
    """이모티콘 서비스 테스트."""

    def test_get_all_emoticons(self):
        """모든 이모티콘 목록 조회."""
        emoticons = EmoticonService.get_all_emoticons()
        assert len(emoticons) > 0
        assert all("id" in e for e in emoticons)
        assert all("name" in e for e in emoticons)
        assert all("emoji" in e for e in emoticons)

    def test_get_all_emoticons_by_category(self):
        """카테고리별 이모티콘 조회."""
        basic = EmoticonService.get_all_emoticons(category=EmoticonCategory.BASIC)
        poker = EmoticonService.get_all_emoticons(category=EmoticonCategory.POKER)
        
        assert len(basic) > 0
        assert len(poker) > 0
        assert all(e["category"] == "basic" for e in basic)
        assert all(e["category"] == "poker" for e in poker)

    def test_get_emoticon_by_id_valid(self):
        """유효한 ID로 이모티콘 조회."""
        emoticon = EmoticonService.get_emoticon_by_id("thumbs_up")
        assert emoticon is not None
        assert emoticon.id == "thumbs_up"
        assert emoticon.name == "좋아요"
        assert emoticon.emoji == "👍"

    def test_get_emoticon_by_id_invalid(self):
        """유효하지 않은 ID로 조회."""
        emoticon = EmoticonService.get_emoticon_by_id("invalid_id")
        assert emoticon is None

    def test_is_valid_emoticon_id_valid(self):
        """유효한 이모티콘 ID 확인."""
        assert EmoticonService.is_valid_emoticon_id("thumbs_up") is True
        assert EmoticonService.is_valid_emoticon_id("clap") is True
        assert EmoticonService.is_valid_emoticon_id("good_game") is True

    def test_is_valid_emoticon_id_invalid(self):
        """유효하지 않은 이모티콘 ID 확인."""
        assert EmoticonService.is_valid_emoticon_id("invalid") is False
        assert EmoticonService.is_valid_emoticon_id("") is False
        assert EmoticonService.is_valid_emoticon_id("123") is False

    def test_get_emoticons_by_category(self):
        """카테고리별 이모티콘 조회 메서드."""
        emotion = EmoticonService.get_emoticons_by_category(EmoticonCategory.EMOTION)
        assert len(emotion) > 0
        assert all(e["category"] == "emotion" for e in emotion)

    def test_get_available_categories(self):
        """사용 가능한 카테고리 목록."""
        categories = EmoticonService.get_available_categories()
        assert len(categories) == len(EmoticonCategory)
        
        category_ids = [c["id"] for c in categories]
        assert "basic" in category_ids
        assert "poker" in category_ids
        assert "emotion" in category_ids


class TestEmoticonModel:
    """Emoticon 모델 테스트."""

    def test_default_emoticons_count(self):
        """기본 이모티콘 수."""
        assert len(DEFAULT_EMOTICONS) >= 20

    def test_emoticon_map_consistency(self):
        """이모티콘 맵 일관성."""
        assert len(EMOTICON_MAP) == len(DEFAULT_EMOTICONS)
        for emoticon in DEFAULT_EMOTICONS:
            assert emoticon.id in EMOTICON_MAP
            assert EMOTICON_MAP[emoticon.id] == emoticon

    def test_emoticon_immutability(self):
        """이모티콘 불변성 (frozen dataclass)."""
        emoticon = DEFAULT_EMOTICONS[0]
        with pytest.raises(Exception):  # FrozenInstanceError
            emoticon.name = "변경된 이름"  # type: ignore

    def test_emoticon_category_enum(self):
        """이모티콘 카테고리 열거형."""
        assert EmoticonCategory.BASIC.value == "basic"
        assert EmoticonCategory.POKER.value == "poker"
        assert EmoticonCategory.EMOTION.value == "emotion"
        assert EmoticonCategory.CELEBRATION.value == "celebration"
        assert EmoticonCategory.TAUNT.value == "taunt"

    def test_all_emoticons_have_required_fields(self):
        """모든 이모티콘 필수 필드 존재."""
        for emoticon in DEFAULT_EMOTICONS:
            assert emoticon.id is not None
            assert emoticon.name is not None
            assert emoticon.emoji is not None
            assert emoticon.category is not None
            assert isinstance(emoticon.is_premium, bool)

    def test_emoticon_ids_unique(self):
        """이모티콘 ID 고유성."""
        ids = [e.id for e in DEFAULT_EMOTICONS]
        assert len(ids) == len(set(ids))

    def test_emoticons_have_emojis(self):
        """모든 이모티콘이 이모지 포함."""
        for emoticon in DEFAULT_EMOTICONS:
            assert emoticon.emoji is not None
            assert len(emoticon.emoji) > 0


class TestEmoticonCategories:
    """카테고리별 이모티콘 테스트."""

    def test_basic_category_exists(self):
        """기본 카테고리 이모티콘 존재."""
        basic = [e for e in DEFAULT_EMOTICONS if e.category == EmoticonCategory.BASIC]
        assert len(basic) >= 4

    def test_poker_category_exists(self):
        """포커 카테고리 이모티콘 존재."""
        poker = [e for e in DEFAULT_EMOTICONS if e.category == EmoticonCategory.POKER]
        assert len(poker) >= 4

    def test_emotion_category_exists(self):
        """감정 카테고리 이모티콘 존재."""
        emotion = [e for e in DEFAULT_EMOTICONS if e.category == EmoticonCategory.EMOTION]
        assert len(emotion) >= 5

    def test_celebration_category_exists(self):
        """축하 카테고리 이모티콘 존재."""
        celebration = [e for e in DEFAULT_EMOTICONS if e.category == EmoticonCategory.CELEBRATION]
        assert len(celebration) >= 3

    def test_taunt_category_exists(self):
        """도발 카테고리 이모티콘 존재."""
        taunt = [e for e in DEFAULT_EMOTICONS if e.category == EmoticonCategory.TAUNT]
        assert len(taunt) >= 2
