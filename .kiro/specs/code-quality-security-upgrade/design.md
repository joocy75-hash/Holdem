# Design Document

## Overview

이 문서는 Texas Hold'em 포커 게임의 코드 품질, 보안, 성능 개선을 위한 기술 설계를 정의합니다. 코드 리뷰에서 발견된 문제점들을 해결하고, 프로덕션 환경에서 안정적으로 운영될 수 있는 시스템을 구축합니다.

## Architecture

### 현재 아키텍처 문제점

```
┌─────────────────────────────────────────────────────────────┐
│                    Current Issues                            │
├─────────────────────────────────────────────────────────────┤
│ 1. Memory Leaks                                              │
│    - _table_locks never cleaned up                          │
│    - _timeout_tasks accumulate                              │
│                                                              │
│ 2. Race Conditions                                           │
│    - Concurrent START_GAME possible                         │
│    - Bot loop can overlap with user actions                 │
│                                                              │
│ 3. Weak Type Safety                                          │
│    - Dict[str, Any] return types                            │
│    - Frontend uses 'any' types                              │
│                                                              │
│ 4. Hardcoded Values                                          │
│    - Bot delays: random.triangular(2.0, 5.0, 3.0)          │
│    - Hand result delay: asyncio.sleep(5.0)                  │
└─────────────────────────────────────────────────────────────┘
```

### 개선된 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    Improved Architecture                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Settings   │───▶│ ActionHandler│───▶│  PokerTable  │  │
│  │  (External)  │    │  (Cleanup)   │    │  (TypedDict) │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                   │                    │          │
│         ▼                   ▼                    ▼          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Logging    │    │ GameManager  │    │   Metrics    │  │
│  │ (Structured) │    │  (Cleanup)   │    │ (Prometheus) │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. 메모리 관리 컴포넌트

#### ActionHandler Cleanup

```python
# backend/app/ws/handlers/action.py

class ActionHandler(BaseHandler):
    """Enhanced ActionHandler with proper cleanup."""
    
    async def cleanup_table_resources(self, room_id: str) -> None:
        """Clean up all resources associated with a table.
        
        Called when a table is removed or reset.
        """
        # Cancel and remove timeout task
        await self._cancel_turn_timeout(room_id)
        
        # Remove table lock
        if room_id in self._table_locks:
            del self._table_locks[room_id]
            logger.info(f"[CLEANUP] Removed lock for room {room_id}")
    
    async def cleanup_all_resources(self) -> None:
        """Clean up all resources. Called on shutdown."""
        for room_id in list(self._timeout_tasks.keys()):
            await self._cancel_turn_timeout(room_id)
        
        self._table_locks.clear()
        self._timeout_tasks.clear()
        logger.info("[CLEANUP] All ActionHandler resources cleaned up")
```

#### GameManager Cleanup

```python
# backend/app/game/manager.py

class GameManager:
    """Enhanced GameManager with cleanup callbacks."""
    
    def __init__(self):
        self._tables: Dict[str, PokerTable] = {}
        self._lock = asyncio.Lock()
        self._cleanup_callbacks: List[Callable[[str], Awaitable[None]]] = []
    
    def register_cleanup_callback(
        self, 
        callback: Callable[[str], Awaitable[None]]
    ) -> None:
        """Register a callback to be called when a table is removed."""
        self._cleanup_callbacks.append(callback)
    
    async def remove_table(self, room_id: str) -> bool:
        """Remove a table and trigger cleanup callbacks."""
        async with self._lock:
            if room_id not in self._tables:
                return False
            
            # Trigger cleanup callbacks
            for callback in self._cleanup_callbacks:
                try:
                    await callback(room_id)
                except Exception as e:
                    logger.error(f"Cleanup callback failed: {e}")
            
            del self._tables[room_id]
            logger.info(f"[CLEANUP] Table {room_id} removed")
            return True
```

### 2. 타입 정의

#### Backend TypedDict 정의

