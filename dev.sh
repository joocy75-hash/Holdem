#!/bin/bash
# PokerKit Holdem - 로컬 개발 스크립트
#
# DB만 Docker로 실행하고, 백엔드/프론트엔드는 로컬에서 실행
# 코드 수정 시 자동 리로드됨
#
# 사용법:
#   ./dev.sh              # DB 시작 + 백엔드 + 프론트엔드 모두 실행
#   ./dev.sh db           # DB만 시작
#   ./dev.sh backend      # 백엔드만 실행
#   ./dev.sh frontend     # 프론트엔드만 실행
#   ./dev.sh stop         # DB 중지

set -e

cd "$(dirname "$0")"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }
info() { echo -e "${BLUE}[i]${NC} $1"; }

# DB 시작 (postgres + redis)
start_db() {
    log "데이터베이스 시작 중..."
    docker compose -f infra/docker/docker-compose.dev.yml up -d

    # Wait for healthy
    info "DB 준비 대기 중..."
    sleep 3

    # Check health
    if docker exec pokerkit-postgres pg_isready -U postgres -d pokerkit > /dev/null 2>&1; then
        log "PostgreSQL 준비 완료"
    else
        warn "PostgreSQL이 아직 준비 중..."
    fi

    if docker exec pokerkit-redis redis-cli ping > /dev/null 2>&1; then
        log "Redis 준비 완료"
    else
        warn "Redis가 아직 준비 중..."
    fi
}

# 백엔드 실행
start_backend() {
    log "백엔드 시작..."
    cd backend

    # venv 활성화
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    else
        error "Python venv가 없습니다. 'python -m venv .venv && pip install -r requirements.txt' 실행하세요."
        exit 1
    fi

    # .env 확인
    if [ ! -f ".env" ]; then
        warn ".env 파일이 없습니다. 기본값 사용"
    fi

    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}

# 프론트엔드 실행
start_frontend() {
    log "프론트엔드 시작..."
    cd frontend

    # node_modules 확인
    if [ ! -d "node_modules" ]; then
        warn "node_modules가 없습니다. npm install 실행 중..."
        npm install
    fi

    npm run dev
}

# DB 중지
stop_db() {
    log "데이터베이스 중지..."
    docker compose -f infra/docker/docker-compose.dev.yml down
    log "완료"
}

case "${1:-all}" in
    all|"")
        echo "=========================================="
        echo "  PokerKit Holdem - 개발 환경 시작"
        echo "=========================================="
        echo ""

        # Check Docker
        if ! docker info &> /dev/null; then
            error "Docker가 실행 중이 아닙니다."
            exit 1
        fi

        start_db

        echo ""
        info "백엔드와 프론트엔드를 각각 새 터미널에서 실행하세요:"
        echo ""
        echo "  터미널 1 (백엔드):"
        echo "    cd backend && source .venv/bin/activate"
        echo "    uvicorn app.main:app --reload"
        echo ""
        echo "  터미널 2 (프론트엔드):"
        echo "    cd frontend && npm run dev"
        echo ""
        echo "  또는 한 줄로:"
        echo "    ./dev.sh backend   # 새 터미널에서"
        echo "    ./dev.sh frontend  # 새 터미널에서"
        echo ""
        echo "=========================================="
        echo "  접속 URL:"
        echo "    프론트엔드: http://localhost:3000"
        echo "    백엔드 API: http://localhost:8000"
        echo "    API 문서:   http://localhost:8000/docs"
        echo "=========================================="
        ;;

    db)
        start_db
        log "DB가 백그라운드에서 실행 중입니다."
        ;;

    backend|back|b)
        start_backend
        ;;

    frontend|front|f)
        start_frontend
        ;;

    stop|down)
        stop_db
        ;;

    status)
        docker compose -f infra/docker/docker-compose.dev.yml ps
        ;;

    *)
        echo "사용법: ./dev.sh [옵션]"
        echo ""
        echo "옵션:"
        echo "  (없음)    DB 시작 + 사용법 안내"
        echo "  db        데이터베이스만 시작"
        echo "  backend   백엔드 실행 (uvicorn --reload)"
        echo "  frontend  프론트엔드 실행 (npm run dev)"
        echo "  stop      DB 중지"
        echo "  status    서비스 상태"
        ;;
esac
