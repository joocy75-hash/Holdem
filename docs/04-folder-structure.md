# 프로젝트 폴더 구조

> PokerKit 기반 텍사스 홀덤 웹서비스 권장 디렉토리 구조

---

## 전체 구조

```
pokerkit-holdem/
├── backend/                    # 백엔드 서버
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI 엔트리포인트
│   │   ├── config.py          # 설정 관리
│   │   ├── api/               # REST API 라우터
│   │   │   ├── __init__.py
│   │   │   ├── auth.py        # 인증 API
│   │   │   ├── rooms.py       # 방 관리 API
│   │   │   ├── users.py       # 유저 API
│   │   │   └── history.py     # 핸드 히스토리 API
│   │   ├── ws/                # WebSocket 핸들러
│   │   │   ├── __init__.py
│   │   │   ├── gateway.py     # WS 게이트웨이
│   │   │   ├── lobby.py       # 로비 채널
│   │   │   └── table.py       # 테이블 채널
│   │   ├── engine/            # 게임 엔진 레이어
│   │   │   ├── __init__.py
│   │   │   ├── core.py        # PokerKit 래퍼
│   │   │   ├── state.py       # 상태 모델
│   │   │   ├── actions.py     # 액션 처리
│   │   │   └── snapshot.py    # 스냅샷 직렬화
│   │   ├── orchestrator/      # 테이블 오케스트레이터
│   │   │   ├── __init__.py
│   │   │   ├── table.py       # 테이블 관리
│   │   │   └── hand.py        # 핸드 관리
│   │   ├── models/            # DB 모델 (SQLAlchemy)
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── room.py
│   │   │   ├── table.py
│   │   │   ├── hand.py
│   │   │   └── audit.py
│   │   ├── schemas/           # Pydantic 스키마
│   │   │   ├── __init__.py
│   │   │   ├── events.py      # WS 이벤트 스키마
│   │   │   ├── requests.py    # API 요청 스키마
│   │   │   └── responses.py   # API 응답 스키마
│   │   ├── services/          # 비즈니스 로직
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── room.py
│   │   │   └── user.py
│   │   └── utils/             # 유틸리티
│   │       ├── __init__.py
│   │       ├── redis.py       # Redis 클라이언트
│   │       ├── db.py          # DB 연결
│   │       └── logging.py     # 구조화 로깅
│   ├── tests/                 # 테스트
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   ├── alembic/               # DB 마이그레이션
│   │   ├── versions/
│   │   └── env.py
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── pyproject.toml
│   └── Dockerfile
│
├── frontend/                   # 프론트엔드
│   ├── src/
│   │   ├── app/               # Next.js App Router
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx       # 랜딩/로그인
│   │   │   ├── lobby/
│   │   │   │   └── page.tsx
│   │   │   ├── table/
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx
│   │   │   └── profile/
│   │   │       └── page.tsx
│   │   ├── components/        # UI 컴포넌트
│   │   │   ├── common/        # 공통 컴포넌트
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Modal.tsx
│   │   │   │   ├── Toast.tsx
│   │   │   │   └── Loading.tsx
│   │   │   ├── lobby/         # 로비 컴포넌트
│   │   │   │   ├── RoomList.tsx
│   │   │   │   ├── RoomCard.tsx
│   │   │   │   └── CreateRoomModal.tsx
│   │   │   ├── table/         # 테이블 컴포넌트
│   │   │   │   ├── Table.tsx
│   │   │   │   ├── Seat.tsx
│   │   │   │   ├── ActionPanel.tsx
│   │   │   │   ├── PotDisplay.tsx
│   │   │   │   ├── CommunityCards.tsx
│   │   │   │   └── Timer.tsx
│   │   │   └── layout/        # 레이아웃
│   │   │       ├── Header.tsx
│   │   │       ├── ConnectionBanner.tsx
│   │   │       └── Footer.tsx
│   │   ├── hooks/             # 커스텀 훅
│   │   │   ├── useWebSocket.ts
│   │   │   ├── useLobby.ts
│   │   │   ├── useTable.ts
│   │   │   └── useAuth.ts
│   │   ├── stores/            # 상태 관리 (Zustand)
│   │   │   ├── authStore.ts
│   │   │   ├── lobbyStore.ts
│   │   │   └── tableStore.ts
│   │   ├── lib/               # 유틸리티
│   │   │   ├── api.ts         # REST API 클라이언트
│   │   │   ├── ws.ts          # WebSocket 클라이언트
│   │   │   └── constants.ts
│   │   ├── types/             # TypeScript 타입
│   │   │   ├── events.ts      # WS 이벤트 타입
│   │   │   ├── game.ts        # 게임 상태 타입
│   │   │   └── api.ts         # API 타입
│   │   └── styles/            # 스타일
│   │       └── globals.css
│   ├── public/                # 정적 파일
│   │   ├── cards/             # 카드 이미지
│   │   └── sounds/            # 효과음
│   ├── tests/                 # 테스트
│   │   ├── components/
│   │   └── e2e/
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   └── Dockerfile
│
├── infra/                      # 인프라 설정
│   ├── docker/
│   │   ├── docker-compose.yml
│   │   ├── docker-compose.dev.yml
│   │   └── docker-compose.prod.yml
│   ├── nginx/
│   │   └── nginx.conf
│   ├── scripts/
│   │   ├── init-db.sh
│   │   └── deploy.sh
│   └── k8s/                   # (선택) Kubernetes
│       ├── deployment.yaml
│       └── service.yaml
│
├── docs/                       # 문서
│   ├── 01-setup-local.md
│   ├── 02-env-vars.md
│   ├── 03-dev-workflow.md
│   ├── 04-folder-structure.md  # 이 문서
│   ├── 10-engine-architecture.md
│   ├── 11-engine-state-model.md
│   ├── 20-realtime-protocol-v1.md
│   ├── 21-error-codes-v1.md
│   ├── 22-idempotency-ordering.md
│   ├── 30-ui-ia.md
│   ├── 31-table-ui-spec.md
│   ├── 32-lobby-ui-spec.md
│   ├── 33-ui-components.md
│   ├── 40-reconnect-recovery.md
│   ├── 41-state-consistency.md
│   ├── 42-timer-turn-rules.md
│   ├── 50-test-plan.md
│   ├── 51-observability.md
│   ├── 52-deploy-staging.md
│   ├── 60-license-audit.md
│   ├── 61-third-party-assets.md
│   └── ADR/                   # Architecture Decision Records
│       └── ADR-0001-pokerkit-core.md
│
├── .github/                    # GitHub 설정
│   └── workflows/
│       ├── ci.yml
│       └── deploy.yml
│
├── .env.example               # 환경변수 예시
├── .gitignore
├── README.md
├── PROGRESS_CHECKPOINT.md     # 진행 체크포인트
└── WORKPLAN_*.md              # 작업계획서
```

