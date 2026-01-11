PokerKit 기반 텍사스 홀덤 웹서비스 상용화 작업계획서 (Claude Code용)
0. 문서 목적

본 문서는 PokerKit을 게임 엔진 코어로 채택하여, **웹 기반 실시간 멀티플레이 텍사스 홀덤 서비스(로비/테이블/관전/재접속/핸드 히스토리)**를 상용 수준의 품질로 구축하기 위한 단계별 작업계획서다.

핵심 원칙: 서버 authoritative(판정/상태결정은 서버만), 클라이언트는 상태 렌더링 중심

산출물 중심: 구현(코드) 이전에 **스펙/문서/게이트/완료정의(DoD)**를 확정하여, 작업이 끝없이 늘어나는 것을 방지한다.

라이선스/품질 근거: PokerKit은 MIT License이며 , 문서에서 정적 타입체크·doctest·unit test 기반으로 99% 코드 커버리지를 주장한다. 또한 “온라인 포커 구현(online poker casino implementation)” 용례를 직접 언급한다.

1. 프로젝트 목표와 범위
1.1 최종 목표(Outcome)

상용급 UX/UI

로비(방 목록/검색/필터/생성/입장), 테이블(좌석/턴/액션/타이머/채팅), 프로필/설정 등 핵심 화면 완성도 확보

오류/재접속/로딩/빈 상태 등 “서비스 품질” UX 내장

실시간 안정성

소켓 끊김/지연/중복 액션/역순 도착 등 실전 이슈를 “규칙과 스펙”으로 선제 차단

재접속 시 상태 복구 100% 재현 가능

확장성/유지보수성

게임 엔진(PokerKit) ↔ 실시간 게이트웨이(WebSocket) ↔ API ↔ DB를 모듈 경계로 분리

이후 토너먼트/멀티 변형/리플레이/분석/AI 등 확장 가능

1.2 In Scope

PokerKit 기반 게임 엔진 레이어 설계(상태/액션/검증/핸드 진행/쇼다운 결과)

FastAPI 기반 REST + WebSocket(또는 동급 Python 스택) 설계

Redis + PostgreSQL 기반 서비스 설계(세션/룸 브로드캐스트/로그/핸드 히스토리)

실시간 이벤트 프로토콜 v1(스키마/에러코드/멱등성 규칙 포함)

관전/재접속/핸드 히스토리(기록·조회)까지 포함한 MVP 스펙

테스트 플랜/관측(로그·메트릭)/배포(스테이징) 문서

1.3 Out of Scope(Backlog로만 관리)

토너먼트(대규모 브라켓/운영툴)

멀티 게임 변형(오마하/스터드 등) 구조만 대비, MVP는 홀덤 고정

AI 봇/강화학습(향후)

고급 리플레이 편집기(향후)

2. 상용화 품질 기준(Non-Functional Requirements)
2.1 코드/문서 품질 목표

스펙 문서만으로 프론트/백/QA가 독립적으로 작업 가능

모든 규칙은 “왜/무엇/검증”이 포함된 ADR로 남김

릴리즈 전 체크리스트(DoD) 통과가 필수

2.2 안정성 목표(정량/정성)

재접속: 끊김 후 5초 내 재연결 시도, 복구 완료 후 즉시 플레이 가능(핸드 중 복구 포함)

멱등성: 같은 액션 요청이 중복 도착해도 결과 1회만 반영

상태 일관성: 클라 상태가 오래되면 자동으로 스냅샷 재동기화

2.3 보안/운영 기본

인증/세션 만료/레이트리밋/감사로그(audit log) 설계 포함

운영 로그는 PII 최소화(닉네임/ID는 허용, 민감정보 저장 금지)

3. 권장 아키텍처(모듈 경계)
3.1 컴포넌트

Game Core (PokerKit Engine Layer)

PokerKit을 사용해 게임 상태 전이와 검증을 수행

문서에서 온라인 포커 구현까지 활용 가능성을 명시

신뢰성 근거(정적 타입·테스트·99% 커버리지 주장)

Table Orchestrator(서버 authoritative)

“요청(Action Request)”을 받아 엔진에 적용

