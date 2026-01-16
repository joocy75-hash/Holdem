# 백엔드 및 관리자 대시보드 업그레이드 설계 문서

> 작성일: 2026-01-16

---

## 1. 아키텍처 개요

### 1.1 시스템 구성도

```
┌─────────────────────────────────────────────────────────────────┐
│                        Admin Dashboard                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐         ┌─────────────────┐               │
│  │ Admin Frontend  │ ◄─────► │ Admin Backend   │               │
│  │ (Next.js 14)    │  REST   │ (FastAPI)       │               │
│  └─────────────────┘         └────────┬────────┘               │
│                                       │                         │
│                              ┌────────▼────────┐               │
│                              │   Admin DB      │               │
│                              │  (PostgreSQL)   │               │
│                              └─────────────────┘               │
└─────────────────────────────────────────────────────────────────┘
                                       │
                                       │ Read-Only / Admin API
                                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Main Game System                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐         ┌─────────────────┐               │
│  │ Game Frontend   │ ◄─────► │ Game Backend    │               │
│  │ (Next.js)       │   WS    │ (FastAPI)       │               │
│  └─────────────────┘         └────────┬────────┘               │
│                                       │                         │
│                    ┌──────────────────┼──────────────────┐     │
│                    ▼                  ▼                  ▼     │
│           ┌─────────────┐    ┌─────────────┐    ┌───────────┐ │
│           │  Main DB    │    │   Redis     │    │  TRON     │ │
│           │ (PostgreSQL)│    │  (Cache)    │    │ Network   │ │
│           └─────────────┘    └─────────────┘    └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 데이터 흐름

1. **Admin Dashboard → Main System (읽기)**
   - Admin Backend가 Main DB에 읽기 전용 연결
   - Redis에서 실시간 메트릭 조회

2. **Admin Dashboard → Main System (쓰기)**
   - Admin Backend가 Main Backend의 Admin API 호출
   - 제재, 잔액 조정 등 민감한 작업

3. **암호화폐 연동**
   - Admin Backend가 TRON 네트워크 직접 연결
   - 입출금 모니터링 및 처리

---

## 2. 관리자 대시보드 설계

### 2.1 대시보드 모니터링

#### 메트릭 수집 아키텍처

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Main Backend   │────►│     Redis       │◄────│  Admin Backend  │
│  (메트릭 발행)   │     │  (메트릭 저장)   │     │  (메트릭 조회)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │ Admin Frontend  │
                                               │  (차트 렌더링)   │
                                               └─────────────────┘
```

#### Redis 키 구조

```
# CCU (동시 접속자)
ccu:current -> int
ccu:history:{timestamp} -> int

# DAU (일일 활성 사용자)
dau:{date} -> int
dau:hourly:{date}:{hour} -> int

# 방 통계
rooms:active -> int
rooms:players:total -> int
rooms:distribution:{type} -> int

# 서버 상태
server:health:cpu -> float
server:health:memory -> float
server:health:latency -> float
```

### 2.2 사용자 관리

#### 검색 API 설계

```python
# GET /api/users
# Query Parameters:
# - search: str (username, email, user_id)
# - is_banned: bool
# - balance_min: int
# - balance_max: int
# - registered_after: datetime
# - registered_before: datetime
# - last_login_after: datetime
# - page: int
# - page_size: int
# - sort_by: str
# - sort_order: asc|desc

# Response:
{
    "items": [
        {
            "id": "uuid",
            "username": "string",
            "email": "string",
            "balance": 0,
            "is_banned": false,
            "created_at": "datetime",
            "last_login": "datetime"
        }
    ],
    "total": 0,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
}
```

### 2.3 제재 시스템

#### Ban 모델

```python
class Ban(Base):
    __tablename__ = "bans"
    
    id: str  # UUID
    user_id: str  # 제재 대상
    admin_id: str  # 제재 실행 관리자
    ban_type: BanType  # TEMPORARY, PERMANENT, CHAT_ONLY
    reason: str
    expires_at: datetime | None  # 임시 제재 만료 시간
    created_at: datetime
    lifted_at: datetime | None  # 해제 시간
    lifted_by: str | None  # 해제 관리자

class BanType(Enum):
    TEMPORARY = "temporary"
    PERMANENT = "permanent"
    CHAT_ONLY = "chat_only"
```

#### 제재 플로우

```
1. 관리자가 제재 요청
2. Admin Backend가 Ban 레코드 생성
3. Admin Backend가 Main Backend Admin API 호출
4. Main Backend가 사용자 세션 종료
5. Main Backend가 로그인 차단 플래그 설정
6. AuditLog 기록
```

