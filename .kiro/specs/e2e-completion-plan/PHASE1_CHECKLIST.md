# Phase 1: 백엔드 치트 API 완성 체크리스트

## 📋 개요
- **우선순위**: 높음
- **예상 소요 시간**: 4-6시간
- **상태**: ✅ 완료

---

## 1.1 게임 매니저 치트 기능 구현

### 파일: `backend/app/game/manager.py`

#### 1.1.1 create_table_sync() 메서드 확인/수정
- [x] 메서드 존재 여부 확인
- [x] 동기적 테이블 생성 로직 구현
- [x] 반환값 확인 (Table 객체)
- [x] 테스트 완료

---

#### 1.1.2 reset_table() 메서드 확인/수정
- [x] 메서드 존재 여부 확인
- [x] 테이블 상태 완전 초기화 로직
- [x] 모든 플레이어 제거 로직
- [x] 게임 상태 리셋 로직
- [x] 테스트 완료

---

#### 1.1.3 force_phase_change() 메서드 추가
- [x] 메서드 시그니처 정의
- [x] 페이즈 전환 로직 구현 (preflop → flop → turn → river → showdown)
- [x] 커뮤니티 카드 자동 생성 로직
- [x] WebSocket 브로드캐스트 연동
- [x] 테스트 완료

---

#### 1.1.4 inject_cards() 메서드 추가
- [x] 메서드 시그니처 정의
- [x] 플레이어 카드 주입 로직
- [x] 커뮤니티 카드 설정 로직
- [x] 다음 핸드에서 주입된 카드 사용하도록 구현
- [x] 테스트 완료

---

#### 1.1.5 force_pot() 메서드 추가
- [x] 메서드 시그니처 정의
- [x] 메인 팟 설정 로직
- [x] 사이드 팟 설정 로직
- [x] 테스트 완료

---

#### 1.1.6 start_hand_immediately() 메서드 추가
- [x] 메서드 시그니처 정의
- [x] 즉시 핸드 시작 로직
- [x] 주입된 카드 적용 로직
- [x] 테스트 완료

---

#### 1.1.7 add_bot_player() 메서드 추가
- [x] 메서드 시그니처 정의
- [x] 봇 플레이어 생성 로직
- [x] 자동 착석 로직
- [x] 봇 전략 저장 로직
- [x] 테스트 완료

---

#### 1.1.8 force_action() 메서드 추가
- [x] 메서드 시그니처 정의
- [x] 플레이어 액션 강제 실행 로직
- [x] 테스트 완료

---

#### 1.1.9 force_timeout() 메서드 추가
- [x] 메서드 시그니처 정의
- [x] 타임아웃 강제 실행 (자동 폴드)
- [x] 테스트 완료

---

#### 1.1.10 set_timer() 메서드 추가
- [x] 메서드 시그니처 정의
- [x] 타이머 값 설정 로직
- [x] 일시정지 기능
- [x] 테스트 완료

---

#### 1.1.11 get_table_full_state() 메서드 추가
- [x] 메서드 시그니처 정의
- [x] 전체 테이블 상태 반환 로직
- [x] 테스트 완료

---

## 1.2 치트 API 엔드포인트 실제 동작 구현

### 파일: `backend/app/api/dev.py`

#### 1.2.1 /tables/{table_id}/force-phase 실제 구현
- [x] 현재 코드 분석
- [x] GameManager.force_phase_change() 호출 연동
- [x] 에러 핸들링 추가
- [x] WebSocket 브로드캐스트 연동
- [x] 테스트 완료

---

#### 1.2.2 /tables/{table_id}/inject-deck 실제 구현
- [x] 현재 코드 분석
- [x] GameManager.inject_cards() 호출 연동
- [x] 카드 형식 검증 추가
- [x] 테스트 완료

---

#### 1.2.3 /tables/{table_id}/force-pot 실제 구현
- [x] 현재 코드 분석
- [x] 팟 금액 즉시 변경 로직
- [x] WebSocket 브로드캐스트 연동
- [x] 테스트 완료

---

#### 1.2.4 /tables/{table_id}/start-hand 실제 구현
- [x] 현재 코드 분석
- [x] 즉시 새 핸드 시작 로직
- [x] 최소 플레이어 수 체크 (2명 이상)
- [x] WebSocket 브로드캐스트 연동
- [x] 테스트 완료

---

#### 1.2.5 /tables/{table_id}/add-bot 실제 구현
- [x] 현재 코드 분석
- [x] 봇 플레이어 생성 로직
- [x] 자동 착석 로직
- [x] WebSocket 브로드캐스트 연동
- [x] 테스트 완료

---

#### 1.2.6 /tables/{table_id}/force-action 실제 구현
- [x] 현재 코드 분석
- [x] GameManager.force_action() 호출 연동
- [x] WebSocket 브로드캐스트 연동
- [x] 테스트 완료

---

#### 1.2.7 /tables/{table_id}/force-timeout 실제 구현
- [x] 현재 코드 분석
- [x] GameManager.force_timeout() 호출 연동
- [x] WebSocket 브로드캐스트 연동
- [x] 테스트 완료

---

#### 1.2.8 /tables/{table_id}/set-timer 실제 구현
- [x] 현재 코드 분석
- [x] GameManager.set_timer() 호출 연동
- [x] WebSocket 브로드캐스트 연동
- [x] 테스트 완료

---

## 1.3 WebSocket 브로드캐스트 연동

