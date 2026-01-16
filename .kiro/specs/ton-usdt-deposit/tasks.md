# TON/USDT 자동 입금 시스템 - 상세 태스크 목록

> 작성일: 2026-01-16

---

## Phase 1: 기획 & 준비 (Week 1)

### 1.1 요구사항 확정
- [ ] 지원 금액 단위 결정 (10만원 고정 vs 다양한 금액)
- [ ] 만료 시간 확정 (30분)
- [ ] 금액 허용 오차 확정 (±0.5%)
- [ ] 메모 형식 확정 (`user_{id}_{timestamp}_{random}`)

### 1.2 TON Wallet 설정
- [ ] Mainnet Hot Wallet 생성
  - Tonkeeper 또는 CLI로 지갑 생성
  - 니모닉 안전 보관 (암호화)
  
- [ ] USDT Jetton Wallet 주소 확인
  - Hot Wallet의 USDT Jetton Wallet 주소 조회
  - tonviewer.com에서 확인
  
- [ ] Cold Wallet 계획
  - Cold Wallet 주소 생성
  - 이동 임계값 설정 (예: Hot > 5000 USDT 시 이동)

### 1.3 DB 마이그레이션
- [ ] deposit_requests 테이블 생성
  ```
  파일: admin-backend/alembic/versions/002_ton_deposit_requests.py
  ```

- [ ] crypto_deposits 모델 확장
  - network 필드 추가 (TRON/TON)
  - memo 필드 추가
  - expires_at 필드 추가

### 1.4 Telegram Bot 설정
- [ ] @BotFather에서 봇 생성
- [ ] 봇 토큰 발급
- [ ] 환경변수 설정 (TELEGRAM_BOT_TOKEN)
- [ ] 관리자 알림 채널 생성

---

## Phase 2: 입금 신청 & QR 발급 (Week 2)

### 2.1 환율 서비스 구현
```python
# 파일: admin-backend/app/services/crypto/ton_exchange_rate.py

class TonExchangeRateService:
    """USDT/KRW 환율 서비스"""
    
    async def get_usdt_krw_rate(self) -> Decimal:
        """현재 USDT/KRW 환율 조회"""
        pass
    
    async def calculate_usdt_amount(self, krw_amount: int) -> Decimal:
        """KRW → USDT 변환"""
        pass
    
    async def get_rate_history(self, hours: int = 24) -> list:
        """환율 히스토리 조회"""
        pass
```

- [ ] CoinGecko API 연동
  - GET https://api.coingecko.com/api/v3/simple/price?ids=tether&vs_currencies=krw
  - Rate limiting 처리

- [ ] Binance API 폴백
  - USDT/KRW 직접 페어 없으면 USDT/USDC → USDC/KRW 계산

- [ ] Redis 캐싱
  - 키: `exchange_rate:usdt_krw`
  - TTL: 30초

- [ ] 환율 히스토리 저장
  - 1분 간격 기록
  - exchange_rate_history 테이블 활용

### 2.2 입금 요청 API 구현
```python
# 파일: admin-backend/app/api/ton_deposit.py

@router.post("/deposit/request")
async def create_deposit_request(
    user_id: str,
    amount_krw: int = 100000,
    telegram_id: int | None = None
) -> DepositRequestResponse:
    """입금 요청 생성"""
    pass

@router.get("/deposit/status/{request_id}")
async def get_deposit_status(request_id: str) -> DepositStatusResponse:
    """입금 상태 조회"""
    pass
```

- [ ] 입금 요청 생성 로직
  - 환율 조회
  - USDT 금액 계산 (decimals=6)
  - 고유 메모 생성
  - expires_at 설정 (now + 30분)
  - DB 저장

- [ ] ton:// URI 생성
  ```
  ton://transfer/{WALLET_ADDRESS}?amount={NANO_USDT}&text={MEMO}
  ```
  - amount: USDT × 10^6 (nano units)
  - text: 고유 메모

- [ ] 응답 모델 정의
  ```python
  class DepositRequestResponse(BaseModel):
      request_id: str
      wallet_address: str
      amount_usdt: Decimal
      exchange_rate: Decimal
      memo: str
      qr_uri: str
      qr_image_base64: str
      expires_at: datetime
      expires_in_seconds: int
  ```

