# Implementation Plan: 상용급 홀덤 E2E 테스트 로드맵 (피망 스타일 포함)

## Overview

Playwright 기반의 상용급 온라인 포커 E2E 테스트 시스템입니다. 7개 Phase, 22단계로 구성되며, 기본 인프라부터 피망 홀덤 스타일 UI/UX, 카드 쪼기(Squeeze) 애니메이션, 보안 감사까지 포괄합니다.

---

## Phase 1: 기반 인프라 구축

- [x] 1. 프로젝트 구조 및 환경 설정
  - [x] 1.1 E2E 테스트 디렉토리 구조 생성
    - `tests/e2e/` 하위에 도메인별 분리: auth, lobby, table, security, stress
    - fixtures, pages, utils 폴더 구성
    - _Requirements: 전체 구조_
  - [x] 1.2 Playwright 설정 파일 구성
    - testDir, baseURL, trace, screenshot, video 설정
    - CI/CD 파이프라인용 reporter 설정 (html, json, junit)
    - _Requirements: 테스트 환경_
  - [x] 1.3 package.json 테스트 스크립트 추가
    - `test:e2e`, `test:e2e:ui`, `test:e2e:ci`, `test:e2e:headed` 스크립트
    - _Requirements: 실행 편의성_
  - [x] 1.4 치트 API 클라이언트 구현
    - 테스트용 관리자 API: 덱 주입, 타이머 강제 종료, 강제 페이즈 전환
    - `utils/cheat-api.ts` 구현
    - _Requirements: 테스트 효율화_

- [x] 2. Page Object Models (POM) 설계
  - [x] 2.1 LoginPage 클래스 구현
    - goto, login, signup, getErrorMessage, toggleSignupMode
    - _Requirements: 1.1~1.5_
  - [x] 2.2 LobbyPage 클래스 구현
    - goto, waitForTables, getTableCount, joinTable, clickTab, logout
    - _Requirements: 2.1~2.5_
  - [x] 2.3 TablePage 클래스 구현 (좌석/바이인)
    - goto, waitForTableLoad, clickEmptySeat, confirmBuyIn, getMyPosition, getMyChipStack
    - _Requirements: 3.1~3.5_
  - [x] 2.4 TablePage 클래스 구현 (게임 액션)
    - fold, check, call, raise, allIn, waitForMyTurn, hasActionButtons
    - _Requirements: 4.1~4.5_
  - [x] 2.5 TablePage 클래스 구현 (게임 상태)
    - isMyTurn, getCurrentPhase, getPotAmount, getSidePots, getCommunityCardCount, getHoleCards
    - getDealerPosition, getSmallBlindPosition, getBigBlindPosition
    - _Requirements: 5.1~5.5, 9.x_
  - [x] 2.6 TablePage 클래스 구현 (타이머/퇴장)
    - getTimerValue, waitForTurnTimeout, leaveTable, sitOut, sitIn
    - _Requirements: 7.x, 8.x_

- [x] 3. 멀티 클라이언트 제어 Fixtures
  - [x] 3.1 테스트 유저 생성 유틸리티
    - createTestUser(prefix), createTestUsers(count) 함수
    - 고유 ID 생성, 초기 잔액 설정
    - _Requirements: 인증 테스트 기반_
  - [x] 3.2 인증 Fixture 구현
    - 로그인된 상태의 page를 제공하는 authenticatedPage fixture
    - _Requirements: 4.x_
  - [x] 3.3 Multi-Player Fixture 구현 (2인)
    - playerA, playerB 독립 브라우저 컨텍스트
    - setupBothPlayersAtTable(tableId) 헬퍼
    - _Requirements: 8.x_
  - [x] 3.4 Multi-Player Fixture 구현 (N인)
    - createPlayers(n) 함수: 2~6명 동시 제어
    - 각 플레이어별 독립 세션 및 TablePage 인스턴스
    - _Requirements: 11.x (사이드 팟)_

---

## Phase 2: 기본 진입 및 인증

