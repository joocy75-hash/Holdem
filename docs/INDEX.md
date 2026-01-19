# 📚 문서 인덱스

> 프로젝트의 모든 문서를 체계적으로 정리한 인덱스입니다.

**최종 업데이트**: 2026-01-19

---

## 🚀 시작하기

| 문서 | 설명 | 대상 |
|------|------|------|
| [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md) | 여러 계정 작업 시 빠른 참조 가이드 | 모든 개발자 ⭐ |
| [WORK_PLAN_2026.md](WORK_PLAN_2026.md) | 백엔드/프론트/관리자 작업 계획서 | 모든 개발자 ⭐⭐⭐ |
| [WORK_SUMMARY.md](WORK_SUMMARY.md) | 작업 계획서 요약 및 사용법 | 모든 개발자 ⭐ |
| [QUICKSTART.md](../QUICKSTART.md) | 프로젝트 설치 및 실행 가이드 | 신규 개발자 |

---

## 🏗️ 프로젝트 설정

### 환경 설정
| 문서 | 설명 |
|------|------|
| [01-setup-local.md](01-setup-local.md) | 로컬 개발 환경 설정 |
| [02-env-vars.md](02-env-vars.md) | 환경변수 설명 |
| [04-folder-structure.md](04-folder-structure.md) | 폴더 구조 |

### 개발 프로세스
| 문서 | 설명 |
|------|------|
| [03-dev-workflow.md](03-dev-workflow.md) | Git 브랜치 전략, 커밋 컨벤션, 코드 스타일 |

---

## 🎮 게임 엔진 & 아키텍처

| 문서 | 설명 |
|------|------|
| [10-engine-architecture.md](10-engine-architecture.md) | 게임 엔진 아키텍처 |
| [11-engine-state-model.md](11-engine-state-model.md) | 상태 모델 및 상태 관리 |
| [ADR/ADR-0001-pokerkit-core.md](ADR/ADR-0001-pokerkit-core.md) | PokerKit 코어 라이브러리 선정 ADR |

---

## 🔌 실시간 통신 & API

### WebSocket 프로토콜
| 문서 | 설명 |
|------|------|
| [20-realtime-protocol-v1.md](20-realtime-protocol-v1.md) | WebSocket 프로토콜 v1 스펙 |
| [21-error-codes-v1.md](21-error-codes-v1.md) | 에러 코드 정의 |
| [22-idempotency-ordering.md](22-idempotency-ordering.md) | 멱등성 및 순서 보장 규칙 |

### API 레퍼런스
| 문서 | 설명 |
|------|------|
| [API_REFERENCE.md](API_REFERENCE.md) | REST API 및 WebSocket 이벤트 명세 |
| [FRONTEND_INTEGRATION_GUIDE.md](FRONTEND_INTEGRATION_GUIDE.md) | 프론트엔드 연동 가이드 (TypeScript 예제) |

---

## 🎨 UI/UX 스펙

| 문서 | 설명 |
|------|------|
| [30-ui-ia.md](30-ui-ia.md) | UI 정보 아키텍처 |
| [31-table-ui-spec.md](31-table-ui-spec.md) | 테이블 UI 스펙 |
| [32-lobby-ui-spec.md](32-lobby-ui-spec.md) | 로비 UI 스펙 |
| [33-ui-components.md](33-ui-components.md) | UI 컴포넌트 라이브러리 |

---

## 🔄 게임 로직 & 상태 관리

| 문서 | 설명 |
|------|------|
| [40-reconnect-recovery.md](40-reconnect-recovery.md) | 재연결 및 복구 메커니즘 |
| [41-state-consistency.md](41-state-consistency.md) | 상태 일관성 보장 |
| [42-timer-turn-rules.md](42-timer-turn-rules.md) | 타이머 및 턴 관리 규칙 |

---

## 🚢 운영 & 배포