```python
# backend/app/game/types.py

from typing import TypedDict, List, Optional
from enum import Enum

class ActionType(str, Enum):
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"
    ALL_IN = "all_in"

class PlayerState(TypedDict):
    seat: int
    position: int
    userId: str
    username: str
    stack: int
    bet: int
    totalBet: int
    status: str
    isBot: bool
    isCurrent: bool
    isDealer: bool

class ActionResult(TypedDict):
    success: bool
    action: Optional[str]
    amount: int
    seat: Optional[int]
    pot: int
    phase: str
    phase_changed: bool
    new_community_cards: List[str]
    hand_complete: bool
    hand_result: Optional['HandResult']
    players: List['PlayerStateUpdate']
    currentBet: int
    currentPlayer: Optional[int]

class HandResult(TypedDict):
    winners: List['WinnerInfo']
    showdown: List['ShowdownInfo']
    pot: int
    communityCards: List[str]
    eliminatedPlayers: List['EliminatedPlayer']

class WinnerInfo(TypedDict):
    seat: int
    position: int
    userId: str
    amount: int

class ShowdownInfo(TypedDict):
    seat: int
    position: int
    holeCards: List[str]

class EliminatedPlayer(TypedDict):
    seat: int
    userId: str
    nickname: str

class AvailableActions(TypedDict):
    actions: List[str]
    call_amount: int
    min_raise: Optional[int]
    max_raise: Optional[int]
```

#### Frontend 타입 정의

```typescript
// frontend/src/types/websocket.ts

export enum EventType {
  AUTH = 'AUTH',
  CONNECTION_STATE = 'CONNECTION_STATE',
  TABLE_SNAPSHOT = 'TABLE_SNAPSHOT',
  TABLE_STATE_UPDATE = 'TABLE_STATE_UPDATE',
  ACTION_REQUEST = 'ACTION_REQUEST',
  ACTION_RESULT = 'ACTION_RESULT',
  TURN_PROMPT = 'TURN_PROMPT',
  HAND_STARTED = 'HAND_STARTED',
  HAND_RESULT = 'HAND_RESULT',
  COMMUNITY_CARDS = 'COMMUNITY_CARDS',
  TURN_CHANGED = 'TURN_CHANGED',
  TIMEOUT_FOLD = 'TIMEOUT_FOLD',
  PLAYER_ELIMINATED = 'PLAYER_ELIMINATED',
  ERROR = 'ERROR',
  PING = 'PING',
  PONG = 'PONG',
}

export interface WebSocketMessage<T = unknown> {
  type: EventType;
  payload: T;
  requestId?: string;
  traceId?: string;
}

export interface ActionResultPayload {
  success: boolean;
  tableId: string;
  action?: {
    type: string;
    amount: number;
    position: number;
  };
  pot?: number;
  phase?: string;
  errorCode?: string;
  errorMessage?: string;
}

export interface TurnPromptPayload {
  tableId: string;
  position: number;
  allowedActions: AllowedAction[];
  deadlineAt: string;
  turnStartTime: number;
  turnTime: number;
  pot: number;
  currentBet: number;
}

export interface AllowedAction {
  type: 'fold' | 'check' | 'call' | 'bet' | 'raise' | 'all_in';
  amount?: number;
  minAmount?: number;
  maxAmount?: number;
}
```

### 3. 설정 외부화

```python
# backend/app/config.py (추가 설정)

class Settings(BaseSettings):
    # ... existing settings ...
    
    # Bot Timing Settings
    bot_think_time_min: float = Field(
        default=2.0,
        description="Minimum bot thinking time in seconds",
    )
    bot_think_time_max: float = Field(
        default=5.0,
        description="Maximum bot thinking time in seconds",
    )
    bot_think_time_mode: float = Field(
        default=3.0,
        description="Most likely bot thinking time (triangular distribution mode)",
    )
    bot_extra_think_probability: float = Field(
        default=0.2,
        description="Probability of bot taking extra thinking time",
    )
    
    # Game Timing Settings
    hand_result_display_seconds: float = Field(
        default=5.0,
        description="Time to display hand result before next hand",
    )
    phase_transition_delay_seconds: float = Field(
        default=1.5,
        description="Delay after community cards are dealt",
    )
    
    # Turn Timer Settings
    turn_time_default: int = Field(
        default=15,
        description="Default turn time in seconds",
    )
    turn_time_utg: int = Field(
        default=20,
        description="UTG (first to act preflop) turn time in seconds",
    )
```

### 4. 보안 헤더 강화

