# 백엔드 및 관리자 대시보드 업그레이드 작업 계획서

> 작성일: 2026-01-16
> 버전: 1.0

---

## 1. 개요

본 문서는 온라인 홀덤 게임 시스템의 백엔드 및 관리자 대시보드(Backoffice)에 대한 추가 작업 및 업그레이드 계획을 정리합니다.

### 현재 구현 상태 요약

| 영역 | 완료율 | 상태 |
|------|--------|------|
| 핵심 게임 로직 | 100% | ✅ 완료 |
| 사용자 관리 | 60% | 🔄 진행중 |
| 방/테이블 관리 | 93% | 🔄 진행중 |
| 인게임 기능 | 60% | 🔄 진행중 |
| 네트워킹 | 92% | 🔄 진행중 |
| 데이터베이스 | 82% | 🔄 진행중 |
| UI/UX | 85% | 🔄 진행중 |
| 보안 | 55% | ⚠️ 주의 필요 |
| **Backoffice** | **0%** | ❌ 미시작 |

---

## 2. 관리자 대시보드 (Admin Dashboard) 잔여 작업

### Phase 3: 대시보드 및 모니터링 (미완료)

**우선순위: 높음** | **예상 소요: 1주**

#### 백엔드 작업
- [ ] CCU/DAU 집계 서비스 완성 (Redis 실시간 조회)
- [ ] 방/플레이어 통계 서비스 구현
- [ ] 매출 통계 서비스 구현 (일별/주별/월별 레이크)

#### 프론트엔드 작업
- [ ] 메인 대시보드 레이아웃 구현
- [ ] CCU/DAU 차트 컴포넌트 (Recharts, 5초 자동 갱신)
- [ ] 매출 카드 및 통계 컴포넌트
- [ ] 서버 상태 표시 컴포넌트 (CPU, 메모리, 레이턴시)

---

### Phase 4: 사용자 관리 (미완료)

**우선순위: 높음** | **예상 소요: 1주**

#### 백엔드 작업
- [ ] 사용자 검색 API 완성 (username, email, user_id)
- [ ] 사용자 상세 정보 API (계정, 잔액, 활동, 로그인 기록)
- [ ] 거래 내역 조회 API

#### 프론트엔드 작업
- [ ] 사용자 목록 페이지 (DataTable, 검색, 필터, 정렬)
- [ ] 사용자 상세 페이지 (탭: 정보, 거래, 로그인, 핸드)

---

### Phase 5: 제재 및 감사 로그 (미완료)

**우선순위: 높음** | **예상 소요: 1주**

#### 백엔드 작업
- [ ] Ban 서비스 구현 (임시/영구, 채팅 금지)
- [ ] 메인 백엔드 Admin API 연동 (MainAPIClient)
- [ ] AuditLog 서비스 구현

#### 프론트엔드 작업
- [ ] 제재 목록 페이지
- [ ] 제재 생성 다이얼로그

---

### Phase 6-9: 암호화폐 관리 - TON/USDT 입금 시스템 (변경됨)

**우선순위: 중간** | **예상 소요: 8주**

> ⚠️ **중요 변경**: 기존 TRON(TRC-20) 기반에서 **TON 네트워크 기반 USDT Jetton**으로 변경
> 상세 계획: `.kiro/specs/ton-usdt-deposit/` 참조

#### Phase 6: TON 기본 인프라 (Week 5-6)
- [ ] TonExchangeRateService (CoinGecko/Binance API)
- [ ] TonClient (pytoniq, USDT Jetton)
- [ ] deposit_requests 테이블 생성
- [ ] Telegram Bot 기본 설정

#### Phase 7: 입금 신청 & QR 발급 (Week 6)
- [ ] 입금 요청 API 구현
- [ ] QR 코드 생성 서비스
- [ ] ton:// URI 생성
- [ ] Telegram Bot 입금 명령어

#### Phase 8: 입금 감지 & 자동 승인 (Week 7-8)
- [ ] TonDepositMonitor (Polling 방식)
- [ ] Jetton transfer 감지
- [ ] 메모 매칭 + 자동 승인
- [ ] 만료 처리 로직
- [ ] Telegram 알림 서비스

#### Phase 9: 지갑 관리 & 보안 (Week 8)
- [ ] Cold Wallet 자동 이동
- [ ] 핫월렛 잔액 모니터링
- [ ] 스캠 Jetton 방지
- [ ] Rate Limiting

---

### Phase 10: 추가 기능 (미완료)

**우선순위: 중간** | **예상 소요: 1주**

- [ ] 방 관리 기능 (목록, 상세, 강제 종료)
- [ ] 핸드 리플레이 기능
- [ ] 공지/점검 관리 기능
- [ ] 의심 사용자 관리 기능
- [ ] 자산 수동 조정 기능

---

### Phase 11: 배포 및 운영 준비 (미완료)

**우선순위: 낮음** | **예상 소요: 1주**

