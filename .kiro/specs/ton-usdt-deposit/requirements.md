# TON/USDT 기반 자동 입금 시스템 - 최종 작업계획서

> 작성일: 2026-01-16
> 버전: 1.0

---

## 1. 프로젝트 개요

### 1.1 프로젝트 명
**TON 가상계좌 자동 충전 시스템** (10만원 단위 정확 매칭 + 시간제한)

### 1.2 목표
- 회원이 Telegram Bot/웹에서 "10만원 입금 신청" → 실시간 환율로 USDT 금액 계산 → QR코드 발급
- QR 발급 후 **30분 시간제한** (서버 측 만료 처리)
- 고객 입금 → 자동 감지 → Telegram 알림 + 내부 포인트 자동 승인
- 자동 확인 지연 목표: **10~60초 이내**

### 1.3 주요 특징
| 특징 | 설명 |
|------|------|
| 가상계좌 방식 | 매번 동적 QR + 고유 메모 + 시간제한 |
| 지갑 호환성 | Telegram @wallet, Tonkeeper 등 외부 지갑 지원 |
| 지원 코인 | **USDT (Jetton)** 우선 (가격 안정성), TON 옵션 |
| 시간제한 | QR 발급 후 30분 내 입금 필수 |

### 1.4 현재 기준 가격 (2026년 1월 16일)
- 1 USDT ≈ 1,468 ~ 1,473 KRW
- 100,000 KRW ≈ **68.0 ~ 68.1 USDT**
- 1 TON ≈ 2,400 ~ 2,500 KRW (변동성 있음)

### 1.5 USDT Jetton 정보
- **Master 주소**: `EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs`
- **Decimals**: 6 (1 USDT = 1,000,000 units)

---

## 2. 시스템 흐름도

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           입금 신청 플로우                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. 회원 → Bot/웹에서 입금 신청 (예: /deposit 100000)                    │
│                          │                                              │
│                          ▼                                              │
│  2. 서버 → 실시간 가격 API 호출 (CoinGecko/Binance)                      │
│           → USDT 금액 계산 (예: 68.027 USDT)                            │
│           → 고유 메모 생성: user_{telegram_id}_{timestamp}_{random4}     │
│           → expires_at = now() + 30분                                   │
│           → ton://transfer URI 생성                                     │
│                          │                                              │
│                          ▼                                              │
│  3. Bot → QR 이미지 + 주소 + 금액 + 메모 + "30분 내 입금" 전송           │
│                          │                                              │
│                          ▼                                              │
│  4. 고객 → QR 스캔 → Tonkeeper/@wallet에서 입금                         │
│                          │                                              │
│                          ▼                                              │
│  5. 서버 → TON API polling (5~10초) → Jetton transfer 감지              │
│           → 메모 매칭 + amount ≥ calculated × 0.995                     │
│           → now() < expires_at 확인                                     │
│                          │                                              │
│              ┌───────────┴───────────┐                                  │
│              ▼                       ▼                                  │
│         [조건 충족]              [만료/불일치]                           │
│              │                       │                                  │
│              ▼                       ▼                                  │
│  6. 승인 → DB balance += 100000   만료 알림 → 재신청 유도               │
│         → status = confirmed      또는 수동 검토 큐                     │
│              │                                                          │
│              ▼                                                          │
│  7. Telegram 알림 → "입금 확인 완료! 10만원 충전되었습니다."             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 기술 스택

| 항목 | 기술 | 이유 |
|------|------|------|
| Telegram Bot | Python + aiogram v3 | 비동기 + TON 호환 최고 |
| 백엔드 | Python FastAPI | 기존 admin-backend와 통합 |
| DB | PostgreSQL | 기존 인프라 활용, 트랜잭션 안전 |
| TON 라이브러리 | pytoniq / tonapi-python | Jetton 지원 + 최신 |
| 가격 API | CoinGecko / Binance API | KRW 실시간 정확 |
| QR 생성 | qrcode[pil] | ton:// URI 이미지 생성 |
| 입금 확인 | TON Center API polling → tonapi.io webhook | 초기 polling, 중기 webhook |
| 캐싱 | Redis | 환율 캐싱, 세션 관리 |

---

## 4. 데이터베이스 스키마

### 4.1 기존 모델 수정 (admin-backend/app/models/crypto.py)