```python
# backend/app/middleware/security_headers.py (개선)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enhanced security headers middleware."""
    
    def __init__(self, app: Callable, settings: Settings):
        super().__init__(app)
        self.settings = settings
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.headers.get("upgrade", "").lower() == "websocket":
            return await call_next(request)
        
        response = await call_next(request)
        
        # Existing headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Enhanced: Content Security Policy
        if self.settings.app_env == "production":
            csp = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self' wss: https:; "
                "font-src 'self'; "
                "frame-ancestors 'none';"
            )
            response.headers["Content-Security-Policy"] = csp
            
            # HSTS for production
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        # Permissions Policy
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), "
            "gyroscope=(), magnetometer=(), microphone=(), "
            "payment=(), usb=()"
        )
        
        # Cache control for API
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, max-age=0"
            response.headers["Pragma"] = "no-cache"
        
        return response
```

### 5. Rate Limiting 개선

```python
# backend/app/middleware/rate_limit.py (개선)

class SlidingWindowRateLimiter:
    """Sliding window rate limiter using Redis sorted sets."""
    
    def __init__(self, redis: Redis, settings: Settings):
        self.redis = redis
        self.settings = settings
    
    async def is_allowed(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> tuple[bool, int, int]:
        """Check if request is allowed.
        
        Returns:
            (is_allowed, remaining, retry_after)
        """
        now = time.time()
        window_start = now - window_seconds
        
        pipe = self.redis.pipeline()
        
        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start)
        
        # Count current entries
        pipe.zcard(key)
        
        # Add current request
        pipe.zadd(key, {str(now): now})
        
        # Set expiry
        pipe.expire(key, window_seconds)
        
        results = await pipe.execute()
        current_count = results[1]
        
        if current_count >= limit:
            # Get oldest entry to calculate retry_after
            oldest = await self.redis.zrange(key, 0, 0, withscores=True)
            if oldest:
                retry_after = int(oldest[0][1] + window_seconds - now) + 1
            else:
                retry_after = window_seconds
            
            return False, 0, retry_after
        
        return True, limit - current_count - 1, 0


class EnhancedRateLimitMiddleware(BaseHTTPMiddleware):
    """Enhanced rate limiting with sliding window and user-based limits."""
    
    # Per-user rate limits (authenticated requests)
    USER_RATE_LIMITS: dict[str, tuple[int, int]] = {
        "/api/v1/auth/refresh": (20, 60),
        "/api/v1/rooms": (60, 60),
        "default": (200, 60),
    }
    
    # Per-IP rate limits (unauthenticated)
    IP_RATE_LIMITS: dict[str, tuple[int, int]] = {
        "/api/v1/auth/login": (5, 60),
        "/api/v1/auth/register": (3, 60),
        "default": (100, 60),
    }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # ... implementation with sliding window ...
```

### 6. 구조화된 로깅

```python
# backend/app/logging_config.py (개선)

import structlog
from typing import Any

def configure_logging(settings: Settings) -> None:
    """Configure structured logging."""
    
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]
    
    if settings.app_env == "production":
        # JSON output for production
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Pretty output for development
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


# Usage in handlers
logger = structlog.get_logger()

async def handle_action(self, conn, event):
    log = logger.bind(
        user_id=conn.user_id,
        room_id=event.payload.get("tableId"),
        action=event.payload.get("actionType"),
        trace_id=event.trace_id,
    )
    
    log.info("action_received")
    
    try:
        result = await self._process_action(...)
        log.info("action_processed", success=True, pot=result.get("pot"))
    except Exception as e:
        log.error("action_failed", error=str(e), exc_info=True)
        raise
```

## Data Models

### Error Response Model

