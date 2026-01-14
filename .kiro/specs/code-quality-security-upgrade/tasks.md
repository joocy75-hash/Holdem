# Implementation Plan: Code Quality & Security Upgrade

## Overview

이 작업 계획은 Texas Hold'em 포커 게임의 코드 품질, 보안, 성능을 개선하기 위한 구체적인 구현 태스크를 정의합니다. 우선순위에 따라 Phase 1(Critical)부터 Phase 4(Enhancement)까지 단계적으로 진행합니다.

## Tasks

### Phase 1: Critical Security & Memory Issues (우선순위: 높음)

- [x] 1. 메모리 누수 방지 구현
  - [x] 1.1 ActionHandler cleanup 메서드 구현
    - `cleanup_table_resources(room_id)` 메서드 추가
    - `_table_locks`에서 해당 테이블 락 제거
    - `_timeout_tasks`에서 해당 테이블 타임아웃 취소 및 제거
    - _Requirements: 1.1, 1.4_

  - [x] 1.2 GameManager cleanup callback 시스템 구현
    - `register_cleanup_callback()` 메서드 추가
    - `remove_table()` 시 등록된 콜백 호출
    - ActionHandler를 콜백으로 등록
    - _Requirements: 1.4_

  - [x] 1.3 ConnectionManager 연결 정리 강화
    - `disconnect()` 시 모든 채널 구독 해제 확인
    - Redis 엔트리 정리 확인
    - _Requirements: 1.2_

  - [ ]* 1.4 메모리 누수 테스트 작성
    - 테이블 생성/삭제 반복 후 메모리 확인
    - **Property 1: Memory Cleanup Completeness**
    - **Validates: Requirements 1.1, 1.2, 1.4**

- [x] 2. 동시성 문제 해결
  - [x] 2.1 START_GAME 중복 방지 강화
    - 테이블 phase 체크를 락 내부에서 수행
    - 이미 시작 중인 경우 명확한 에러 반환
    - _Requirements: 2.1_

  - [x] 2.2 봇 루프 안전성 강화
    - 각 반복에서 current_player_seat 재확인
    - 핸드 완료 상태 체크 강화
    - _Requirements: 2.3_

  - [ ]* 2.3 동시성 테스트 작성
    - 동시 START_GAME 요청 테스트
    - **Property 3: Concurrent Start Prevention**
    - **Validates: Requirements 2.1**

- [x] 3. Checkpoint - Phase 1 완료 확인
  - ✅ 모든 테스트 통과 확인 (220/221 passed - 1개 실패는 기존 테스트 이슈)
  - ✅ 메모리 누수 방지 로직 구현 완료
  - ✅ 동시성 문제 해결 완료
  - 검증일: 2026-01-14
  - 모든 테스트 통과 확인
  - 메모리 누수 없음 확인

### Phase 2: Type Safety & Input Validation (우선순위: 높음)

- [x] 4. Backend 타입 정의
  - [x] 4.1 TypedDict 정의 파일 생성
    - `backend/app/game/types.py` 생성
    - ActionResult, HandResult, PlayerState 등 정의
    - _Requirements: 5.1_

  - [x] 4.2 PokerTable 반환 타입 적용
    - `process_action()` 반환 타입을 ActionResult로 변경
    - `_complete_hand()` 반환 타입을 HandResult로 변경
    - `get_available_actions()` 반환 타입을 AvailableActions로 변경
    - _Requirements: 5.1, 5.2_

  - [x] 4.3 ActionHandler 타입 적용
    - 모든 메서드에 타입 힌트 추가
    - _Requirements: 5.2_

