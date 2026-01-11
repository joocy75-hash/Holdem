# PokerKit 기반 텍사스 홀덤 웹서비스 상용화 작업계획서 (Claude Code용) v2.0

---

## 0. 문서 목적

본 문서는 PokerKit을 게임 엔진 코어로 채택하여, **웹 기반 실시간 멀티플레이 텍사스 홀덤 서비스(로비/테이블/관전/재접속/핸드 히스토리)**를 상용 수준의 품질로 구축하기 위한 단계별 작업계획서다.

### 핵심 원칙
- **서버 authoritative**: 판정/상태결정은 서버만 수행
- **클라이언트**: 상태 렌더링 중심
- **산출물 중심**: 구현(코드) 이전에 스펙/문서/게이트/완료정의(DoD)를 확정

### 라이선스/품질 근거
- PokerKit은 MIT License
- 정적 타입체크·doctest·unit test 기반 99% 코드 커버리지
- "온라인 포커 구현(online poker casino implementation)" 용례 직접 언급

---

## ⚠️ 세션 중단 대비 필수 지침

> **중요**: 여러 계정으로 작업 시 토큰 소진으로 인한 갑작스러운 세션 중단이 발생할 수 있습니다.
> 아래 지침을 **반드시** 준수하여 작업 손실을 방지하세요.

### 📋 진행상황 추적 규칙

1. **TodoWrite 도구 필수 사용**
   - 모든 작업 시작 전 TodoWrite로 작업 목록 생성
   - 개별 작업 완료 즉시 `completed` 상태로 변경
   - 절대 여러 작업을 묶어서 한 번에 완료 처리하지 않음

2. **작업 완료 시 즉시 커밋**
   - 각 단계(P0~P6) 완료 시 즉시 git commit
   - 커밋 메시지에 완료된 Phase 번호 명시
   - 예: `git commit -m "P1 완료: 엔진 레이어 설계 문서 작성"`

3. **체크포인트 파일 유지**
   - `PROGRESS_CHECKPOINT.md` 파일에 현재 진행 상황 기록
   - 각 Phase 완료 시 해당 파일 업데이트

### 📍 진행상황 체크포인트 템플릿

```markdown
# 작업 진행 체크포인트
최종 업데이트: [날짜/시간]

## 완료된 Phase
- [x] P0 - 레포 스캐폴딩 (완료일: YYYY-MM-DD)
- [ ] P1 - 엔진 레이어 설계
- [ ] P2 - 실시간 프로토콜 v1
- [ ] P3 - UI/UX 스펙
- [ ] P4 - 안정성 스펙
- [ ] P5 - 테스트/관측/배포
- [ ] P6 - 라이선스 감사

## 현재 작업 중
- Phase: P1
- 작업 내용: docs/10-engine-architecture.md 작성 중
- 진행률: 50%

## 다음 작업
- P1의 남은 문서 작성
```

---

## 1. Claude Code 서브에이전트 활용 가이드

Claude Code는 특수 목적 에이전트를 제공합니다. 각 Phase에 적합한 에이전트를 활용하세요.

### 1.1 주요 서브에이전트 (Task 도구)

| 에이전트 | 용도 | 활용 Phase |
|---------|------|-----------|
| `Explore` | 코드베이스 탐색, 파일 검색, 구조 파악 | P0, P1 |
| `Plan` | 구현 계획 수립, 아키텍처 설계 | P1, P2, P3 |
| `code-architect` | 기존 패턴 분석 후 아키텍처 설계 | P1, P2 |
| `code-reviewer` | 코드 리뷰, 품질 검증 | P5, P6 |
| `code-explorer` | 기능 구현 경로 추적, 의존성 분석 | P1, P4 |

### 1.2 Skill 활용 (Skill 도구)

| Skill | 명령어 | 용도 |
|-------|--------|------|
| `commit` | `/commit` | git 커밋 생성 |
| `commit-push-pr` | `/commit-push-pr` | 커밋, 푸시, PR 한 번에 |
| `feature-dev` | `/feature-dev` | 가이드 기반 기능 개발 |
| `code-review` | `/code-review` | PR 코드 리뷰 |
| `review-pr` | `/review-pr` | 종합 PR 리뷰 |