- [x] 4. 인증(Auth) 및 세션 보안 테스트
  - [x] 4.1 로그인 페이지 UI 테스트
    - 이메일/비밀번호 필드 존재 확인
    - _Requirements: 1.1_
  - [x] 4.2 로그인 성공 테스트
    - 유효한 자격증명으로 로비 리다이렉트 확인
    - _Requirements: 1.2_
  - [x] 4.3 로그인 실패 테스트
    - 잘못된 자격증명으로 에러 메시지 확인
    - _Requirements: 1.3_
  - [x] 4.4 회원가입 플로우 테스트
    - 토글, 추가 필드, 가입 완료 확인
    - _Requirements: 1.4, 1.5_
  - [x] 4.5 토큰 만료 처리 테스트
    - 만료된 토큰으로 API 호출 시 재인증 플로우 확인
    - _Requirements: 신규 - 세션 보안_
  - [x] 4.6 중복 로그인 차단 테스트
    - 동일 계정 다중 세션 시 이전 세션 종료 확인
    - _Requirements: 신규 - 세션 보안_

- [x] 5. 로비 및 테이블 참가 테스트
  - [x] 5.1 테이블 목록 표시 테스트
    - 인증 후 테이블 카드 렌더링 확인
    - _Requirements: 2.1_
  - [x] 5.2 테이블 입장 네비게이션 테스트
    - 테이블 클릭 시 URL 변경 확인
    - _Requirements: 2.2_
  - [x] 5.3 탭 필터링 테스트
    - 전체/홀덤/토너먼트 탭 전환 확인
    - _Requirements: 2.4_
  - [x] 5.4 로그아웃 테스트
    - 로그아웃 후 로그인 페이지 리다이렉트 확인
    - _Requirements: 2.5_
  - [x] 5.5 관전자(Spectator) 보안 테스트
    - 관전자 입장 시 타인 Hole Card가 WS 패킷에 미포함 확인
    - Network 탭 또는 WS 메시지 검증
    - _Requirements: 신규 - 보안_

- [x] 6. 좌석 점유 및 스택 설정 테스트
  - [x] 6.1 테이블 UI 렌더링 테스트
    - 좌석 위치, 테이블 요소 확인
    - _Requirements: 3.1_
  - [x] 6.2 바이인 모달 테스트
    - 빈 좌석 클릭 시 모달 표시 확인
    - _Requirements: 3.2_
  - [x] 6.3 바이인 완료 테스트
    - 바이인 후 좌석 착석 및 칩 스택 확인
    - _Requirements: 3.3_
  - [x] 6.4 잔액 부족 테스트
    - 최소 바이인 미달 시 에러 메시지 확인
    - _Requirements: 3.4_
  - [x] 6.5 좌석 Race Condition 테스트
    - 두 유저가 동시에 같은 좌석 클릭 시 단 한 명만 승인 확인
    - _Requirements: 신규 - 동시성_

- [x] 7. Checkpoint A - 기본 통과 의례
  - 2인 착석 후 핸드 시작까지 "Happy Path" 100% 성공 확인
  - 문제 발생 시 사용자에게 질문

---

## Phase 3: 핵심 게임 로직 및 상호작용

- [x] 8. 멀티플레이어 액션 & 서버 권위(Authority) 테스트
  - [x] 8.1 베팅 동기화 테스트 (Property 1)
    - Player A 레이즈 → Player B UI 업데이트 확인
    - **Property 1: Betting Synchronization**
    - **Validates: Requirements 4.1, 4.4**
  - [x] 8.2 턴 표시 테스트 (Property 2)
    - 턴인 플레이어에게 액션 버튼 표시 확인
    - **Property 2: Turn Indication Consistency**
    - **Validates: Requirements 4.2**
  - [x] 8.3 폴드 상태 동기화 테스트 (Property 3)
    - 폴드 후 상대방 UI에 FOLD 표시 확인
    - **Property 3: Fold State Consistency**
    - **Validates: Requirements 4.3**
  - [x] 8.4 Negative Test: 턴 아닐 때 액션 시도
    - 내 턴이 아닐 때 Raise 시도 → 서버 Reject 확인
    - _Requirements: 신규 - 서버 권위_
  - [x] 8.5 Negative Test: 폴드 후 베팅 시도
    - 이미 폴드한 유저의 베팅 → 서버 Reject 확인
    - _Requirements: 신규 - 서버 권위_
  - [x] 8.6 Idempotency 테스트
    - 동일 action_id 패킷 2회 전송 → 팟 중복 계산 방지 확인
    - _Requirements: 신규 - 멱등성_