### 2.3 QR 코드 생성 서비스
```python
# 파일: admin-backend/app/services/crypto/qr_generator.py

class QRGenerator:
    """QR 코드 생성 서비스"""
    
    def generate_ton_transfer_qr(
        self,
        address: str,
        amount_nano: int,
        memo: str
    ) -> str:
        """ton:// URI QR 코드 생성 (Base64)"""
        pass
```

- [ ] qrcode[pil] 라이브러리 설치
- [ ] ton:// URI QR 생성
- [ ] Base64 인코딩
- [ ] 이미지 크기/품질 설정

### 2.4 Telegram Bot 기본 구현
```python
# 파일: admin-backend/app/bot/deposit_bot.py

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message

router = Router()

@router.message(Command("deposit"))
async def handle_deposit(message: Message):
    """입금 요청 처리"""
    pass

@router.message(Command("status"))
async def handle_status(message: Message):
    """입금 상태 조회"""
    pass
```

- [ ] aiogram v3 설치 및 설정
- [ ] /deposit 명령어 처리
- [ ] /status 명령어 처리
- [ ] QR 이미지 전송
- [ ] 안내 메시지 템플릿
  ```
  💰 입금 안내
  
  금액: 100,000 KRW = 68.03 USDT
  주소: EQ...
  메모: user_123456_...
  
  ⏰ 30분 내에 입금해주세요!
  만료: 2026-01-16 15:30:00
  
  📱 QR 코드를 스캔하거나 주소를 복사하세요.
  ```

---

## Phase 3: 입금 감지 & 자동 승인 (Week 3-4)

### 3.1 TON Client 구현
```python
# 파일: admin-backend/app/services/crypto/ton_client.py

class TonClient:
    """TON 네트워크 클라이언트"""
    
    async def get_jetton_wallet_address(
        self,
        owner_address: str,
        jetton_master: str
    ) -> str:
        """Jetton Wallet 주소 조회"""
        pass
    
    async def get_jetton_transfers(
        self,
        jetton_wallet: str,
        limit: int = 100
    ) -> list[JettonTransfer]:
        """Jetton 전송 내역 조회"""
        pass
    
    async def get_transaction_by_hash(
        self,
        tx_hash: str
    ) -> Transaction:
        """트랜잭션 상세 조회"""
        pass
```

- [ ] pytoniq 또는 tonapi-python 설치
- [ ] TON Center API 연동
  - GET /getTransactions
  - GET /getJettonTransfers
  
- [ ] tonapi.io 연동 (선택)
  - Webhook 지원
  - 더 빠른 응답

- [ ] Jetton Wallet 주소 조회
  - USDT Master 주소로 Jetton Wallet 주소 계산

### 3.2 입금 모니터링 서비스
```python
# 파일: admin-backend/app/services/crypto/ton_deposit_monitor.py

class TonDepositMonitor:
    """TON 입금 모니터링 서비스"""
    
    async def start_polling(self):
        """Polling 시작"""
        pass
    
    async def check_new_deposits(self):
        """새 입금 확인"""
        pass
    
    async def match_deposit(
        self,
        transfer: JettonTransfer
    ) -> DepositRequest | None:
        """입금과 요청 매칭"""
        pass
```

- [ ] Polling 루프 구현
  - 5~10초 간격
  - 마지막 확인 시점 저장

- [ ] Jetton transfer 감지
  - USDT Jetton Wallet 모니터링
  - 새 incoming transfer 필터링

- [ ] 메모 매칭 로직
  - transfer.comment == deposit_request.memo
  - 대소문자 무시

- [ ] 금액 검증
  - transfer.amount >= calculated × 0.995
  - ±0.5% 허용 오차

### 3.3 자동 승인 로직
```python
# 파일: admin-backend/app/services/crypto/deposit_processor.py

class DepositProcessor:
    """입금 처리 서비스"""
    
    async def process_deposit(
        self,
        request: DepositRequest,
        transfer: JettonTransfer
    ) -> bool:
        """입금 처리 (자동 승인)"""
        pass
    
    async def credit_balance(
        self,
        user_id: str,
        amount_krw: int
    ):
        """잔액 충전"""
        pass
```

