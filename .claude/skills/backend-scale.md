# Backend Scale Skill - 홀덤 포커 300-500명 동시접속

> 텍사스 홀덤 포커 게임 백엔드 스케일링 작업 skill
> **버전**: 1.3 Final

---

## 프로젝트 개요

### 목표
- **동시 접속자**: 300-500명
- **활성 테이블**: 50-80개
- **응답 시간**: 액션 처리 < 100ms (p95)

### 핵심 비즈니스 로직
```
게임 머니: KRW (원화) 표시
입금: 암호화폐 → KRW 변환
출금: KRW → 암호화폐 변환
지원 코인: BTC, ETH, USDT, USDC
```

---

## 기술 스택

### 핵심 기술
| 레이어 | 기술 | 용도 |
|--------|------|------|
| API 서버 | FastAPI + Uvicorn | REST API, WebSocket |
| 게임 엔진 | PokerKit | 텍사스 홀덤 로직 |
| 메인 DB | PostgreSQL 15+ | 영구 데이터 저장 |
| 캐시/실시간 | Redis 7+ | 세션, 게임 상태, Pub/Sub |
| 프로세스 관리 | Gunicorn | 멀티 워커 관리 |
| 작업 큐 | Celery | 비동기 작업 처리 |

### 추천 오픈소스 (v1.3 추가)
| 라이브러리 | 용도 | 효과 |
|-----------|------|------|
| **orjson** | JSON 직렬화 | 3-10배 성능 향상 |
| **structlog** | 구조화 로깅 | 디버깅/모니터링 용이 |
| **httpx** | 비동기 HTTP | 암호화폐 API 호출 |
| **tenacity** | 재시도 로직 | 외부 API 안정성 |
| **slowapi** | Rate Limiting | DDoS/악용 방지 |
| **sentry-sdk** | 에러 추적 | 프로덕션 모니터링 |
| **msgpack** | Binary 직렬화 | WebSocket 50-70% 감소 |

```bash
# 설치
pip install orjson structlog httpx tenacity slowapi sentry-sdk msgpack celery
```

---

## 작업 계획서 참조

**메인 문서**: [BACKEND_SCALE_WORKPLAN.md](../../../BACKEND_SCALE_WORKPLAN.md)

### Phase 구조 (11단계)
| Phase | 작업 내용 | 우선순위 |
|-------|---------|----------|
| 1 | 커넥션 풀 & 인프라 강화 | ⭐⭐⭐⭐⭐ |
| 2 | WebSocket 클러스터링 (Sticky Session) | ⭐⭐⭐⭐⭐ |
| 3 | 데이터베이스 최적화 | ⭐⭐⭐⭐⭐ |
| 4 | Redis 고가용성 + 게임 상태 캐싱 | ⭐⭐⭐⭐⭐ |
| 5 | KRW + 암호화폐 입출금 | ⭐⭐⭐⭐⭐ |
| 6 | Rake & 경제 시스템 | ⭐⭐⭐⭐ |
| 7 | 부하 테스트 (k6) | ⭐⭐⭐⭐⭐ |
| 8 | 모니터링 (Prometheus/Grafana) | ⭐⭐⭐⭐ |
| 9 | 운영 안정화 | ⭐⭐⭐ |
| 10 | 성능 최적화 (MessagePack, Celery) | ⭐⭐⭐⭐ |
| 11 | 오픈소스 통합 (orjson, structlog 등) | ⭐⭐⭐⭐ |

---

## 작업 규칙 (필수)

### 세션 중단 대비
```
╔═══════════════════════════════════════════════════════════════╗
║  ⚠️ 토큰 한도로 작업이 갑자기 중단될 수 있음                    ║
╠═══════════════════════════════════════════════════════════════╣
║  필수 규칙:                                                    ║
║  ✓ 각 하위 작업 완료 즉시 [ ] → [x] 체크                       ║
║  ✓ 단계 완료 시 날짜/시간 기록                                  ║
║  ✓ Phase 완료 시 git commit 실행                               ║
║  ✓ 작업 중단 전 반드시 git add . 실행                           ║
╚═══════════════════════════════════════════════════════════════╝
```

### 작업 시작 시
1. BACKEND_SCALE_WORKPLAN.md 읽기
2. 현재 Phase 확인 (미완료 체크박스 찾기)
3. 미완료 작업부터 순차 진행

### 작업 완료 시
```bash
# 1. 완료 체크박스 업데이트
# 2. 커밋
git add .
git commit -m "Phase X.Y 완료: [작업 설명]"
```

