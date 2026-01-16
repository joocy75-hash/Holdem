# TON/USDT 입금 시스템 개발 스킬

## 프로젝트 개요
TON 네트워크 기반 USDT Jetton 자동 입금 시스템 개발

## 작업 규칙

### 1. 단계별 작업 원칙
- **한 번에 하나의 Step만 작업**
- 각 Step 완료 후 반드시 **검증 테스트 실행**
- 테스트 통과 후 **WORK_PROGRESS.md에 완료 체크 (✅)** 표시
- 다음 Step으로 진행 전 **이전 Step 완료 확인**

### 2. 서브에이전트 사용 원칙
- 복잡한 작업은 **전문 서브에이전트** 사용
- 코드 작성 전 `context-gatherer` 먼저 실행하여 관련 파일 파악
- 멀티 파일 작업 시 `general-task-execution` 활용

### 3. 검증 테스트 원칙
```bash
# 백엔드 단위 테스트
cd admin-backend && pytest tests/ -v

# 특정 테스트 파일
pytest tests/services/test_ton_exchange_rate.py -v

# 프론트엔드 빌드 검증
cd admin-frontend && npm run build

# 서버 실행 확인
cd admin-backend && python -c "from app.main import app; print('OK')"
```

### 4. 중단 대비 원칙
- 각 Step 완료 시 즉시 `WORK_PROGRESS.md` 업데이트
- 작업 중단 시 현재 진행 상태 기록
- 재개 시 `WORK_PROGRESS.md`에서 마지막 완료 Step 확인

## 파일 구조

```
admin-backend/
├── app/
│   ├── api/
│   │   ├── ton_deposit.py          # 입금 신청 API
│   │   └── admin_ton_deposit.py    # 관리자 API
│   ├── bot/
│   │   └── deposit_bot.py          # Telegram Bot
│   ├── models/
│   │   ├── crypto.py               # 모델 확장
│   │   └── deposit_request.py      # 입금 요청 모델
│   ├── services/
│   │   ├── crypto/
│   │   │   ├── ton_client.py       # TON 네트워크 클라이언트
│   │   │   ├── ton_exchange_rate.py # 환율 서비스
│   │   │   ├── ton_deposit_monitor.py # 입금 모니터링
│   │   │   ├── deposit_processor.py # 입금 처리
│   │   │   ├── deposit_request_service.py # 입금 요청 서비스
│   │   │   └── qr_generator.py     # QR 생성
│   │   └── telegram_notifier.py    # Telegram 알림
│   └── tasks/
│       └── deposit_expiry.py       # 만료 처리
├── tests/
│   └── services/
│       ├── test_ton_exchange_rate.py
│       ├── test_ton_client.py
│       ├── test_deposit_processor.py
│       └── test_qr_generator.py

admin-frontend/
├── src/
│   ├── app/(dashboard)/
│   │   └── deposits/
│   │       └── page.tsx            # 입금 관리 페이지
│   └── components/
│       └── crypto/
│           ├── DepositList.tsx     # 입금 목록
│           └── DepositDetail.tsx   # 입금 상세
```

## 핵심 상수

```python
# USDT Jetton Master 주소 (공식)
USDT_MASTER_ADDRESS = "EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs"

# USDT decimals
USDT_DECIMALS = 6  # 1 USDT = 1,000,000 units

# 입금 설정
DEPOSIT_EXPIRY_MINUTES = 30
DEPOSIT_AMOUNT_TOLERANCE = 0.005  # ±0.5%
DEPOSIT_POLLING_INTERVAL = 10  # seconds

# 환율 캐시
EXCHANGE_RATE_CACHE_TTL = 30  # seconds
```

## API 엔드포인트

```
# 입금 신청
POST /api/deposit/request
GET  /api/deposit/status/{request_id}

# 관리자
GET  /api/admin/deposits
GET  /api/admin/deposits/{id}
POST /api/admin/deposits/{id}/manual-confirm
POST /api/admin/deposits/{id}/reject
```

## 환경변수

```env
# TON Network
TON_NETWORK=mainnet
TON_HOT_WALLET_ADDRESS=EQ...
TON_USDT_MASTER_ADDRESS=EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs

# TON API
TONAPI_KEY=...
TON_CENTER_API_KEY=...

# Telegram Bot
TELEGRAM_BOT_TOKEN=...
TELEGRAM_ADMIN_CHAT_ID=...

# Exchange Rate API
COINGECKO_API_KEY=...
```

## 작업 진행 현황 확인

작업 시작 전 반드시 확인:
```
.kiro/specs/ton-usdt-deposit/WORK_PROGRESS.md
```

## 관련 문서

- `.kiro/specs/ton-usdt-deposit/requirements.md` - 요구사항
- `.kiro/specs/ton-usdt-deposit/tasks.md` - 태스크 목록
- `.kiro/specs/ton-usdt-deposit/design.md` - 기술 설계
- `.kiro/specs/ton-usdt-deposit/WORK_PROGRESS.md` - 진행 현황

## 테스트 명령어

```bash
# 전체 테스트
cd admin-backend && pytest tests/ -v

# 커버리지 포함
pytest tests/ -v --cov=app --cov-report=term-missing

# 특정 테스트만
pytest tests/services/test_ton_exchange_rate.py -v -k "test_get_rate"
```

## 주의사항

1. **USDT Master 주소 하드코딩** - 스캠 Jetton 방지
2. **메모 필수** - 입금 매칭에 사용
3. **30분 만료** - 만료 후 입금은 수동 처리
4. **금액 허용 오차** - ±0.5% 허용
5. **Testnet 먼저** - Mainnet 전 반드시 Testnet 테스트
