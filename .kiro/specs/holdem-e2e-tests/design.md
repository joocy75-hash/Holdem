# Design Document: 상용급 홀덤 E2E 테스트 시스템

## Overview

Playwright를 활용한 상용급 온라인 포커 게임의 E2E 테스트 시스템입니다. 멀티 브라우저 컨텍스트로 2~6명 멀티플레이어 시뮬레이션, 사이드 팟, 재접속 복구, 보안 감사까지 검증합니다.

핵심 설계 원칙:
- Page Object Model (POM): 페이지별 추상화
- Multi-Browser Context: 독립 세션으로 멀티플레이어 시뮬레이션
- 치트 API 활용: 덱 주입, 타이머 제어로 테스트 효율화
- 도메인별 분리: auth, lobby, table, security, stress

## Architecture

```
frontend/tests/e2e/
├── fixtures/
│   ├── auth.fixture.ts
│   ├── multi-player.fixture.ts
│   └── n-player.fixture.ts
├── pages/
│   ├── login.page.ts
│   ├── lobby.page.ts
│   └── table.page.ts
├── specs/
│   ├── auth/
│   ├── lobby/
│   ├── table/
│   ├── security/
│   ├── recovery/
│   └── stress/
└── utils/
    ├── test-users.ts
    ├── cheat-api.ts
    ├── wait-helpers.ts
    └── ws-inspector.ts
```

## Correctness Properties

### Property 1: Betting Synchronization
*For any* betting action by Player A, Player B's UI should reflect updated pot within 2 seconds.
**Validates: Requirements 4.1, 4.4**

### Property 2: Turn Indication Consistency
*For any* player whose turn it is, action buttons should be displayed.
**Validates: Requirements 4.2**

### Property 3: Fold State Consistency
*For any* player who folds, status should show "FOLD" across all clients.
**Validates: Requirements 4.3**

### Property 4: Winner Pot Distribution
*For any* winner at showdown, chip stack should increase by pot amount.
**Validates: Requirements 6.2**

### Property 5: Side Pot Separation
*For any* all-in, main pot and side pots should be correctly separated.
**Validates: Requirements 10.1, 10.2**

### Property 6: Server Authority
*For any* out-of-turn action, server should reject it.
**Validates: Requirements 11.1, 11.2**

### Property 7: Idempotency
*For any* duplicate action_id, server should process only once.
**Validates: Requirements 11.3**

### Property 8: Card Security
*For any* spectator, WS messages should never contain others' hole cards.
**Validates: Requirements 11.4**

### Property 9: Reconnection Recovery
*For any* reconnection, game state should be fully restored.
**Validates: Requirements 12.1, 12.2**

## Release Gate Criteria

1. 사이드 팟 분배 오차 0%
2. 재접속 상태 복구 성공률 100%
3. 타인 카드 정보 노출 0건
4. 중복 액션 방어 성공
