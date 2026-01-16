# 백엔드 및 관리자 대시보드 업그레이드 스킬

## 프로젝트 개요
온라인 홀덤 게임 시스템의 백엔드 보안 강화 및 관리자 대시보드 완성

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
# Admin Backend 테스트
cd admin-backend && pytest tests/ -v

# Admin Frontend 빌드
cd admin-frontend && npm run build

# Backend 테스트
cd backend && pytest tests/ -v

# 서버 실행 확인
cd admin-backend && python -c "from app.main import app; print('OK')"
cd backend && python -c "from app.main import app; print('OK')"
```

### 4. 중단 대비 원칙
- 각 Step 완료 시 즉시 `WORK_PROGRESS.md` 업데이트
- 작업 중단 시 현재 진행 상태 기록
- 재개 시 `WORK_PROGRESS.md`에서 마지막 완료 Step 확인

## 파일 구조

### Admin Backend
```
admin-backend/
├── app/
│   ├── api/
│   │   ├── dashboard.py      # 대시보드 API
│   │   ├── users.py          # 사용자 관리 API
│   │   ├── bans.py           # 제재 관리 API
│   │   └── audit.py          # 감사 로그 API
│   ├── services/
│   │   ├── metrics_service.py     # 메트릭 서비스
│   │   ├── statistics_service.py  # 통계 서비스
│   │   ├── ban_service.py         # 제재 서비스
│   │   ├── audit_service.py       # 감사 로그 서비스
│   │   └── main_api_client.py     # 메인 백엔드 연동
│   └── models/
│       ├── admin_user.py
│       ├── audit_log.py
│       └── suspicious.py
```

### Admin Frontend
```
admin-frontend/
├── src/
│   ├── app/(dashboard)/
│   │   ├── page.tsx           # 대시보드 메인
│   │   ├── users/page.tsx     # 사용자 목록
│   │   ├── users/[id]/page.tsx # 사용자 상세
│   │   └── bans/page.tsx      # 제재 관리
│   └── components/
│       ├── dashboard/
│       │   ├── CCUChart.tsx
│       │   ├── RevenueCard.tsx
│       │   └── ServerHealthCard.tsx
│       └── users/
│           ├── UserTable.tsx
│           └── BanDialog.tsx
```

### Backend (보안 강화)
```
backend/
├── app/
│   └── services/
│       ├── anti_collusion.py      # 담합 방지
│       ├── chip_dumping_detector.py # 칩 밀어주기 탐지
│       ├── bot_detector.py        # 봇 탐지
│       ├── anomaly_detector.py    # 이상 탐지
│       └── auto_ban.py            # 자동 제재
```

## 작업 진행 현황 확인

작업 시작 전 반드시 확인:
```
.kiro/specs/backend-admin-upgrade/WORK_PROGRESS.md
```

## 관련 문서

- `.kiro/specs/backend-admin-upgrade/requirements.md` - 요구사항
- `.kiro/specs/backend-admin-upgrade/tasks.md` - 태스크 목록
- `.kiro/specs/backend-admin-upgrade/design.md` - 기술 설계
- `.kiro/specs/backend-admin-upgrade/WORK_PROGRESS.md` - 진행 현황
- `.kiro/specs/admin-dashboard/` - 기존 관리자 대시보드 스펙

## 테스트 명령어

```bash
# Admin Backend 전체 테스트
cd admin-backend && pytest tests/ -v

# Admin Frontend 빌드
cd admin-frontend && npm run build

# Backend 전체 테스트
cd backend && pytest tests/ -v

# 특정 테스트만
pytest tests/services/test_ban_service.py -v

# 커버리지 포함
pytest tests/ -v --cov=app --cov-report=term-missing
```

## 주요 API 엔드포인트

### 대시보드
```
GET /api/dashboard/summary
GET /api/dashboard/ccu
GET /api/dashboard/ccu/history
GET /api/dashboard/dau
GET /api/dashboard/rooms
GET /api/dashboard/server/health
```

### 사용자 관리
```
GET  /api/users
GET  /api/users/{id}
GET  /api/users/{id}/transactions
GET  /api/users/{id}/login-history
```

### 제재 관리
```
GET  /api/bans
POST /api/bans
DELETE /api/bans/{id}
```

## 주의사항

1. **메인 DB 읽기 전용** - Admin에서 메인 DB 직접 수정 금지
2. **Admin API 사용** - 제재 등 쓰기 작업은 메인 백엔드 Admin API 호출
3. **감사 로그 필수** - 모든 관리자 액션 기록
4. **권한 검증** - RBAC 미들웨어 적용 확인
5. **테스트 필수** - 각 Step 완료 후 반드시 테스트 실행
