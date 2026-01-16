# TON/USDT 입금 시스템 가이드

## 목차
1. [개요](#개요)
2. [사용자 가이드](#사용자-가이드)
3. [관리자 매뉴얼](#관리자-매뉴얼)
4. [기술 문서](#기술-문서)
5. [FAQ](#faq)

---

## 개요

TON/USDT 입금 시스템은 Telegram Bot을 통해 사용자가 USDT를 입금하고 KRW 잔액을 충전할 수 있는 시스템입니다.

### 주요 기능
- **Telegram Bot**: /deposit 명령어로 입금 요청
- **QR 코드 생성**: TON 지갑 앱에서 스캔 가능한 QR 코드
- **실시간 환율**: CoinGecko/Binance API 연동
- **자동 입금 확인**: 블록체인 모니터링으로 자동 승인
- **관리자 대시보드**: 입금 현황 모니터링 및 수동 처리

### 지원 지갑
- Tonkeeper
- @wallet (Telegram)
- TON Space
- 기타 TON 호환 지갑

---

## 사용자 가이드

### 입금 방법

#### 1. Telegram Bot 시작
1. Telegram에서 입금 봇을 검색하여 시작
2. `/start` 명령어로 봇 활성화

#### 2. 입금 요청
1. `/deposit` 명령어 입력
2. 입금할 금액(KRW) 입력 (최소 10,000원 ~ 최대 10,000,000원)
3. QR 코드와 입금 정보 수신

#### 3. USDT 전송
1. TON 지갑 앱에서 QR 코드 스캔
2. **중요**: 메모(Comment)를 반드시 포함하여 전송
3. 표시된 USDT 금액 전송

#### 4. 입금 확인
- 자동 확인: 약 1-5분 소요
- 확인 완료 시 Telegram 알림 수신
- `/status` 명령어로 입금 내역 확인

### 주의사항
⚠️ **메모(Comment) 필수**: 메모 없이 전송 시 자동 매칭 불가
⚠️ **만료 시간**: 입금 요청 후 30분 내 전송 필요
⚠️ **금액 정확성**: 표시된 USDT 금액과 동일하게 전송

### 명령어 목록
| 명령어 | 설명 |
|--------|------|
| `/start` | 봇 시작 및 환영 메시지 |
| `/help` | 도움말 표시 |
| `/deposit` | 입금 요청 시작 |
| `/status` | 최근 입금 내역 조회 |
| `/rate` | 현재 환율 조회 |
| `/cancel` | 진행 중인 작업 취소 |

---

## 관리자 매뉴얼

### 대시보드 접속
1. 관리자 페이지 로그인
2. 좌측 메뉴에서 "입금 관리" 선택

### 입금 목록 조회
- **필터링**: 상태별 필터 (대기중/완료/만료/취소)
- **검색**: 사용자 ID로 검색
- **페이지네이션**: 20건씩 표시

### 통계 카드
- **대기중**: 현재 처리 대기 중인 입금 건수
- **오늘 완료**: 오늘 완료된 입금 건수 및 USDT 합계
- **총 완료**: 전체 완료된 입금 건수 및 USDT 합계
- **만료/취소**: 만료 및 취소된 입금 건수

### 수동 승인
자동 매칭이 실패한 경우 수동으로 승인할 수 있습니다.

1. 입금 목록에서 대기중인 항목 클릭
2. 상세 정보 확인
3. "수동 승인" 버튼 클릭
4. TX Hash 입력 (블록체인 트랜잭션 해시)
5. 승인 완료

### 수동 거부
잘못된 입금 요청을 거부할 수 있습니다.

1. 입금 목록에서 대기중인 항목 클릭
2. "거부" 버튼 클릭
3. 거부 사유 입력
4. 거부 완료

### 알림 설정
- **대량 입금 알림**: 설정 금액 이상 입금 시 관리자 알림
- **수동 검토 필요**: 자동 매칭 실패 시 관리자 알림

---

## 기술 문서

### 아키텍처
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Telegram   │────▶│   Admin     │────▶│   Main      │
│    Bot      │     │   Backend   │     │   Backend   │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
              ┌─────────┐   ┌─────────┐
              │  Redis  │   │ Admin DB│
              │ (Cache) │   │(Postgres)│
              └─────────┘   └─────────┘
```

### 주요 컴포넌트

#### 1. TonExchangeRateService
- USDT/KRW 환율 조회
- CoinGecko API (Primary)
- Binance API (Fallback)
- Redis 캐싱 (30초 TTL)

#### 2. QRGenerator
- ton:// URI 생성
- QR 코드 이미지 생성 (PNG/Base64)
- Jetton 파라미터 포함

#### 3. DepositRequestService
- 입금 요청 생성/조회
- 고유 메모 생성
- 상태 관리

#### 4. TonClient
- TON 블록체인 연동
- TonAPI + TON Center 폴백
- Jetton 전송 조회

#### 5. TonDepositMonitor
- 블록체인 폴링
- 메모 매칭
- 금액 검증 (±0.5% tolerance)

#### 6. DepositProcessor
- 입금 처리
- 잔액 업데이트
- 감사 로그 생성

#### 7. TelegramNotifier
- 사용자 알림
- 관리자 알림
- aiogram 3.x 기반

### API 엔드포인트

#### 사용자 API
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | /api/ton/deposit/request | 입금 요청 생성 |
| GET | /api/ton/deposit/status/{id} | 상태 조회 |
| GET | /api/ton/deposit/request/{id} | 상세 조회 |
| GET | /api/ton/deposit/rate | 환율 조회 |

#### 관리자 API
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | /api/admin/deposits | 입금 목록 |
| GET | /api/admin/deposits/stats | 통계 |
| GET | /api/admin/deposits/{id} | 상세 |
| POST | /api/admin/deposits/{id}/approve | 수동 승인 |
| POST | /api/admin/deposits/{id}/reject | 수동 거부 |
| GET | /api/admin/deposits/pending/count | 대기 건수 |

### 환경 변수
```bash
# TON Network
TON_NETWORK=testnet  # or mainnet
TON_HOT_WALLET_ADDRESS=your-wallet-address
TON_USDT_MASTER_ADDRESS=EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs
TONAPI_KEY=your-tonapi-key
TON_CENTER_API_KEY=your-toncenter-key

# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_ADMIN_CHAT_ID=your-admin-chat-id

# Deposit Settings
DEPOSIT_EXPIRY_MINUTES=30
DEPOSIT_AMOUNT_TOLERANCE=0.005
DEPOSIT_POLLING_INTERVAL=10
```

### 데이터베이스 스키마
```sql
CREATE TABLE deposit_requests (
    id UUID PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    telegram_id BIGINT,
    requested_krw INTEGER NOT NULL,
    calculated_usdt DECIMAL(18,6) NOT NULL,
    exchange_rate DECIMAL(18,6) NOT NULL,
    memo VARCHAR(255) UNIQUE NOT NULL,
    qr_data TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    confirmed_at TIMESTAMP,
    tx_hash VARCHAR(255)
);
```

---

## FAQ

### Q: 입금이 자동으로 확인되지 않아요
A: 다음 사항을 확인해주세요:
1. 메모(Comment)를 정확히 입력했는지 확인
2. 만료 시간(30분) 내에 전송했는지 확인
3. 정확한 USDT 금액을 전송했는지 확인

자동 확인이 안 되면 관리자에게 문의하세요.

### Q: 환율은 어떻게 결정되나요?
A: CoinGecko API에서 실시간 USDT/KRW 환율을 조회합니다. 환율은 30초마다 갱신됩니다.

### Q: 최소/최대 입금 금액은 얼마인가요?
A: 최소 10,000원, 최대 10,000,000원입니다.

### Q: 입금 요청 후 얼마나 기다려야 하나요?
A: 입금 요청 후 30분 내에 USDT를 전송해야 합니다. 30분이 지나면 요청이 만료됩니다.

### Q: 잘못된 금액을 보냈어요
A: 관리자에게 문의하세요. 수동으로 처리해드립니다.

### Q: 메모 없이 보냈어요
A: 관리자에게 TX Hash와 함께 문의하세요. 수동으로 매칭해드립니다.

### Q: 지원하는 지갑은 무엇인가요?
A: Tonkeeper, @wallet (Telegram), TON Space 등 TON 네트워크를 지원하는 모든 지갑에서 사용 가능합니다.

---

## 버전 정보
- **버전**: 1.0.0
- **최종 업데이트**: 2026-01-16
- **작성자**: Development Team