- [x] 9. 블라인드 및 버튼 이동 규칙 테스트
  - [x] 9.1 딜러 버튼 이동 테스트
    - 매 핸드 종료 후 딜러 버튼 시계방향 이동 확인
    - _Requirements: 신규 - 포커 규칙_
  - [x] 9.2 SB/BB 위치 테스트
    - 딜러 기준 SB, BB 위치 정확성 확인
    - _Requirements: 신규 - 포커 규칙_
  - [x] 9.3 Heads-up(2인) 특수 규칙 테스트
    - 2인 플레이 시 딜러=SB, 상대=BB 규칙 확인
    - _Requirements: 신규 - 포커 규칙_
  - [x] 9.4 플레이어 이탈 후 버튼 이동 테스트
    - 중간 플레이어 이탈 시 버튼 스킵 로직 확인
    - _Requirements: 신규 - 포커 규칙_

- [x] 10. 스트리트 전환 및 베팅 라운드 테스트
  - [x] 10.1 Preflop → Flop 전환 테스트
    - 프리플랍 베팅 완료 후 플랍(3장) 표시 확인
    - _Requirements: 5.2_
  - [x] 10.2 Flop → Turn 전환 테스트
    - 플랍 베팅 완료 후 턴(4장) 표시 확인
    - _Requirements: 5.3_
  - [x] 10.3 Turn → River 전환 테스트
    - 턴 베팅 완료 후 리버(5장) 표시 확인
    - _Requirements: 5.4_
  - [x] 10.4 전원 체크 시 즉시 전환 테스트
    - 모든 플레이어 체크 시 다음 스트리트로 즉시 전환 확인
    - _Requirements: 4.5_
  - [x] 10.5 베팅 금액 일치 시 전환 테스트
    - 모든 플레이어 베팅 금액 일치 시 전환 확인
    - _Requirements: 4.5_

---

## Phase 4: 고급 포커 로직

- [x] 11. 사이드 팟(Side Pot) 생성 테스트
  - [x] 11.1 올인 시 메인 팟 분리 테스트
    - 올인 플레이어 발생 시 메인 팟과 사이드 팟 분리 확인
    - _Requirements: 6.2 확장_
  - [x] 11.2 사이드 팟 계산 정확성 테스트
    - 3인 플레이: A(100칩) 올인, B/C(500칩) 추가 레이즈
    - 메인 팟: 300칩(100×3), 사이드 팟: 800칩((500-100)×2) 확인
    - _Requirements: 6.2 확장_
  - [x] 11.3 다중 사이드 팟 테스트
    - 4인 플레이: A(100), B(200), C(500), D(500) 올인
    - 메인 팟 + 사이드 팟 1 + 사이드 팟 2 정확 분리 확인
    - _Requirements: 6.2 확장_
  - [x] 11.4 사이드 팟 승자 분배 테스트
    - 메인 팟 승자와 사이드 팟 승자가 다를 때 정확 분배 확인
    - _Requirements: 6.2 확장_

- [x] 11-1. 플레이어 이탈 및 Sit-out 처리 테스트
  - [x] 11-1.1 핸드 중 나가기 테스트
    - 내 턴에 나가기 → 즉시 Auto-fold 처리 확인
    - 기여한 칩은 팟에 그대로 유지 확인
    - _Requirements: 8.2_
  - [x] 11-1.2 Sit-out 상태 테스트
    - Sit-out 시 다음 핸드부터 자동 폴드 확인
    - _Requirements: 신규 - Sit-out_
  - [x] 11-1.3 Sit-in 복귀 테스트
    - Sit-out 후 Sit-in 시 다음 핸드부터 참여 확인
    - _Requirements: 신규 - Sit-out_