### 2.4 암호화폐 관리

#### 입금 처리 플로우

```
1. DepositMonitor가 TRON 네트워크 모니터링
2. 시스템 지갑으로 USDT 입금 감지
3. CryptoDeposit 레코드 생성 (status: PENDING)
4. 블록 확인 수 모니터링
5. 20 confirmations 도달 시 status: CONFIRMED
6. 사용자 게임 잔액에 반영
7. status: CREDITED
```

#### 출금 처리 플로우

```
1. 사용자가 출금 요청
2. CryptoWithdrawal 레코드 생성 (status: PENDING)
3. 관리자가 출금 대기열 확인
4. 금액에 따른 승인 권한 검증
5. 2FA 재인증
6. HSM/KMS로 트랜잭션 서명
7. TRON 네트워크로 전송
8. 트랜잭션 해시 기록
9. status: COMPLETED
```

---

## 3. 백엔드 보안 강화 설계

### 3.1 부정 행위 탐지

#### Anti-Collusion 시스템

```python
class AntiCollusionService:
    """담합 방지 서비스"""
    
    async def check_same_ip(self, room_id: str, user_id: str, ip: str) -> bool:
        """같은 IP가 이미 방에 있는지 확인"""
        pass
    
    async def check_device_fingerprint(
        self, room_id: str, user_id: str, fingerprint: str
    ) -> bool:
        """같은 기기가 이미 방에 있는지 확인"""
        pass
    
    async def detect_chip_dumping(
        self, user_id: str, opponent_id: str, hands: list
    ) -> float:
        """칩 밀어주기 패턴 점수 계산 (0.0 ~ 1.0)"""
        pass
```

#### 의심 패턴 정의

| 패턴 | 설명 | 점수 |
|------|------|------|
| 연속 폴드 | 특정 상대에게 연속 5회 이상 폴드 | 0.3 |
| 비정상 베팅 | 약한 핸드로 큰 베팅 후 폴드 | 0.4 |
| 동일 IP | 같은 방에 동일 IP 존재 | 0.5 |
| 칩 이동 | 특정 상대에게 일방적 칩 이동 | 0.6 |

### 3.2 봇 탐지

#### 행동 패턴 분석

```python
class BotDetector:
    """봇 탐지 서비스"""
    
    async def analyze_response_time(
        self, user_id: str, actions: list
    ) -> float:
        """응답 시간 분석 (너무 일정하면 의심)"""
        pass
    
    async def analyze_action_pattern(
        self, user_id: str, hands: list
    ) -> float:
        """액션 패턴 분석 (너무 규칙적이면 의심)"""
        pass
    
    async def calculate_bot_score(self, user_id: str) -> float:
        """종합 봇 점수 계산 (0.0 ~ 1.0)"""
        pass
```

### 3.3 패킷 암호화

#### WebSocket 메시지 암호화

```python
class EncryptedWebSocket:
    """암호화된 WebSocket 통신"""
    
    async def handshake(self, websocket: WebSocket) -> bytes:
        """키 교환 (ECDH)"""
        pass
    
    def encrypt(self, message: dict, session_key: bytes) -> bytes:
        """메시지 암호화 (AES-256-GCM)"""
        pass
    
    def decrypt(self, ciphertext: bytes, session_key: bytes) -> dict:
        """메시지 복호화"""
        pass
```

---

## 4. 데이터베이스 스키마

### 4.1 Admin DB 추가 테이블

```sql
-- 제재 테이블
CREATE TABLE bans (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    admin_id UUID NOT NULL,
    ban_type VARCHAR(20) NOT NULL,
    reason TEXT NOT NULL,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    lifted_at TIMESTAMP,
    lifted_by UUID
);

-- 암호화폐 입금
CREATE TABLE crypto_deposits (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    tx_hash VARCHAR(66) UNIQUE NOT NULL,
    wallet_address VARCHAR(42) NOT NULL,
    usdt_amount DECIMAL(18, 6) NOT NULL,
    krw_amount BIGINT NOT NULL,
    exchange_rate DECIMAL(10, 2) NOT NULL,
    confirmations INT DEFAULT 0,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    confirmed_at TIMESTAMP,
    credited_at TIMESTAMP
);

-- 암호화폐 출금
CREATE TABLE crypto_withdrawals (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    destination_wallet VARCHAR(42) NOT NULL,
    usdt_amount DECIMAL(18, 6) NOT NULL,
    krw_amount BIGINT NOT NULL,
    exchange_rate DECIMAL(10, 2) NOT NULL,
    network_fee DECIMAL(18, 6),
    tx_hash VARCHAR(66),
    status VARCHAR(20) NOT NULL,
    approved_by UUID,
    approved_at TIMESTAMP,
    rejected_by UUID,
    rejected_at TIMESTAMP,
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- 의심 활동
CREATE TABLE suspicious_activities (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    activity_type VARCHAR(50) NOT NULL,
    score DECIMAL(3, 2) NOT NULL,
    details JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    reviewed_by UUID,
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 4.2 Main DB 추가 인덱스

```sql
-- 부정 행위 분석용 인덱스
CREATE INDEX idx_hand_history_users ON hand_history (user_id, created_at);
CREATE INDEX idx_hand_history_room ON hand_history (room_id, created_at);
CREATE INDEX idx_actions_user_time ON hand_actions (user_id, action_time);
```

---

## 5. API 설계

### 5.1 Admin API 엔드포인트

```
# 대시보드
GET  /api/dashboard/summary
GET  /api/dashboard/ccu
GET  /api/dashboard/ccu/history
GET  /api/dashboard/dau
GET  /api/dashboard/dau/history
GET  /api/dashboard/rooms
GET  /api/dashboard/server/health

