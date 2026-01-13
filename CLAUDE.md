# Claude Code 작업 지침

## 구조
- `backend/app/` - FastAPI (ws/, engine/, bot/, api/, services/)
- `frontend/src/` - Next.js 14 + TypeScript

## 코드 규칙
- 일반 코더가 아닌 온라인 게임 기획 및 개발자의 관점에서 생각하라.
- 기존 패턴 따르기
- 변수명 영어, 주석/에러메시지 한글 OK
- snake_case(백엔드) ↔ camelCase(프론트) Pydantic alias 사용

## WebSocket
- 메시지: `{type, payload}` (클라→서버), `{type, ts, traceId, payload}` (서버→클라)
- 이벤트 정의: `backend/app/ws/events.py`
- **중요**: 메시지 수신은 반드시 `recv()` 직접 호출 (폴링 X)

## 봇 시스템
- URL 설정: `BOT_API_URL`, `BOT_WS_URL` 환경변수
- 봇 API: `/api/v1/bots/*` (인증 미적용 상태)

## 테스트
```bash
cd backend && pytest tests/ -v
```

## 주의
- 수정 전 관련 코드 먼저 읽기
- 과도한 추상화/리팩토링 금지
- 요청한 것만 수정