결과를 “상태 이벤트(State Update)”로 브로드캐스트

멱등성/정렬/재전송 규칙 적용

Real-time Gateway (WebSocket)

로비/테이블 채널 관리

연결 상태 관리(heartbeat, reconnect 안내)

API Layer (REST)

로그인/프로필/방 관리/히스토리 조회 등 비실시간 영역 담당

Storage

PostgreSQL: 유저/룸/테이블 메타/핸드 요약/감사로그

Redis: 세션 캐시, pub/sub 브로드캐스트, rate limit, 짧은 TTL 상태

Front-end

로비/테이블/프로필/설정

서버 상태를 렌더링(낙관적 UI 최소화)

3.2 “서버 authoritative” 규칙(필수)

클라이언트는 승패/팟 분배/턴 판단을 하지 않는다.

클라는 오직 ACTION_REQUEST를 보내고, 서버가 TABLE_SNAPSHOT/TABLE_STATE_UPDATE로 상태를 내려준다.

모든 액션에는 requestId를 포함(멱등성 키).

4. 데이터 설계(권장)
4.1 DB 테이블(초안)

users(id, nickname, avatar_url, created_at, status)

sessions(id, user_id, refresh_token_hash, last_seen_at, expires_at)

rooms(id, name, config_json, status, created_at)

tables(id, room_id, max_seats, status, state_version, updated_at)

hands(id, table_id, hand_no, started_at, ended_at, result_json)

hand_events(id, hand_id, seq_no, event_type, payload_json, created_at)

audit_logs(id, actor_user_id, action, context_json, created_at)

핵심 포인트

운영/분석/리플레이를 위해 hand_events는 append-only로 설계

현재 상태는 Redis 캐시 + DB 메타(state_version)로 관리

상태 불일치 시 TABLE_SNAPSHOT으로 강제 복구

4.2 상태 모델(런타임)

LobbyState: rooms[], announcements, userSession

TableState:

tableId, handId, phase(preflop/flop/turn/river/showdown)

seats[]: userId, seatNo, stack, bet, status(active/folded/allin/out)

communityCards, pot, blinds, dealerPos, currentTurn

allowedActions(for current player), minRaise, timers(turnDeadlineAt)

stateVersion(단조 증가)

5. 실시간 이벤트 프로토콜 v1 (스펙)
5.1 공통 Envelope

type: string (예: TABLE_SNAPSHOT)

ts: server timestamp

traceId: 서버 생성 추적 ID

requestId: 클라 요청이면 필수(응답/에러는 echo)

payload: object

version: v1

5.2 이벤트 목록(v1)

로비

LOBBY_SNAPSHOT (초기 로드/재동기화)

ROOM_CREATE_REQUEST → ROOM_CREATE_RESULT

ROOM_JOIN_REQUEST → ROOM_JOIN_RESULT

ROOM_LIST_UPDATE(선택)

테이블

TABLE_SNAPSHOT (입장/재접속 시 필수)

TABLE_STATE_UPDATE (상태 변경 브로드캐스트)

TURN_PROMPT (현재 턴/가능 액션/제한시간)

액션

ACTION_REQUEST (fold/call/raise/check)

ACTION_RESULT (accepted/rejected + reason)

SHOWDOWN_RESULT (승자/팟 분배 요약)

시스템

ERROR (표준 에러)

CONNECTION_STATE (reconnecting/recovered/disconnected)

PING / PONG(선택)

채팅

CHAT_MESSAGE

CHAT_HISTORY

5.3 에러 코드 체계(v1 예시)

AUTH_REQUIRED

ROOM_NOT_FOUND

TABLE_NOT_FOUND

TABLE_FULL

NOT_YOUR_TURN

INVALID_ACTION

INSUFFICIENT_STACK

STALE_STATE_VERSION (클라 상태 구버전 → 스냅샷 재요청)

6. 재접속/일관성/멱등성 규칙(상용 필수)
6.1 재접속(Recovery)

소켓 끊김 감지 → CONNECTION_STATE: reconnecting

재연결 성공 → 서버는 즉시 TABLE_SNAPSHOT(또는 클라 요청 후 제공)

