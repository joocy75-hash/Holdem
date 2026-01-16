# 코드 리뷰 보고서

**작성일**: 2026-01-16
**검토 대상**: admin-backend, admin-frontend, backend, frontend (변경/추가된 파일)

---

## 목차

1. [요약](#1-요약)
2. [Critical 이슈](#2-critical-이슈-즉시-수정-필요)
3. [High 이슈](#3-high-이슈-우선-수정-필요)
4. [Medium 이슈](#4-medium-이슈-검토-후-수정)
5. [Low 이슈](#5-low-이슈-개선-권장)
6. [수정 가이드](#6-수정-가이드)
7. [액션 아이템](#7-액션-아이템)

---

## 1. 요약

### 발견된 이슈 통계

| 등급 | 개수 | 카테고리 |
|------|------|----------|
| 🔴 Critical | 6 | 보안 취약점, 인증 누락 |
| 🟠 High | 12 | 에러 처리, 데이터 무결성 |
| 🟡 Medium | 8 | 코드 품질, 설정 문제 |
| 🟢 Low | 5 | 타입 설계, 유지보수성 |

### 주요 위험 영역

1. **보안**: SQL Injection, 인증 누락, 민감 정보 노출
2. **안정성**: Silent failure 패턴으로 인한 디버깅 불가
3. **금융 무결성**: 입금 처리 중 분산 트랜잭션 불일치 가능성
4. **운영**: 환경변수 하드코딩으로 프로덕션 배포 문제

---

## 2. Critical 이슈 (즉시 수정 필요)

### 2.1 SQL Injection 취약점

**파일**: `admin-backend/app/services/statistics_service.py`
**라인**: 379-382
**신뢰도**: 95%

```python
# 취약한 코드
query = text("""
    ...
    WHERE created_at > NOW() - INTERVAL ':hours hours'
    ...
""".replace(':hours', str(hours)))
```

**문제점**:
- 파라미터를 문자열 치환(`.replace()`)으로 처리
- SQLAlchemy의 파라미터 바인딩을 우회
- `hours` 값에 악성 SQL 삽입 가능

**수정 방법**:
```python
# 안전한 코드
query = text("""
    WHERE created_at > NOW() - :hours * INTERVAL '1 hour'
""")
result = await self.db.execute(query, {"hours": hours})
```

---

### 2.2 입금 API 인증 완전 누락

**파일**: `admin-backend/app/api/ton_deposit.py`
**라인**: 전체
**신뢰도**: 100%

```python
# 현재: 인증 없이 누구나 접근 가능
@router.post("/request", ...)
async def create_deposit_request(
    request: DepositRequestCreate,
    db: AsyncSession = Depends(get_admin_db),  # 인증 없음!
):
```

**문제점**:
- 모든 엔드포인트에 인증이 없음
- 공격자가 임의의 `user_id`로 입금 요청 생성 가능
- 다른 사용자의 입금 요청 상태 조회 가능

**공격 시나리오**:
```bash
# 공격자가 다른 사용자 사칭
curl -X POST /deposit/request \
  -d '{"user_id": "victim_id", "requested_krw": 1000000}'
```

**수정 방법**:
```python
from app.auth import get_current_user

@router.post("/request", ...)
async def create_deposit_request(
    request: DepositRequestCreate,
    current_user: User = Depends(get_current_user),  # 인증 추가
    db: AsyncSession = Depends(get_admin_db),
):
    # user_id를 토큰에서 추출
    if request.user_id != current_user.id:
        raise HTTPException(403, "다른 사용자의 입금 요청을 생성할 수 없습니다")
```

---

### 2.3 JWT Secret 하드코딩

**파일**: `admin-backend/app/config.py`
**라인**: 20, 26
**신뢰도**: 100%

```python
jwt_secret_key: str = "admin-secret-key-change-in-production"  # 위험!
main_api_key: str = "admin-api-key"  # 위험!
```

**문제점**:
- 기본값이 하드코딩됨
- 프로덕션에서 변경하지 않으면 JWT 토큰 위조 가능
- 메인 API 무단 접근 가능

**수정 방법**:
```python
from pydantic import Field

class Settings(BaseSettings):
    jwt_secret_key: str = Field(..., min_length=32)  # 기본값 제거, 필수
    main_api_key: str = Field(..., min_length=32)
```

---

### 2.4 API URL 하드코딩

**파일**: `admin-frontend/src/app/(auth)/login/page.tsx`
**라인**: 30, 47
**신뢰도**: 100%

```typescript
const response = await fetch('http://localhost:8001/api/auth/login', {
  // ...
});
```

**문제점**:
- `localhost:8001`이 프론트엔드 코드에 하드코딩
- 프로덕션 배포 시 동작하지 않음

**수정 방법**:
```typescript
// .env.local
NEXT_PUBLIC_API_URL=http://localhost:8001

// 코드
const API_URL = process.env.NEXT_PUBLIC_API_URL;
const response = await fetch(`${API_URL}/api/auth/login`, {
  // ...
});
```

---

### 2.5 분산 트랜잭션 불일치

**파일**: `admin-backend/app/services/crypto/deposit_processor.py`
**라인**: 100-119
**신뢰도**: 95%

```python
# Step 1: 메인 API 호출 (잔액 증가) - 성공
await self.credit_balance(...)

# Step 2: 상태 업데이트 - 실패 가능!
request.status = DepositRequestStatus.CONFIRMED

# Step 3: 감사 로그 - 실패 가능!
await self._create_audit_log(...)

# 커밋 - 여기서 실패하면?
await self.admin_db.commit()
```

**문제점**:
- Step 1 성공 후 Step 2-3 실패 시 불일치 발생
- 잔액은 증가했지만 DB에는 pending 상태 유지
- Two-Phase Commit 없음

**수정 방법**:
```python
# 옵션 1: Saga Pattern (보상 트랜잭션)
try:
    await self.credit_balance(...)
    request.status = DepositRequestStatus.CONFIRMED
    await self.admin_db.commit()
except Exception:
    # 보상 트랜잭션: 잔액 롤백
    await self.debit_balance(user_id, amount_krw, "rollback")
    raise

# 옵션 2: Idempotency Key 사용
await self.credit_balance(
    idempotency_key=f"deposit_{request.id}",
    ...
)
```

---

### 2.6 핫월렛 정보 평문 노출

**파일**: `admin-backend/app/services/crypto/ton_client.py`
**라인**: 69, 71
**신뢰도**: 90%

```python
self.wallet_address = wallet_address or settings.ton_hot_wallet_address
self.api_key = api_key or settings.ton_center_api_key
```

**문제점**:
- 핫월렛 주소와 API 키가 환경변수에 평문 저장
- `.env` 파일 유출 시 자산 탈취 위험

**수정 방법**:
- AWS Secrets Manager 또는 HashiCorp Vault 사용
- 환경변수 대신 암호화된 키 저장소 활용

---

## 3. High 이슈 (우선 수정 필요)

### 3.1 Silent Failure - 모든 예외 삼킴

**파일**: `admin-backend/app/services/statistics_service.py`
**라인**: 69-78, 111-112, 145-146, 179-180, 208-209 등
**영향 범위**: 9개 메서드

```python
except Exception:
    return []  # 에러 로깅 없이 빈 데이터 반환
```

**문제점**:
- DB 연결 끊김, SQL 오류 등 모든 예외가 숨겨짐
- 관리자가 "매출 0원"을 보고 실제 문제를 인지 못함
- 운영 중 디버깅 불가능

**영향받는 서비스**:
| 서비스 | 파일 | 라인 |
|--------|------|------|
| StatisticsService | statistics_service.py | 69, 111, 145, 179, 208, 249, 277, 311, 363, 395, 426 |
| BanService | ban_service.py | 227-234, 260-261 |
| AuditService | audit_service.py | 76-89, 177-184, 222-223 |
| TonClient | ton_client.py | 153-155, 205-211, 245-247, 329-331, 367-369 |

**수정 방법**:
```python
import logging

logger = logging.getLogger(__name__)

async def get_daily_revenue(self, days: int = 30) -> list[dict]:
    try:
        # ... 쿼리 실행
    except sqlalchemy.exc.OperationalError as e:
        logger.error(f"DB 연결 오류 - 일별 매출 조회 실패: {e}")
        raise DatabaseError("DB 연결 오류") from e
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}", exc_info=True)
        raise
```

---

### 3.2 입력 검증 부족 - 최대값 없음

**파일**: `admin-backend/app/api/ton_deposit.py`
**라인**: 28

```python
class DepositRequestCreate(BaseModel):
    requested_krw: int = Field(..., ge=10000)  # 최소값만 있음!
```

**문제점**:
- `requested_krw=999999999999` 같은 극단적 값 입력 가능
- 정수 오버플로우 또는 시스템 부하 유발

**수정 방법**:
```python
class DepositRequestCreate(BaseModel):
    requested_krw: int = Field(..., ge=10000, le=100000000)  # 최대 1억원
```

---

### 3.3 수동 승인 시 tx_hash 없이 처리 가능

**파일**: `admin-backend/app/services/crypto/deposit_processor.py`
**라인**: 272

```python
tx_hash = tx_hash or f"manual_{admin_user_id}_{datetime.utcnow().timestamp()}"
```

**문제점**:
- 실제 블록체인 트랜잭션 없이 승인 가능
- 내부자가 실제 입금 없이 임의로 잔액 충전 가능

**수정 방법**:
- 수동 승인 시에도 tx_hash 필수 입력
- 또는 별도의 승인 권한 레벨 분리

---

### 3.4 IP 주소 미기록

**파일**: `admin-backend/app/services/crypto/deposit_processor.py`
**라인**: 202, 292, 350

```python
ip_address="0.0.0.0",  # Should be passed from request context
```

**문제점**:
- 관리자 행위의 IP 주소가 기록되지 않음
- 내부자 공격 시 추적 불가

**수정 방법**:
```python
# API 레이어에서 IP 전달
from fastapi import Request

async def manual_approve(
    deposit_id: UUID,
    request: ManualApproveRequest,
    req: Request,
    ...
):
    ip_address = req.client.host if req.client else None
```

---

### 3.5 TON Client 에러 시 잘못된 기본값 반환

**파일**: `admin-backend/app/services/crypto/ton_client.py`
**라인**: 367-369

```python
except Exception as e:
    logger.error(f"Error getting wallet balance: {e}")
    return Decimal("0")  # 0과 조회 실패를 구분 불가!
```

**문제점**:
- 잔액 0원과 조회 실패를 구분할 수 없음
- 암호화폐 입금 처리에서 금전적 손실 가능

**수정 방법**:
```python
class TonClientError(Exception):
    pass

async def get_wallet_balance(self, ...) -> Decimal:
    try:
        # ...
    except Exception as e:
        logger.error(f"잔액 조회 실패: {e}", exc_info=True)
        raise TonClientError(f"잔액 조회 실패: {e}")
```

---

### 3.6 연속 폴링 실패 시 알림 없음

**파일**: `admin-backend/app/services/crypto/ton_deposit_monitor.py`
**라인**: 82-83

```python
except Exception as e:
    logger.error(f"Error in polling loop: {e}")
    # 그냥 계속 진행
```

**문제점**:
- 동일 에러가 반복 발생 시 로그 폭발
- 연속 실패 감지 및 알림 로직 없음

**수정 방법**:
```python
self._consecutive_errors = 0
MAX_CONSECUTIVE_ERRORS = 5

try:
    await self.check_new_deposits()
    self._consecutive_errors = 0
except Exception as e:
    self._consecutive_errors += 1
    logger.error(f"폴링 오류 ({self._consecutive_errors}회 연속): {e}")
    if self._consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
        await self.notify_admin("입금 모니터링 오류 지속 발생")
```

---

### 3.7 localStorage에 토큰 저장 (XSS 취약)

**파일**: `admin-frontend/src/app/(auth)/login/page.tsx`
**라인**: 72

```typescript
localStorage.setItem('admin-auth', JSON.stringify(authData));
```

**문제점**:
- XSS 공격 시 토큰 탈취 가능
- 관리자 계정 탈취로 이어질 수 있음

**수정 방법**:
- httpOnly 쿠키로 토큰 저장
- 또는 BFF(Backend for Frontend) 패턴 사용

---

### 3.8 프론트엔드 에러 처리 미흡

**파일**: `frontend/src/app/lobby/page.tsx`
**라인**: 36-38

```typescript
} catch (error) {
  console.error('방 목록 로드 실패:', error);
  // 사용자에게 에러 표시 없음!
}
```

**문제점**:
- 네트워크 오류 시에도 빈 목록처럼 보임
- "방이 없습니다" vs "서버 연결 실패" 구분 불가

**수정 방법**:
```typescript
const [error, setError] = useState<string | null>(null);

try {
  const response = await tablesApi.list();
  setRooms(response.data.rooms || []);
} catch (error) {
  console.error('방 목록 로드 실패:', error);
  setError('서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.');
}

// 렌더링
{error && <ErrorMessage message={error} onRetry={fetchRooms} />}
```

---

### 3.9 AuditService SQL Injection 가능성

**파일**: `admin-backend/app/services/audit_service.py`
**라인**: 133, 138

```python
where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
count_query = text(f"SELECT COUNT(*) FROM audit_logs WHERE {where_sql}")
```

**문제점**:
- f-string으로 동적 SQL 생성
- `where_clauses`는 파라미터 바인딩을 사용하지만, 구조 자체가 취약

**수정 방법**:
- SQLAlchemy ORM 사용
- 또는 화이트리스트 기반 필터링

---

### 3.10 ban_type 검증 없음

**파일**: `admin-backend/app/services/ban_service.py`
**라인**: 24

```python
async def create_ban(
    self,
    user_id: str,
    ban_type: str,  # 문자열 - 검증 없음!
    ...
):
```

**문제점**:
- `ban_type`이 임의의 문자열 허용
- 잘못된 유형 입력 시 예기치 않은 동작

**수정 방법**:
```python
from enum import Enum

class BanType(str, Enum):
    TEMPORARY = "temporary"
    PERMANENT = "permanent"
    CHAT_ONLY = "chat_only"

async def create_ban(
    self,
    user_id: str,
    ban_type: BanType,  # Enum 사용
    ...
):
```

---

### 3.11 재시도 로직 없음

**파일**: `admin-backend/app/services/crypto/deposit_processor.py`
**라인**: 160-169

```python
response = await client.post(
    f"{self.main_api_url}/api/wallet/credit",
    json={...},
)
# 재시도 없음!
```

**문제점**:
- 네트워크 일시적 오류 시 바로 실패
- 입금 상태 불일치 발생 가능

**수정 방법**:
```python
import tenacity

@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=1, max=10),
    retry=tenacity.retry_if_exception_type(httpx.HTTPError),
)
async def credit_balance(self, ...):
    # ...
```

---

### 3.12 감사 로그 실패 시 로깅 없음

**파일**: `admin-backend/app/services/audit_service.py`
**라인**: 76-89

```python
except Exception as e:
    # 감사 로그 실패는 주요 작업을 중단시키지 않음
    return {
        ...
        "error": str(e)  # 로깅 없이 응답에만 포함!
    }
```

**문제점**:
- `logger.error()` 호출 없음
- 감사 로그 누락 추적 불가
- 컴플라이언스 감사 시 문제

**수정 방법**:
```python
except Exception as e:
    logger.error(
        f"감사 로그 저장 실패 - admin: {admin_username}, action: {action}: {e}",
        exc_info=True
    )
    return {...}
```

---

## 4. Medium 이슈 (검토 후 수정)

### 4.1 CSRF 토큰 없음

**파일**: `admin-backend/app/main.py`
**라인**: 18-24

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**권장**: 중요 작업에 CSRF 토큰 또는 2FA 추가

---

### 4.2 시간대 불일치

**파일**: 여러 파일
**영향**: 날짜/시간 비교 오류 가능

```python
datetime.utcnow()  # naive datetime
expires_at.replace(tzinfo=None)  # timezone 제거
```

**권장**: `datetime.now(timezone.utc)` 사용으로 통일

---

### 4.3 매직 넘버 하드코딩

**파일**: `admin-backend/app/services/bot_detector.py` 등

```python
if response_time_ms < 50:  # 매직 넘버
    bot_score += 30
```

**권장**: 설정 파일로 분리

---

### 4.4 HTTP 클라이언트 리소스 누수 가능

**파일**: `admin-backend/app/services/crypto/ton_exchange_rate.py`

```python
self._http_client: Optional[httpx.AsyncClient] = None
# close() 호출이 보장되지 않음
```

**권장**: Context manager 또는 `__del__` 구현

---

### 4.5 콘솔 로그 프로덕션 노출

**파일**: `admin-frontend/src/app/(auth)/login/page.tsx`

```typescript
console.log('[Login] Button clicked');
console.error('[Login] Error:', err);
```

**권장**: 프로덕션 빌드에서 콘솔 로그 제거

---

### 4.6 에러 응답 파싱 미흡

**파일**: `admin-frontend/src/lib/deposits-api.ts`

```typescript
// API 에러 응답 구조 파싱 없이 throw
```

**권장**: 에러 응답 타입 정의 및 파싱

---

### 4.7 날짜 파싱 에러 미처리

**파일**: `admin-backend/app/api/statistics.py`
**라인**: 128-129

```python
start = datetime.strptime(start_date, "%Y-%m-%d")  # ValueError 가능
```

**권장**: try-except로 감싸고 사용자 친화적 에러 메시지

---

### 4.8 PostgreSQL 특화 문법 사용

**파일**: `admin-backend/app/services/anti_collusion.py`

```sql
array_agg(...)  # PostgreSQL only
```

**권장**: DB 이식성 고려 시 ORM 사용

---

## 5. Low 이슈 (개선 권장)

### 5.1 JettonTransfer가 변경 가능한 dataclass

```python
@dataclass
class JettonTransfer:  # mutable
```

**권장**: `@dataclass(frozen=True)` 사용

---

### 5.2 Pydantic 스키마 미사용

서비스 레이어에서 `dict` 반환이 많음

**권장**: Pydantic 모델로 응답 타입 정의

---

### 5.3 DepositRequest 상태 전이 메서드 없음

```python
request.status = DepositRequestStatus.CONFIRMED  # 직접 변경
```

**권장**: `confirm()`, `expire()`, `cancel()` 메서드 구현

---

### 5.4 탐지 서비스 반환 타입 느슨함

```python
async def detect_bots(self) -> list[dict]:  # dict 구조 불명확
```

**권장**: dataclass 또는 TypedDict 사용

---

### 5.5 Decimal 반올림 정책 미명시

```python
amount = Decimal(amount_nano) / Decimal(10 ** USDT_DECIMALS)
```

**권장**: `quantize()` 및 `ROUND_DOWN` 명시

---

## 6. 수정 가이드

### 6.1 SQL Injection 수정 패턴

```python
# Before (취약)
query = text("SELECT * FROM users WHERE id = " + user_id)
query = text(f"SELECT * FROM users WHERE id = {user_id}")
query = text("SELECT * ... :hours ...".replace(':hours', str(hours)))

# After (안전)
query = text("SELECT * FROM users WHERE id = :user_id")
result = await db.execute(query, {"user_id": user_id})
```

### 6.2 에러 처리 패턴

```python
# Before (Silent Failure)
except Exception:
    return []

# After (명시적 에러 처리)
except sqlalchemy.exc.OperationalError as e:
    logger.error(f"DB 연결 오류: {e}")
    raise DatabaseConnectionError("DB 연결 오류") from e
except Exception as e:
    logger.error(f"예상치 못한 오류: {e}", exc_info=True)
    raise
```

### 6.3 인증 추가 패턴

```python
# router 정의
from app.auth import get_current_user, require_roles

@router.post("/deposit/request")
async def create_request(
    data: DepositRequestCreate,
    current_user: User = Depends(get_current_user),  # 인증
    db: AsyncSession = Depends(get_admin_db),
):
    # 권한 검증
    if data.user_id != current_user.id:
        raise HTTPException(403, "권한 없음")
```

### 6.4 환경변수 패턴

```python
# config.py
class Settings(BaseSettings):
    jwt_secret_key: str = Field(
        ...,  # 필수 (기본값 없음)
        min_length=32,
        description="JWT 서명 키 (최소 32자)"
    )

# .env (프로덕션)
JWT_SECRET_KEY=your-very-long-and-secure-random-string-here
```

```typescript
// frontend: .env.local
NEXT_PUBLIC_API_URL=https://api.example.com

// 사용
const API_URL = process.env.NEXT_PUBLIC_API_URL!;
```

---

## 7. 액션 아이템

### 🔴 즉시 조치 (금일 내)

| # | 항목 | 파일 | 담당 |
|---|------|------|------|
| 1 | SQL Injection 수정 | statistics_service.py:379-382 | Backend |
| 2 | ton_deposit.py 인증 추가 | ton_deposit.py 전체 | Backend |
| 3 | JWT Secret 환경변수 필수화 | config.py:20 | Backend |
| 4 | API URL 환경변수화 | login/page.tsx:30,47 | Frontend |

### 🟠 단기 조치 (1주일 내)

| # | 항목 | 파일 | 담당 |
|---|------|------|------|
| 1 | Silent failure 에러 로깅 추가 | statistics_service.py 등 9개 | Backend |
| 2 | 입금 최대값 제한 추가 | ton_deposit.py:28 | Backend |
| 3 | 수동 승인 tx_hash 필수화 | deposit_processor.py:272 | Backend |
| 4 | IP 주소 기록 | deposit_processor.py | Backend |
| 5 | 재시도 로직 추가 | deposit_processor.py | Backend |
| 6 | 프론트엔드 에러 표시 | lobby/page.tsx | Frontend |
| 7 | localStorage → httpOnly 쿠키 | login/page.tsx | Frontend |

### 🟡 중기 조치 (1개월 내)

| # | 항목 | 파일 | 담당 |
|---|------|------|------|
| 1 | CSRF 토큰 구현 | main.py | Backend |
| 2 | 분산 트랜잭션 보상 로직 | deposit_processor.py | Backend |
| 3 | 핫월렛 정보 Secrets Manager 이관 | ton_client.py | DevOps |
| 4 | ban_type Enum화 | ban_service.py | Backend |
| 5 | 시간대 처리 통일 | 전체 | Backend |
| 6 | 2FA 도입 | auth 모듈 | Backend |

### 🟢 장기 개선 (분기 내)

| # | 항목 | 파일 | 담당 |
|---|------|------|------|
| 1 | Pydantic 스키마 도입 | 서비스 레이어 전체 | Backend |
| 2 | 타입 설계 개선 | 모델/서비스 | Backend |
| 3 | 설정 외부화 | 탐지 서비스들 | Backend |
| 4 | 컴플라이언스 감사 체계 | audit_service.py | Backend |

---

## 부록: 검토 파일 목록

### admin-backend
- `app/api/ton_deposit.py` - **Critical**
- `app/api/admin_ton_deposit.py` - High
- `app/services/statistics_service.py` - **Critical**
- `app/services/ban_service.py` - High
- `app/services/audit_service.py` - High
- `app/services/crypto/deposit_processor.py` - **Critical**
- `app/services/crypto/ton_client.py` - High
- `app/services/crypto/ton_exchange_rate.py` - Medium
- `app/services/crypto/ton_deposit_monitor.py` - High
- `app/config.py` - **Critical**

### admin-frontend
- `src/app/(auth)/login/page.tsx` - **Critical**
- `src/app/(dashboard)/page.tsx` - Medium
- `src/lib/deposits-api.ts` - Medium

### frontend
- `src/app/lobby/page.tsx` - High
- `src/app/login/page.tsx` - Medium

---

**보고서 작성**: Claude Code
**검토일**: 2026-01-16
