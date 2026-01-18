"""채팅 핸들러 테스트."""

import pytest

from app.ws.handlers.chat import ChatType


class TestChatType:
    """채팅 타입 테스트."""

    def test_chat_type_values(self):
        """채팅 타입 값 확인."""
        assert ChatType.PUBLIC.value == "public"
        assert ChatType.PLAYERS_ONLY.value == "players_only"

    def test_chat_type_from_string(self):
        """문자열에서 채팅 타입 변환."""
        assert ChatType("public") == ChatType.PUBLIC
        assert ChatType("players_only") == ChatType.PLAYERS_ONLY

    def test_invalid_chat_type_raises(self):
        """잘못된 채팅 타입 예외."""
        with pytest.raises(ValueError):
            ChatType("invalid")

    def test_chat_type_is_string_enum(self):
        """ChatType이 str Enum인지 확인."""
        assert isinstance(ChatType.PUBLIC.value, str)
        assert isinstance(ChatType.PLAYERS_ONLY.value, str)


class TestChatTypeUsage:
    """채팅 타입 사용 시나리오 테스트."""

    def test_default_is_public(self):
        """기본값은 public."""
        default_type = "public"
        try:
            chat_type = ChatType(default_type)
        except ValueError:
            chat_type = ChatType.PUBLIC
        
        assert chat_type == ChatType.PUBLIC

    def test_fallback_to_public_on_invalid(self):
        """잘못된 값은 public으로 폴백."""
        invalid_type = "invalid_type"
        try:
            chat_type = ChatType(invalid_type)
        except ValueError:
            chat_type = ChatType.PUBLIC
        
        assert chat_type == ChatType.PUBLIC

    def test_players_only_type(self):
        """플레이어 전용 타입."""
        chat_type = ChatType("players_only")
        assert chat_type == ChatType.PLAYERS_ONLY

    def test_chat_message_structure(self):
        """채팅 메시지 구조 테스트."""
        from uuid import uuid4
        from datetime import datetime

        chat_message = {
            "messageId": str(uuid4()),
            "tableId": "table-123",
            "userId": "user-456",
            "nickname": "TestPlayer",
            "message": "Hello!",
            "chatType": ChatType.PUBLIC.value,
            "isPlayer": True,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # 필수 필드 확인
        assert "messageId" in chat_message
        assert "tableId" in chat_message
        assert "userId" in chat_message
        assert "nickname" in chat_message
        assert "message" in chat_message
        assert "chatType" in chat_message
        assert "timestamp" in chat_message

        # chatType 값 확인
        assert chat_message["chatType"] in ["public", "players_only"]

    def test_masked_message_for_spectators(self):
        """관전자용 마스킹된 메시지."""
        original_message = {
            "messageId": "msg-123",
            "message": "Secret strategy!",
            "chatType": ChatType.PLAYERS_ONLY.value,
        }

        # 마스킹 처리
        masked_message = original_message.copy()
        masked_message["message"] = "[플레이어 전용 채팅]"
        masked_message["masked"] = True

        assert masked_message["masked"] is True
        assert masked_message["message"] == "[플레이어 전용 채팅]"
        assert original_message["message"] == "Secret strategy!"


class TestChatChannels:
    """채팅 채널 테스트."""

    def test_table_channel_format(self):
        """테이블 채널 형식."""
        table_id = "table-abc123"
        channel = f"table:{table_id}"
        assert channel == "table:table-abc123"

    def test_players_channel_format(self):
        """플레이어 채널 형식."""
        table_id = "table-abc123"
        channel = f"table:{table_id}:players"
        assert channel == "table:table-abc123:players"

    def test_spectators_channel_format(self):
        """관전자 채널 형식."""
        table_id = "table-abc123"
        channel = f"table:{table_id}:spectators"
        assert channel == "table:table-abc123:spectators"
