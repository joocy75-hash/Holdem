# 관측성 (Observability) 설계

> 로깅, 메트릭, 트레이싱 설계

---

## 1. 로깅

### 1.1 구조화 로그 형식

```json
{
  "timestamp": "2026-01-11T10:30:00.000Z",
  "level": "INFO",
  "logger": "app.ws.table",
  "message": "Action processed",
  "traceId": "abc-123-def",
  "requestId": "req-456",
  "userId": "user-789",
  "tableId": "table-001",
  "handId": "hand-002",
  "stateVersion": 15,
  "action": "raise",
  "amount": 100,
  "processingTimeMs": 12,
  "result": "accepted"
}
```

### 1.2 필수 로그 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `timestamp` | ISO8601 | 로그 시간 |
| `level` | string | DEBUG/INFO/WARNING/ERROR |
| `logger` | string | 로거 이름 |
| `message` | string | 로그 메시지 |
| `traceId` | string | 분산 추적 ID |

### 1.3 컨텍스트별 추가 필드

| 컨텍스트 | 필드 |
|---------|------|
| 인증 | `userId`, `sessionId` |
| 테이블 | `tableId`, `handId`, `stateVersion` |
| 액션 | `action`, `amount`, `result` |
| 성능 | `processingTimeMs` |

### 1.4 로그 레벨 가이드

| 레벨 | 용도 |
|------|------|
| DEBUG | 개발 디버깅 정보 |
| INFO | 정상 동작 기록 |
| WARNING | 잠재적 문제 |
| ERROR | 오류 발생 |

### 1.5 로깅 구현

```python
import structlog

logger = structlog.get_logger()

async def process_action(table_id: str, action: Action):
    log = logger.bind(
        table_id=table_id,
        action=action.type,
        amount=action.amount
    )
    
    start = time.time()
    try:
        result = await _do_process(action)
        log.info(
            "Action processed",
            result="accepted",
            processing_time_ms=(time.time() - start) * 1000
        )
        return result
    except InvalidActionError as e:
        log.warning(
            "Action rejected",
            result="rejected",
            reason=str(e)
        )
        raise
```

---

## 2. 메트릭

### 2.1 핵심 메트릭

| 메트릭 | 타입 | 설명 |
|--------|------|------|
| `ws_connections_active` | Gauge | 활성 WebSocket 연결 수 |
| `tables_active` | Gauge | 활성 테이블 수 |
| `rooms_active` | Gauge | 활성 방 수 |
| `hands_completed_total` | Counter | 완료된 핸드 수 |
| `actions_processed_total` | Counter | 처리된 액션 수 |
| `action_latency_seconds` | Histogram | 액션 처리 지연 |
| `reconnect_total` | Counter | 재연결 횟수 |
| `snapshot_requests_total` | Counter | 스냅샷 요청 수 |

### 2.2 메트릭 라벨

```python
# 액션 메트릭 라벨
action_latency.labels(
    action_type="raise",
    result="accepted"
).observe(latency)

# 연결 메트릭 라벨
ws_connections.labels(
    status="connected"
).inc()
```

### 2.3 Prometheus 설정

```python
from prometheus_client import Counter, Gauge, Histogram

ws_connections = Gauge(
    'ws_connections_active',
    'Active WebSocket connections',
    ['status']
)

action_latency = Histogram(
    'action_latency_seconds',
    'Action processing latency',
    ['action_type', 'result'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0]
)

actions_total = Counter(
    'actions_processed_total',
    'Total actions processed',
    ['action_type', 'result']
)
```

---

## 3. 트레이싱

### 3.1 트레이스 ID 전파

```python
# 요청 시작 시 트레이스 ID 생성/추출
@app.middleware("http")
async def trace_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-ID") or generate_trace_id()
    
    with structlog.contextvars.bind_contextvars(trace_id=trace_id):
        response = await call_next(request)
        response.headers["X-Trace-ID"] = trace_id
        return response
```

### 3.2 스팬 구조

```
[HTTP Request]
  └── [Auth Validation]
  └── [WebSocket Handler]
        └── [Action Processing]
              └── [Engine Apply]
              └── [State Save]
        └── [Broadcast]
```

---

## 4. 알림

### 4.1 알림 규칙

| 조건 | 심각도 | 액션 |
|------|--------|------|
| 에러율 > 1% | Warning | Slack 알림 |
| 에러율 > 5% | Critical | PagerDuty |
| 지연 p95 > 500ms | Warning | Slack 알림 |
| 연결 수 급감 | Critical | PagerDuty |

### 4.2 Alertmanager 설정

```yaml
groups:
  - name: poker-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(actions_processed_total{result="error"}[5m]) > 0.01
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
```

---

## 5. 대시보드

### 5.1 운영 대시보드 패널

| 패널 | 메트릭 |
|------|--------|
| 활성 연결 | `ws_connections_active` |
| 활성 테이블 | `tables_active` |
| 액션 처리량 | `rate(actions_processed_total[1m])` |
| 액션 지연 | `action_latency_seconds` |
| 에러율 | `rate(actions_processed_total{result="error"}[5m])` |
| 재연결율 | `rate(reconnect_total[5m])` |

---

## 관련 문서

- [50-test-plan.md](./50-test-plan.md) - 테스트 플랜
- [52-deploy-staging.md](./52-deploy-staging.md) - 배포 가이드
