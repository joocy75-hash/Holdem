"""아바타 서비스 테스트."""

import pytest

from app.services.avatar import (
    Avatar,
    AvatarCategory,
    AvatarService,
    DEFAULT_AVATARS,
    AVATAR_MAP,
)


class TestAvatarService:
    """아바타 서비스 테스트."""

    def test_get_all_avatars(self):
        """모든 아바타 목록 조회."""
        avatars = AvatarService.get_all_avatars()
        assert len(avatars) == 10
        assert all("id" in a for a in avatars)
        assert all("name" in a for a in avatars)
        assert all("imageUrl" in a for a in avatars)

    def test_get_avatar_by_id_valid(self):
        """유효한 ID로 아바타 조회."""
        avatar = AvatarService.get_avatar_by_id("1")
        assert avatar is not None
        assert avatar.id == "1"
        assert avatar.name == "에이스"

    def test_get_avatar_by_id_invalid(self):
        """유효하지 않은 ID로 조회."""
        avatar = AvatarService.get_avatar_by_id("999")
        assert avatar is None

    def test_is_valid_avatar_id_valid(self):
        """유효한 아바타 ID 확인."""
        assert AvatarService.is_valid_avatar_id("1") is True
        assert AvatarService.is_valid_avatar_id("5") is True
        assert AvatarService.is_valid_avatar_id("10") is True

    def test_is_valid_avatar_id_invalid(self):
        """유효하지 않은 아바타 ID 확인."""
        assert AvatarService.is_valid_avatar_id("0") is False
        assert AvatarService.is_valid_avatar_id("11") is False
        assert AvatarService.is_valid_avatar_id("abc") is False

    def test_get_avatar_url_valid(self):
        """유효한 ID로 URL 조회."""
        url = AvatarService.get_avatar_url("3")
        assert url == "/assets/avatars/avatar_03.png"

    def test_get_avatar_url_none(self):
        """None인 경우 기본 URL."""
        url = AvatarService.get_avatar_url(None)
        assert url == "/assets/avatars/avatar_01.png"

    def test_get_avatar_url_invalid(self):
        """유효하지 않은 ID면 기본 URL."""
        url = AvatarService.get_avatar_url("999")
        assert url == "/assets/avatars/avatar_01.png"

    def test_get_default_avatar_id(self):
        """기본 아바타 ID."""
        assert AvatarService.get_default_avatar_id() == "1"

    def test_get_available_avatars_for_user(self):
        """사용자용 아바타 목록."""
        avatars = AvatarService.get_available_avatars_for_user(user_level=0)
        assert len(avatars) > 0
        assert all("id" in a for a in avatars)


class TestAvatarModel:
    """아바타 모델 테스트."""

    def test_default_avatars_count(self):
        """기본 아바타 10개."""
        assert len(DEFAULT_AVATARS) == 10

    def test_avatar_map_consistency(self):
        """아바타 맵 일관성."""
        assert len(AVATAR_MAP) == len(DEFAULT_AVATARS)
        for avatar in DEFAULT_AVATARS:
            assert avatar.id in AVATAR_MAP
            assert AVATAR_MAP[avatar.id] == avatar

    def test_avatar_immutability(self):
        """아바타 불변성 (frozen dataclass)."""
        avatar = DEFAULT_AVATARS[0]
        with pytest.raises(Exception):  # FrozenInstanceError
            avatar.name = "변경된 이름"  # type: ignore

    def test_avatar_category_enum(self):
        """아바타 카테고리 열거형."""
        assert AvatarCategory.DEFAULT.value == "default"
        assert AvatarCategory.PREMIUM.value == "premium"
        assert AvatarCategory.EVENT.value == "event"

    def test_all_avatars_have_required_fields(self):
        """모든 아바타 필수 필드 존재."""
        for avatar in DEFAULT_AVATARS:
            assert avatar.id is not None
            assert avatar.name is not None
            assert avatar.image_url is not None
            assert avatar.category is not None
            assert isinstance(avatar.is_available, bool)

    def test_avatar_ids_unique(self):
        """아바타 ID 고유성."""
        ids = [a.id for a in DEFAULT_AVATARS]
        assert len(ids) == len(set(ids))

    def test_avatar_ids_are_sequential(self):
        """아바타 ID가 1-10 순차적."""
        expected_ids = [str(i) for i in range(1, 11)]
        actual_ids = [a.id for a in DEFAULT_AVATARS]
        assert actual_ids == expected_ids