- [ ] 조건 검증
  - 메모 일치
  - 금액 충족 (±0.5%)
  - 만료 전 (now < expires_at)
  - 중복 아님 (tx_hash unique)

- [ ] 승인 처리
  - deposit_request.status = 'confirmed'
  - deposit_request.tx_hash = transfer.tx_hash
  - deposit_request.confirmed_at = now()

- [ ] 잔액 업데이트
  - user.balance += requested_krw
  - 트랜잭션 로그 기록

- [ ] crypto_deposits 레코드 생성
  - 영구 기록용

### 3.4 만료 처리 로직
```python
# 파일: admin-backend/app/tasks/deposit_expiry.py

async def check_expired_deposits():
    """만료된 입금 요청 처리"""
    pass

async def notify_expiry(request: DepositRequest):
    """만료 알림 발송"""
    pass
```

- [ ] Cron job 설정 (1분 간격)
- [ ] 만료 조건 확인
  - status == 'pending'
  - expires_at < now()

- [ ] 만료 처리
  - status = 'expired'
  - 알림 발송

### 3.5 Telegram 알림 서비스
```python
# 파일: admin-backend/app/services/telegram_notifier.py

class TelegramNotifier:
    """Telegram 알림 서비스"""
    
    async def notify_deposit_confirmed(
        self,
        telegram_id: int,
        amount_krw: int
    ):
        """입금 확인 알림"""
        pass
    
    async def notify_deposit_expired(
        self,
        telegram_id: int
    ):
        """만료 알림"""
        pass
    
    async def notify_admin(
        self,
        message: str
    ):
        """관리자 알림"""
        pass
```

- [ ] 입금 확인 알림
  ```
  ✅ 입금 확인 완료!
  
  충전 금액: 100,000원
  현재 잔액: 500,000원
  
  감사합니다! 🎉
  ```

- [ ] 만료 알림
  ```
  ⏰ 입금 시간이 만료되었습니다.
  
  다시 /deposit 명령어로 신청해주세요.
  ```

- [ ] 관리자 알림
  - 고액 입금 (100만원 이상)
  - 이상 거래 (메모 불일치 등)
  - 시스템 오류

---

## Phase 4: 예외 처리 & 보안 (Week 5)

### 4.1 예외 케이스 처리
- [ ] 메모 없는 입금
  - 수동 검토 큐에 추가
  - 관리자 알림

- [ ] 금액 부족 입금
  - 수동 검토 큐에 추가
  - 부분 승인 또는 환불 결정

- [ ] 만료 후 입금
  - 무시 (자동 승인 안 함)
  - 수동 환불 플로우 안내

- [ ] 중복 입금 방지
  - tx_hash unique 제약
  - 이미 처리된 트랜잭션 스킵

### 4.2 Cold Wallet 이동
```python
# 파일: admin-backend/app/tasks/cold_wallet_transfer.py

async def transfer_to_cold_wallet():
    """Cold Wallet으로 자금 이동"""
    pass
```

- [ ] 자동 이동 스크립트
  - 매일 또는 매주 실행
  - Hot Wallet 잔고 > 임계값 시 이동

- [ ] 이동 로직
  - Hot Wallet 잔고 조회
  - 최소 잔고 유지 (예: 1000 USDT)
  - 초과분 Cold Wallet으로 전송

- [ ] 이동 기록
  - 트랜잭션 해시 저장
  - 관리자 알림

### 4.3 보안 강화
- [ ] Rate Limiting
  - 입금 요청: 분당 5회
  - 상태 조회: 분당 30회

- [ ] 스캠 Jetton 방지
  - USDT Master 주소 하드코딩
  - 다른 Jetton 무시

- [ ] API 키 보호
  - 환경변수 암호화
  - 키 로테이션 계획

---

## Phase 5: 관리자 대시보드 연동 (Week 6)

