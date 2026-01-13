# Phase 2: 멀티플레이어 Fixture 개선 체크리스트

## 📋 개요
- **우선순위**: 높음
- **예상 소요 시간**: 3-4시간
- **상태**: ✅ 완료
- **의존성**: Phase 1 완료 필요
- **완료일**: 2026-01-13

---

## 2.1 테스트 유저 생성 개선

### 파일: `frontend/tests/e2e/utils/test-users.ts`

#### 2.1.1 UUID v4 형식으로 ID 생성 수정
- [x] 현재 코드 분석
- [x] `generateUniqueId()` 함수를 UUID v4 형식으로 수정
- [x] Format: `xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx`
- [x] 테스트 완료

---

#### 2.1.2 유저 ID 반환 형식 수정
- [x] 백엔드 회원가입 응답에서 실제 user_id 추출
- [x] 409 에러 시 로그인 시도하여 실제 ID 획득
- [x] 테스트 완료

---

#### 2.1.3 병렬 유저 생성 지원
- [x] `createTestUsers()` 함수를 Promise.all로 병렬 생성
- [x] 최대 9명까지 지원
- [x] 테스트 완료

---

#### 2.1.4 타입 안전성 개선
- [x] `any` 타입 제거
- [x] `AxiosError` 타입 사용
- [x] 테스트 완료

---

## 2.2 멀티플레이어 Fixture 개선

### 파일: `frontend/tests/e2e/fixtures/multi-player.fixture.ts`

#### 2.2.1 플레이어 세션 생성 안정화
- [x] 현재 코드 분석
- [x] 로그인 실패 시 재시도 로직 추가 (최대 3회)
- [x] 타임아웃 15초로 설정
- [x] 에러 메시지 개선
- [x] 테스트 완료

---

#### 2.2.2 setupBothPlayersAtTable 함수 개선
- [x] 현재 코드 분석
- [x] `findAvailableSeat()` 함수로 동적 좌석 탐색
- [x] 좌석 상태 확인 후 클릭 로직 추가
- [x] `waitForPlayerSeated()` 호출로 착석 확인
- [x] `SetupOptions` 인터페이스로 옵션 지원
- [x] 테스트 완료

---

#### 2.2.3 게임 시작 대기 로직 추가
- [x] `waitForGameStart` 옵션 추가 (기본값: true)
- [x] `waitForPhase('preflop')` 호출로 게임 시작 확인
- [x] 테스트 완료

---

#### 2.2.4 3인 이상 플레이어 fixture 추가
- [x] `ThreePlayerFixtures` 인터페이스 정의
- [x] `threePlayerTest` fixture 구현
- [x] `setupAllPlayersAtTable` 함수 구현
- [x] `MultiPlayerFixtures` 인터페이스 정의
- [x] `createMultiPlayerTest(n)` 팩토리 함수 구현
- [x] `fourPlayerTest`, `fivePlayerTest`, `sixPlayerTest` 추가
- [x] 테스트 완료

---

## 2.3 Wait Helper 함수 개선

### 파일: `frontend/tests/e2e/utils/wait-helpers.ts`

#### 2.3.1 타입 안전성 개선
- [x] `any` 타입 제거
- [x] Window 인터페이스 확장으로 `__gameWebSocket` 타입 정의
- [x] 테스트 완료

---

#### 2.3.2 기존 함수들 확인
- [x] `waitForPhase()` - 이미 잘 구현됨 ✅
- [x] `waitForPlayerSeated()` - 이미 잘 구현됨 ✅
- [x] `waitForTurn()` - 이미 잘 구현됨 ✅
- [x] `waitForShowdown()` - 이미 잘 구현됨 ✅
- [x] `waitForNewHand()` - 이미 잘 구현됨 ✅

---

## 2.4 테스트 스펙 파일 정리

### 파일: `frontend/tests/e2e/specs/table/*.spec.ts`

#### 2.4.1 multiplayer.spec.ts 정리
- [x] 사용하지 않는 import 제거 (`test`, `waitForTurn`)
- [x] Window 인터페이스 확장 추가
- [x] `any` 타입 제거
- [x] 테스트 완료

---

#### 2.4.2 seating.spec.ts 정리
- [x] 사용하지 않는 import 제거 (`test`, `LobbyPage`)
- [x] 테스트 완료

---

## ✅ Phase 2 완료 체크포인트

```bash
# 멀티플레이어 테스트 실행
cd frontend
npm run test:e2e -- --grep "multiplayer" --project=chromium

# 착석 테스트 실행
npm run test:e2e -- --grep "seating" --project=chromium
```

---

## 📝 작업 노트

### 완료된 주요 변경사항

1. **test-users.ts**
   - UUID v4 형식 생성 함수로 변경
   - 병렬 유저 생성 지원
   - 타입 안전성 개선 (AxiosError 사용)

2. **multi-player.fixture.ts**
   - 전면 재작성
   - 재시도 로직 추가 (최대 3회)
   - 동적 좌석 탐색 기능
   - 게임 시작 대기 옵션
   - 3-6인 플레이어 fixture 추가
   - SetupOptions 인터페이스로 유연한 설정

3. **wait-helpers.ts**
   - Window 인터페이스 확장으로 타입 안전성 개선

4. **테스트 스펙 파일**
   - 사용하지 않는 import 정리
   - 타입 오류 수정
