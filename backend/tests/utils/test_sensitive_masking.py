"""Tests for sensitive data masking in logging."""

import pytest

from app.logging_config import (
    mask_email,
    mask_ip_address,
    mask_card_number,
    mask_token,
    mask_string_value,
    mask_dict_value,
    sensitive_data_filter,
    MASKED_FIELDS,
    PARTIAL_MASK_FIELDS,
)


class TestMaskEmail:
    """Tests for email masking."""

    def test_mask_standard_email(self):
        """Standard email should be masked."""
        assert mask_email("user@example.com") == "u***@example.com"

    def test_mask_long_local_part(self):
        """Long local part should show first char only."""
        assert mask_email("longusername@domain.org") == "l***@domain.org"

    def test_mask_single_char_local(self):
        """Single char local part should become asterisk."""
        assert mask_email("a@test.com") == "*@test.com"

    def test_mask_subdomain_email(self):
        """Email with subdomain should preserve domain."""
        assert mask_email("admin@mail.company.co.kr") == "a***@mail.company.co.kr"

    def test_invalid_email_unchanged(self):
        """Invalid email (no @) should be unchanged."""
        assert mask_email("notanemail") == "notanemail"


class TestMaskIPAddress:
    """Tests for IP address masking."""

    def test_mask_standard_ip(self):
        """Standard IP should mask last two octets."""
        assert mask_ip_address("192.168.1.100") == "192.168.xxx.xxx"

    def test_mask_localhost(self):
        """Localhost IP should be masked."""
        assert mask_ip_address("127.0.0.1") == "127.0.xxx.xxx"

    def test_mask_public_ip(self):
        """Public IP should be masked."""
        assert mask_ip_address("8.8.8.8") == "8.8.xxx.xxx"

    def test_invalid_ip_unchanged(self):
        """Invalid IP should be unchanged."""
        assert mask_ip_address("not.an.ip") == "not.an.ip"
        assert mask_ip_address("192.168.1") == "192.168.1"


class TestMaskCardNumber:
    """Tests for credit card number masking."""

    def test_mask_card_with_dashes(self):
        """Card with dashes should show last 4 digits."""
        assert mask_card_number("1234-5678-9012-3456") == "****-****-****-3456"

    def test_mask_card_with_spaces(self):
        """Card with spaces should show last 4 digits."""
        assert mask_card_number("1234 5678 9012 3456") == "****-****-****-3456"

    def test_mask_card_no_separator(self):
        """Card without separators should show last 4 digits."""
        assert mask_card_number("1234567890123456") == "****-****-****-3456"

    def test_mask_short_number(self):
        """Short number should return asterisks."""
        assert mask_card_number("123") == "****"


class TestMaskToken:
    """Tests for JWT/token masking."""

    def test_mask_jwt_token(self):
        """JWT token should be truncated and masked."""
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        result = mask_token(token)
        assert result.startswith("eyJhbGciOi")
        assert result.endswith("[MASKED]")
        assert "***" in result

    def test_mask_short_token(self):
        """Short token should be completely masked."""
        assert mask_token("abc123") == "[MASKED]"

    def test_mask_api_key(self):
        """API key should be masked."""
        result = mask_token("sk_live_abcdefghijklmnop")
        assert result.startswith("sk_live_ab")
        assert "[MASKED]" in result


class TestMaskStringValue:
    """Tests for string value masking with patterns."""

    def test_mask_email_in_string(self):
        """Email in string should be masked."""
        result = mask_string_value("User email is user@example.com")
        assert "u***@example.com" in result
        assert "user@example.com" not in result

    def test_mask_ip_in_string(self):
        """IP in string should be masked."""
        result = mask_string_value("Client IP: 192.168.1.100")
        assert "192.168.xxx.xxx" in result
        assert "192.168.1.100" not in result

    def test_mask_multiple_sensitive_data(self):
        """Multiple sensitive data should all be masked."""
        result = mask_string_value(
            "User admin@test.com from 10.0.0.1 logged in"
        )
        assert "a***@test.com" in result
        assert "10.0.xxx.xxx" in result

    def test_mask_password_field(self):
        """Password field in JSON-like string should be masked."""
        result = mask_string_value('{"password": "secret123"}')
        assert "[MASKED]" in result
        assert "secret123" not in result

    def test_mask_jwt_in_string(self):
        """JWT in string should be masked."""
        jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.rTCH8cLoGxAm_xw68z-zXVKi9ie6xJn9tnVWjd_9ftE"
        result = mask_string_value(f"Token: {jwt}")
        assert jwt not in result
        assert "[MASKED]" in result