---

## 핵심 파일 경로

### 백엔드 구조
```
backend/
├── app/
│   ├── api/           # REST 엔드포인트
│   │   ├── auth.py
│   │   ├── rooms.py
│   │   ├── users.py
│   │   └── wallet.py  # 암호화폐 입출금
│   ├── engine/        # 게임 엔진 (PokerKit 래퍼)
│   │   ├── core.py
│   │   └── snapshot.py
│   ├── services/      # 비즈니스 로직
│   │   ├── auth.py
│   │   ├── room.py
│   │   ├── crypto_deposit.py
│   │   ├── crypto_withdrawal.py
│   │   ├── exchange_rate.py
│   │   └── rake.py
│   ├── ws/            # WebSocket
│   │   ├── gateway.py
│   │   ├── events.py
│   │   ├── pubsub.py
│   │   └── handlers/
│   ├── cache/         # Redis 캐싱
│   │   ├── table_cache.py
│   │   └── sync_service.py
│   ├── tasks/         # Celery 태스크
│   │   ├── celery_app.py
│   │   ├── settlement.py
│   │   └── analytics.py
│   ├── middleware/    # 미들웨어
│   │   └── rate_limit.py
│   ├── utils/         # 유틸리티
│   │   ├── json_utils.py
│   │   └── http_client.py
│   ├── models/        # SQLAlchemy 모델
│   ├── schemas/       # Pydantic 스키마
│   ├── config.py      # 설정
│   ├── logging_config.py
│   └── main.py        # 앱 진입점
├── tests/
└── alembic/           # DB 마이그레이션
```

### 설정 파일
- `.env` / `.env.example` - 환경 변수
- `backend/app/config.py` - 앱 설정

---

## 주요 구현 패턴

### 1. DB Connection Pool (Phase 1)
```python
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=50,
    max_overflow=30,
    pool_pre_ping=True
)
```

### 2. Redis Pub/Sub (Phase 2)
```python
# 발행
await redis.publish(f"table:{table_id}", json.dumps(event))

# 구독
async for message in pubsub.listen():
    await websocket.send_json(message)
```

### 3. 암호화폐 입금 처리 (Phase 5)
```python
# 1. 지갑 주소 생성
# 2. 블록체인 입금 감지 (webhook)
# 3. 환율 조회 (BTC/KRW)
# 4. KRW 잔액 업데이트
# 5. 감사 로그 기록 (3중)
```

### 4. 분산 락 (Phase 4)
```lua
-- Redis Lua Script
if redis.call("SET", key, value, "NX", "EX", ttl) then
    return 1
end
return 0
```

### 5. MessagePack 직렬화 (Phase 10)
```python
import msgpack

def encode(data: dict) -> bytes:
    return msgpack.packb(data, use_bin_type=True)
```

### 6. 구조화 로깅 (Phase 11)
```python
import structlog
logger = structlog.get_logger()
logger.info("player_action", table_id=tid, action=action)
```

---

## 테스트 명령어

```bash
# 단위 테스트
cd backend && pytest tests/ -v

# 특정 테스트
pytest tests/api/test_auth.py -v

# 부하 테스트 (k6)
k6 run tests/load/websocket_test.js --vus 100 --duration 5m

# Celery 워커 실행
celery -A app.tasks.celery_app worker -Q settlement -c 2
```

---

## 주의사항

### 보안
- 암호화폐 개인키 절대 코드에 하드코딩 금지
- 환경 변수 또는 Vault 사용
- 모든 금융 거래 3중 로깅 (DB + Redis Stream + 파일)
- Rate Limiting 필수 (slowapi)

### 성능
- JSON → orjson (3-10배 향상)
- WebSocket → MessagePack (50-70% 감소)
- 게임 상태 → Redis Hash 캐싱 (DB 부하 70-90% 감소)
- 정산/통계 → Celery 비동기 처리

### 동시성
- 잔액 변경 시 분산 락 필수
- 테이블당 하나의 상태 관리자
- stateVersion으로 순서 보장

### 관측성
- structlog: 구조화 로깅
- sentry-sdk: 에러 추적
- Prometheus + Grafana: 메트릭 대시보드

---

## 관련 문서

- [docs/10-engine-architecture.md](../../../docs/10-engine-architecture.md) - 엔진 아키텍처
- [docs/20-realtime-protocol-v1.md](../../../docs/20-realtime-protocol-v1.md) - WebSocket 프로토콜
- [docs/51-observability.md](../../../docs/51-observability.md) - 모니터링 설계
