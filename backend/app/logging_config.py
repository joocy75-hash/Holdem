"""Structured logging configuration using structlog.

Phase 11: structlog integration for better debugging and monitoring.

Features:
- JSON-formatted logs for production
- Console-formatted logs for development
- Request context (trace_id, user_id, table_id)
- Performance timing
- Sensitive data masking (email, IP, card numbers, tokens)
"""

import logging
import re
import sys
from typing import Any

import structlog
from structlog.types import Processor


# =============================================================================
# Sensitive Data Masking
# =============================================================================

# Patterns for sensitive data detection
SENSITIVE_PATTERNS = {
    # Email: user@domain.com -> u***@domain.com
    "email": re.compile(
        r'\b([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'
    ),
    # IP Address: 192.168.1.100 -> 192.168.xxx.xxx
    "ip_address": re.compile(
        r'\b(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\b'
    ),
    # Credit Card: 1234-5678-9012-3456 -> ****-****-****-3456
    "card_number": re.compile(
        r'\b(\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?)(\d{4})\b'
    ),
    # JWT Token: eyJ... -> eyJ***[MASKED]
    "jwt_token": re.compile(
        r'\b(eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*)\b'
    ),
    # Password field in JSON/dict: "password": "secret" -> "password": "[MASKED]"
    "password_field": re.compile(
        r'(["\']?password["\']?\s*[:=]\s*)["\']?[^"\'}\s,]+["\']?',
        re.IGNORECASE
    ),
    # Secret/Token field: "secret": "value" -> "secret": "[MASKED]"
    "secret_field": re.compile(
        r'(["\']?(?:secret|token|api_key|apikey|auth)["\']?\s*[:=]\s*)["\']?[^"\'}\s,]+["\']?',
        re.IGNORECASE
    ),
}

# Fields that should be completely masked
MASKED_FIELDS = {
    "password", "password_hash", "secret", "token", "refresh_token",
    "access_token", "api_key", "apikey", "authorization", "auth_token",
    "totp_code", "backup_code", "secret_encrypted",
}

# Fields that should be partially masked
PARTIAL_MASK_FIELDS = {
    "email", "ip_address", "ip", "client_ip", "user_agent",
}


def mask_email(email: str) -> str:
    """Mask email address: user@domain.com -> u***@domain.com"""
    if "@" not in email:
        return email
    local, domain = email.rsplit("@", 1)
    if len(local) <= 1:
        return f"*@{domain}"
    return f"{local[0]}***@{domain}"


def mask_ip_address(ip: str) -> str:
    """Mask IP address: 192.168.1.100 -> 192.168.xxx.xxx"""
    parts = ip.split(".")
    if len(parts) != 4:
        return ip
    return f"{parts[0]}.{parts[1]}.xxx.xxx"


def mask_card_number(card: str) -> str:
    """Mask card number: 1234-5678-9012-3456 -> ****-****-****-3456"""
    # Remove separators and get last 4 digits
    digits = re.sub(r'[-\s]', '', card)
    if len(digits) < 4:
        return "****"
    return f"****-****-****-{digits[-4:]}"


def mask_token(token: str) -> str:
    """Mask JWT or other tokens: eyJ... -> eyJ***[MASKED]"""
    if len(token) <= 10:
        return "[MASKED]"
    return f"{token[:10]}***[MASKED]"


def mask_string_value(value: str) -> str:
    """Apply masking patterns to a string value."""
    result = value
    
    # Mask emails
    result = SENSITIVE_PATTERNS["email"].sub(
        lambda m: f"{mask_email(m.group(0))}",
        result
    )
    
    # Mask IP addresses
    result = SENSITIVE_PATTERNS["ip_address"].sub(
        lambda m: mask_ip_address(m.group(0)),
        result
    )
    
    # Mask card numbers
    result = SENSITIVE_PATTERNS["card_number"].sub(
        lambda m: mask_card_number(m.group(0)),
        result
    )
    
    # Mask JWT tokens
    result = SENSITIVE_PATTERNS["jwt_token"].sub(
        lambda m: mask_token(m.group(0)),
        result
    )
    
    # Mask password fields
    result = SENSITIVE_PATTERNS["password_field"].sub(
        r'\1"[MASKED]"',
        result
    )
    
    # Mask secret fields
    result = SENSITIVE_PATTERNS["secret_field"].sub(
        r'\1"[MASKED]"',
        result
    )
    
    return result


def mask_dict_value(key: str, value: Any) -> Any:
    """Mask a dictionary value based on its key."""
    key_lower = key.lower()
    
    # Completely mask sensitive fields
    if key_lower in MASKED_FIELDS:
        return "[MASKED]"
    
    # Partially mask certain fields
    if key_lower in PARTIAL_MASK_FIELDS:
        if isinstance(value, str):
            if key_lower == "email":
                return mask_email(value)
            elif key_lower in ("ip_address", "ip", "client_ip"):
                return mask_ip_address(value)
            elif key_lower == "user_agent":
                # Truncate user agent to first 50 chars
                return value[:50] + "..." if len(value) > 50 else value
    
    # For string values, apply pattern-based masking
    if isinstance(value, str):
        return mask_string_value(value)
    
    return value


def sensitive_data_filter(
    logger: logging.Logger,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Structlog processor to mask sensitive data in log events.
    
    This processor scans all event dictionary values and masks:
    - Email addresses
    - IP addresses
    - Credit card numbers
    - JWT tokens
    - Password and secret fields
    """
    masked_dict = {}
    
    for key, value in event_dict.items():
        if isinstance(value, dict):
            # Recursively mask nested dicts
            masked_dict[key] = {
                k: mask_dict_value(k, v) for k, v in value.items()
            }
        elif isinstance(value, list):
            # Handle lists
            masked_dict[key] = [
                mask_dict_value(key, item) if isinstance(item, str) else item
                for item in value
            ]
        else:
            masked_dict[key] = mask_dict_value(key, value)
    
    return masked_dict


def configure_logging(
    log_level: str = "INFO",
    json_logs: bool = False,
    app_env: str = "development",
) -> None:
    """Configure structured logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        json_logs: If True, output JSON logs (for production)
        app_env: Application environment
    """
    # Determine if we should use JSON logs
    use_json = json_logs or app_env == "production"

    # Shared processors for all loggers
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        sensitive_data_filter,  # Add sensitive data masking
    ]

    if use_json:
        # Production: JSON output
        shared_processors.append(structlog.processors.format_exc_info)
        renderer: Processor = structlog.processors.JSONRenderer()
    else:
        # Development: colored console output
        shared_processors.append(structlog.dev.set_exc_info)
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    # Configure structlog
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name (defaults to caller's module)

    Returns:
        Bound logger instance

    Usage:
        logger = get_logger(__name__)
        logger.info("player_action", table_id="123", action="fold")
    """
    return structlog.get_logger(name)


def bind_context(**kwargs: Any) -> None:
    """Bind context variables to all subsequent log calls.

    Args:
        **kwargs: Context variables to bind

    Usage:
        bind_context(trace_id="abc123", user_id="user456")
        logger.info("processing request")  # includes trace_id and user_id
    """
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_context() -> None:
    """Clear all bound context variables."""
    structlog.contextvars.clear_contextvars()


def unbind_context(*keys: str) -> None:
    """Remove specific context variables.

    Args:
        *keys: Keys to remove from context
    """
    structlog.contextvars.unbind_contextvars(*keys)