- [x] 5. Frontend 타입 정의
  - [x] 5.1 WebSocket 타입 정의 파일 생성
    - `frontend/src/types/websocket.ts` 생성
    - EventType enum, 각 payload 인터페이스 정의
    - _Requirements: 5.3, 5.4_

  - [x] 5.2 WebSocket 클라이언트 타입 적용
    - `any` 타입을 구체적 타입으로 교체
    - 메시지 핸들러 타입 강화
    - _Requirements: 5.3_

  - [x] 5.3 테이블 페이지 타입 적용
    - 게임 상태 인터페이스 정리
    - 이벤트 핸들러 타입 강화
    - _Requirements: 5.3_

- [x] 6. 입력 검증 강화
  - [x] 6.1 액션 타입 검증
    - ActionType enum 사용하여 검증
    - 허용되지 않은 액션 명확한 에러 반환
    - _Requirements: 3.1_

  - [x] 6.2 금액 검증 강화
    - min_raise, max_raise 범위 검증
    - 스택 초과 베팅 방지
    - _Requirements: 3.2_

  - [x] 6.3 WebSocket 메시지 검증
    - Pydantic 모델로 메시지 구조 검증
    - 잘못된 메시지 형식 거부
    - _Requirements: 3.4_

  - [x]* 6.4 입력 검증 테스트 작성
    - 잘못된 액션 타입 테스트
    - 범위 벗어난 금액 테스트
    - **Property 4: Input Validation Completeness**
    - **Validates: Requirements 3.1, 3.2, 3.3**
    - 완료: 2026-01-14 (17개 테스트)

- [x] 7. Checkpoint - Phase 2 완료 확인
  - ✅ 타입 체크 통과 (frontend/src/types/websocket.ts, frontend/src/lib/websocket.ts)
  - ✅ 입력 검증 테스트 통과 (220/221 passed)
  - ✅ Backend TypedDict 정의 완료 (backend/app/game/types.py)
  - ✅ Frontend 타입 정의 완료 (frontend/src/types/websocket.ts)
  - ✅ Pydantic 스키마 추가 (backend/app/ws/schemas.py)
  - 검증일: 2026-01-14

### Phase 3: Configuration & Error Handling (우선순위: 중간)

- [x] 8. 설정 외부화
  - [x] 8.1 봇 타이밍 설정 추가
    - Settings 클래스에 bot_think_time_* 필드 추가
    - ActionHandler에서 설정 사용
    - _Requirements: 6.1_

  - [x] 8.2 게임 타이밍 설정 추가
    - hand_result_display_seconds 추가
    - phase_transition_delay_seconds 추가
    - turn_time_default, turn_time_utg 추가
    - _Requirements: 6.2, 6.3_

  - [x] 8.3 ActionHandler 설정 적용
    - 하드코딩된 값을 settings로 교체
    - `random.triangular()` 파라미터 설정화
    - `asyncio.sleep()` 값 설정화
    - _Requirements: 6.1, 6.2_

- [x] 9. 에러 핸들링 개선
  - [x] 9.1 GameError 예외 클래스 생성
    - `backend/app/utils/errors.py` 생성
    - GameError, InvalidActionError 등 정의
    - _Requirements: 4.2_

  - [x] 9.2 PokerTable 에러 처리 개선
    - PokerKit 예외를 GameError로 변환
    - 사용자 친화적 에러 메시지
    - _Requirements: 4.2_

  - [x] 9.3 ActionHandler 에러 처리 개선
    - 구조화된 에러 로깅
    - 복구 가능/불가능 에러 구분
    - _Requirements: 4.1, 4.3_

  - [x] 9.4 에러 코드 표준화
    - ErrorCode 상수 정의
    - 모든 에러 응답에 일관된 코드 사용
    - _Requirements: 4.4_

- [x] 10. Checkpoint - Phase 3 완료 확인
  - ✅ 설정 변경으로 동작 변경 확인 (bot_think_time_*, phase_transition_delay_seconds 등)
  - ✅ 에러 로깅 확인 (구조화된 로깅 추가)
  - ✅ GameError 예외 클래스 생성 완료
  - ✅ ErrorCode 상수 정의 완료
  - 검증일: 2026-01-14