재접속 중에는 액션 버튼 비활성화(사용자 혼란 방지)

재접속 후 stateVersion을 기준으로 정상 동기화 확인

6.2 멱등성(Idempotency)

모든 ACTION_REQUEST는 requestId 포함

서버는 (tableId, userId, requestId)를 키로 중복 처리 방지

결과는 동일 requestId에 대해 동일하게 반환(재전송 안전)

6.3 정렬/역순 도착(Ordering)

서버는 상태 이벤트에 stateVersion 포함

클라는 stateVersion이 감소하면 무시하고 TABLE_SNAPSHOT 재요청

테이블별 단일 처리 루프(또는 큐)를 통해 서버에서 순서를 보장(설계 문서로 고정)

7. 테스트 전략(최소로 강하게)
7.1 테스트 목표

“상용 MVP”에서 가장 빈번한 사고(끊김/중복/턴 꼬임/상태 불일치)를 자동/수동 테스트로 포착

7.2 필수 시나리오(체크리스트)

방 생성 → 입장 → 착석 → 핸드 시작

2~6명에서 턴 이동 정상

콜/레이즈/폴드 기본 액션 정상, 불가능 액션 거부(에러코드 확인)

핸드 종료/쇼다운 결과 정상 브로드캐스트

재접속: 핸드 중 끊김 → 복구 → 상태 일치

중복 클릭: 동일 requestId 재전송 → 결과 1회 반영

관전: 테이블 스냅샷/업데이트 정상 수신

7.3 품질 게이트

MVP 릴리즈 전: 위 7개 시나리오 100% 통과가 “배포 조건”

8. 관측/운영(Observability)
8.1 구조화 로그(JSON) 필수 키

traceId, requestId, userId, roomId, tableId, handId, stateVersion

이벤트 처리 시간(ms), 액션 결과(accepted/rejected + reason)

8.2 메트릭(최소)

active websocket connections

tables active / rooms active

action latency p50/p95

reconnect rate

snapshot rate(테이블별 스냅샷 빈도)

8.3 장애 대응 기본

“상태 꼬임” 발생 시: 강제 TABLE_SNAPSHOT 재동기화 루틴

이벤트/핸드 로그 기반 사후 분석 가능(append-only 기록)

9. 배포 설계(스테이징 → 프로덕션)
9.1 환경 분리

dev / staging / prod 환경변수 분리

DB 마이그레이션 전략 문서화(버전/롤백 포함)

9.2 롤백 플랜(필수)

직전 이미지(컨테이너)로 즉시 롤백

DB 스키마 변경은 “하위 호환” 우선(파괴적 변경 금지)

10. 라이선스/서드파티 점검(상용 필수)
10.1 PokerKit 라이선스

PokerKit은 MIT License로 배포된다.

10.2 배포 시 체크리스트

LICENSE/NOTICE 포함 정책 확정(웹앱 배포물/레포/도커 이미지)

프론트 폰트/아이콘/사운드/이미지의 라이선스 별도 점검

주요 의존성 라이선스 요약표 작성

11. 단계별 로드맵(Phases) + 산출물 + Gate

중요: 각 Phase는 “문서 산출물”이 완성되고 Gate를 통과해야 다음 단계로 이동한다.

P0 — 레포 스캐폴딩 & 개발 워크플로 문서

산출물

docs/01-setup-local.md

docs/02-env-vars.md

docs/03-dev-workflow.md

docs/04-folder-structure.md

Gate

 신규 환경에서 문서만 보고 로컬 구동 플랜이 명확

P1 — 엔진 레이어(PokerKit) 설계 확정

산출물

docs/10-engine-architecture.md

docs/11-engine-state-model.md

docs/ADR-0001-pokerkit-core.md

(근거) 온라인 구현 용례 및 99% 커버리지 주장 인용

Gate

 엔진 I/O(액션 입력, 상태 출력, 스냅샷 직렬화)가 고정됨

P2 — 실시간 프로토콜 v1 확정(가장 중요)

산출물

docs/20-realtime-protocol-v1.md

docs/21-error-codes-v1.md