- [x] 12. 쇼다운(Showdown) 및 결과 분배 테스트
  - [x] 12.1 승자 표시 테스트
    - WIN 배지 표시 확인
    - _Requirements: 6.1_
  - [x] 12.2 팟 분배 테스트 (Property 4)
    - 승자 칩 스택 증가 확인
    - **Property 4: Winner Pot Distribution**
    - **Validates: Requirements 6.2**
  - [x] 12.3 쇼다운 카드 공개 테스트
    - 쇼다운 시 남은 플레이어 Hole Card 공개 확인
    - _Requirements: 5.5_
  - [x] 12.4 Rounding/Odd Chip 테스트 (2인 동점)
    - 메인 팟 501칩, 2인 동점 → A: 251칩, B: 250칩 분배 확인
    - 팟 합계와 지급 합계 일치 확인
    - _Requirements: 신규 - Odd Chip_
  - [x] 12.5 Rounding/Odd Chip 테스트 (3인 동점)
    - 100칩 3인 분배 → A: 34, B: 33, C: 33 확인
    - 남는 1칩이 Position 규칙(딜러 좌측)에 따라 분배 확인
    - _Requirements: 신규 - Odd Chip_
  - [x] 12.6 새 핸드 시작 테스트
    - 핸드 종료 후 새 핸드 시작, 칩 스택 유지 확인
    - _Requirements: 6.4_

---

## Phase 5: 안정성 및 복구

- [x] 13. 타이머 및 타임아웃(Auto-fold) 테스트
  - [x] 13.1 타이머 표시 테스트
    - 턴 시작 시 카운트다운 표시 확인
    - _Requirements: 7.1_
  - [x] 13.2 자동 폴드 테스트
    - 타임아웃 시 자동 폴드 확인
    - _Requirements: 7.2_
  - [x] 13.3 액션 후 타이머 중지 테스트
    - 액션 수행 후 타이머 사라짐 확인
    - _Requirements: 7.3_
  - [x] 13.4 서버-클라이언트 타이머 동기화 테스트
    - 서버 타이머와 클라이언트 UI 타이머 오차 ±1초 이내 확인
    - _Requirements: 신규 - 타이머 동기화_

- [x] 14. 재접속(Reconnect) 및 메시지 순서 테스트
  - [x] 14.1 브라우저 새로고침 복구 테스트
    - 게임 중 새로고침 후 상태(카드, 베팅 단계, 팟) 복구 확인
    - _Requirements: 신규 - 재접속_
  - [x] 14.2 네트워크 단절 후 재접속 테스트
    - 오프라인 → 온라인 전환 시 WebSocket 재연결 확인
    - 게임 상태 동기화 확인
    - _Requirements: 신규 - 재접속_
  - [x] 14.3 Out-of-order 메시지 처리 테스트
    - Betting_Update가 Turn_Start보다 늦게 도착해도 올바른 상태 렌더링 확인
    - 시퀀스 번호 기반 정렬 확인
    - _Requirements: 신규 - 메시지 순서_
  - [x] 14.4 재접속 후 Hole Card 복구 테스트
    - 재접속 시 내 Hole Card가 정확히 복구되는지 확인
    - _Requirements: 신규 - 재접속_

- [x] 15. 서버 재시작 및 프로세스 크래시 복구 테스트
  - [x] 15.1 서버 재시작 후 핸드 복구 테스트
    - 게임 도중 서버 재시작 → DB/Redis 스냅샷에서 핸드 복구 확인
    - _Requirements: 신규 - 서버 복구_
  - [x] 15.2 복구 후 팟 금액 유지 테스트
    - 복구 후 팟 금액이 정확히 유지되는지 확인
    - _Requirements: 신규 - 서버 복구_
  - [x] 15.3 복구 후 타이머 유지 테스트
    - 복구 후 남은 타이머가 정확히 유지되는지 확인
    - _Requirements: 신규 - 서버 복구_
  - [x] 15.4 복구 후 Hole Card 유지 테스트
    - 복구 후 플레이어들의 Hole Card가 그대로 유지되는지 확인
    - _Requirements: 신규 - 서버 복구_