### 1.3 Phase별 서브에이전트 활용 권장

```
P0 (스캐폴딩)
├── Explore: 기존 프로젝트 구조 파악
└── /commit: 초기 구조 커밋

P1 (엔진 설계)
├── Explore: PokerKit 라이브러리 구조 분석
├── Plan: 엔진 레이어 아키텍처 설계
└── code-architect: 상태 모델 설계

P2 (프로토콜 설계)
├── Plan: 이벤트 프로토콜 구조 설계
└── code-architect: WebSocket 구조 설계

P3 (UI/UX 스펙)
├── frontend-design: UI 컴포넌트 설계
└── Plan: 화면 흐름 설계

P4 (안정성 스펙)
├── code-explorer: 재접속 로직 분석
└── Plan: 복구 시나리오 설계

P5 (테스트/배포)
├── code-reviewer: 전체 코드 품질 검토
├── pr-test-analyzer: 테스트 커버리지 분석
└── /review-pr: 최종 PR 리뷰

P6 (라이선스)
└── Explore: 의존성 라이선스 스캔
```

---

## 2. 프로젝트 목표와 범위

### 2.1 최종 목표(Outcome)

**상용급 UX/UI**
- 로비(방 목록/검색/필터/생성/입장)
- 테이블(좌석/턴/액션/타이머/채팅)
- 프로필/설정 등 핵심 화면 완성도 확보
- 오류/재접속/로딩/빈 상태 등 "서비스 품질" UX 내장

**실시간 안정성**
- 소켓 끊김/지연/중복 액션/역순 도착 등 실전 이슈를 "규칙과 스펙"으로 선제 차단
- 재접속 시 상태 복구 100% 재현 가능

**확장성/유지보수성**
- 게임 엔진(PokerKit) ↔ 실시간 게이트웨이(WebSocket) ↔ API ↔ DB 모듈 경계 분리
- 이후 토너먼트/멀티 변형/리플레이/분석/AI 등 확장 가능

### 2.2 In Scope

- PokerKit 기반 게임 엔진 레이어 설계
- FastAPI 기반 REST + WebSocket 설계
- Redis + PostgreSQL 기반 서비스 설계
- 실시간 이벤트 프로토콜 v1
- 관전/재접속/핸드 히스토리 MVP 스펙
- 테스트 플랜/관측/배포 문서

### 2.3 Out of Scope (Backlog)

- 토너먼트(대규모 브라켓/운영툴)
- 멀티 게임 변형(오마하/스터드 등) - 구조만 대비
- AI 봇/강화학습
- 고급 리플레이 편집기

---

## 3. 상용화 품질 기준 (NFR)

### 3.1 코드/문서 품질 목표
- 스펙 문서만으로 프론트/백/QA 독립 작업 가능
- 모든 규칙은 ADR로 "왜/무엇/검증" 포함
- 릴리즈 전 DoD 체크리스트 통과 필수

### 3.2 안정성 목표
- **재접속**: 끊김 후 5초 내 재연결, 복구 완료 후 즉시 플레이
- **멱등성**: 중복 액션 요청 시 결과 1회만 반영
- **상태 일관성**: 클라 상태 오래되면 자동 스냅샷 재동기화

### 3.3 보안/운영 기본
- 인증/세션 만료/레이트리밋/감사로그 설계 포함
- 운영 로그 PII 최소화

---

## 4. 권장 아키텍처

### 4.1 컴포넌트