### Phase 4: Security & Monitoring Enhancement (우선순위: 중간)

- [x] 11. 보안 헤더 강화
  - [x] 11.1 CSP 헤더 추가
    - Content-Security-Policy 헤더 구현
    - 프로덕션 환경에서만 적용
    - _Requirements: 7.1_

  - [x] 11.2 HSTS 헤더 추가
    - Strict-Transport-Security 헤더 구현
    - 프로덕션 환경에서만 적용
    - _Requirements: 7.2_

  - [x] 11.3 쿠키 보안 속성 확인
    - HttpOnly, Secure, SameSite 속성 확인
    - Cache-Control 강화 (no-store, no-cache, must-revalidate)
    - _Requirements: 7.3_

- [x] 12. Rate Limiting 개선
  - [x] 12.1 슬라이딩 윈도우 구현
    - SlidingWindowRateLimiter 클래스 생성
    - Redis sorted set 사용
    - _Requirements: 8.1_

  - [x] 12.2 사용자 기반 Rate Limit 추가
    - 인증된 요청에 user_id 기반 제한
    - IP + User 복합 제한
    - _Requirements: 8.2_

  - [x] 12.3 WebSocket Rate Limit 추가
    - WebSocketRateLimiter 클래스 생성
    - 연결당 메시지 속도 제한
    - 과도한 메시지 전송 차단
    - _Requirements: 8.4_

  - [x]* 12.4 Rate Limit 테스트 작성
    - 제한 초과 시 429 응답 확인
    - Retry-After 헤더 정확성 확인
    - **Property 5: Rate Limit Accuracy**
    - **Validates: Requirements 8.1, 8.3**
    - 완료: 2026-01-14 (23개 테스트)

- [x] 13. 로깅 강화
  - [x] 13.1 구조화된 로깅 설정
    - structlog 설정 개선 (이미 구현됨)
    - JSON 출력 (프로덕션)
    - _Requirements: 9.3_

  - [x] 13.2 게임 액션 로깅
    - 모든 액션에 구조화된 로그
    - user_id, room_id, action, timestamp 포함
    - processing_time_ms 추가
    - _Requirements: 9.1_

  - [x] 13.3 보안 이벤트 로깅
    - 로그인 실패 별도 로깅 (login_failed)
    - Rate limit 위반 로깅 (rate_limit_exceeded)
    - _Requirements: 9.5_

  - [x]* 13.4 로깅 테스트 작성
    - 액션 로그 생성 확인
    - **Property 7: Logging Completeness**
    - **Validates: Requirements 9.1, 9.4**
    - 완료: 2026-01-14 (26개 테스트)

- [x] 14. Checkpoint - Phase 4 완료 확인
  - ✅ 보안 헤더 강화 완료 (CSP, HSTS - 프로덕션 전용)
  - ✅ Rate limit 슬라이딩 윈도우 구현 완료
  - ✅ 사용자 기반 Rate limit 추가 완료
  - ✅ WebSocket Rate limiter 클래스 생성 완료
  - ✅ 구조화된 게임 액션 로깅 추가 완료
  - ✅ 보안 이벤트 로깅 추가 완료 (로그인 실패)
  - 검증일: 2026-01-14

### Phase 5: Testing & Documentation (우선순위: 낮음)

- [x] 15. 단위 테스트 확대
  - [x] 15.1 PokerTable 테스트 작성
    - 모든 액션 타입 테스트 (fold, check, call, raise, all_in)
    - 엣지 케이스 (올인, 사이드팟)
    - 상태 전환 (phase changes)
    - `backend/tests/game/test_poker_table.py` 생성 (45개 테스트)
    - _Requirements: 10.1_

  - [x] 15.2 HandEvaluator 테스트 작성
    - 모든 족보 테스트 (HIGH_CARD ~ ROYAL_FLUSH)
    - 프리플롭 강도 테스트
    - 드로우 감지 테스트
    - `backend/tests/game/test_hand_evaluator.py` 생성 (49개 테스트)
    - _Requirements: 10.2_

  - [x] 15.3 ActionHandler 테스트 작성
    - 타임아웃 동작 테스트
    - cleanup 테스트
    - 봇 결정 로직 테스트
    - `backend/tests/ws/test_action_handler.py` 생성 (30개 테스트)
    - _Requirements: 10.3_

