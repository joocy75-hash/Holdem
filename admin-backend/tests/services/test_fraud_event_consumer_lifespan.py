"""Tests for FraudEventConsumer lifespan integration.

**Validates: Requirements 4.1**
"""

import pytest
from unittest.mock import MagicMock, AsyncMock


class TestLifespanConfig:
    """서버 설정 테스트."""

    def test_fraud_consumer_enabled_default(self):
        """fraud_consumer_enabled 기본값 확인."""
        from app.config import Settings
        
        # 필수 필드 제공
        settings = Settings(
            jwt_secret_key="test-secret-key-at-least-32-characters-long",
            main_api_key="test-api-key-at-least-16-chars",
        )
        
        assert settings.fraud_consumer_enabled is True

    def test_fraud_consumer_can_be_disabled(self):
        """fraud_consumer_enabled=False 설정 가능."""
        from app.config import Settings
        
        settings = Settings(
            jwt_secret_key="test-secret-key-at-least-32-characters-long",
            main_api_key="test-api-key-at-least-16-chars",
            fraud_consumer_enabled=False,
        )
        
        assert settings.fraud_consumer_enabled is False


class TestDatabaseSessionFactories:
    """데이터베이스 세션 팩토리 테스트."""

    def test_get_admin_db_session_returns_session(self):
        """get_admin_db_session이 세션을 반환."""
        from app.database import get_admin_db_session
        
        session = get_admin_db_session()
        assert session is not None

    def test_get_main_db_session_returns_session(self):
        """get_main_db_session이 세션을 반환."""
        from app.database import get_main_db_session
        
        session = get_main_db_session()
        assert session is not None


class TestMainAppHasLifespan:
    """main.py에 lifespan이 설정되어 있는지 확인."""

    def test_app_has_lifespan(self):
        """FastAPI app에 lifespan이 설정됨."""
        from app.main import app
        
        # FastAPI 앱이 lifespan을 가지고 있는지 확인
        assert app.router.lifespan_context is not None