- [x] 16. 부하 테스트 (Multi-Table Load)
  - [x] 16.1 다중 테이블 동시 액션 테스트
    - 10개 테이블 동시 액션 시 이벤트 누락 없음 확인
    - _Requirements: 신규 - 부하_
  - [x] 16.2 대규모 테이블 부하 테스트
    - 100개 이상 테이블 동시 운영 시 응답 시간 측정
    - _Requirements: 신규 - 부하_
  - [x] 16.3 WebSocket 연결 안정성 테스트
    - 다수 연결 시 연결 끊김 없음 확인
    - _Requirements: 신규 - 부하_

---

## Phase 6: 피망 스타일 UI/UX 테스트

- [x] 18. 족보 안내 UI 테스트 (피망 스타일)
  - [x] 18.1 홀카드 딜링 시 족보 표시 테스트
    - 홀카드 2장 받았을 때 현재 족보(하이카드/페어 등) 표시 확인
    - _Requirements: 14.1_
  - [x] 18.2 커뮤니티 카드 오픈 시 족보 업데이트 테스트
    - 플랍/턴/리버 오픈 시 족보 가이드 실시간 업데이트 확인
    - _Requirements: 14.2_
  - [x] 18.3 족보 변경 애니메이션 테스트
    - 원페어 → 투페어 등 족보 변경 시 애니메이션 확인
    - _Requirements: 14.3_
  - [x] 18.4 족보 정확성 검증 테스트
    - 치트 API로 특정 카드 주입 후 표시된 족보와 실제 족보 100% 일치 확인
    - _Requirements: 14.4_

- [x] 19. 베팅 편의 버튼 테스트 (피망 스타일)
  - [x] 19.1 1/4 Pot 버튼 계산 테스트
    - 팟 1000칩일 때 버튼 클릭 → 250칩 입력 확인
    - _Requirements: 15.1_
  - [x] 19.2 1/2 Pot 버튼 계산 테스트
    - 팟 1000칩일 때 버튼 클릭 → 500칩 입력 확인
    - _Requirements: 15.2_
  - [x] 19.3 3/4 Pot 버튼 계산 테스트
    - 팟 1000칩일 때 버튼 클릭 → 750칩 입력 확인
    - _Requirements: 15.3_
  - [x] 19.4 Pot 버튼 계산 테스트
    - 팟 1000칩일 때 버튼 클릭 → 1000칩 입력 확인
    - _Requirements: 15.4_
  - [x] 19.5 실시간 팟 변경 반영 테스트
    - 상대방 베팅으로 팟 증가 시 버튼 금액 자동 재계산 확인
    - _Requirements: 15.5_
  - [x] 19.6 스택 초과 방지 테스트
    - 계산 금액이 내 스택 초과 시 스택 금액으로 자동 조정 확인
    - _Requirements: 15.6_

- [x] 20. 쇼다운 하이라이트 테스트 (피망 스타일)
  - [x] 20.1 승리 족보 카드 하이라이트 테스트
    - 쇼다운 시 승리 족보 5장만 밝게 강조 확인
    - _Requirements: 16.1_
  - [x] 20.2 비사용 카드 딤 처리 테스트
    - 승리 족보에 사용되지 않은 카드 어둡게 처리 확인
    - _Requirements: 16.2_
  - [x] 20.3 스플릿 팟 하이라이트 테스트
    - 동점 시 각 승자의 족보 카드 개별 하이라이트 확인
    - _Requirements: 16.3_
  - [x] 20.4 하이라이트 정확성 검증 테스트
    - 치트 API로 특정 카드 주입 후 하이라이트된 카드와 실제 승리 족보 100% 일치 확인
    - _Requirements: 16.4_

