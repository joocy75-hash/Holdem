# TON/USDT 자동 입금 시스템 - 기술 설계 문서

> 작성일: 2026-01-16

---

## 1. 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         TON 입금 시스템 아키텍처                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐               │
│  │  Telegram   │     │    Web      │     │   Admin     │               │
│  │    Bot      │     │  Frontend   │     │  Dashboard  │               │
│  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘               │
│         │                   │                   │                       │
│         └───────────────────┼───────────────────┘                       │
│                             │                                           │
│                             ▼                                           │
│                    ┌─────────────────┐                                  │
│                    │  Admin Backend  │                                  │
│                    │    (FastAPI)    │                                  │
│                    └────────┬────────┘                                  │
│                             │                                           │
│         ┌───────────────────┼───────────────────┐                       │
│         ▼                   ▼                   ▼                       │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │ PostgreSQL  │    │    Redis    │    │ TON Network │                 │
│  │  (DB)       │    │  (Cache)    │    │  (Blockchain)│                │
│  └─────────────┘    └─────────────┘    └─────────────┘                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 핵심 컴포넌트

### 2.1 TonExchangeRateService
실시간 USDT/KRW 환율 조회 및 캐싱

```python
class TonExchangeRateService:
    CACHE_KEY = "exchange_rate:usdt_krw"
    CACHE_TTL = 30  # seconds
    
    async def get_usdt_krw_rate(self) -> Decimal:
        # 1. Redis 캐시 확인
        cached = await redis.get(self.CACHE_KEY)
        if cached:
            return Decimal(cached)
        
        # 2. CoinGecko API 호출
        rate = await self._fetch_from_coingecko()
        if not rate:
            # 3. Binance 폴백
            rate = await self._fetch_from_binance()
        
        # 4. 캐시 저장
        await redis.setex(self.CACHE_KEY, self.CACHE_TTL, str(rate))
        
        # 5. 히스토리 저장
        await self._save_rate_history(rate)
        
        return rate
```


### 2.2 TonClient
TON 네트워크 연동 클라이언트

```python
class TonClient:
    USDT_MASTER = "EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs"
    USDT_DECIMALS = 6
    
    async def get_jetton_wallet_address(
        self,
        owner_address: str
    ) -> str:
        """소유자의 USDT Jetton Wallet 주소 조회"""
        # TON Center API 또는 tonapi.io 사용
        pass
    
    async def get_jetton_transfers(
        self,
        jetton_wallet: str,
        after_lt: int | None = None
    ) -> list[JettonTransfer]:
        """Jetton 전송 내역 조회"""
        pass
```

### 2.3 DepositRequestService
입금 요청 생성 및 관리

```python
class DepositRequestService:
    EXPIRY_MINUTES = 30
    AMOUNT_TOLERANCE = Decimal("0.005")  # 0.5%
    
    async def create_request(
        self,
        user_id: str,
        amount_krw: int,
        telegram_id: int | None = None
    ) -> DepositRequest:
        # 1. 환율 조회
        rate = await exchange_service.get_usdt_krw_rate()
        
        # 2. USDT 금액 계산
        amount_usdt = Decimal(amount_krw) / rate
        
        # 3. 고유 메모 생성
        memo = self._generate_memo(user_id)
        
        # 4. ton:// URI 생성
        qr_uri = self._generate_ton_uri(amount_usdt, memo)
        
        # 5. QR 이미지 생성
        qr_image = qr_generator.generate(qr_uri)
        
        # 6. DB 저장
        request = DepositRequest(
            user_id=user_id,
            telegram_id=telegram_id,
            requested_krw=amount_krw,
            calculated_usdt=amount_usdt,
            exchange_rate=rate,
            memo=memo,
            qr_data=qr_uri,
            expires_at=datetime.utcnow() + timedelta(minutes=self.EXPIRY_MINUTES)
        )
        
        return request
    
    def _generate_memo(self, user_id: str) -> str:
        timestamp = int(time.time())
        random_suffix = secrets.token_hex(2)
        return f"user_{user_id[:8]}_{timestamp}_{random_suffix}"
    
    def _generate_ton_uri(
        self,
        amount_usdt: Decimal,
        memo: str
    ) -> str:
        # USDT는 decimals=6이므로 × 10^6
        nano_amount = int(amount_usdt * 1_000_000)
        return f"ton://transfer/{HOT_WALLET_ADDRESS}?amount={nano_amount}&text={memo}"
```