```
┌─────────────────────────────────────────────────────────────┐
│                        Front-end                             │
│         (로비/테이블/프로필/설정 - 상태 렌더링)                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Real-time Gateway (WebSocket)                   │
│         (로비/테이블 채널, heartbeat, reconnect)              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   API Layer (REST)                           │
│         (로그인/프로필/방 관리/히스토리 조회)                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Table Orchestrator (서버 authoritative)         │
│    (액션 처리, 엔진 적용, 상태 브로드캐스트, 멱등성/정렬)       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│               Game Core (PokerKit Engine)                    │
│         (게임 상태 전이, 검증, 99% 커버리지)                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        Storage                               │
│   PostgreSQL: 유저/룸/테이블/핸드/감사로그                     │
│   Redis: 세션 캐시, pub/sub, rate limit                       │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 "서버 authoritative" 규칙 (필수)

- 클라이언트는 승패/팟 분배/턴 판단을 하지 않음
- 클라는 `ACTION_REQUEST` 전송, 서버가 `TABLE_SNAPSHOT/TABLE_STATE_UPDATE` 반환
- 모든 액션에 `requestId` 포함 (멱등성 키)

---

## 5. 데이터 설계

### 5.1 DB 테이블 (초안)

```sql
users(id, nickname, avatar_url, created_at, status)
sessions(id, user_id, refresh_token_hash, last_seen_at, expires_at)
rooms(id, name, config_json, status, created_at)
tables(id, room_id, max_seats, status, state_version, updated_at)
hands(id, table_id, hand_no, started_at, ended_at, result_json)
hand_events(id, hand_id, seq_no, event_type, payload_json, created_at)
audit_logs(id, actor_user_id, action, context_json, created_at)
```

### 5.2 상태 모델 (런타임)

```typescript
interface LobbyState {
  rooms: Room[];
  announcements: Announcement[];
  userSession: UserSession;
}