- [x] 21. 카드 쪼기(Squeeze) 애니메이션 테스트
  - [x] 21.1 드래그 비례 카드 공개 테스트
    - 카드 위로 드래그 시 드래그 거리에 비례해 카드 공개 확인
    - _Requirements: 17.1_
  - [x] 21.2 임계값 초과 시 완전 뒤집기 테스트
    - 드래그 거리가 임계값 초과 시 카드 완전 뒤집힘 확인
    - _Requirements: 17.2_
  - [x] 21.3 Snap Back 테스트
    - 임계값 미만에서 손 떼면 카드가 원래 위치로 돌아감 확인
    - _Requirements: 17.3_
  - [x] 21.4 앞뒷면 전환 부드러움 테스트
    - 카드 쪼기 중 앞면/뒷면 전환이 자연스러운지 확인
    - _Requirements: 17.4_
  - [x] 21.5 UI 잠금 테스트
    - 카드 쪼기 애니메이션 중 베팅 버튼 등 다른 UI 조작 차단 확인
    - _Requirements: 17.5_
  - [x] 21.6 UI 잠금 해제 테스트
    - 카드 공개 완료 후 UI 조작 다시 가능 확인
    - _Requirements: 17.6_
  - [x] 21.7 그래픽 버그 검증 테스트
    - 다양한 드래그 각도에서 이미지 깨짐, 카드 숫자 조기 노출 없음 확인
    - _Requirements: 17.7_

---

## Phase 7: 최종 릴리즈 게이트

- [x] 22. Final Checkpoint & Security Audit
  - [x] 22.1 사이드 팟 분배 오차 검증
    - 모든 사이드 팟 테스트 통과, 오차 0% 확인
    - **Release Gate 1**
  - [x] 22.2 재접속 상태 복구 검증
    - 재접속 테스트 성공률 100% 확인
    - **Release Gate 2**
  - [x] 22.3 보안 감사: 타인 카드 정보 노출
    - 관전자/상대방에게 Hole Card 노출 0건 확인
    - WS 패킷 검사, Network 탭 분석
    - **Release Gate 3**
  - [x] 22.4 Idempotency 방어 검증
    - 중복 액션 방어 성공 확인
    - **Release Gate 4**
  - [x] 22.5 피망 스타일 UI 정확성 검증
    - 족보 가이드, 베팅 버튼, 하이라이트 100% 정확 확인
    - **Release Gate 5**
  - [x] 22.6 카드 쪼기 UX 검증
    - 모든 Squeeze 테스트 통과, 그래픽 버그 0건 확인
    - **Release Gate 6**
  - [x] 22.7 전체 테스트 스위트 실행
    - 모든 테스트 통과 확인
    - CI/CD 파이프라인 Green 상태 확인

---

## Notes

### 핵심 포인트
- **Phase 1-2**: 기반 인프라와 기본 진입 테스트 (빠른 피드백 루프)
- **Phase 3**: 멀티플레이어 상호작용의 핵심 (서버 권위, Idempotency)
- **Phase 4**: 상용급 필수 로직 (사이드 팟, Odd Chip 분배)
- **Phase 5**: 안정성 (재접속, 서버 복구, 부하)
- **Phase 6**: 피망 스타일 UI/UX (족보 가이드, 베팅 버튼, 하이라이트, 카드 쪼기)
- **Phase 7**: 릴리즈 게이트 (보안 감사 포함)

### 피망 스타일 UI/UX 테스트 포인트
- **족보 안내 UI**: 카드 오픈 시 실시간 족보 업데이트, 정확성 100%
- **베팅 편의 버튼**: 1/4, 1/2, 3/4, Pot 버튼 클릭 시 정확한 금액 계산
- **쇼다운 하이라이트**: 승리 족보 5장만 강조, 나머지 딤 처리
- **카드 쪼기(Squeeze)**: 드래그 비례 공개, Snap Back, UI 잠금

### 치트 API 활용
- 덱 주입: 특정 카드 조합 테스트 (예: 동점 상황, 특정 족보)
- 타이머 강제 종료: 타임아웃 테스트 시간 단축
- 강제 페이즈 전환: 스트리트 전환 테스트 효율화

### 테스트 실행 전 필수 조건
- 백엔드 서버 실행 중
- 테스트용 DB 초기화
- 치트 API 활성화 (개발/테스트 환경만)

### Release Gate 기준 (6개)
1. 사이드 팟 분배 오차 0%
2. 재접속 시 상태 복구 성공률 100%
3. 타인 카드 정보 노출(보안) 0건
4. 중복 액션(Idempotency) 방어 성공
5. 피망 스타일 UI 정확성 100% (족보, 베팅 버튼, 하이라이트)
6. 카드 쪼기 그래픽 버그 0건
