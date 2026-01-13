# Holdem 프로젝트 전체 문서

> **목적**: 다음 개발자 및 Claude Code가 프로젝트를 빠르게 파악할 수 있도록 작성된 종합 문서

---

## 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [기술 스택](#2-기술-스택)
3. [디렉토리 구조](#3-디렉토리-구조)
4. [백엔드 아키텍처](#4-백엔드-아키텍처)
5. [게임 엔진](#5-게임-엔진)
6. [WebSocket 실시간 통신](#6-websocket-실시간-통신)
7. [프론트엔드 아키텍처](#7-프론트엔드-아키텍처)
8. [데이터베이스 스키마](#8-데이터베이스-스키마)
9. [API 엔드포인트](#9-api-엔드포인트)
10. [게임 플로우](#10-게임-플로우)
11. [설정 및 환경변수](#11-설정-및-환경변수)
12. [개발 가이드](#12-개발-가이드)
13. [알려진 이슈 및 TODO](#13-알려진-이슈-및-todo)

---

## 1. 프로젝트 개요

### 1.1 프로젝트 설명
온라인 텍사스 홀덤 포커 게임 플랫폼. 실시간 멀티플레이어 게임을 지원하며, 봇 플레이어와 함께 플레이 가능.

### 1.2 주요 기능
- **실시간 포커 게임**: 최대 9인 테이블, 텍사스 홀덤 규칙
- **WebSocket 기반 통신**: 실시간 게임 상태 동기화
- **봇 시스템**: AI 봇 플레이어 (보수적 전략)
- **지갑 시스템**: KRW 잔액 관리, 암호화폐 입출금 (구조만 존재)
- **인증 시스템**: JWT 기반 인증, 세션 관리

### 1.3 현재 상태
- **작동하는 기능**: 로그인/회원가입, 로비, 테이블 생성/참여, 실시간 게임 플레이, 봇
- **미완성 기능**: 토너먼트, 지갑 입출금, VIP 시스템

---

## 2. 기술 스택

### 2.1 백엔드
| 기술 | 버전 | 용도 |
|------|------|------|
| Python | 3.11+ | 런타임 |
| FastAPI | - | 웹 프레임워크 |
| SQLAlchemy | 2.0 | ORM (async) |
| PostgreSQL | - | 데이터베이스 |
| Redis | - | 캐시, pub/sub, 세션 |
| PokerKit | - | 포커 게임 엔진 |
| Pydantic | v2 | 데이터 검증 |
| orjson | - | 고속 JSON |

### 2.2 프론트엔드
| 기술 | 버전 | 용도 |
|------|------|------|
| Next.js | 16.1.1 | App Router |
| React | 19.2.3 | UI |
| TypeScript | 5+ | 타입 안전성 |
| Tailwind CSS | 4 | 스타일링 |
| Zustand | 5.0.10 | 상태 관리 |
| Axios | 1.13.2 | HTTP 클라이언트 |

---

## 3. 디렉토리 구조

### 3.1 백엔드
```
backend/
├── app/
│   ├── main.py                 # FastAPI 앱 진입점
│   ├── config.py               # 환경설정
│   │
│   ├── api/                    # REST API 라우터
│   │   ├── auth.py             # 인증 (/auth/*)
│   │   ├── rooms.py            # 게임실 (/rooms/*)
│   │   ├── users.py            # 사용자 (/users/*)
│   │   ├── wallet.py           # 지갑 (/wallet/*)
│   │   └── deps.py             # 의존성 (인증, DB 세션)
│   │
│   ├── models/                 # SQLAlchemy 모델
│   │   ├── user.py             # User, Session
│   │   ├── room.py             # Room
│   │   ├── table.py            # Table
│   │   ├── hand.py             # Hand, HandEvent
│   │   └── wallet.py           # WalletTransaction
│   │
│   ├── schemas/                # Pydantic 스키마
│   │   ├── common.py           # 공통 (BaseSchema, Error)
│   │   ├── requests.py         # 요청 스키마
│   │   └── responses.py        # 응답 스키마
│   │
│   ├── services/               # 비즈니스 로직
│   │   ├── auth.py             # 인증 서비스
│   │   ├── room.py             # 게임실 서비스
│   │   ├── game.py             # 게임 서비스
│   │   └── wallet.py           # 지갑 서비스
│   │
│   ├── game/                   # 게임 엔진 (현재 사용)
│   │   ├── poker_table.py      # PokerTable 클래스
│   │   └── manager.py          # GameManager 싱글톤
│   │
│   ├── engine/                 # 새 엔진 (마이그레이션 중)
│   │   ├── core.py             # PokerKitWrapper
│   │   ├── state.py            # 불변 상태 모델
│   │   └── snapshot.py         # 상태 직렬화
│   │
│   ├── ws/                     # WebSocket
│   │   ├── gateway.py          # WS 엔드포인트
│   │   ├── manager.py          # ConnectionManager
│   │   ├── events.py           # 이벤트 타입 (39개)
│   │   ├── messages.py         # 메시지 구조
│   │   └── handlers/           # 이벤트 핸들러
│   │       ├── system.py       # PING/PONG
│   │       ├── lobby.py        # 로비/방 관리
│   │       ├── table.py        # 테이블/좌석
│   │       ├── action.py       # 게임 액션
│   │       └── chat.py         # 채팅
│   │
│   ├── cache/                  # Redis 캐싱
│   ├── middleware/             # HTTP 미들웨어
│   └── utils/                  # 유틸리티
│
├── alembic/                    # DB 마이그레이션
├── tests/                      # 테스트
└── requirements.txt
```

### 3.2 프론트엔드
```
frontend/src/
├── app/                        # Next.js App Router
│   ├── layout.tsx              # Root 레이아웃
│   ├── page.tsx                # 홈 (리다이렉트)
│   ├── login/page.tsx          # 로그인/회원가입
│   ├── lobby/page.tsx          # 로비
│   ├── table/[id]/page.tsx     # 게임 테이블 (핵심)
│   ├── bot-test/page.tsx       # 봇 테스트 (개발용)
│   └── globals.css             # 전역 스타일
│
├── components/                 # 재사용 컴포넌트
│   └── lobby/                  # 로비 UI
│
├── lib/                        # 유틸리티
│   ├── api.ts                  # Axios 클라이언트
│   ├── websocket.ts            # WebSocket 클라이언트
│   └── handEvaluator.ts        # 족보 계산
│
└── stores/                     # Zustand 상태
    ├── auth.ts                 # 인증
    └── game.ts                 # 게임/테이블
```

---

## 4. 백엔드 아키텍처

### 4.1 레이어 구조
```
┌─────────────────────────────────────┐
│           API Layer                 │  ← REST 라우터 (api/)
│         (FastAPI Routers)           │
├─────────────────────────────────────┤
│         Service Layer               │  ← 비즈니스 로직 (services/)
│    (AuthService, RoomService, ...)  │
├─────────────────────────────────────┤
│          Data Layer                 │  ← ORM 모델 (models/)
│   (SQLAlchemy Models, Redis)        │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│        WebSocket Layer              │  ← 실시간 통신 (ws/)
│   (Gateway → Handlers → Manager)    │
├─────────────────────────────────────┤
│         Game Engine                 │  ← 게임 로직 (game/)
│   (PokerTable, GameManager)         │
└─────────────────────────────────────┘
```

### 4.2 주요 서비스

#### AuthService (`services/auth.py`)
- 회원가입/로그인
- JWT 토큰 발급/검증
- 세션 관리

#### RoomService (`services/room.py`)
- 게임실 CRUD
- 플레이어 참여/퇴장
- 페이지네이션

#### GameManager (`game/manager.py`)
- 메모리 기반 테이블 관리
- 싱글톤 패턴 (`game_manager`)
- 테이블 생성/조회/삭제

---

## 5. 게임 엔진

### 5.1 PokerTable 클래스 (`game/poker_table.py`)

**역할**: 메모리에서 게임 상태 관리, PokerKit 라이브러리 래핑

**핵심 속성**:
```python
class PokerTable:
    room_id: str
    players: Dict[int, Player]      # 좌석별 플레이어
    phase: GamePhase                # WAITING/PREFLOP/FLOP/TURN/RIVER/SHOWDOWN
    pot: int
    community_cards: List[str]
    current_player_seat: int
    _state: PokerKit.State          # PokerKit 내부 상태
```

**핵심 메서드**:
| 메서드 | 설명 |
|--------|------|
| `seat_player(seat, player)` | 플레이어 착석 |
| `remove_player(seat)` | 플레이어 퇴장 |
| `start_new_hand()` | 핸드 시작 (딜링, 블라인드) |
| `process_action(user_id, action, amount)` | 액션 처리 |
| `get_available_actions(user_id)` | 가능한 액션 조회 |
| `get_state_for_player(user_id)` | 플레이어 관점 상태 |

### 5.2 게임 진행 흐름

```
[WAITING]
    ↓ START_GAME (최소 2명)
[PREFLOP]
    - 홀카드 배분 (2장씩)
    - 블라인드 포스팅
    - 액션 (UTG부터)
    ↓ 모두 동일 베팅
[FLOP]
    - 커뮤니티 카드 3장
    - 액션 (딜러 왼쪽부터)
    ↓
[TURN]
    - 커뮤니티 카드 1장
    - 액션
    ↓
[RIVER]
    - 커뮤니티 카드 1장
    - 액션
    ↓
[SHOWDOWN]
    - 카드 오픈
    - 승자 결정
    - 팟 배분
    ↓
[WAITING] (5초 후 자동 다음 핸드)
```

### 5.3 좌석 배치 (9인 테이블)

```
        [7]       [8]
    [5]               [6]
    [3]               [4]
    [1]               [2]
            [0]
          (ME)

시계방향 순서: 0 → 1 → 3 → 5 → 7 → 8 → 6 → 4 → 2
```

### 5.4 봇 시스템

**봇 감지**:
```python
def is_bot_player(player):
    return player.is_bot or player.user_id.startswith("bot_")
```

**봇 전략** (보수적):
1. 체크 가능 → 체크
2. 콜 금액 ≤ 스택 30% 또는 80% 확률 → 콜
3. 15% 확률로 최소 레이즈
4. 나머지 → 폴드

**봇 생각 시간**: 2-7초 (평균 3초)

---

## 6. WebSocket 실시간 통신

### 6.1 연결 흐름

```
클라이언트 ─[WebSocket]→ 서버
         ←[5초 대기]─
클라이언트 ─[AUTH {token}]→
         ←[CONNECTION_STATE]─ (연결 완료)
```

### 6.2 메시지 포맷

**클라이언트 → 서버**:
```json
{
  "type": "ACTION_REQUEST",
  "payload": { "actionType": "raise", "amount": 100 }
}
```

**서버 → 클라이언트**:
```json
{
  "type": "ACTION_RESULT",
  "ts": 1673500000000,
  "traceId": "uuid",
  "payload": { "success": true }
}
```

### 6.3 주요 이벤트

| 그룹 | 이벤트 | 방향 | 설명 |
|------|--------|------|------|
| **시스템** | PING/PONG | 양방향 | 하트비트 |
| **로비** | SUBSCRIBE_LOBBY | C→S | 로비 구독 |
| | LOBBY_SNAPSHOT | S→C | 방 목록 |
| **테이블** | SUBSCRIBE_TABLE | C→S | 테이블 구독 |
| | TABLE_SNAPSHOT | S→C | 테이블 상태 |
| | TABLE_STATE_UPDATE | S→C | 상태 변경 |
| | SEAT_REQUEST | C→S | 좌석 요청 |
| | TURN_PROMPT | S→C | 턴 알림 |
| **게임** | START_GAME | C→S | 게임 시작 |
| | ACTION_REQUEST | C→S | 액션 (폴드/콜/레이즈) |
| | HAND_RESULT | S→C | 핸드 결과 |

### 6.4 채널 시스템

| 채널 | 용도 |
|------|------|
| `lobby` | 로비 업데이트 (방 목록) |
| `table:{room_id}` | 특정 테이블 업데이트 |

### 6.5 핸들러 구조

```
Gateway (ws/gateway.py)
    ↓ 이벤트 라우팅
┌─────────────────────────────────┐
│ SystemHandler  → PING/PONG     │
│ LobbyHandler   → 로비/방 관리   │
│ TableHandler   → 좌석/퇴장     │
│ ActionHandler  → 게임 액션     │  ← 핵심!
│ ChatHandler    → 채팅          │
└─────────────────────────────────┘
    ↓ 브로드캐스트
ConnectionManager (ws/manager.py)
```

---

## 7. 프론트엔드 아키텍처

### 7.1 페이지 구조

| 경로 | 설명 |
|------|------|
| `/` | 인증 확인 → 리다이렉트 |
| `/login` | 로그인/회원가입 |
| `/lobby` | 테이블 목록, 참여 |
| `/table/[id]` | 게임 플레이 (핵심) |
| `/bot-test` | 봇 관리 (개발용) |

### 7.2 상태 관리 (Zustand)

**AuthStore**:
```typescript
{
  user: User | null
  isAuthenticated: boolean
  login(email, password): Promise<void>
  logout(): Promise<void>
}
```

**GameStore**:
```typescript
{
  tables: Table[]
  seatedRoomIds: string[]
  fetchTables(): Promise<void>
  joinTable(tableId, buyIn): Promise<void>
}
```

### 7.3 WebSocket 클라이언트 (`lib/websocket.ts`)

- **싱글톤**: `wsClient`
- **자동 재연결**: 지수 백오프 (최대 5회)
- **핑 유지**: 30초마다

```typescript
wsClient.connect(token)
wsClient.send(event, data)
wsClient.on(event, handler)
```

### 7.4 게임 테이블 페이지 (`table/[id]/page.tsx`)

**~1800줄의 핵심 페이지**

**주요 기능**:
- WebSocket 연결 및 이벤트 처리
- 9인 좌석 렌더링 (PlayerSeat 컴포넌트)
- 액션 버튼 (폴드/체크/콜/베팅/레이즈)
- 턴 타이머 (5초 대기 + 5초 카운트다운)
- 쇼다운 결과 표시

**컴포넌트**:
- `PlayerSeat`: 플레이어 정보, 카드, 타이머
- `PlayingCard`: 카드 렌더링
- `BuyInModal`: 바이인 입력

---

## 8. 데이터베이스 스키마

### 8.1 User
```sql
User
├── id (UUID, PK)
├── email (unique)
├── password_hash
├── nickname (unique)
├── balance / krw_balance
├── status (active/suspended/deleted)
└── created_at, updated_at
```

### 8.2 Room
```sql
Room
├── id (UUID, PK)
├── name
├── owner_id (FK → User)
├── config (JSONB)
│   ├── max_seats, small_blind, big_blind
│   └── buy_in_min, buy_in_max
├── status (waiting/playing/closed)
└── current_players
```

### 8.3 Table
```sql
Table
├── id (UUID, PK)
├── room_id (FK → Room)
├── seats (JSONB)
│   └── {"0": {user_id, stack}, "1": null, ...}
├── game_state (JSONB)
│   └── {phase, pot, community_cards, ...}
└── hand_number
```

### 8.4 Hand / HandEvent
```sql
Hand
├── id, table_id, hand_number
├── initial_state (JSONB)
└── result (JSONB)

HandEvent
├── id, hand_id, seq_no
├── event_type (fold/check/call/bet/raise)
└── payload (JSONB)
```

---

## 9. API 엔드포인트

### 9.1 인증 (`/api/v1/auth`)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | /register | 회원가입 |
| POST | /login | 로그인 |
| POST | /refresh | 토큰 갱신 |
| POST | /logout | 로그아웃 |

### 9.2 게임실 (`/api/v1/rooms`)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | / | 목록 조회 |
| GET | /{id} | 상세 조회 |
| POST | / | 생성 |
| POST | /{id}/join | 참여 |
| POST | /{id}/leave | 퇴장 |
| GET | /my-seats | 내 좌석 |

### 9.3 사용자 (`/api/v1/users`)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | /me | 내 정보 |
| PUT | /me | 프로필 수정 |

---

## 10. 게임 플로우

### 10.1 참여 플로우
```
[로비] 테이블 선택 → [바이인 입력] → SEAT_REQUEST
→ SEAT_RESULT → TABLE_SNAPSHOT 수신 → 게임 대기
```

### 10.2 게임 플로우
```
START_GAME → HAND_STARTED (홀카드)
→ TURN_PROMPT (턴 알림) → ACTION_REQUEST (액션)
→ ACTION_RESULT → TABLE_STATE_UPDATE
→ ... (반복)
→ HAND_RESULT (쇼다운) → [5초 대기] → 다음 핸드
```

### 10.3 봇 루프
```
_process_next_turn():
    현재 플레이어 확인
    ├─ 봇 → 자동 액션 (2-7초 대기)
    │       → 브로드캐스트 → 루프 계속
    └─ 인간 → TURN_PROMPT 전송 → 대기
```

---

## 11. 설정 및 환경변수

### 11.1 백엔드 (`backend/.env`)

```bash
# 앱
APP_ENV=development
APP_DEBUG=true
LOG_LEVEL=DEBUG

# 데이터베이스
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/holdem

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-secret-key-min-32-chars
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# 게임
DEFAULT_SMALL_BLIND=10
DEFAULT_BIG_BLIND=20
TURN_TIMEOUT_SECONDS=30

# CORS
CORS_ORIGINS=http://localhost:3000
```

### 11.2 프론트엔드 (`frontend/.env.local`)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

---

## 12. 개발 가이드

### 12.1 로컬 실행

**백엔드**:
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# DB 마이그레이션
alembic upgrade head

# 실행
uvicorn app.main:app --reload
```

**프론트엔드**:
```bash
cd frontend
npm install
npm run dev
```

### 12.2 테스트

```bash
cd backend
pytest tests/ -v
```

### 12.3 코드 규칙

- **백엔드**: snake_case
- **프론트엔드**: camelCase
- **Pydantic alias**: snake_case ↔ camelCase 변환
- 주석/에러 메시지: 한글 OK
- 변수명: 영어

---

## 13. 알려진 이슈 및 TODO

### 13.1 현재 이슈

1. **액션 모달 위치**: 아바타 wrapper로 중앙 정렬 완료
2. **턴 타이머**: 클라이언트 시간 기준으로 수정 완료
3. **폴드 버튼**: 체크 가능 시 숨김 (의도된 동작)

### 13.2 TODO

- [ ] 토너먼트 기능 구현
- [ ] 지갑 입출금 연동
- [ ] VIP 시스템
- [ ] 핸드 히스토리 조회
- [ ] 에러 바운더리 추가
- [ ] 테스트 코드 보강

### 13.3 아키텍처 마이그레이션

현재 `game/poker_table.py` (메모리 기반) 사용 중.
`engine/` (불변 상태 기반)으로 마이그레이션 계획 있음.

---

## 부록: 핵심 파일 위치

| 기능 | 파일 |
|------|------|
| 게임 로직 | `backend/app/game/poker_table.py` |
| 게임 매니저 | `backend/app/game/manager.py` |
| 액션 핸들러 | `backend/app/ws/handlers/action.py` |
| 테이블 핸들러 | `backend/app/ws/handlers/table.py` |
| WS 이벤트 정의 | `backend/app/ws/events.py` |
| 게임 테이블 UI | `frontend/src/app/table/[id]/page.tsx` |
| WS 클라이언트 | `frontend/src/lib/websocket.ts` |
| API 클라이언트 | `frontend/src/lib/api.ts` |

---

*마지막 업데이트: 2026-01-13*