interface TableState {
  tableId: string;
  handId: string;
  phase: 'preflop' | 'flop' | 'turn' | 'river' | 'showdown';
  seats: Seat[];
  communityCards: Card[];
  pot: number;
  blinds: Blinds;
  dealerPos: number;
  currentTurn: number;
  allowedActions: Action[];
  minRaise: number;
  timers: { turnDeadlineAt: number };
  stateVersion: number; // 단조 증가
}
```

---

## 6. 실시간 이벤트 프로토콜 v1

### 6.1 공통 Envelope

```json
{
  "type": "TABLE_SNAPSHOT",
  "ts": 1704067200000,
  "traceId": "abc-123-def",
  "requestId": "client-req-001",
  "payload": {},
  "version": "v1"
}
```

### 6.2 이벤트 목록 (v1)

| 카테고리 | 이벤트 | 설명 |
|---------|--------|------|
| 로비 | `LOBBY_SNAPSHOT` | 초기 로드/재동기화 |
| | `ROOM_CREATE_REQUEST/RESULT` | 방 생성 |
| | `ROOM_JOIN_REQUEST/RESULT` | 방 입장 |
| 테이블 | `TABLE_SNAPSHOT` | 입장/재접속 시 필수 |
| | `TABLE_STATE_UPDATE` | 상태 변경 브로드캐스트 |
| | `TURN_PROMPT` | 현재 턴/가능 액션/제한시간 |
| 액션 | `ACTION_REQUEST` | fold/call/raise/check |
| | `ACTION_RESULT` | accepted/rejected + reason |
| | `SHOWDOWN_RESULT` | 승자/팟 분배 요약 |
| 시스템 | `ERROR` | 표준 에러 |
| | `CONNECTION_STATE` | reconnecting/recovered |
| | `PING/PONG` | heartbeat |
| 채팅 | `CHAT_MESSAGE` | 메시지 전송 |
| | `CHAT_HISTORY` | 히스토리 조회 |

### 6.3 에러 코드 체계

```
AUTH_REQUIRED
ROOM_NOT_FOUND
TABLE_NOT_FOUND
TABLE_FULL
NOT_YOUR_TURN
INVALID_ACTION
INSUFFICIENT_STACK
STALE_STATE_VERSION
```

---

## 7. 재접속/일관성/멱등성 규칙

### 7.1 재접속 (Recovery)
1. 소켓 끊김 감지 → `CONNECTION_STATE: reconnecting`
2. 재연결 성공 → 서버 즉시 `TABLE_SNAPSHOT` 제공
3. 재접속 중 액션 버튼 비활성화
4. `stateVersion` 기준 정상 동기화 확인

### 7.2 멱등성 (Idempotency)
- 모든 `ACTION_REQUEST`는 `requestId` 포함
- 서버는 `(tableId, userId, requestId)` 키로 중복 처리 방지
- 동일 `requestId`에 대해 동일 결과 반환

### 7.3 정렬/역순 도착 (Ordering)
- 서버는 `stateVersion` 포함
- 클라는 `stateVersion` 감소 시 무시, `TABLE_SNAPSHOT` 재요청
- 테이블별 단일 처리 루프로 순서 보장

---

## 8. 테스트 전략

### 8.1 필수 시나리오 체크리스트

```markdown
[ ] 방 생성 → 입장 → 착석 → 핸드 시작
[ ] 2~6명 턴 이동 정상
[ ] 콜/레이즈/폴드 기본 액션, 불가능 액션 거부
[ ] 핸드 종료/쇼다운 결과 브로드캐스트
[ ] 재접속: 핸드 중 끊김 → 복구 → 상태 일치
[ ] 중복 클릭: 동일 requestId 재전송 → 결과 1회 반영
[ ] 관전: 테이블 스냅샷/업데이트 정상 수신
```

### 8.2 품질 게이트
- MVP 릴리즈 전: 위 7개 시나리오 100% 통과 필수

---

## 9. 관측/운영 (Observability)

### 9.1 구조화 로그 필수 키
```json
{
  "traceId": "",
  "requestId": "",
  "userId": "",
  "roomId": "",
  "tableId": "",
  "handId": "",
  "stateVersion": 0,
  "processingTimeMs": 0,
  "actionResult": "accepted|rejected",
  "reason": ""
}
```

### 9.2 메트릭 (최소)
- active websocket connections
- tables active / rooms active
- action latency p50/p95
- reconnect rate
- snapshot rate

---

## 10. 배포 설계

### 10.1 환경 분리
- dev / staging / prod 환경변수 분리
- DB 마이그레이션 버전/롤백 문서화

### 10.2 롤백 플랜
- 직전 컨테이너 이미지로 즉시 롤백
- DB 스키마 변경은 하위 호환 우선

---

## 11. 라이선스 점검

### 11.1 PokerKit 라이선스
- MIT License로 배포
- 상용 사용 가능

### 11.2 배포 체크리스트
- LICENSE/NOTICE 포함 정책 확정
- 프론트 폰트/아이콘/사운드/이미지 라이선스 점검
- 주요 의존성 라이선스 요약표 작성

---

## 12. 단계별 로드맵 + 완료 체크 시스템

> **⚠️ 필수**: 각 Phase 완료 시 반드시 체크포인트 기록 및 git commit

---

### P0 — 레포 스캐폴딩 & 개발 워크플로 문서

**산출물**
- [ ] `docs/01-setup-local.md`
- [ ] `docs/02-env-vars.md`
- [ ] `docs/03-dev-workflow.md`
- [ ] `docs/04-folder-structure.md`

**Gate**
- [ ] 신규 환경에서 문서만 보고 로컬 구동 플랜이 명확

**권장 서브에이전트**
```
Task(Explore): 기존 프로젝트 구조 파악
```

**완료 시 필수 액션**
```bash
# 1. TodoWrite로 P0 완료 표시
# 2. PROGRESS_CHECKPOINT.md 업데이트
# 3. git commit
git add docs/ PROGRESS_CHECKPOINT.md
git commit -m "P0 완료: 레포 스캐폴딩 및 개발 워크플로 문서"
```

---

### P1 — 엔진 레이어(PokerKit) 설계 확정

**산출물**
- [ ] `docs/10-engine-architecture.md`
- [ ] `docs/11-engine-state-model.md`
- [ ] `docs/ADR-0001-pokerkit-core.md`

**Gate**
- [ ] 엔진 I/O(액션 입력, 상태 출력, 스냅샷 직렬화)가 고정됨

**권장 서브에이전트**
```
Task(Explore): PokerKit 라이브러리 구조 분석
Task(Plan): 엔진 레이어 아키텍처 설계
Task(code-architect): 상태 모델 설계
```

**완료 시 필수 액션**
```bash
git add docs/ PROGRESS_CHECKPOINT.md
git commit -m "P1 완료: 엔진 레이어 설계 문서"
```

---

### P2 — 실시간 프로토콜 v1 확정 (가장 중요)

**산출물**
- [ ] `docs/20-realtime-protocol-v1.md`
- [ ] `docs/21-error-codes-v1.md`
- [ ] `docs/22-idempotency-ordering.md`

**Gate**
- [ ] 프론트/백이 스펙만으로 독립 개발 가능

**권장 서브에이전트**
```
Task(Plan): 이벤트 프로토콜 구조 설계
Task(code-architect): WebSocket 구조 설계
```

**완료 시 필수 액션**
```bash
git add docs/ PROGRESS_CHECKPOINT.md
git commit -m "P2 완료: 실시간 프로토콜 v1 스펙"
```

---

### P3 — 상용급 UI/UX 스펙 확정

**산출물**
- [ ] `docs/30-ui-ia.md`
- [ ] `docs/31-table-ui-spec.md`
- [ ] `docs/32-lobby-ui-spec.md`
- [ ] `docs/33-ui-components.md`

**Gate**
- [ ] 턴/가능 액션/타이머/연결상태 UX가 누락 없이 정의됨

**권장 서브에이전트**
```
Skill(frontend-design): UI 컴포넌트 설계
Task(Plan): 화면 흐름 설계
```

**완료 시 필수 액션**
```bash
git add docs/ PROGRESS_CHECKPOINT.md
git commit -m "P3 완료: UI/UX 스펙 문서"
```

---

### P4 — 안정성 스펙 (재접속/복구/일관성)

**산출물**
- [ ] `docs/40-reconnect-recovery.md`
- [ ] `docs/41-state-consistency.md`
- [ ] `docs/42-timer-turn-rules.md`

**Gate**
- [ ] 끊김→복구 시나리오가 테스트 가능한 수준으로 명문화됨

**권장 서브에이전트**
```
Task(code-explorer): 재접속 로직 분석
Task(Plan): 복구 시나리오 설계
```

**완료 시 필수 액션**
```bash
git add docs/ PROGRESS_CHECKPOINT.md
git commit -m "P4 완료: 안정성 스펙 문서"
```

---

### P5 — 테스트/관측/배포 문서 완성

**산출물**
- [ ] `docs/50-test-plan.md`
- [ ] `docs/51-observability.md`
- [ ] `docs/52-deploy-staging.md`

**Gate**
- [ ] MVP 체크리스트 기반 QA가 가능

**권장 서브에이전트**
```
Task(code-reviewer): 전체 코드 품질 검토
Task(pr-test-analyzer): 테스트 커버리지 분석
Skill(/review-pr): 최종 PR 리뷰
```

**완료 시 필수 액션**
```bash
git add docs/ PROGRESS_CHECKPOINT.md
git commit -m "P5 완료: 테스트/관측/배포 문서"
```

---

### P6 — 라이선스/에셋 감사 완료

**산출물**
- [ ] `docs/60-license-audit.md`
- [ ] `docs/61-third-party-assets.md`

**Gate**
- [ ] 상용 배포 시 고지/포함 방식이 확정됨

**권장 서브에이전트**
```
Task(Explore): 의존성 라이선스 스캔
```

**완료 시 필수 액션**
```bash
git add docs/ PROGRESS_CHECKPOINT.md
git commit -m "P6 완료: 라이선스 감사 문서"
```

---

## 13. 완료 정의 (DoD)

모두 만족 시 "PokerKit 기반 상용 MVP 스펙 완료":

- [ ] PokerKit 코어 기반 엔진 설계 문서 완료
- [ ] 실시간 이벤트 프로토콜 v1 완료
- [ ] 로비/테이블 UI 스펙(상용 UX) 완료
- [ ] 재접속/중복/타이머/일관성 규칙 문서 완료
- [ ] 테스트 플랜/관측/스테이징 배포 문서 완료
- [ ] 라이선스/서드파티 에셋 점검 문서 완료

---

## 14. Claude Code 실행 프롬프트 (Phase별)

### 공통 지시 (항상 맨 위에 붙여넣기)

```
## 필수 규칙
1. 구현 코드를 작성하지 말고, 문서/스펙/ADR만 작성한다.
2. 추측 금지: 근거가 없으면 '불명확'으로 표시하고 TODO로 남긴다.
3. 스코프 확장 금지: 추가 아이디어는 Backlog로만 기록한다.