```python
# 네트워크 타입 추가
class NetworkType(str, Enum):
    TRON = "tron"      # 기존 TRC-20
    TON = "ton"        # 새로 추가

# CryptoDeposit 모델 확장
class CryptoDeposit(Base):
    # 기존 필드...
    network: NetworkType  # 네트워크 타입 추가
    memo: str            # TON 메모 (고유 식별자)
    expires_at: datetime  # 만료 시간 (30분)
    requested_krw: int    # 요청 KRW 금액 (100000)
```

### 4.2 새 테이블: 입금 요청 (Deposit Requests)

```sql
CREATE TABLE deposit_requests (
    id UUID PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    telegram_id BIGINT,                    -- Telegram 사용자 ID
    requested_krw BIGINT NOT NULL,         -- 요청 금액 (100000)
    calculated_usdt DECIMAL(20, 6) NOT NULL, -- 계산된 USDT
    exchange_rate DECIMAL(10, 2) NOT NULL,  -- 적용 환율
    memo VARCHAR(100) UNIQUE NOT NULL,      -- 고유 메모
    qr_data TEXT NOT NULL,                  -- ton:// URI
    status VARCHAR(20) DEFAULT 'pending',   -- pending/confirmed/expired/cancelled
    expires_at TIMESTAMP NOT NULL,          -- 만료 시간
    created_at TIMESTAMP DEFAULT NOW(),
    confirmed_at TIMESTAMP,
    tx_hash VARCHAR(66),                    -- 확인된 트랜잭션 해시
    
    INDEX idx_memo (memo),
    INDEX idx_status_expires (status, expires_at),
    INDEX idx_user_id (user_id)
);
```

---

## 5. API 설계

### 5.1 입금 신청 API

```
POST /api/deposit/request
Request:
{
    "user_id": "uuid",
    "telegram_id": 123456789,  // optional
    "amount_krw": 100000
}

Response:
{
    "request_id": "uuid",
    "wallet_address": "EQ...",
    "amount_usdt": 68.027,
    "exchange_rate": 1470.50,
    "memo": "user_123456789_1705401234_a1b2",
    "qr_uri": "ton://transfer/EQ...?amount=68027000&text=user_123456789_...",
    "qr_image_base64": "...",
    "expires_at": "2026-01-16T15:30:00Z",
    "expires_in_seconds": 1800
}
```

### 5.2 입금 상태 조회 API

```
GET /api/deposit/status/{request_id}

Response:
{
    "request_id": "uuid",
    "status": "pending|confirmed|expired",
    "amount_krw": 100000,
    "amount_usdt": 68.027,
    "expires_at": "2026-01-16T15:30:00Z",
    "remaining_seconds": 1234,
    "tx_hash": null,
    "confirmed_at": null
}
```

### 5.3 관리자 API

```
GET /api/admin/deposits                    # 입금 목록
GET /api/admin/deposits/{id}               # 입금 상세
POST /api/admin/deposits/{id}/manual-confirm  # 수동 승인
POST /api/admin/deposits/{id}/reject       # 거부
GET /api/admin/wallet/balance              # 핫월렛 잔액
```

---

## 6. 개발 단계별 일정

### Phase 1: 기획 & 준비 (Week 1)

- [ ] 1.1 요구사항 최종 확정
  - 30분 만료, ±0.5% 금액 여유, 메모 규칙
  - 지원 금액 단위 (10만원 고정 vs 다양한 금액)

- [ ] 1.2 TON Hot Wallet 생성
  - Mainnet 지갑 생성
  - USDT Jetton Wallet 주소 확인
  - Cold Wallet 이동 계획 수립

- [ ] 1.3 DB 스키마 설계 및 마이그레이션
  - deposit_requests 테이블 생성
  - 기존 crypto_deposits 모델 확장

- [ ] 1.4 Telegram Bot 생성
  - @BotFather에서 봇 생성
  - 봇 토큰 발급 및 환경변수 설정

### Phase 2: 입금 신청 & QR 발급 (Week 2)

- [ ] 2.1 환율 서비스 구현
  - CoinGecko API 연동 (USDT/KRW)
  - Binance API 폴백
  - Redis 캐싱 (30초 TTL)
  - 파일: `admin-backend/app/services/crypto/ton_exchange_rate.py`

- [ ] 2.2 입금 요청 API 구현
  - USDT 금액 계산 (decimals=6)
  - 고유 메모 생성
  - expires_at 설정 (30분)
  - 파일: `admin-backend/app/api/ton_deposit.py`