docs/22-idempotency-ordering.md

Gate

 프론트/백이 스펙만으로 독립 개발 가능

P3 — 상용급 UI/UX 스펙 확정

산출물

docs/30-ui-ia.md

docs/31-table-ui-spec.md

docs/32-lobby-ui-spec.md

docs/33-ui-components.md

Gate

 턴/가능 액션/타이머/연결상태 UX가 누락 없이 정의됨

P4 — 안정성 스펙(재접속/복구/일관성)

산출물

docs/40-reconnect-recovery.md

docs/41-state-consistency.md

docs/42-timer-turn-rules.md

Gate

 끊김→복구 시나리오가 테스트 가능한 수준으로 명문화됨

P5 — 테스트/관측/배포 문서 완성

산출물

docs/50-test-plan.md

docs/51-observability.md

docs/52-deploy-staging.md

Gate

 MVP 체크리스트 기반 QA가 가능

P6 — 라이선스/에셋 감사 완료

산출물

docs/60-license-audit.md

docs/61-third-party-assets.md

Gate

 상용 배포 시 고지/포함 방식이 확정됨(MIT 근거 포함)

12. 완료 정의(DoD)

아래를 모두 만족하면 “PokerKit 기반 상용 MVP 스펙 완료”로 정의한다.

 PokerKit 코어 기반 엔진 설계 문서 완료(상태/액션/스냅샷/버전)

 실시간 이벤트 프로토콜 v1(에러/멱등성/재접속 포함) 완료

 로비/테이블 UI 스펙(상용 UX) 완료

 재접속/중복/타이머/일관성 규칙 문서 완료

 테스트 플랜/관측/스테이징 배포 문서 완료

 라이선스/서드파티 에셋 점검 문서 완료(MIT 근거 포함)

13. Claude Code 실행 프롬프트(복붙용, “코드 작성 금지” 포함)
공통 지시(항상 맨 위에 붙여넣기)

“너는 구현 코드를 작성하지 말고, 문서/스펙/ADR만 작성한다.”

“추측 금지: 근거가 없으면 ‘불명확’으로 표시하고 TODO로 남긴다.”

“스코프 확장 금지: 추가 아이디어는 Backlog로만 기록한다.”

P0 프롬프트

“PokerKit 기반 상용 웹서비스를 위한 권장 레포 구조(backend/frontend/infra/docs)를 제안하고, 로컬 셋업/환경변수/개발 워크플로 문서를 작성하라.”

P1 프롬프트

“PokerKit을 게임 코어로 쓰는 엔진 레이어 설계를 문서화하라. 상태 모델, 액션 모델, 스냅샷 직렬화, stateVersion 정책, 서버 authoritative 원칙을 포함하라. PokerKit 문서의 신뢰성 근거(정적 타입체크/테스트/99% 커버리지 주장)와 온라인 구현 용례를 ADR에 인용하라.”

P2 프롬프트

“실시간 이벤트 프로토콜 v1을 작성하라. 이벤트 목록, envelope 규칙, payload 스키마, 에러 코드, 멱등성(requestId), ordering(stateVersion), 재접속 복구 절차를 포함하라.”

P3 프롬프트

“상용급 UI/UX 스펙 문서를 작성하라. 로비/테이블/프로필/설정 IA, 컴포넌트 트리, 연결상태 배너, 토스트/모달/로딩/빈상태 UX를 상세히 정의하라.”

P4 프롬프트

“재접속/상태복구/중복방지/타이머 규칙 문서를 작성하라. 특히 reconnect 후 TABLE_SNAPSHOT 동기화, stale version 처리, 중복 클릭 방지 규칙을 명문화하라.”

P5 프롬프트

“최소 테스트 플랜, 관측(로그/메트릭) 설계, 스테이징 배포/롤백 문서를 작성하라. 체크리스트 기반으로 QA가 가능해야 한다.”

P6 프롬프트

“상용 배포를 위한 라이선스/서드파티 에셋 점검 문서를 작성하라. PokerKit이 MIT 라이선스임을 근거와 함께 명시하고, 의존성/에셋 라이선스 체크 표 템플릿을 포함하라.”