### 파일: `backend/app/api/dev.py`

#### 1.3.1 브로드캐스트 헬퍼 함수 추가
- [x] broadcast_to_table() 함수 구현
- [x] broadcast_table_state_update() 함수 구현
- [x] broadcast_community_cards() 함수 구현
- [x] broadcast_turn_prompt() 함수 구현

---

#### 1.3.2 치트 API 호출 시 WebSocket 브로드캐스트
- [x] force-phase 엔드포인트 브로드캐스트 연동
- [x] force-showdown 엔드포인트 브로드캐스트 연동
- [x] start-hand 엔드포인트 브로드캐스트 연동
- [x] force-action 엔드포인트 브로드캐스트 연동
- [x] force-pot 엔드포인트 브로드캐스트 연동
- [x] add-bot 엔드포인트 브로드캐스트 연동
- [x] force-timeout 엔드포인트 브로드캐스트 연동
- [x] set-timer 엔드포인트 브로드캐스트 연동

---

#### 1.3.3 강제 페이즈 변경 시 이벤트 발송
- [x] TABLE_STATE_UPDATE 이벤트 발송 로직
- [x] COMMUNITY_CARDS 이벤트 발송 로직
- [x] TURN_PROMPT 이벤트 발송 로직
- [x] 테스트 완료

---

## ✅ Phase 1 완료 체크포인트

```bash
# 1. 테이블 생성
TABLE_ID=$(curl -s -X POST -H "X-Dev-Key: dev-key" \
  -H "Content-Type: application/json" \
  -d '{"small_blind": 10, "big_blind": 20}' \
  http://localhost:8000/api/dev/tables/create | jq -r '.data.table_id')

# 2. 봇 추가
curl -X POST -H "X-Dev-Key: dev-key" \
  -H "Content-Type: application/json" \
  -d '{"stack": 1000}' \
  http://localhost:8000/api/dev/tables/$TABLE_ID/add-bot

curl -X POST -H "X-Dev-Key: dev-key" \
  -H "Content-Type: application/json" \
  -d '{"stack": 1000}' \
  http://localhost:8000/api/dev/tables/$TABLE_ID/add-bot

# 3. 핸드 시작
curl -X POST -H "X-Dev-Key: dev-key" \
  http://localhost:8000/api/dev/tables/$TABLE_ID/start-hand

# 4. 페이즈 전환
curl -X POST -H "X-Dev-Key: dev-key" \
  -H "Content-Type: application/json" \
  -d '{"phase": "flop"}' \
  http://localhost:8000/api/dev/tables/$TABLE_ID/force-phase

# 5. 상태 확인
curl -H "X-Dev-Key: dev-key" \
  http://localhost:8000/api/dev/tables/$TABLE_ID/state

# 6. 타이머 설정
curl -X POST -H "X-Dev-Key: dev-key" \
  -H "Content-Type: application/json" \
  -d '{"remaining_seconds": 10}' \
  http://localhost:8000/api/dev/tables/$TABLE_ID/set-timer

# 7. 강제 타임아웃
curl -X POST -H "X-Dev-Key: dev-key" \
  -H "Content-Type: application/json" \
  -d '{}' \
  http://localhost:8000/api/dev/tables/$TABLE_ID/force-timeout
```

---

## 📝 작업 노트

### 2025-01-13 완료된 작업:

1. **GameManager 메서드 추가** (`backend/app/game/manager.py`):
   - `force_phase_change()` - 페이즈 강제 전환 (커뮤니티 카드 자동 생성)
   - `inject_cards()` - 홀카드/커뮤니티 카드 주입
   - `force_pot()` - 팟 금액 강제 설정
   - `start_hand_immediately()` - 즉시 핸드 시작
   - `add_bot_player()` - 봇 플레이어 추가
   - `force_action()` - 플레이어 액션 강제 실행
   - `force_timeout()` - 타임아웃 강제 (자동 폴드)
   - `set_timer()` - 타이머 값 설정
   - `get_table_full_state()` - 디버깅용 전체 상태 조회

2. **치트 API 엔드포인트 실제 구현** (`backend/app/api/dev.py`):
   - 모든 엔드포인트가 실제 GameManager 메서드를 호출하도록 구현
   - WebSocket 브로드캐스트 연동 완료

3. **WebSocket 브로드캐스트 헬퍼 함수** (`backend/app/api/dev.py`):
   - `broadcast_to_table()` - 테이블 채널로 메시지 브로드캐스트
   - `broadcast_table_state_update()` - TABLE_STATE_UPDATE 이벤트 발송
   - `broadcast_community_cards()` - COMMUNITY_CARDS 이벤트 발송
   - `broadcast_turn_prompt()` - TURN_PROMPT 이벤트 발송

### 브로드캐스트 이벤트 매핑:
- `force-phase` → TABLE_STATE_UPDATE + COMMUNITY_CARDS + TURN_PROMPT
- `force-showdown` → TABLE_STATE_UPDATE + COMMUNITY_CARDS
- `start-hand` → HAND_STARTED + TURN_PROMPT
- `force-action` → TABLE_STATE_UPDATE + COMMUNITY_CARDS (페이즈 변경 시) + TURN_PROMPT
- `force-pot` → TABLE_STATE_UPDATE
- `add-bot` → TABLE_STATE_UPDATE
- `force-timeout` → TABLE_STATE_UPDATE + TURN_PROMPT
- `set-timer` → TURN_PROMPT (업데이트된 타이머 정보)