### 5.1 관리자 API 구현
```python
# 파일: admin-backend/app/api/admin_ton_deposit.py

@router.get("/admin/deposits")
async def list_deposits(
    status: str | None = None,
    page: int = 1,
    page_size: int = 20
) -> PaginatedDeposits:
    """입금 목록 조회"""
    pass

@router.get("/admin/deposits/{id}")
async def get_deposit(id: str) -> DepositDetail:
    """입금 상세 조회"""
    pass

@router.post("/admin/deposits/{id}/manual-confirm")
async def manual_confirm(id: str, admin_id: str) -> bool:
    """수동 승인"""
    pass

@router.post("/admin/deposits/{id}/reject")
async def reject_deposit(id: str, reason: str) -> bool:
    """거부"""
    pass
```

- [ ] 입금 목록 API
  - 상태별 필터링
  - 날짜 범위 필터링
  - 페이지네이션

- [ ] 입금 상세 API
  - 요청 정보
  - 트랜잭션 정보
  - 사용자 정보

- [ ] 수동 승인 API
  - 관리자 권한 검증
  - 감사 로그 기록

- [ ] 거부 API
  - 거부 사유 기록
  - 환불 플로우 연동

### 5.2 관리자 UI 구현
```typescript
// 파일: admin-frontend/src/app/(dashboard)/deposits/page.tsx

export default function DepositsPage() {
  // 입금 목록 페이지
}
```

- [ ] 입금 대기열 페이지
  - 상태별 탭 (대기/확인중/완료/만료)
  - 검색 및 필터
  - 페이지네이션

- [ ] 입금 상세 모달
  - 요청 정보
  - QR 코드 미리보기
  - 트랜잭션 정보 (있는 경우)

- [ ] 수동 승인/거부 버튼
  - 확인 다이얼로그
  - 거부 사유 입력

### 5.3 통계 대시보드
- [ ] 일별/주별/월별 입금 통계
- [ ] 환율 히스토리 차트
- [ ] 핫월렛 잔액 표시

---

## Phase 6: 테스트 & 론칭 (Week 7-8)

### 6.1 Testnet 테스트
- [ ] TON Testnet 환경 설정
- [ ] 테스트 USDT 획득
- [ ] 전체 플로우 테스트
  - 입금 요청 → QR 발급 → 입금 → 자동 승인

### 6.2 스트레스 테스트
- [ ] 동시 50건 입금 요청
- [ ] Polling 성능 측정
- [ ] DB 부하 테스트

### 6.3 Mainnet 이전
- [ ] 환경변수 전환
- [ ] 실제 입금 테스트 (소액)
- [ ] 모니터링 확인

### 6.4 모니터링 설정
- [ ] Sentry 에러 추적
- [ ] Telegram 알림 채널
- [ ] Grafana 대시보드
  - 입금 성공률
  - 평균 처리 시간
  - 핫월렛 잔액

### 6.5 문서화
- [ ] 사용자 가이드
- [ ] 관리자 매뉴얼
- [ ] FAQ
  - "텔레그램 없이 Tonkeeper 사용법"
  - "입금이 안 되는 경우"
  - "만료 후 입금한 경우"

---

## 체크리스트 요약

### Week 1
- [ ] 요구사항 확정
- [ ] TON Wallet 설정
- [ ] DB 마이그레이션
- [ ] Telegram Bot 생성

### Week 2
- [ ] 환율 서비스 구현
- [ ] 입금 요청 API 구현
- [ ] QR 코드 생성
- [ ] Telegram Bot 기본 동작

### Week 3-4
- [ ] TON Client 구현
- [ ] 입금 모니터링 서비스
- [ ] 자동 승인 로직
- [ ] 만료 처리 로직
- [ ] Telegram 알림

### Week 5
- [ ] 예외 케이스 처리
- [ ] Cold Wallet 이동
- [ ] 보안 강화

### Week 6
- [ ] 관리자 API
- [ ] 관리자 UI
- [ ] 통계 대시보드

### Week 7-8
- [ ] Testnet 테스트
- [ ] 스트레스 테스트
- [ ] Mainnet 이전
- [ ] 모니터링 설정
- [ ] 문서화

---

## 의존성 패키지

```txt
# admin-backend/requirements.txt 추가
aiogram>=3.0.0
pytoniq>=0.1.0
qrcode[pil]>=7.4.0
httpx>=0.25.0
```