### 2.4 TonDepositMonitor
입금 모니터링 및 자동 승인

```python
class TonDepositMonitor:
    POLLING_INTERVAL = 10  # seconds
    
    async def start_polling(self):
        """Polling 루프 시작"""
        while True:
            try:
                await self.check_new_deposits()
            except Exception as e:
                logger.error(f"Polling error: {e}")
            
            await asyncio.sleep(self.POLLING_INTERVAL)
    
    async def check_new_deposits(self):
        # 1. 새 Jetton transfer 조회
        transfers = await ton_client.get_jetton_transfers(
            jetton_wallet=HOT_WALLET_JETTON_ADDRESS,
            after_lt=self.last_lt
        )
        
        for transfer in transfers:
            # 2. 메모로 요청 매칭
            request = await self.match_deposit(transfer)
            if request:
                # 3. 자동 승인 처리
                await deposit_processor.process_deposit(request, transfer)
    
    async def match_deposit(
        self,
        transfer: JettonTransfer
    ) -> DepositRequest | None:
        if not transfer.comment:
            return None
        
        # 메모로 요청 조회
        request = await db.query(DepositRequest).filter(
            DepositRequest.memo == transfer.comment,
            DepositRequest.status == "pending",
            DepositRequest.expires_at > datetime.utcnow()
        ).first()
        
        if not request:
            return None
        
        # 금액 검증 (±0.5% 허용)
        min_amount = request.calculated_usdt * (1 - AMOUNT_TOLERANCE)
        if transfer.amount < min_amount:
            return None
        
        return request
```

### 2.5 DepositProcessor
입금 처리 및 잔액 업데이트

```python
class DepositProcessor:
    async def process_deposit(
        self,
        request: DepositRequest,
        transfer: JettonTransfer
    ):
        async with db.transaction():
            # 1. 요청 상태 업데이트
            request.status = "confirmed"
            request.tx_hash = transfer.tx_hash
            request.confirmed_at = datetime.utcnow()
            
            # 2. 사용자 잔액 업데이트
            await self.credit_balance(
                request.user_id,
                request.requested_krw
            )
            
            # 3. crypto_deposits 레코드 생성
            deposit = CryptoDeposit(
                user_id=request.user_id,
                tx_hash=transfer.tx_hash,
                network=NetworkType.TON,
                amount_usdt=transfer.amount,
                amount_krw=request.requested_krw,
                exchange_rate=request.exchange_rate,
                memo=request.memo,
                status=TransactionStatus.COMPLETED
            )
            db.add(deposit)
            
            # 4. 알림 발송
            await telegram_notifier.notify_deposit_confirmed(
                request.telegram_id,
                request.requested_krw
            )
```

---

## 3. 데이터 모델

### 3.1 DepositRequest (새 테이블)

```python
class DepositRequest(Base):
    __tablename__ = "deposit_requests"
    
    id: str                    # UUID
    user_id: str               # 사용자 ID
    telegram_id: int | None    # Telegram 사용자 ID
    requested_krw: int         # 요청 금액 (100000)
    calculated_usdt: Decimal   # 계산된 USDT
    exchange_rate: Decimal     # 적용 환율
    memo: str                  # 고유 메모 (unique)
    qr_data: str               # ton:// URI
    status: str                # pending/confirmed/expired/cancelled
    expires_at: datetime       # 만료 시간
    created_at: datetime
    confirmed_at: datetime | None
    tx_hash: str | None        # 확인된 트랜잭션 해시
```

### 3.2 CryptoDeposit 확장

```python
class CryptoDeposit(Base):
    # 기존 필드...
    network: NetworkType       # TRON / TON (새 필드)
    memo: str | None           # TON 메모 (새 필드)
```

---

## 4. API 상세 설계

### 4.1 입금 요청 API