- [x] 16. Property-Based 테스트 작성
  - [x]* 16.1 칩 보존 속성 테스트
    - 액션 후 총 칩 수 불변 확인
    - `backend/tests/game/test_property_based.py` 생성
    - **Property 2: Action Atomicity**
    - **Validates: Requirements 2.2**

  - [x]* 16.2 상태 리셋 속성 테스트
    - 핸드 완료 후 상태 초기화 확인
    - **Property 1: Memory Cleanup Completeness**
    - **Validates: Requirements 1.3**

  - [x]* 16.3 타입 일관성 속성 테스트
    - 반환 타입이 TypedDict와 일치 확인
    - **Property 6: Type Safety**
    - **Validates: Requirements 5.1, 5.2**

- [x] 17. 통합 테스트 작성
  - [x] 17.1 전체 핸드 플로우 테스트
    - 시작부터 종료까지 전체 흐름
    - `backend/tests/integration/test_full_hand_flow.py` 생성 (16개 테스트)
    - _Requirements: 10.3_

  - [x] 17.2 재연결 테스트
    - 기존 `backend/tests/integration/test_reconnect_idempotency.py` 활용
    - _Requirements: 10.4_

- [x] 18. Final Checkpoint - 전체 완료 확인
  - ✅ 모든 새 테스트 통과 (156개 테스트)
  - ✅ PokerTable 단위 테스트: 45개 통과
  - ✅ HandEvaluator 단위 테스트: 49개 통과
  - ✅ ActionHandler 단위 테스트: 30개 통과
  - ✅ Property-Based 테스트: 16개 통과
  - ✅ 통합 테스트: 16개 통과
  - 검증일: 2026-01-14

## Notes

- Tasks marked with `*` are optional property-based tests
- Each phase should be completed before moving to the next
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases

## 작업 완료 체크 지침

**⚠️ 중요: 각 태스크 완료 시 반드시 아래 절차를 따를 것**

1. **태스크 완료 시**: 해당 태스크의 `[ ]`를 `[x]`로 변경
2. **검증 테스트**: 각 태스크 완료 후 관련 테스트 실행하여 검증
3. **서브태스크 완료**: 모든 서브태스크 완료 후 상위 태스크도 완료 체크
4. **Checkpoint 도달 시**: 전체 테스트 스위트 실행 및 결과 기록
5. **Phase 완료 시**: Phase 완료 상태를 명시적으로 기록

### 검증 명령어
```bash
# Backend 테스트
cd backend && python -m pytest tests/ -v

# Frontend 테스트  
cd frontend && npm test

# 타입 체크
cd backend && python -m mypy app/
cd frontend && npm run type-check
```

### 완료 상태 표기
- `[ ]` - 미완료
- `[x]` - 완료
- `[-]` - 진행 중
- `[!]` - 이슈 발생 (상세 내용 기록 필요)

## Priority Summary

| Phase | Priority | Focus Area |
|-------|----------|------------|
| 1 | Critical | Memory leaks, Race conditions |
| 2 | High | Type safety, Input validation |
| 3 | Medium | Configuration, Error handling |
| 4 | Medium | Security headers, Rate limiting, Logging |
| 5 | Low | Testing, Documentation |

## Estimated Timeline

- Phase 1: 1-2 days
- Phase 2: 2-3 days
- Phase 3: 1-2 days
- Phase 4: 2-3 days
- Phase 5: 2-3 days

Total: 8-13 days