## 세션 중단 대비 필수
1. 작업 시작 전 TodoWrite로 작업 목록 생성
2. 개별 작업 완료 즉시 completed 상태로 변경
3. Phase 완료 시 즉시 git commit
4. PROGRESS_CHECKPOINT.md 업데이트

## 권장 서브에이전트 활용
- 코드베이스 탐색: Task(Explore)
- 아키텍처 설계: Task(Plan), Task(code-architect)
- 코드 리뷰: Task(code-reviewer)
- 커밋: Skill(/commit)
```

---

### P0 프롬프트

```
[공통 지시 붙여넣기]

## 작업 내용
PokerKit 기반 상용 웹서비스를 위한 권장 레포 구조(backend/frontend/infra/docs)를 제안하고,
로컬 셋업/환경변수/개발 워크플로 문서를 작성하라.

## 활용할 서브에이전트
- Task(Explore): 기존 프로젝트 구조 파악

## 완료 체크리스트
- [ ] docs/01-setup-local.md 작성
- [ ] docs/02-env-vars.md 작성
- [ ] docs/03-dev-workflow.md 작성
- [ ] docs/04-folder-structure.md 작성
- [ ] PROGRESS_CHECKPOINT.md 업데이트
- [ ] git commit 완료
```

---

### P1 프롬프트

```
[공통 지시 붙여넣기]