| 문서 | 설명 |
|------|------|
| [51-observability.md](51-observability.md) | 로깅, 메트릭, 트레이싱 |
| [52-deploy-staging.md](52-deploy-staging.md) | 스테이징 배포 가이드 |

---

## 💰 TON/USDT 입금 시스템

| 문서 | 설명 |
|------|------|
| [TON_USDT_DEPOSIT_GUIDE.md](TON_USDT_DEPOSIT_GUIDE.md) | TON/USDT 입금 시스템 사용자 및 관리자 가이드 |

---

## 📜 라이선스 & 법적 고지

| 문서 | 설명 |
|------|------|
| [60-license-audit.md](60-license-audit.md) | 오픈소스 라이선스 감사 |
| [61-third-party-assets.md](61-third-party-assets.md) | 서드파티 에셋 목록 |

---

## 🗄️ 아카이브

| 폴더 | 설명 |
|------|------|
| [archive/](archive/) | 구버전 문서 보관 (참고용) |

---

## 📌 문서 카테고리 요약

### 신규 개발자 필독
1. [QUICKSTART.md](../QUICKSTART.md)
2. [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md)
3. [WORK_PLAN_2026.md](WORK_PLAN_2026.md)
4. [03-dev-workflow.md](03-dev-workflow.md)

### 백엔드 개발자
- 게임 엔진 (10-11)
- 실시간 통신 (20-22)
- 게임 로직 (40-42)
- WORK_PLAN_2026.md (Phase 1-5)

### 프론트엔드 개발자
- UI/UX 스펙 (30-33)
- API 연동 (API_REFERENCE.md, FRONTEND_INTEGRATION_GUIDE.md)
- WORK_PLAN_2026.md (Phase 6-9)

### 관리자/DevOps
- 운영 & 배포 (51-52)
- TON/USDT 시스템
- WORK_PLAN_2026.md (Phase 10)

---

## 🔍 문서 검색 팁

### 키워드별 문서 찾기

| 키워드 | 관련 문서 |
|--------|----------|
| WebSocket | 20-realtime-protocol-v1.md, API_REFERENCE.md |
| 게임 로직 | 10-11, 40-42, WORK_PLAN_2026.md (Phase 1-4) |
| UI 컴포넌트 | 30-33, WORK_PLAN_2026.md (Phase 6-9) |
| 테스트 | WORK_PLAN_2026.md (Phase 5, 검증 프로세스) |
| 배포 | 52-deploy-staging.md |
| 에러 처리 | 21-error-codes-v1.md |
| 재연결 | 40-reconnect-recovery.md |

### 빠른 찾기
```bash
# 특정 키워드가 포함된 문서 검색
grep -r "키워드" docs/*.md

# 파일명으로 검색
find docs -name "*keyword*.md"
```

---

## 📝 문서 작성 가이드

### 새 문서 추가 시
1. 적절한 번호 범위 선택:
   - 00-09: 프로젝트 설정
   - 10-19: 아키텍처
   - 20-29: 실시간 통신
   - 30-39: UI/UX
   - 40-49: 게임 로직
   - 50-59: 운영
   - 60-69: 법적 고지
   - 70-79: (예약)
   - 80-89: (예약)
   - 90-99: (예약)

2. 파일명 규칙: `번호-kebab-case.md`
3. 이 INDEX.md 업데이트

### 문서 작성 템플릿
```markdown
# 문서 제목

> 간단한 설명

---

## 목차
1. [섹션 1](#섹션-1)
2. [섹션 2](#섹션-2)

---

## 섹션 1

내용...

---

## 관련 문서
- [다른-문서.md](./다른-문서.md)
```

---

## 🔄 문서 업데이트 이력

| 날짜 | 변경 사항 |
|------|----------|
| 2026-01-19 | INDEX.md 생성, 중복 문서 아카이브 |
| 2026-01-19 | WORK_PLAN_2026.md, QUICK_START_GUIDE.md 추가 |

---

**유지보수**: 이 인덱스는 문서 추가/삭제 시 함께 업데이트해야 합니다.
