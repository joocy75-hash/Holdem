# 로컬 개발 환경 셋업 가이드

> PokerKit 기반 텍사스 홀덤 웹서비스 로컬 개발 환경 구성

---

## 사전 요구사항

### 필수 설치

| 도구 | 버전 | 용도 |
|------|------|------|
| Python | 3.11+ | 백엔드 런타임 |
| Node.js | 20 LTS+ | 프론트엔드 런타임 |
| Docker | 24+ | 컨테이너 환경 |
| Docker Compose | 2.20+ | 멀티 컨테이너 관리 |
| Git | 2.40+ | 버전 관리 |

### 권장 설치

| 도구 | 용도 |
|------|------|
| uv | Python 패키지 관리 (pip 대체) |
| pnpm | Node.js 패키지 관리 (npm 대체) |
| direnv | 환경변수 자동 로드 |

---

## 1. 레포지토리 클론

```bash
git clone <repository-url>
cd pokerkit-holdem
```

---

## 2. 환경변수 설정

```bash
# 환경변수 예시 파일 복사
cp .env.example .env

# 필요시 .env 파일 수정
# 상세 내용은 docs/02-env-vars.md 참조
```

---

## 3. 인프라 서비스 실행 (Docker)

```bash
# PostgreSQL + Redis 실행
docker compose -f infra/docker/docker-compose.dev.yml up -d

# 상태 확인
docker compose -f infra/docker/docker-compose.dev.yml ps
```

### 서비스 포트

| 서비스 | 포트 | 용도 |
|--------|------|------|
| PostgreSQL | 5432 | 메인 데이터베이스 |
| Redis | 6379 | 세션/캐시/pub-sub |

---

## 4. 백엔드 셋업

### 4.1 가상환경 생성 및 의존성 설치

```bash
cd backend

# uv 사용 (권장)
uv venv
source .venv/bin/activate  # macOS/Linux
uv pip install -r requirements.txt
uv pip install -r requirements-dev.txt

# 또는 pip 사용
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 4.2 데이터베이스 마이그레이션

```bash
# 마이그레이션 실행
alembic upgrade head

# 마이그레이션 상태 확인
alembic current
```

### 4.3 백엔드 서버 실행

```bash
# 개발 서버 실행 (hot reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 또는
python -m uvicorn app.main:app --reload
```

### 4.4 API 문서 확인

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 5. 프론트엔드 셋업

### 5.1 의존성 설치

```bash
cd frontend

# pnpm 사용 (권장)
pnpm install

# 또는 npm 사용
npm install
```

### 5.2 개발 서버 실행

```bash
# 개발 서버 실행
pnpm dev

# 또는
npm run dev
```

### 5.3 접속 확인

- 프론트엔드: http://localhost:3000

---

## 6. 전체 스택 실행 (Docker Compose)

모든 서비스를 Docker로 한 번에 실행:

```bash
# 전체 스택 빌드 및 실행
docker compose -f infra/docker/docker-compose.yml up --build

# 백그라운드 실행
docker compose -f infra/docker/docker-compose.yml up -d --build
```

---

## 7. 개발 도구 설정

### VS Code 권장 익스텐션

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "charliermarsh.ruff",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "bradlc.vscode-tailwindcss"
  ]
}
```

### Pre-commit 훅 설정

```bash
# pre-commit 설치
pip install pre-commit

# 훅 설치
pre-commit install

# 수동 실행
pre-commit run --all-files
```

---

## 8. 테스트 실행

### 백엔드 테스트

```bash
cd backend

# 전체 테스트
pytest

# 커버리지 포함
pytest --cov=app --cov-report=html

# 특정 테스트
pytest tests/unit/test_engine.py -v
```

### 프론트엔드 테스트

```bash
cd frontend

# 유닛 테스트
pnpm test

# E2E 테스트
pnpm test:e2e
```

---

## 9. 트러블슈팅

### PostgreSQL 연결 실패

```bash
# Docker 컨테이너 상태 확인
docker ps

# 로그 확인
docker logs pokerkit-postgres

# 포트 충돌 확인
lsof -i :5432
```

### Redis 연결 실패

```bash
# Redis 연결 테스트
redis-cli -h localhost -p 6379 ping
```

### Python 의존성 충돌

```bash
# 가상환경 재생성
rm -rf .venv
uv venv
uv pip install -r requirements.txt
```

### Node.js 의존성 문제

```bash
# node_modules 재설치
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

---

## 10. 유용한 명령어

```bash
# 모든 Docker 컨테이너 중지
docker compose -f infra/docker/docker-compose.dev.yml down

# 볼륨 포함 삭제 (DB 데이터 초기화)
docker compose -f infra/docker/docker-compose.dev.yml down -v

# 로그 확인
docker compose -f infra/docker/docker-compose.dev.yml logs -f

# 백엔드 린트
cd backend && ruff check .

# 프론트엔드 린트
cd frontend && pnpm lint
```

---

## 관련 문서

- [02-env-vars.md](./02-env-vars.md) - 환경변수 상세 설명
- [03-dev-workflow.md](./03-dev-workflow.md) - 개발 워크플로
- [04-folder-structure.md](./04-folder-structure.md) - 폴더 구조