---

## 디렉토리 설명

### backend/

| 디렉토리 | 역할 |
|---------|------|
| `api/` | REST API 엔드포인트 (인증, 방 관리, 히스토리) |
| `ws/` | WebSocket 게이트웨이 및 채널 핸들러 |
| `engine/` | PokerKit 래퍼, 게임 상태/액션 관리 |
| `orchestrator/` | 테이블/핸드 라이프사이클 관리 |
| `models/` | SQLAlchemy ORM 모델 |
| `schemas/` | Pydantic 요청/응답/이벤트 스키마 |
| `services/` | 비즈니스 로직 레이어 |
| `utils/` | Redis, DB, 로깅 등 유틸리티 |

### frontend/

| 디렉토리 | 역할 |
|---------|------|
| `app/` | Next.js App Router 페이지 |
| `components/` | 재사용 가능한 UI 컴포넌트 |
| `hooks/` | WebSocket, 상태 관리 커스텀 훅 |
| `stores/` | Zustand 전역 상태 |
| `lib/` | API/WS 클라이언트, 상수 |
| `types/` | TypeScript 타입 정의 |

### infra/

| 디렉토리 | 역할 |
|---------|------|
| `docker/` | Docker Compose 설정 (dev/prod) |
| `nginx/` | 리버스 프록시 설정 |
| `scripts/` | 배포/초기화 스크립트 |
| `k8s/` | (선택) Kubernetes 매니페스트 |

---

## 모듈 경계 원칙

1. **engine/** - 순수 게임 로직, 외부 의존성 최소화
2. **orchestrator/** - 엔진 + 실시간 통신 조율
3. **api/** - REST 엔드포인트, 인증/권한 처리
4. **ws/** - WebSocket 연결 관리, 이벤트 라우팅

```
[Client] → [ws/gateway] → [orchestrator] → [engine/core]
                                              ↓
                                         [PokerKit]
```

---

## 파일 네이밍 규칙

| 구분 | 규칙 | 예시 |
|------|------|------|
| Python 모듈 | snake_case | `hand_history.py` |
| TypeScript 컴포넌트 | PascalCase | `ActionPanel.tsx` |
| TypeScript 유틸 | camelCase | `useWebSocket.ts` |
| 문서 | 번호-kebab-case | `01-setup-local.md` |
| ADR | ADR-번호-제목 | `ADR-0001-pokerkit-core.md` |

---

## 관련 문서

- [01-setup-local.md](./01-setup-local.md) - 로컬 환경 셋업
- [02-env-vars.md](./02-env-vars.md) - 환경변수 설명
- [03-dev-workflow.md](./03-dev-workflow.md) - 개발 워크플로
