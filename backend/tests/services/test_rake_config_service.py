"""Tests for RakeConfigService.

Phase P1-1: 관리자 레이크 설정 UI
"""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from app.models.rake import RakeConfig
from app.services.rake import RakeConfigService, RakeConfigData


class TestRakeConfigService:
    """Tests for RakeConfigService CRUD operations."""

    @pytest.fixture
    def mock_session(self):
        """Create mock async session."""
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.delete = AsyncMock()
        return session

    @pytest.fixture
    def service(self, mock_session):
        """Create RakeConfigService with mock session."""
        return RakeConfigService(mock_session)

    @pytest.fixture
    def sample_config(self):
        """Create sample RakeConfig model."""
        config = MagicMock(spec=RakeConfig)
        config.id = "test-config-id"
        config.small_blind = 500
        config.big_blind = 1000
        config.percentage = Decimal("0.05")
        config.cap_bb = 3
        config.is_active = True
        return config

    # =========================================================================
    # List Tests
    # =========================================================================

    async def test_list_configs_empty(self, service, mock_session):
        """빈 목록 반환 테스트."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        configs = await service.list_configs()

        assert configs == []
        mock_session.execute.assert_called_once()

    async def test_list_configs_with_items(self, service, mock_session, sample_config):
        """설정 목록 반환 테스트."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_config]
        mock_session.execute = AsyncMock(return_value=mock_result)

        configs = await service.list_configs()

        assert len(configs) == 1
        assert configs[0].small_blind == 500

    # =========================================================================
    # Get Tests
    # =========================================================================

    async def test_get_config_found(self, service, mock_session, sample_config):
        """설정 조회 성공 테스트."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_config
        mock_session.execute = AsyncMock(return_value=mock_result)

        config = await service.get_config("test-config-id")

        assert config is not None
        assert config.id == "test-config-id"

    async def test_get_config_not_found(self, service, mock_session):
        """설정 조회 실패 테스트."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        config = await service.get_config("nonexistent-id")

        assert config is None

    async def test_get_config_by_blind_level(self, service, mock_session, sample_config):
        """블라인드 레벨로 설정 조회 테스트."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_config
        mock_session.execute = AsyncMock(return_value=mock_result)

        config = await service.get_config_by_blind_level(500, 1000)

        assert config is not None
        assert config.small_blind == 500
        assert config.big_blind == 1000

    # =========================================================================
    # Create Tests
    # =========================================================================

    async def test_create_config(self, service, mock_session):
        """설정 생성 테스트."""
        config = await service.create_config(
            small_blind=2500,
            big_blind=5000,
            percentage=0.045,
            cap_bb=4,
            is_active=True,
        )

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

        # 생성된 config 객체 확인
        added_config = mock_session.add.call_args[0][0]
        assert added_config.small_blind == 2500
        assert added_config.big_blind == 5000
        assert added_config.percentage == Decimal("0.045")
        assert added_config.cap_bb == 4
        assert added_config.is_active is True

    # =========================================================================
    # Update Tests
    # =========================================================================

    async def test_update_config_percentage(self, service, mock_session, sample_config):
        """퍼센트 수정 테스트."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_config
        mock_session.execute = AsyncMock(return_value=mock_result)

        updated = await service.update_config(
            config_id="test-config-id",
            percentage=0.06,
        )

        assert updated is not None
        assert sample_config.percentage == Decimal("0.06")
        mock_session.flush.assert_called_once()

    async def test_update_config_cap_bb(self, service, mock_session, sample_config):
        """cap_bb 수정 테스트."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_config
        mock_session.execute = AsyncMock(return_value=mock_result)

        updated = await service.update_config(
            config_id="test-config-id",
            cap_bb=5,
        )

        assert updated is not None
        assert sample_config.cap_bb == 5

    async def test_update_config_is_active(self, service, mock_session, sample_config):
        """is_active 수정 테스트."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_config
        mock_session.execute = AsyncMock(return_value=mock_result)

        updated = await service.update_config(
            config_id="test-config-id",
            is_active=False,
        )

        assert updated is not None
        assert sample_config.is_active is False

    async def test_update_config_not_found(self, service, mock_session):
        """존재하지 않는 설정 수정 테스트."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        updated = await service.update_config(
            config_id="nonexistent-id",
            percentage=0.06,
        )

        assert updated is None

    # =========================================================================
    # Delete Tests
    # =========================================================================

    async def test_delete_config_success(self, service, mock_session, sample_config):
        """설정 삭제 성공 테스트."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_config
        mock_session.execute = AsyncMock(return_value=mock_result)

        deleted = await service.delete_config("test-config-id")

        assert deleted is True
        mock_session.delete.assert_called_once_with(sample_config)
        mock_session.flush.assert_called_once()

    async def test_delete_config_not_found(self, service, mock_session):
        """존재하지 않는 설정 삭제 테스트."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        deleted = await service.delete_config("nonexistent-id")

        assert deleted is False
        mock_session.delete.assert_not_called()


class TestRakeServiceDBIntegration:
    """Tests for RakeService DB config integration."""

    @pytest.fixture
    def mock_session(self):
        """Create mock async session."""
        return AsyncMock()

    async def test_get_rake_config_from_db_found(self, mock_session):
        """DB에 설정이 있으면 DB 설정 사용."""
        from app.services.rake import RakeService

        # DB에서 설정 반환하도록 mock
        db_config = MagicMock()
        db_config.percentage = Decimal("0.06")
        db_config.cap_bb = 5

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = db_config
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = RakeService(mock_session)
        config = await service.get_rake_config_from_db(500, 1000)

        assert config.percentage == Decimal("0.06")
        assert config.cap_bb == 5

    async def test_get_rake_config_from_db_not_found(self, mock_session):
        """DB에 설정이 없으면 하드코딩 기본값 사용."""
        from app.services.rake import RakeService, RAKE_CONFIGS

        # DB에서 None 반환
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = RakeService(mock_session)
        config = await service.get_rake_config_from_db(1000, 2000)

        # 하드코딩된 기본값과 동일
        expected = RAKE_CONFIGS.get((1000, 2000))
        assert config.percentage == expected.percentage
        assert config.cap_bb == expected.cap_bb

    async def test_calculate_rake_with_custom_config(self, mock_session):
        """커스텀 설정으로 레이크 계산."""
        from app.engine.state import GamePhase
        from app.services.rake import RakeService, RakeConfigData

        service = RakeService(mock_session)

        # 커스텀 설정: 3% 레이크, 2BB 캡
        custom_config = RakeConfigData(
            percentage=Decimal("0.03"),
            cap_bb=2,
        )

        result = service.calculate_rake(
            pot_total=100000,  # 10만원 팟
            small_blind=500,
            big_blind=1000,
            phase=GamePhase.RIVER,
            winners=[{"position": 0, "amount": 100000}],
            config=custom_config,
        )

        # 3% = 3000원, 캡 2BB = 2000원 → 캡 적용
        assert result.total_rake == 2000
        assert result.applied_nfnd is False