- [ ] 프로덕션 환경 설정
- [ ] Kubernetes 매니페스트
- [ ] 모니터링 설정 (Prometheus, Grafana)
- [ ] 보안 감사 및 침투 테스트

---

## 3. 백엔드 업그레이드 작업

### 3.1 보안 강화 (Security Enhancement)

**우선순위: 높음** | **예상 소요: 2주**

#### 부정 행위 탐지 시스템 (Anti-Collusion)
- [ ] 동일 IP/기기 같은 방 입장 차단
- [ ] 칩 밀어주기(Chip Dumping) 패턴 모니터링
- [ ] 의심 행위 자동 플래깅

#### 봇(Bot) 탐지 시스템
- [ ] 행동 패턴 분석 (응답 시간, 액션 패턴)
- [ ] 머신러닝 기반 이상 탐지
- [ ] 자동 제재 연동

#### 클라이언트 보안
- [ ] 클라이언트 변조 방지 솔루션
- [ ] 패킷 암호화 (WebSocket)
- [ ] 요청 서명 검증

---

### 3.2 사용자 관리 확장

**우선순위: 중간** | **예상 소요: 1주**

- [ ] 소셜 로그인 연동 (Google, Kakao)
- [ ] 성인 인증 / KYC 모듈
- [ ] 아바타 설정 기능
- [ ] 통계 지표 (VPIP, PFR 등)

---

### 3.3 인게임 기능 확장

**우선순위: 중간** | **예상 소요: 1주**

- [ ] 플레이어 전용 채팅 구분
- [ ] 이모티콘 시스템
- [ ] 선물하기 기능
- [ ] 핸드 리플레이 기능

---

### 3.4 네트워킹 최적화

**우선순위: 낮음** | **예상 소요: 3일**

- [ ] 관전자/플레이어 그룹 분리 전송
- [ ] 중간 입장 시 테이블 상황 동기화 (Snapshot)

---

### 3.5 데이터베이스 확장

**우선순위: 낮음** | **예상 소요: 3일**

- [ ] 핸드 히스토리 로그 (MongoDB/Elasticsearch)
- [ ] 부정 행위 분석용 상세 로그

---

## 4. 우선순위 정리

### 🔴 높음 (즉시 착수)

1. **Backoffice Phase 3-5** - 대시보드, 사용자 관리, 제재 시스템
2. **부정 행위 탐지 시스템** - Anti-Collusion, Bot Detection
3. **클라이언트 보안** - 변조 방지, 패킷 암호화

### 🟡 중간 (2-4주 내)

4. **Backoffice Phase 6-9** - 암호화폐 관리
5. **소셜 로그인** - Google, Kakao
6. **인게임 기능 확장** - 이모티콘, 선물하기

### 🟢 낮음 (4주 이후)

7. **Backoffice Phase 10-11** - 추가 기능, 배포 준비
8. **네트워킹 최적화**
9. **데이터베이스 확장**

---

## 5. 예상 일정

| 주차 | 작업 내용 |
|------|----------|
| 1주차 | Backoffice Phase 3 (대시보드 모니터링) |
| 2주차 | Backoffice Phase 4 (사용자 관리) |
| 3주차 | Backoffice Phase 5 (제재/감사 로그) + 부정 행위 탐지 기초 |
| 4주차 | 부정 행위 탐지 완성 + 봇 탐지 시스템 |
| 5-6주차 | TON 기본 인프라 + 입금 신청 & QR 발급 |
| 7-8주차 | 입금 감지 & 자동 승인 + 지갑 관리 |
| 9주차 | Backoffice Phase 10 (추가 기능) |
| 10주차 | Backoffice Phase 11 (배포 준비) + 보안 감사 |

---

## 6. 기술 스택 참고

### Admin Backend
- FastAPI + SQLAlchemy 2.0 + Pydantic v2
- Redis (세션, 캐싱)
- PostgreSQL (Admin DB)

### Admin Frontend
- Next.js 14 + TypeScript
- shadcn/ui + Tailwind CSS
- Zustand (상태 관리)
- Recharts (차트)

### 암호화폐 연동 (TON 네트워크)
- pytoniq / tonapi-python (TON 네트워크)
- CoinGecko / Binance API (환율)
- aiogram v3 (Telegram Bot)
- qrcode[pil] (QR 생성)

---

## 7. 참고 문서

- `.kiro/specs/admin-dashboard/requirements.md` - 관리자 대시보드 요구사항
- `.kiro/specs/admin-dashboard/tasks.md` - 관리자 대시보드 태스크 목록
- `.kiro/specs/ton-usdt-deposit/requirements.md` - TON/USDT 입금 시스템 상세 계획
- `.kiro/specs/ton-usdt-deposit/tasks.md` - TON/USDT 입금 태스크 목록
- `.kiro/specs/ton-usdt-deposit/design.md` - TON/USDT 입금 기술 설계
- `IMPLEMENTATION_STATUS.md` - 전체 구현 현황
- `docs/API_REFERENCE.md` - API 레퍼런스

---

> 이 문서는 프로젝트 진행에 따라 업데이트됩니다.