## 작업 내용
PokerKit을 게임 코어로 쓰는 엔진 레이어 설계를 문서화하라.
- 상태 모델, 액션 모델, 스냅샷 직렬화, stateVersion 정책
- 서버 authoritative 원칙
- PokerKit 문서의 신뢰성 근거(정적 타입체크/테스트/99% 커버리지 주장) ADR에 인용

## 활용할 서브에이전트
- Task(Explore): PokerKit 라이브러리 구조 분석
- Task(Plan): 엔진 레이어 아키텍처 설계
- Task(code-architect): 상태 모델 설계

## 완료 체크리스트
- [ ] docs/10-engine-architecture.md 작성
- [ ] docs/11-engine-state-model.md 작성
- [ ] docs/ADR-0001-pokerkit-core.md 작성
- [ ] PROGRESS_CHECKPOINT.md 업데이트
- [ ] git commit 완료
```

---

### P2 프롬프트

```
[공통 지시 붙여넣기]

## 작업 내용
실시간 이벤트 프로토콜 v1을 작성하라.
- 이벤트 목록, envelope 규칙, payload 스키마
- 에러 코드, 멱등성(requestId), ordering(stateVersion)
- 재접속 복구 절차

## 활용할 서브에이전트
- Task(Plan): 이벤트 프로토콜 구조 설계
- Task(code-architect): WebSocket 구조 설계

## 완료 체크리스트
- [ ] docs/20-realtime-protocol-v1.md 작성
- [ ] docs/21-error-codes-v1.md 작성
- [ ] docs/22-idempotency-ordering.md 작성
- [ ] PROGRESS_CHECKPOINT.md 업데이트
- [ ] git commit 완료
```

---

### P3 프롬프트

```
[공통 지시 붙여넣기]

## 작업 내용
상용급 UI/UX 스펙 문서를 작성하라.
- 로비/테이블/프로필/설정 IA
- 컴포넌트 트리, 연결상태 배너
- 토스트/모달/로딩/빈상태 UX

