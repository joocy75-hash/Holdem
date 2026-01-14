# Requirements Document

## Introduction

이 문서는 Texas Hold'em 포커 게임 프로젝트의 코드 품질, 보안, 성능 개선을 위한 요구사항을 정의합니다. 코드 리뷰를 통해 발견된 문제점들을 체계적으로 해결하고, 프로덕션 환경에서 안정적으로 운영될 수 있도록 개선합니다.

## Glossary

- **ActionHandler**: 게임 액션(fold, check, call, raise)을 처리하는 WebSocket 핸들러
- **PokerTable**: 포커 테이블 상태를 관리하는 핵심 클래스
- **GameManager**: 모든 활성 테이블을 메모리에서 관리하는 싱글톤
- **ConnectionManager**: WebSocket 연결을 관리하는 클래스
- **Rate_Limiter**: API 요청 속도를 제한하는 미들웨어
- **JWT**: JSON Web Token, 인증에 사용되는 토큰
- **TOTP**: Time-based One-Time Password, 2FA에 사용

## Requirements

### Requirement 1: 메모리 누수 방지

**User Story:** As a 시스템 관리자, I want 서버가 장시간 운영되어도 메모리가 안정적으로 유지되기를, so that 서비스 중단 없이 운영할 수 있습니다.

#### Acceptance Criteria

1. WHEN a table is removed, THE ActionHandler SHALL clean up associated locks and timeout tasks from `_table_locks` and `_timeout_tasks` dictionaries
2. WHEN a WebSocket connection is closed, THE ConnectionManager SHALL remove all associated channel subscriptions and Redis entries
3. WHEN a hand completes, THE PokerTable SHALL reset all temporary state variables including `_seat_to_index`, `_index_to_seat`, and `_hand_actions`
4. THE GameManager SHALL provide a `cleanup_table` method that removes all resources associated with a table

### Requirement 2: 동시성 및 레이스 컨디션 방지

**User Story:** As a 플레이어, I want 여러 명이 동시에 액션을 해도 게임이 정상 작동하기를, so that 공정한 게임을 즐길 수 있습니다.

#### Acceptance Criteria

1. WHEN multiple START_GAME requests arrive simultaneously, THE ActionHandler SHALL process only the first request and reject duplicates
2. WHEN a player action is processed, THE PokerTable SHALL use atomic operations to prevent race conditions
3. WHEN bot actions are processed in a loop, THE ActionHandler SHALL verify the current player before each action
4. IF a timeout occurs during action processing, THEN THE ActionHandler SHALL safely cancel the timeout without affecting ongoing actions

### Requirement 3: 입력 검증 강화

**User Story:** As a 보안 담당자, I want 모든 사용자 입력이 철저히 검증되기를, so that 악의적인 입력으로부터 시스템을 보호할 수 있습니다.

#### Acceptance Criteria

1. WHEN a player submits an action, THE ActionHandler SHALL validate action type against allowed values (fold, check, call, raise, all_in)
2. WHEN a bet/raise amount is submitted, THE PokerTable SHALL validate the amount is within min_raise and max_raise bounds
3. WHEN a user joins a table, THE System SHALL validate buy-in amount is within table limits
4. WHEN WebSocket messages are received, THE System SHALL validate message structure before processing
5. IF invalid input is detected, THEN THE System SHALL return a descriptive error without exposing internal details

### Requirement 4: 에러 핸들링 개선

**User Story:** As a 개발자, I want 에러가 발생했을 때 명확한 정보를 얻기를, so that 문제를 빠르게 진단하고 해결할 수 있습니다.

#### Acceptance Criteria

1. WHEN an exception occurs in action processing, THE ActionHandler SHALL log the full stack trace with context information
2. WHEN a PokerKit exception occurs, THE PokerTable SHALL catch and translate it to a user-friendly error message
3. WHEN a bot action fails, THE ActionHandler SHALL log the failure and attempt recovery
4. THE System SHALL use structured logging with consistent fields (user_id, room_id, action, error_code)
5. IF an unrecoverable error occurs, THEN THE System SHALL gracefully terminate the affected hand and notify players