```
POST /api/deposit/request

Request:
{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "telegram_id": 123456789,
    "amount_krw": 100000
}

Response:
{
    "request_id": "660e8400-e29b-41d4-a716-446655440001",
    "wallet_address": "EQBvW8Z5huBkMJYdnfAEM5JqTNLuuU8s0W5UfXQvGsHF3TGH",
    "amount_usdt": "68.027000",
    "exchange_rate": "1470.50",
    "memo": "user_550e8400_1705401234_a1b2",
    "qr_uri": "ton://transfer/EQBvW8Z5huBkMJYdnfAEM5JqTNLuuU8s0W5UfXQvGsHF3TGH?amount=68027000&text=user_550e8400_1705401234_a1b2",
    "qr_image_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
    "expires_at": "2026-01-16T15:30:00Z",
    "expires_in_seconds": 1800
}
```

### 4.2 입금 상태 조회 API

```
GET /api/deposit/status/{request_id}

Response (pending):
{
    "request_id": "660e8400-e29b-41d4-a716-446655440001",
    "status": "pending",
    "amount_krw": 100000,
    "amount_usdt": "68.027000",
    "expires_at": "2026-01-16T15:30:00Z",
    "remaining_seconds": 1234,
    "tx_hash": null,
    "confirmed_at": null
}

Response (confirmed):
{
    "request_id": "660e8400-e29b-41d4-a716-446655440001",
    "status": "confirmed",
    "amount_krw": 100000,
    "amount_usdt": "68.027000",
    "expires_at": "2026-01-16T15:30:00Z",
    "remaining_seconds": 0,
    "tx_hash": "abc123...",
    "confirmed_at": "2026-01-16T15:10:00Z"
}
```

---

## 5. Telegram Bot 설계

### 5.1 명령어

| 명령어 | 설명 |
|--------|------|
| /start | 봇 시작, 사용법 안내 |
| /deposit | 입금 신청 (10만원) |
| /deposit {금액} | 지정 금액 입금 신청 |
| /status | 최근 입금 상태 조회 |
| /balance | 현재 잔액 조회 |
| /help | 도움말 |

### 5.2 메시지 템플릿

**입금 안내 메시지:**
```
💰 입금 안내

금액: 100,000 KRW = 68.03 USDT
환율: 1 USDT = 1,470.50 KRW

📍 입금 주소:
EQBvW8Z5huBkMJYdnfAEM5JqTNLuuU8s0W5UfXQvGsHF3TGH

📝 메모 (필수):
user_550e8400_1705401234_a1b2

⏰ 30분 내에 입금해주세요!
만료: 2026-01-16 15:30:00

📱 QR 코드를 스캔하거나 주소를 복사하세요.
⚠️ 메모를 반드시 입력해주세요!
```

**입금 확인 메시지:**
```
✅ 입금 확인 완료!

충전 금액: 100,000원
입금 금액: 68.03 USDT
현재 잔액: 500,000원

감사합니다! 🎉
```

**만료 알림 메시지:**
```
⏰ 입금 시간이 만료되었습니다.

요청 금액: 100,000원
만료 시간: 2026-01-16 15:30:00

다시 /deposit 명령어로 신청해주세요.
```

---

## 6. 보안 설계

### 6.1 Hot Wallet 보안
- 최소 잔고만 유지 (예: 1,000 USDT)
- 초과분 자동 Cold Wallet 이동
- 니모닉 암호화 저장

### 6.2 스캠 Jetton 방지
```python
USDT_MASTER_ADDRESS = "EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs"

def validate_jetton_transfer(transfer: JettonTransfer) -> bool:
    # Master 주소 검증
    if transfer.jetton_master != USDT_MASTER_ADDRESS:
        logger.warning(f"Invalid Jetton master: {transfer.jetton_master}")
        return False
    return True
```

### 6.3 Rate Limiting
```python
# 입금 요청: 분당 5회
@limiter.limit("5/minute")
async def create_deposit_request(...):
    pass

# 상태 조회: 분당 30회
@limiter.limit("30/minute")
async def get_deposit_status(...):
    pass
```

---

## 7. 모니터링

### 7.1 메트릭
- 입금 요청 수 (분당/시간당/일당)
- 입금 성공률
- 평균 처리 시간
- 만료율
- 핫월렛 잔액

### 7.2 알림
- 고액 입금 (100만원 이상)
- 이상 거래 (메모 불일치)
- 핫월렛 잔액 부족
- 시스템 오류

---

## 8. 참고 자료

- TON 공식 문서: https://docs.ton.org/
- tonapi.io API: https://tonapi.io/api-v2
- pytoniq: https://github.com/yungwine/pytoniq
- USDT Jetton: https://tonviewer.com/EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs
