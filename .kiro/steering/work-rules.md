# 작업 규칙 (Work Rules)

이 문서는 모든 개발 작업에 적용되는 필수 규칙입니다.

---

## 1. 단계별 작업 원칙

### 1.1 한 번에 하나의 Step만 작업
- 여러 Step을 동시에 진행하지 않음
- 각 Step은 명확한 완료 조건을 가짐
- Step 완료 전 다음 Step으로 진행 금지

### 1.2 검증 테스트 필수
각 Step 완료 후 반드시 검증 테스트 실행:

```bash
# 백엔드 테스트
cd backend && pytest tests/ -v
cd admin-backend && pytest tests/ -v

# 프론트엔드 빌드
cd frontend && npm run build
cd admin-frontend && npm run build

# 서버 실행 확인
python -c "from app.main import app; print('OK')"
```

### 1.3 완료 체크 필수
- 테스트 통과 후 `WORK_PROGRESS.md`에 완료 체크 (✅) 표시
- 완료일 및 검증 결과 기록
- 다음 Step 진행 전 이전 Step 완료 확인

---

## 2. 서브에이전트 사용 원칙

### 2.1 context-gatherer 사용
복잡한 코드 작성 전 관련 파일 파악:
- 새로운 기능 개발 시
- 기존 코드 수정 시
- 버그 수정 시

### 2.2 general-task-execution 사용
멀티 파일 작업 시:
- 여러 파일 동시 생성/수정
- 복잡한 리팩토링
- 대규모 테스트 작성

---

## 3. 중단 대비 원칙

### 3.1 즉시 문서 업데이트
- 각 Step 완료 시 즉시 `WORK_PROGRESS.md` 업데이트
- 작업 중단 시 현재 진행 상태 기록
- 미완료 작업 명시

### 3.2 재개 시 확인 사항
1. `WORK_PROGRESS.md`에서 마지막 완료 Step 확인
2. 미완료 작업 확인
3. 이전 Step 완료 상태 검증
4. 현재 Step부터 재개

---

## 4. 코드 품질 원칙

### 4.1 테스트 작성
- 새 기능: 단위 테스트 필수
- 버그 수정: 회귀 테스트 추가
- API: 통합 테스트 포함

### 4.2 문서화
- 복잡한 로직: 주석 추가
- API: docstring 필수
- 설정: 환경변수 문서화

### 4.3 에러 처리
- 예외 상황 처리
- 적절한 에러 메시지
- 로깅 추가

---

## 5. 작업 진행 현황 문서

각 프로젝트별 진행 현황 문서:

| 프로젝트 | 진행 현황 문서 |
|---------|---------------|
| TON/USDT 입금 | `.kiro/specs/ton-usdt-deposit/WORK_PROGRESS.md` |
| 백엔드/관리자 업그레이드 | `.kiro/specs/backend-admin-upgrade/WORK_PROGRESS.md` |

---

## 6. 검증 체크리스트

### Step 완료 시 확인 사항
- [ ] 코드 작성 완료
- [ ] 단위 테스트 통과
- [ ] 빌드 성공
- [ ] 서버 실행 확인
- [ ] WORK_PROGRESS.md 업데이트
- [ ] 완료일 기록
- [ ] 검증 결과 기록

### Phase 완료 시 확인 사항
- [ ] 모든 Step 완료
- [ ] 통합 테스트 통과
- [ ] 체크포인트 조건 충족
- [ ] Phase 완료일 기록