class TestMaskDictValue:
    """Tests for dictionary value masking."""

    def test_mask_password_field(self):
        """Password field should be completely masked."""
        assert mask_dict_value("password", "secret123") == "[MASKED]"

    def test_mask_token_field(self):
        """Token field should be completely masked."""
        assert mask_dict_value("token", "abc123xyz") == "[MASKED]"

    def test_mask_email_field(self):
        """Email field should be partially masked."""
        assert mask_dict_value("email", "user@test.com") == "u***@test.com"

    def test_mask_ip_address_field(self):
        """IP address field should be partially masked."""
        assert mask_dict_value("ip_address", "192.168.1.1") == "192.168.xxx.xxx"

    def test_mask_user_agent_truncation(self):
        """Long user agent should be truncated."""
        long_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        result = mask_dict_value("user_agent", long_ua)
        assert len(result) <= 53  # 50 chars + "..."
        assert result.endswith("...")

    def test_regular_field_unchanged(self):
        """Regular field should be unchanged."""
        assert mask_dict_value("username", "john_doe") == "john_doe"

    def test_non_string_unchanged(self):
        """Non-string values should be unchanged."""
        assert mask_dict_value("count", 42) == 42
        assert mask_dict_value("active", True) is True


class TestSensitiveDataFilter:
    """Tests for the structlog processor."""

    def test_filter_masks_sensitive_fields(self):
        """Filter should mask sensitive fields in event dict."""
        event_dict = {
            "event": "user_login",
            "email": "admin@company.com",
            "password": "supersecret",
            "ip_address": "10.20.30.40",
        }
        
        result = sensitive_data_filter(None, "info", event_dict)
        
        assert result["email"] == "a***@company.com"
        assert result["password"] == "[MASKED]"
        assert result["ip_address"] == "10.20.xxx.xxx"
        assert result["event"] == "user_login"

    def test_filter_handles_nested_dict(self):
        """Filter should handle nested dictionaries."""
        event_dict = {
            "event": "auth",
            "user": {
                "email": "test@example.com",
                "token": "secret_token_123",
            }
        }
        
        result = sensitive_data_filter(None, "info", event_dict)
        
        assert result["user"]["email"] == "t***@example.com"
        assert result["user"]["token"] == "[MASKED]"

    def test_filter_handles_list(self):
        """Filter should handle lists."""
        event_dict = {
            "event": "batch",
            "emails": ["user1@test.com", "user2@test.com"],
        }
        
        result = sensitive_data_filter(None, "info", event_dict)
        
        # List items with email key should be masked
        assert "u***@test.com" in result["emails"][0]

    def test_filter_preserves_non_sensitive(self):
        """Filter should preserve non-sensitive data."""
        event_dict = {
            "event": "game_action",
            "table_id": "table-123",
            "action": "fold",
            "amount": 100,
        }
        
        result = sensitive_data_filter(None, "info", event_dict)
        
        assert result == event_dict


class TestMaskedFieldsConfig:
    """Tests for masked fields configuration."""

    def test_all_password_variants_masked(self):
        """All password-related fields should be in MASKED_FIELDS."""
        assert "password" in MASKED_FIELDS
        assert "password_hash" in MASKED_FIELDS

    def test_all_token_variants_masked(self):
        """All token-related fields should be in MASKED_FIELDS."""
        assert "token" in MASKED_FIELDS
        assert "refresh_token" in MASKED_FIELDS
        assert "access_token" in MASKED_FIELDS
        assert "auth_token" in MASKED_FIELDS

    def test_api_keys_masked(self):
        """API key fields should be in MASKED_FIELDS."""
        assert "api_key" in MASKED_FIELDS
        assert "apikey" in MASKED_FIELDS

    def test_2fa_fields_masked(self):
        """2FA-related fields should be in MASKED_FIELDS."""
        assert "totp_code" in MASKED_FIELDS
        assert "backup_code" in MASKED_FIELDS
        assert "secret_encrypted" in MASKED_FIELDS


class TestPartialMaskFieldsConfig:
    """Tests for partial mask fields configuration."""

    def test_email_in_partial_mask(self):
        """Email should be in PARTIAL_MASK_FIELDS."""
        assert "email" in PARTIAL_MASK_FIELDS

    def test_ip_variants_in_partial_mask(self):
        """IP address variants should be in PARTIAL_MASK_FIELDS."""
        assert "ip_address" in PARTIAL_MASK_FIELDS
        assert "ip" in PARTIAL_MASK_FIELDS
        assert "client_ip" in PARTIAL_MASK_FIELDS

    def test_user_agent_in_partial_mask(self):
        """User agent should be in PARTIAL_MASK_FIELDS."""
        assert "user_agent" in PARTIAL_MASK_FIELDS
