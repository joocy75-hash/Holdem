# 환경변수 설정 가이드

> PokerKit 기반 텍사스 홀덤 웹서비스 환경변수 명세

---

## 환경 구분

| 환경 | 파일 | 용도 |
|------|------|------|
| 로컬 개발 | `.env` | 개발자 로컬 환경 |
| 테스트 | `.env.test` | CI/CD 테스트 환경 |
| 스테이징 | `.env.staging` | 스테이징 서버 |
| 프로덕션 | `.env.prod` | 운영 서버 (시크릿 매니저 권장) |

---

## 백엔드 환경변수

### 애플리케이션 설정

```bash
# 환경 구분
APP_ENV=development  # development | staging | production

# 서버 설정
APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEBUG=true       # production에서는 false

# 로깅
LOG_LEVEL=DEBUG      # DEBUG | INFO | WARNING | ERROR
LOG_FORMAT=json      # json | text
```

### 데이터베이스 (PostgreSQL)

```bash
# 연결 정보
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/pokerkit

# 개별 설정 (DATABASE_URL 대신 사용 가능)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=pokerkit
DB_USER=postgres
DB_PASSWORD=postgres

# 커넥션 풀
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
```

### Redis

```bash
# 연결 정보
REDIS_URL=redis://localhost:6379/0

# 개별 설정
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=        # 로컬에서는 비워둠

# 세션 설정
REDIS_SESSION_TTL=86400  # 24시간 (초)
```

### 인증/보안

```bash
# JWT 설정
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# 세션
SESSION_SECRET_KEY=another-secret-key-for-sessions

# CORS
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
CORS_ALLOW_CREDENTIALS=true
```

### 게임 설정

```bash
# 테이블 설정
DEFAULT_MAX_SEATS=6
DEFAULT_SMALL_BLIND=10
DEFAULT_BIG_BLIND=20
DEFAULT_BUY_IN_MIN=400
DEFAULT_BUY_IN_MAX=2000

# 타이머 설정 (초)
TURN_TIMEOUT=30
RECONNECT_GRACE_PERIOD=60
HEARTBEAT_INTERVAL=15
```

### 레이트 리밋

```bash
# API 레이트 리밋
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60  # 초

# WebSocket 레이트 리밋
WS_RATE_LIMIT_MESSAGES=50
WS_RATE_LIMIT_WINDOW=10
```

---

## 프론트엔드 환경변수

### Next.js 공개 변수 (NEXT_PUBLIC_ 접두사)

```bash
# API 엔드포인트
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

# 기능 플래그
NEXT_PUBLIC_ENABLE_CHAT=true
NEXT_PUBLIC_ENABLE_SPECTATOR=true
NEXT_PUBLIC_ENABLE_HAND_HISTORY=true
```

### 서버 전용 변수

```bash
# 내부 API (SSR용)
INTERNAL_API_URL=http://backend:8000
```

---

## Docker Compose 환경변수

### PostgreSQL

```bash
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=pokerkit
```

### Redis

```bash
REDIS_PASSWORD=  # 개발 환경에서는 비워둠
```

---

## .env.example 템플릿

```bash
# ===========================================
# PokerKit Holdem - Environment Variables
# ===========================================

# ----- Application -----
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEBUG=true
LOG_LEVEL=DEBUG
LOG_FORMAT=json

# ----- Database (PostgreSQL) -----
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/pokerkit
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# ----- Redis -----
REDIS_URL=redis://localhost:6379/0
REDIS_SESSION_TTL=86400

# ----- Authentication -----
JWT_SECRET_KEY=change-this-in-production-use-strong-random-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
SESSION_SECRET_KEY=another-secret-change-in-production

# ----- CORS -----
CORS_ORIGINS=http://localhost:3000
CORS_ALLOW_CREDENTIALS=true

# ----- Game Settings -----
DEFAULT_MAX_SEATS=6
DEFAULT_SMALL_BLIND=10
DEFAULT_BIG_BLIND=20
TURN_TIMEOUT=30
RECONNECT_GRACE_PERIOD=60
HEARTBEAT_INTERVAL=15

# ----- Rate Limiting -----
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# ----- Frontend (Next.js) -----
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
NEXT_PUBLIC_ENABLE_CHAT=true
```

---

## 환경별 주의사항

### Development

- `APP_DEBUG=true` 허용
- 약한 시크릿 키 사용 가능
- CORS 모든 로컬 오리진 허용

### Staging

- `APP_DEBUG=false` 권장
- 프로덕션과 유사한 시크릿 키 사용
- 제한된 CORS 오리진

### Production

- `APP_DEBUG=false` 필수
- 강력한 랜덤 시크릿 키 필수 (최소 32자)
- 시크릿 매니저 사용 권장 (AWS Secrets Manager, HashiCorp Vault 등)
- HTTPS 전용 (`wss://` for WebSocket)
- 환경변수 파일 버전 관리 제외

---

## 시크릿 키 생성

```bash
# Python으로 랜덤 키 생성
python -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL로 생성
openssl rand -base64 32
```

---

## 환경변수 검증

백엔드 시작 시 필수 환경변수 검증:

```python
# app/config.py 예시
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str
    database_url: str
    redis_url: str
    jwt_secret_key: str
    
    class Config:
        env_file = ".env"
```

---

## 관련 문서

- [01-setup-local.md](./01-setup-local.md) - 로컬 환경 셋업
- [03-dev-workflow.md](./03-dev-workflow.md) - 개발 워크플로
- [52-deploy-staging.md](./52-deploy-staging.md) - 스테이징 배포
