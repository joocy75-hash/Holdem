# 🚀 프론트엔드 개발자 퀵스타트 가이드

백엔드 서버를 빠르게 실행하고 프론트엔드 개발을 시작하세요.

---

## 사전 요구사항

- Docker & Docker Compose
- Git

---

## 1. 프로젝트 클론

```bash
git clone https://github.com/joocy75-hash/Holdem.git
cd Holdem
```

---

## 2. 환경변수 설정

```bash
cp .env.example .env
```

기본값으로 바로 실행 가능합니다.

---

## 3. Docker로 DB 실행

```bash
docker-compose -f infra/docker/docker-compose.dev.yml up -d
```

실행되는 서비스:
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

---

## 4. 백엔드 서버 실행

```bash
cd backend

# 가상환경 생성 (최초 1회)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# DB 마이그레이션
alembic upgrade head

# 서버 실행
uvicorn app.main:app --reload --port 8000
```

---

## 5. 연결 확인

| 서비스 | URL |
|--------|-----|
| API 문서 (Swagger) | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |
| WebSocket | ws://localhost:8000/ws?token=ACCESS_TOKEN |

---

## 6. 프론트엔드 연동

### REST API

```typescript
const API_URL = 'http://localhost:8000/api/v1';

// 로그인
const response = await fetch(`${API_URL}/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: 'test@test.com', password: 'Test1234' })
});
const { tokens } = await response.json();
```

### WebSocket

```typescript
const ws = new WebSocket(`ws://localhost:8000/ws?token=${tokens.accessToken}`);

ws.onopen = () => {
  // 로비 구독
  ws.send(JSON.stringify({ type: 'SUBSCRIBE_LOBBY', payload: {} }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log(message.type, message.payload);
};
```

---

## 7. 종료

```bash
# 백엔드 서버: Ctrl+C

# Docker 컨테이너 종료
docker-compose -f infra/docker/docker-compose.dev.yml down

# 데이터도 삭제하려면
docker-compose -f infra/docker/docker-compose.dev.yml down -v
```

---

## 📚 상세 문서

- [API 레퍼런스](docs/API_REFERENCE.md) - REST API, WebSocket 이벤트 상세
- [프론트엔드 연동 가이드](docs/FRONTEND_INTEGRATION_GUIDE.md) - TypeScript 예제 코드
- [WebSocket 프로토콜](docs/20-realtime-protocol-v1.md) - 실시간 통신 명세
- [에러 코드](docs/21-error-codes-v1.md) - 에러 처리 가이드

---

## ❓ 문제 해결

### Docker 포트 충돌
```bash
# 사용 중인 포트 확인
lsof -i :5432
lsof -i :6379

# .env에서 포트 변경
POSTGRES_PORT=5433
REDIS_PORT=6380
```

### DB 연결 실패
```bash
# Docker 컨테이너 상태 확인
docker ps

# 로그 확인
docker logs pokerkit-postgres
docker logs pokerkit-redis
```