# 사용자 관리
GET  /api/users
GET  /api/users/{id}
GET  /api/users/{id}/transactions
GET  /api/users/{id}/login-history
GET  /api/users/{id}/hands

# 제재 관리
GET  /api/bans
POST /api/bans
DELETE /api/bans/{id}

# 암호화폐
GET  /api/crypto/deposits
GET  /api/crypto/deposits/{id}
POST /api/crypto/deposits/{id}/approve
POST /api/crypto/deposits/{id}/reject
GET  /api/crypto/withdrawals
GET  /api/crypto/withdrawals/{id}
POST /api/crypto/withdrawals/{id}/approve
POST /api/crypto/withdrawals/{id}/reject
GET  /api/crypto/wallet/status
GET  /api/crypto/exchange-rate
GET  /api/crypto/exchange-rate/history

# 방 관리
GET  /api/rooms
GET  /api/rooms/{id}
POST /api/rooms/{id}/close

# 핸드 리플레이
GET  /api/hands
GET  /api/hands/{id}
GET  /api/hands/{id}/export

# 의심 사용자
GET  /api/suspicious
GET  /api/suspicious/{id}
POST /api/suspicious/{id}/resolve
```

### 5.2 Main Backend Admin API

```
# 제재 연동
POST /admin/users/{id}/ban
POST /admin/users/{id}/unban

# 잔액 조정
POST /admin/users/{id}/balance/adjust

# 방 관리
POST /admin/rooms/{id}/close
POST /admin/rooms/{id}/message
```

---

## 6. 보안 고려사항

### 6.1 인증 및 권한

- 모든 Admin API는 JWT 인증 필수
- 역할 기반 접근 제어 (RBAC)
- 민감한 작업은 2FA 재인증 필요
- 30분 비활성 시 자동 로그아웃

### 6.2 암호화폐 보안

- 프라이빗 키는 HSM/KMS에만 저장
- 출금 시 다중 승인 필요 (금액별)
- 모든 트랜잭션 감사 로그 기록
- 핫월렛 잔액 임계값 알림

### 6.3 감사 로그

- 모든 관리자 액션 기록
- IP 주소, 타임스탬프 포함
- 변경 전/후 데이터 저장
- 로그 변조 방지 (해시 체인)

---

## 7. 성능 고려사항

### 7.1 캐싱 전략

- CCU/DAU: Redis 캐싱 (5초 TTL)
- 환율: Redis 캐싱 (30초 TTL)
- 사용자 목록: 페이지네이션 필수
- 통계 데이터: 사전 집계 테이블

### 7.2 데이터베이스 최적화

- 읽기 전용 쿼리는 Read Replica 사용
- 대용량 조회는 커서 기반 페이지네이션
- 통계 쿼리는 Materialized View 활용

---

## 8. 테스트 전략

### 8.1 단위 테스트

- 각 서비스 클래스별 단위 테스트
- 모킹을 통한 외부 의존성 격리

### 8.2 통합 테스트

- API 엔드포인트 통합 테스트
- 데이터베이스 연동 테스트

### 8.3 E2E 테스트

- 전체 플로우 테스트 (입금 → 게임 → 출금)
- 제재 플로우 테스트

### 8.4 보안 테스트

- 침투 테스트
- 권한 우회 테스트
- SQL Injection 테스트

---

## 9. 참고 문서

- `.kiro/specs/admin-dashboard/requirements.md`
- `.kiro/specs/admin-dashboard/tasks.md`
- `docs/API_REFERENCE.md`
- `docs/20-realtime-protocol-v1.md`