## 활용할 서브에이전트
- Skill(frontend-design): UI 컴포넌트 설계
- Task(Plan): 화면 흐름 설계

## 완료 체크리스트
- [ ] docs/30-ui-ia.md 작성
- [ ] docs/31-table-ui-spec.md 작성
- [ ] docs/32-lobby-ui-spec.md 작성
- [ ] docs/33-ui-components.md 작성
- [ ] PROGRESS_CHECKPOINT.md 업데이트
- [ ] git commit 완료
```

---

### P4 프롬프트

```
[공통 지시 붙여넣기]

## 작업 내용
재접속/상태복구/중복방지/타이머 규칙 문서를 작성하라.
- reconnect 후 TABLE_SNAPSHOT 동기화
- stale version 처리
- 중복 클릭 방지 규칙

## 활용할 서브에이전트
- Task(code-explorer): 재접속 로직 분석
- Task(Plan): 복구 시나리오 설계

## 완료 체크리스트
- [ ] docs/40-reconnect-recovery.md 작성
- [ ] docs/41-state-consistency.md 작성
- [ ] docs/42-timer-turn-rules.md 작성
- [ ] PROGRESS_CHECKPOINT.md 업데이트
- [ ] git commit 완료
```

---

### P5 프롬프트

```
[공통 지시 붙여넣기]

## 작업 내용
최소 테스트 플랜, 관측(로그/메트릭) 설계, 스테이징 배포/롤백 문서를 작성하라.
- 체크리스트 기반 QA 가능해야 함

## 활용할 서브에이전트
- Task(code-reviewer): 전체 코드 품질 검토
- Task(pr-test-analyzer): 테스트 커버리지 분석
- Skill(/review-pr): 최종 PR 리뷰

## 완료 체크리스트
- [ ] docs/50-test-plan.md 작성
- [ ] docs/51-observability.md 작성
- [ ] docs/52-deploy-staging.md 작성
- [ ] PROGRESS_CHECKPOINT.md 업데이트
- [ ] git commit 완료
```

---

### P6 프롬프트

```
[공통 지시 붙여넣기]

## 작업 내용
상용 배포를 위한 라이선스/서드파티 에셋 점검 문서를 작성하라.
- PokerKit MIT 라이선스 근거 명시
- 의존성/에셋 라이선스 체크 표 템플릿

## 활용할 서브에이전트
- Task(Explore): 의존성 라이선스 스캔

## 완료 체크리스트
- [ ] docs/60-license-audit.md 작성
- [ ] docs/61-third-party-assets.md 작성
- [ ] PROGRESS_CHECKPOINT.md 업데이트
- [ ] git commit 완료
```

---

## 15. 세션 재개 프롬프트

세션이 중단된 후 재개할 때 사용:

```
## 세션 재개
이전 세션이 중단되었습니다. 다음 순서로 진행하세요:

1. PROGRESS_CHECKPOINT.md 파일을 읽어 현재 진행 상황 파악
2. TodoWrite로 남은 작업 목록 복원
3. 중단된 작업부터 이어서 진행
4. 완료된 작업은 건너뛰기

## 파일 확인
cat PROGRESS_CHECKPOINT.md
```

---

## 16. 빠른 참조: 서브에이전트 명령어

```bash
# 코드베이스 탐색
Task(subagent_type="Explore", prompt="...")

# 아키텍처 설계
Task(subagent_type="Plan", prompt="...")
Task(subagent_type="code-architect", prompt="...")

# 코드 분석
Task(subagent_type="code-explorer", prompt="...")

# 코드 리뷰
Task(subagent_type="code-reviewer", prompt="...")

# PR 리뷰
Task(subagent_type="pr-review-toolkit:code-reviewer", prompt="...")

# Skill 사용
Skill(skill="commit")
Skill(skill="commit-push-pr")
Skill(skill="feature-dev")
Skill(skill="frontend-design")
```

---

## 문서 버전
- v2.0: Claude Code 서브에이전트/Skill 활용 가이드, 세션 중단 대비 완료 체크 시스템 추가
- v1.0: 초기 작업계획서