```python
# backend/app/schemas/errors.py

from pydantic import BaseModel
from typing import Optional, Dict, Any

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Dict[str, Any] = {}

class ErrorResponse(BaseModel):
    error: ErrorDetail
    traceId: str

# Standard error codes
class ErrorCode:
    # Auth errors
    AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    AUTH_EMAIL_EXISTS = "AUTH_EMAIL_EXISTS"
    
    # Game errors
    GAME_NOT_YOUR_TURN = "GAME_NOT_YOUR_TURN"
    GAME_INVALID_ACTION = "GAME_INVALID_ACTION"
    GAME_INVALID_AMOUNT = "GAME_INVALID_AMOUNT"
    GAME_TABLE_NOT_FOUND = "GAME_TABLE_NOT_FOUND"
    GAME_NO_ACTIVE_HAND = "GAME_NO_ACTIVE_HAND"
    
    # Rate limit
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # Server errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system.*

### Property 1: Memory Cleanup Completeness
*For any* table that is removed from GameManager, all associated resources (locks, timeout tasks, Redis entries) SHALL be cleaned up within 1 second.
**Validates: Requirements 1.1, 1.2, 1.4**

### Property 2: Action Atomicity
*For any* player action request, the action SHALL either complete fully (state updated, broadcast sent) or fail completely (no state change).
**Validates: Requirements 2.2**

### Property 3: Concurrent Start Prevention
*For any* two simultaneous START_GAME requests for the same table, exactly one SHALL succeed and one SHALL fail with appropriate error.
**Validates: Requirements 2.1**

### Property 4: Input Validation Completeness
*For any* action request with invalid parameters (wrong action type, out-of-range amount), the system SHALL reject with descriptive error without processing.
**Validates: Requirements 3.1, 3.2, 3.3**

### Property 5: Rate Limit Accuracy
*For any* client exceeding rate limits, subsequent requests within the window SHALL be rejected with 429 status and accurate Retry-After header.
**Validates: Requirements 8.1, 8.3**

### Property 6: Type Safety
*For any* function in PokerTable and ActionHandler, return types SHALL match their TypedDict definitions.
**Validates: Requirements 5.1, 5.2**

### Property 7: Logging Completeness
*For any* game action (fold, check, call, raise), a structured log entry SHALL be created with user_id, room_id, action, and timestamp.
**Validates: Requirements 9.1, 9.4**

## Error Handling

### Error Handling Strategy

```python
# backend/app/utils/errors.py

from enum import Enum
from typing import Optional, Dict, Any
import structlog

logger = structlog.get_logger()

class GameError(Exception):
    """Base exception for game-related errors."""
    
    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True,
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        self.recoverable = recoverable
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


class InvalidActionError(GameError):
    """Raised when an invalid action is attempted."""
    pass


class NotYourTurnError(GameError):
    """Raised when a player acts out of turn."""
    pass


class InvalidAmountError(GameError):
    """Raised when bet/raise amount is invalid."""
    pass


# Error handler decorator
def handle_game_errors(func):
    """Decorator to handle game errors consistently."""
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except GameError as e:
            logger.warning(
                "game_error",
                error_code=e.code,
                error_message=e.message,
                details=e.details,
            )
            raise
        except Exception as e:
            logger.error(
                "unexpected_error",
                error=str(e),
                exc_info=True,
            )
            raise GameError(
                code="INTERNAL_ERROR",
                message="An unexpected error occurred",
                recoverable=False,
            )
    
    return wrapper
```

## Testing Strategy

### Unit Tests

1. **PokerTable Tests**
   - Test all action types (fold, check, call, raise, all_in)
   - Test edge cases (all-in, side pots, heads-up)
   - Test state transitions (phase changes)
   - Test cleanup after hand completion

2. **HandEvaluator Tests**
   - Test all hand rankings
   - Test preflop strength evaluation
   - Test draw detection
   - Test edge cases (wheel straight, split pots)

3. **ActionHandler Tests**
   - Test concurrent action handling
   - Test timeout behavior
   - Test cleanup on table removal

### Property-Based Tests

Using `hypothesis` library:

```python
# backend/tests/property/test_poker_table.py

from hypothesis import given, strategies as st
from app.game.poker_table import PokerTable, Player

@given(
    stack=st.integers(min_value=100, max_value=10000),
    action=st.sampled_from(['fold', 'check', 'call', 'raise']),
)
def test_action_preserves_total_chips(stack, action):
    """Total chips in play should remain constant after any action."""
    # Setup table with players
    # Execute action
    # Assert total chips unchanged
    pass

@given(
    num_players=st.integers(min_value=2, max_value=9),
)
def test_hand_completion_resets_state(num_players):
    """After hand completion, all temporary state should be reset."""
    # Setup and play hand to completion
    # Assert all state variables are reset
    pass
```

### Integration Tests

```python
# backend/tests/integration/test_websocket_flow.py

async def test_full_hand_flow():
    """Test complete hand from start to finish."""
    # Connect multiple clients
    # Start hand
    # Execute actions
    # Verify hand result
    # Verify cleanup
    pass

async def test_concurrent_start_game():
    """Test that concurrent START_GAME requests are handled correctly."""
    # Send multiple START_GAME simultaneously
    # Verify only one succeeds
    pass
```

### Test Coverage Requirements

- Backend: >80% line coverage
- Critical paths (action processing, hand evaluation): >95% coverage
- Frontend WebSocket client: >70% coverage