### Requirement 5: 타입 안전성 강화

**User Story:** As a 개발자, I want 코드의 타입이 명확하게 정의되기를, so that 런타임 에러를 줄이고 코드 품질을 높일 수 있습니다.

#### Acceptance Criteria

1. THE Backend SHALL use TypedDict for all dictionary return types in PokerTable methods
2. THE Backend SHALL define explicit types for all function parameters and return values
3. THE Frontend SHALL replace all `any` types with specific interface definitions
4. THE Frontend SHALL define WebSocket message types for all event types
5. WHEN type errors are detected, THE CI/CD pipeline SHALL fail the build

### Requirement 6: 설정 외부화

**User Story:** As a DevOps 엔지니어, I want 하드코딩된 값들이 설정 파일로 분리되기를, so that 환경별로 쉽게 설정을 변경할 수 있습니다.

#### Acceptance Criteria

1. THE Backend SHALL move bot timing constants (think_time_min, think_time_max) to Settings class
2. THE Backend SHALL move game timing constants (hand_result_display_time, phase_transition_delay) to Settings class
3. THE Backend SHALL move WebSocket constants (heartbeat_interval, server_timeout) to Settings class
4. THE Frontend SHALL use environment variables for all configurable values
5. WHEN settings are changed, THE System SHALL apply them without code modification

### Requirement 7: 보안 헤더 강화

**User Story:** As a 보안 담당자, I want 모든 HTTP 응답에 적절한 보안 헤더가 포함되기를, so that 일반적인 웹 공격으로부터 보호받을 수 있습니다.

#### Acceptance Criteria

1. THE SecurityHeadersMiddleware SHALL add Content-Security-Policy header with strict directives
2. THE SecurityHeadersMiddleware SHALL add Strict-Transport-Security header in production
3. THE Backend SHALL set secure cookie attributes (HttpOnly, Secure, SameSite) for all cookies
4. WHEN serving API responses, THE Backend SHALL include appropriate CORS headers based on environment

### Requirement 8: Rate Limiting 강화

**User Story:** As a 시스템 관리자, I want API 요청이 적절히 제한되기를, so that DDoS 공격과 남용으로부터 시스템을 보호할 수 있습니다.

#### Acceptance Criteria

1. THE RateLimitMiddleware SHALL implement sliding window rate limiting instead of fixed window
2. THE RateLimitMiddleware SHALL support user-based rate limiting in addition to IP-based
3. WHEN rate limit is exceeded, THE System SHALL return 429 status with Retry-After header
4. THE System SHALL implement WebSocket message rate limiting per connection
5. THE System SHALL log rate limit violations for security monitoring

### Requirement 9: 로깅 및 모니터링 강화

**User Story:** As a 운영자, I want 시스템 상태를 실시간으로 모니터링하기를, so that 문제를 조기에 발견하고 대응할 수 있습니다.

#### Acceptance Criteria

1. THE System SHALL log all game actions with timestamp, user_id, room_id, and action details
2. THE System SHALL expose Prometheus metrics for connection count, active tables, and action latency
3. THE System SHALL implement structured JSON logging for production environment
4. WHEN errors occur, THE System SHALL include trace_id for request correlation
5. THE System SHALL log security-relevant events (login failures, rate limit violations) separately

### Requirement 10: 테스트 커버리지 확대

**User Story:** As a 개발자, I want 핵심 로직이 테스트로 검증되기를, so that 변경 시 회귀 버그를 방지할 수 있습니다.

#### Acceptance Criteria

1. THE Backend SHALL have unit tests for all PokerTable methods with >80% coverage
2. THE Backend SHALL have unit tests for hand_evaluator with edge cases
3. THE Backend SHALL have integration tests for WebSocket action flow
4. THE Frontend SHALL have unit tests for WebSocket client reconnection logic
5. WHEN tests fail, THE CI/CD pipeline SHALL block deployment