- [ ] 2.3 QR 코드 생성 서비스
  - ton://transfer URI 생성
  - QR 이미지 생성 (qrcode[pil])
  - Base64 인코딩
  - 파일: `admin-backend/app/services/crypto/qr_generator.py`

- [ ] 2.4 Telegram Bot 기본 구현
  - /deposit 명령어 처리
  - QR 이미지 + 안내 메시지 전송
  - 파일: `admin-backend/app/bot/deposit_bot.py`

### Phase 3: 입금 감지 & 자동 승인 (Week 3-4)

- [ ] 3.1 TON Client 구현
  - pytoniq 또는 tonapi-python 연동
  - Jetton Wallet 주소 조회
  - 트랜잭션 조회
  - 파일: `admin-backend/app/services/crypto/ton_client.py`

- [ ] 3.2 입금 모니터링 서비스
  - Polling 방식 (5~10초 간격)
  - Jetton transfer 감지
  - 메모 매칭 로직
  - 파일: `admin-backend/app/services/crypto/ton_deposit_monitor.py`

- [ ] 3.3 자동 승인 로직
  - 조건 검증: 메모 + 금액(±0.5%) + 만료시간
  - 잔액 업데이트
  - 상태 변경 (pending → confirmed)
  - 파일: `admin-backend/app/services/crypto/deposit_processor.py`

- [ ] 3.4 만료 처리 로직
  - Cron job 또는 polling 시 만료 체크
  - status = expired 업데이트
  - 만료 알림 발송
  - 파일: `admin-backend/app/tasks/deposit_expiry.py`

- [ ] 3.5 Telegram 알림 서비스
  - 입금 확인 알림
  - 만료 알림
  - 관리자 알림 (고액/이상 거래)
  - 파일: `admin-backend/app/services/telegram_notifier.py`

### Phase 4: 예외 처리 & 보안 (Week 5)

- [ ] 4.1 예외 케이스 처리
  - 메모 없는 입금 → 수동 검토 큐
  - 금액 부족 입금 → 수동 검토 큐
  - 만료 후 입금 → 무시 + 환불 플로우
  - 중복 입금 방지

- [ ] 4.2 Cold Wallet 이동
  - 자동 이동 스크립트 (매일/매주)
  - 임계값 설정 (Hot Wallet 최소 잔고)
  - 파일: `admin-backend/app/tasks/cold_wallet_transfer.py`

- [ ] 4.3 보안 강화
  - Rate limiting (입금 요청 제한)
  - 2FA 연동 (고액 출금)
  - API 키 보호
  - 스캠 Jetton 방지 (Master 주소 하드코딩)

### Phase 5: 관리자 대시보드 연동 (Week 6)

- [ ] 5.1 관리자 API 구현
  - 입금 목록/상세 조회
  - 수동 승인/거부
  - 핫월렛 잔액 조회
  - 파일: `admin-backend/app/api/admin_ton_deposit.py`

- [ ] 5.2 관리자 UI 구현
  - 입금 대기열 페이지
  - 입금 상세 모달
  - 수동 승인/거부 버튼
  - 파일: `admin-frontend/src/app/(dashboard)/deposits/page.tsx`

- [ ] 5.3 통계 대시보드
  - 일별/주별/월별 입금 통계
  - 환율 히스토리 차트
  - 파일: `admin-frontend/src/components/crypto/DepositStats.tsx`

### Phase 6: 테스트 & 론칭 (Week 7-8)

- [ ] 6.1 Testnet 테스트
  - TON Testnet에서 전체 플로우 테스트
  - 다양한 시나리오 검증

- [ ] 6.2 스트레스 테스트
  - 동시 50건 입금 요청 테스트
  - Polling 성능 테스트

- [ ] 6.3 Mainnet 이전
  - 환경변수 전환
  - 실제 입금 테스트 (소액)

- [ ] 6.4 모니터링 설정
  - Sentry 에러 추적
  - Telegram 알림 채널
  - Grafana 대시보드

- [ ] 6.5 문서화 & FAQ
  - 사용자 가이드
  - "텔레그램 없이 Tonkeeper 사용법"
  - 관리자 매뉴얼

---

## 7. 파일 구조

