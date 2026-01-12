# 🚀 PokerKit 백엔드 설치 가이드

프론트엔드 개발자를 위한 백엔드 서버 설치 및 실행 가이드입니다.

---

## 📋 목차

1. [사전 준비](#-사전-준비)
2. [방법 1: Docker로 전체 실행](#-방법-1-docker로-전체-실행-가장-쉬움-)
3. [방법 2: 로컬 개발 환경](#-방법-2-로컬-개발-환경)
4. [API 테스트하기](#-api-테스트하기)
5. [문제 해결](#-문제-해결)

---

## 🔧 사전 준비

### Docker Desktop 설치 (필수)

**Mac:**
```bash
# Homebrew로 설치
brew install --cask docker

# 또는 공식 사이트에서 다운로드
# https://www.docker.com/products/docker-desktop
```

**Windows:**
```
1. https://www.docker.com/products/docker-desktop 접속
2. "Download for Windows" 클릭
3. 설치 파일 실행
4. 설치 완료 후 Docker Desktop 실행
```

**설치 확인:**
```bash
docker --version
# Docker version 24.0.0 이상이면 OK

docker-compose --version
# Docker Compose version v2.0.0 이상이면 OK
```

### Git 설치 (필수)

**Mac:**
```bash
# Xcode Command Line Tools와 함께 설치됨
xcode-select --install

# 또는 Homebrew로 설치
brew install git
```

**Windows:**
```
1. https://git-scm.com/download/win 접속
2. 설치 파일 다운로드 및 실행
3. 기본 옵션으로 설치
```

**설치 확인:**
```bash
git --version
# git version 2.30.0 이상이면 OK
```

---

## 🐳 방법 1: Docker로 전체 실행 (가장 쉬움) ⭐

> Python 설치 없이 Docker만으로 모든 것을 실행합니다.
> 프론트엔드 개발만 할 때 추천!

### Step 1: 터미널 열기

**Mac:**
- `Cmd + Space` → "터미널" 검색 → 실행

**Windows:**
- `Win + R` → "cmd" 입력 → 실행
- 또는 PowerShell 실행

### Step 2: 작업 폴더로 이동

```bash
# 원하는 폴더로 이동 (예: 바탕화면)
cd ~/Desktop          # Mac
cd %USERPROFILE%\Desktop   # Windows
```

### Step 3: 프로젝트 다운로드

```bash
git clone https://github.com/joocy75-hash/Holdem.git
```

출력 예시:
```
Cloning into 'Holdem'...
remote: Enumerating objects: 1234, done.
remote: Counting objects: 100% (1234/1234), done.
Receiving objects: 100% (1234/1234), 2.50 MiB | 5.00 MiB/s, done.
```

### Step 4: 프로젝트 폴더로 이동

```bash
cd Holdem
```

### Step 5: 환경변수 파일 생성

```bash
# Mac/Linux
cp .env.example .env

# Windows (CMD)
copy .env.example .env

# Windows (PowerShell)
Copy-Item .env.example .env
```

### Step 6: Docker 서비스 실행

```bash
docker-compose -f infra/docker/docker-compose.full.yml up -d
```

출력 예시:
```
[+] Running 4/4
 ✔ Network pokerkit-network       Created
 ✔ Container pokerkit-postgres    Started
 ✔ Container pokerkit-redis       Started
 ✔ Container pokerkit-backend     Started
```

### Step 7: 실행 확인

```bash
# 컨테이너 상태 확인
docker ps
```

출력 예시:
```
CONTAINER ID   IMAGE              STATUS          PORTS
abc123         pokerkit-backend   Up 30 seconds   0.0.0.0:8000->8000/tcp
def456         postgres:16        Up 35 seconds   0.0.0.0:5432->5432/tcp
ghi789         redis:7            Up 35 seconds   0.0.0.0:6379->6379/tcp
```

### Step 8: 브라우저에서 확인

브라우저를 열고 아래 주소로 접속:

```
http://localhost:8000/docs
```

Swagger UI가 보이면 성공! 🎉

### 서비스 종료

```bash
# 종료 (데이터 유지)
docker-compose -f infra/docker/docker-compose.full.yml down

# 종료 + 데이터 삭제 (완전 초기화)
docker-compose -f infra/docker/docker-compose.full.yml down -v
```

---

## 💻 방법 2: 로컬 개발 환경

> DB는 Docker로, 백엔드는 로컬에서 실행합니다.
> 백엔드 코드를 수정하면서 테스트할 때 추천!

### 추가 요구사항: Python 설치

**Mac:**
```bash
# Homebrew로 설치
brew install python@3.11

# 설치 확인
python3 --version
# Python 3.11.x 이상이면 OK
```

**Windows:**
```
1. https://www.python.org/downloads/ 접속
2. "Download Python 3.11.x" 클릭
3. 설치 시 "Add Python to PATH" 체크 필수!
4. 설치 완료
```

```bash
# 설치 확인
python --version
# Python 3.11.x 이상이면 OK
```

### Step 1-4: 방법 1과 동일

프로젝트 다운로드 및 환경변수 설정까지 동일합니다.

### Step 5: DB만 Docker로 실행

```bash
docker-compose -f infra/docker/docker-compose.dev.yml up -d
```

출력 예시:
```
[+] Running 3/3
 ✔ Network pokerkit-network       Created
 ✔ Container pokerkit-postgres    Started
 ✔ Container pokerkit-redis       Started
```

### Step 6: 백엔드 폴더로 이동

```bash
cd backend
```

### Step 7: Python 가상환경 생성

```bash
# Mac/Linux
python3 -m venv .venv

# Windows
python -m venv .venv
```

### Step 8: 가상환경 활성화

```bash
# Mac/Linux
source .venv/bin/activate

# Windows (CMD)
.venv\Scripts\activate.bat

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

활성화되면 터미널 앞에 `(.venv)`가 표시됩니다:
```
(.venv) user@computer:~/Holdem/backend$
```

### Step 9: 패키지 설치

```bash
pip install -r requirements.txt
```

출력 예시:
```
Collecting fastapi==0.109.0
  Downloading fastapi-0.109.0.whl (92 kB)
...
Successfully installed fastapi-0.109.0 ...
```

### Step 10: 데이터베이스 테이블 생성

```bash
alembic upgrade head
```

출력 예시:
```
INFO  [alembic.runtime.migration] Running upgrade  -> abc123, initial
INFO  [alembic.runtime.migration] Running upgrade abc123 -> def456, add_users
```

### Step 11: 서버 실행

```bash
uvicorn app.main:app --reload --port 8000
```

출력 예시:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345]
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Step 12: 브라우저에서 확인

```
http://localhost:8000/docs
```

### 서비스 종료

```bash
# 백엔드 서버: Ctrl+C

# Docker DB 종료
cd ..  # Holdem 폴더로 이동
docker-compose -f infra/docker/docker-compose.dev.yml down
```

---

## 🧪 API 테스트하기

### 1. 회원가입 테스트

**터미널에서:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test1234",
    "nickname": "tester"
  }'
```

**응답 예시:**
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "nickname": "tester",
    "avatarUrl": null,
    "balance": 0
  },
  "tokens": {
    "accessToken": "eyJhbGciOiJIUzI1NiIs...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIs...",
    "tokenType": "Bearer",
    "expiresIn": 1800
  }
}
```

### 2. 로그인 테스트

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test1234"
  }'
```

### 3. 방 목록 조회 (인증 필요)

```bash
# 위 로그인 응답에서 accessToken 복사 후 사용
curl http://localhost:8000/api/v1/rooms \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

### 4. Swagger UI에서 테스트

1. http://localhost:8000/docs 접속
2. 우측 상단 "Authorize" 버튼 클릭
3. `Bearer {accessToken}` 형식으로 입력
4. 각 API 엔드포인트에서 "Try it out" 클릭하여 테스트

### 5. WebSocket 연결 테스트

브라우저 개발자 도구 Console에서:
```javascript
const token = "YOUR_ACCESS_TOKEN";  // 로그인 응답의 accessToken
const ws = new WebSocket(`ws://localhost:8000/ws?token=${token}`);

ws.onopen = () => {
  console.log("✅ WebSocket 연결됨!");
  
  // 로비 구독
  ws.send(JSON.stringify({
    type: "SUBSCRIBE_LOBBY",
    payload: {},
    ts: Date.now(),
    traceId: "test-123",
    version: "v1"
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("📩 메시지 수신:", data.type, data.payload);
};

ws.onerror = (error) => {
  console.error("❌ WebSocket 에러:", error);
};

ws.onclose = () => {
  console.log("🔌 WebSocket 연결 종료");
};
```

---

## 🔗 접속 URL 정리

| 서비스 | URL | 설명 |
|--------|-----|------|
| API 문서 (Swagger) | http://localhost:8000/docs | API 테스트 UI |
| API 문서 (ReDoc) | http://localhost:8000/redoc | API 문서 (읽기용) |
| Health Check | http://localhost:8000/health | 서버 상태 확인 |
| WebSocket | ws://localhost:8000/ws?token=TOKEN | 실시간 연결 |

---

## ❓ 문제 해결

### "docker: command not found"

Docker Desktop이 설치되지 않았거나 실행 중이 아닙니다.
1. Docker Desktop 설치 확인
2. Docker Desktop 앱 실행
3. 시스템 트레이에서 Docker 아이콘이 "Running" 상태인지 확인

### "port is already in use"

해당 포트를 다른 프로그램이 사용 중입니다.

```bash
# 사용 중인 프로세스 확인 (Mac/Linux)
lsof -i :8000
lsof -i :5432
lsof -i :6379

# 프로세스 종료
kill -9 <PID>
```

### "connection refused" (DB 연결 실패)

Docker 컨테이너가 실행 중인지 확인:
```bash
docker ps

# 컨테이너가 없으면 다시 실행
docker-compose -f infra/docker/docker-compose.dev.yml up -d
```

### "alembic: command not found"

가상환경이 활성화되지 않았습니다:
```bash
# Mac/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### DB 완전 초기화

```bash
# 모든 컨테이너와 데이터 삭제
docker-compose -f infra/docker/docker-compose.dev.yml down -v

# 다시 시작
docker-compose -f infra/docker/docker-compose.dev.yml up -d

# 테이블 재생성
cd backend
alembic upgrade head
```

### 로그 확인

```bash
# 백엔드 로그
docker logs pokerkit-backend -f

# PostgreSQL 로그
docker logs pokerkit-postgres -f

# Redis 로그
docker logs pokerkit-redis -f
```

---

## 📚 추가 문서

| 문서 | 설명 |
|------|------|
| [docs/API_REFERENCE.md](docs/API_REFERENCE.md) | REST API, WebSocket 이벤트 상세 명세 |
| [docs/FRONTEND_INTEGRATION_GUIDE.md](docs/FRONTEND_INTEGRATION_GUIDE.md) | TypeScript 연동 코드 예제 |
| [docs/20-realtime-protocol-v1.md](docs/20-realtime-protocol-v1.md) | WebSocket 프로토콜 상세 |
| [docs/21-error-codes-v1.md](docs/21-error-codes-v1.md) | 에러 코드 목록 |
| [docs/30-ui-ia.md](docs/30-ui-ia.md) | UI 화면 구조 |
| [docs/33-ui-components.md](docs/33-ui-components.md) | UI 컴포넌트 스펙 |

---

## 💬 도움이 필요하면

백엔드 관련 문의사항이 있으면 이슈를 등록해주세요:
https://github.com/joocy75-hash/Holdem/issues