```
admin-backend/
├── app/
│   ├── api/
│   │   ├── ton_deposit.py          # 입금 신청 API
│   │   └── admin_ton_deposit.py    # 관리자 API
│   ├── bot/
│   │   └── deposit_bot.py          # Telegram Bot
│   ├── models/
│   │   └── crypto.py               # 모델 확장
│   ├── services/
│   │   ├── crypto/
│   │   │   ├── ton_client.py       # TON 네트워크 클라이언트
│   │   │   ├── ton_exchange_rate.py # 환율 서비스
│   │   │   ├── ton_deposit_monitor.py # 입금 모니터링
│   │   │   ├── deposit_processor.py # 입금 처리
│   │   │   └── qr_generator.py     # QR 생성
│   │   └── telegram_notifier.py    # Telegram 알림
│   └── tasks/
│       ├── deposit_expiry.py       # 만료 처리
│       └── cold_wallet_transfer.py # Cold Wallet 이동

admin-frontend/
├── src/
│   ├── app/(dashboard)/
│   │   └── deposits/
│   │       └── page.tsx            # 입금 관리 페이지
│   └── components/
│       └── crypto/
│           ├── DepositList.tsx     # 입금 목록
│           ├── DepositDetail.tsx   # 입금 상세
│           └── DepositStats.tsx    # 입금 통계
```

---

## 8. 환경변수

```env
# TON Network
TON_NETWORK=mainnet                    # mainnet / testnet
TON_HOT_WALLET_ADDRESS=EQ...           # Hot Wallet 주소
TON_HOT_WALLET_MNEMONIC=...            # Hot Wallet 니모닉 (암호화 저장)
TON_USDT_MASTER_ADDRESS=EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs

# TON API
TONAPI_KEY=...                         # tonapi.io API 키
TON_CENTER_API_KEY=...                 # toncenter.com API 키

# Telegram Bot
TELEGRAM_BOT_TOKEN=...                 # Bot 토큰
TELEGRAM_ADMIN_CHAT_ID=...             # 관리자 알림 채널

# Exchange Rate API
COINGECKO_API_KEY=...                  # CoinGecko API 키 (선택)
BINANCE_API_KEY=...                    # Binance API 키 (폴백)

# Deposit Settings
DEPOSIT_EXPIRY_MINUTES=30              # 입금 만료 시간
DEPOSIT_AMOUNT_TOLERANCE=0.005         # 금액 허용 오차 (0.5%)
DEPOSIT_POLLING_INTERVAL=10            # Polling 간격 (초)
HOT_WALLET_MIN_BALANCE=1000            # Hot Wallet 최소 잔고 (USDT)
```

---

## 9. 예상 비용

| 항목 | 비용 |
|------|------|
| 개발 (내부) | - |
| 서버/VPS | 월 3~10만 원 |
| TON API (tonapi.io) | 월 5~20만 원 |
| CoinGecko API | 무료 (기본) |
| **총 월 운영비** | **약 10~30만 원** |

---

## 10. 리스크 & 대응

| 리스크 | 대응 |
|--------|------|
| 가격 변동 | USDT 우선 사용 (거의 0%), TON 사용 시 ±2% 여유 |
| 만료 후 입금 | 서버 무시 + 알림, 수동 환불 플로우 |
| 네트워크 지연 | confirm 1~2회 + retry |
| 보안 | Hot 최소 잔고, multisig 고려, API 키 보호 |
| 스캠 Jetton | Master 주소 하드코딩 + 검증 |

---

## 11. 체크포인트

### Week 2 완료 조건
- [ ] 환율 API 정상 동작
- [ ] QR 코드 생성 확인
- [ ] Telegram Bot 기본 동작

### Week 4 완료 조건
- [ ] Testnet에서 입금 감지 확인
- [ ] 자동 승인 플로우 동작
- [ ] 만료 처리 동작

### Week 6 완료 조건
- [ ] 관리자 대시보드 연동 완료
- [ ] 수동 승인/거부 동작

### Week 8 완료 조건
- [ ] Mainnet 실제 입금 테스트 완료
- [ ] 모니터링 설정 완료
- [ ] 문서화 완료

---

## 12. 참고 자료

- TON 공식 문서: https://docs.ton.org/
- tonapi.io: https://tonapi.io/
- pytoniq: https://github.com/yungwine/pytoniq
- USDT Jetton: https://tonviewer.com/EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs

---

> 이 계획서로 진행하면 **완벽한 가상계좌 수준**의 안전하고 사용자 친화적인 자동 입금 시스템이 완성됩니다.
