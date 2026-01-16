# 백엔드 및 관리자 대시보드 업그레이드 태스크 목록

> 작성일: 2026-01-16

---

## Part A: 관리자 대시보드 잔여 작업

### Phase 3: 대시보드 및 모니터링 (Week 1)

- [ ] A1. 메트릭 수집 서비스 완성
  - [ ] A1.1 CCU/DAU 집계 서비스 구현
    - Redis에서 실시간 접속자 수 조회
    - 시간별 DAU 집계 쿼리
    - 파일: `admin-backend/app/services/metrics_service.py`
    - 요구사항: 1.1, 1.2

  - [ ] A1.2 방/플레이어 통계 서비스 구현
    - 활성 방 수, 플레이어 분포 조회
    - 메인 DB 연동
    - 파일: `admin-backend/app/services/statistics_service.py`
    - 요구사항: 1.3

  - [ ] A1.3 매출 통계 서비스 완성
    - 일별/주별/월별 레이크 수익 집계
    - 날짜 범위 필터링
    - 파일: `admin-backend/app/services/statistics_service.py`
    - 요구사항: 2.1, 2.2, 2.3, 2.4

- [ ] A2. 대시보드 UI 구현
  - [ ] A2.1 메인 대시보드 레이아웃 구현
    - 사이드바 네비게이션
    - 헤더 (사용자 정보, 로그아웃)
    - 파일: `admin-frontend/src/app/(dashboard)/layout.tsx`
    - 요구사항: 1.1

  - [ ] A2.2 CCU/DAU 차트 컴포넌트 구현
    - Recharts 라인 차트
    - 5초 자동 갱신
    - 파일: `admin-frontend/src/components/dashboard/CCUChart.tsx`
    - 요구사항: 1.1, 1.2

  - [ ] A2.3 매출 카드 및 통계 컴포넌트 구현
    - 일별/주별/월별 탭
    - 날짜 범위 선택기
    - 파일: `admin-frontend/src/components/dashboard/RevenueCard.tsx`
    - 요구사항: 2.1, 2.4

  - [ ] A2.4 서버 상태 표시 컴포넌트 완성
    - CPU, 메모리, 레이턴시 게이지
    - 임계값 초과 시 경고 표시
    - 파일: `admin-frontend/src/components/dashboard/ServerHealthCard.tsx`
    - 요구사항: 1.4, 1.5

---

### Phase 4: 사용자 관리 (Week 2)

- [ ] A3. 사용자 조회 서비스 구현
  - [ ] A3.1 사용자 검색 API 완성
    - username, email, user_id 검색
    - 페이지네이션 및 필터링
    - 파일: `admin-backend/app/api/users.py`
    - 요구사항: 5.1, 5.5

  - [ ] A3.2 사용자 상세 정보 API 구현
    - 계정 정보, 잔액, 최근 활동
    - 로그인 기록 (IP 포함)
    - 거래 내역
    - 파일: `admin-backend/app/api/users.py`
    - 요구사항: 5.2, 5.3, 5.4

- [ ] A4. 사용자 관리 UI 완성
  - [ ] A4.1 사용자 목록 페이지 완성
    - DataTable with 검색, 필터, 정렬
    - 페이지네이션
    - 파일: `admin-frontend/src/app/(dashboard)/users/page.tsx`
    - 요구사항: 5.1, 5.5

  - [ ] A4.2 사용자 상세 페이지 구현
    - 탭 구조 (정보, 거래, 로그인, 핸드)
    - 제재 버튼
    - 파일: `admin-frontend/src/app/(dashboard)/users/[id]/page.tsx`
    - 요구사항: 5.2, 5.3, 5.4

---

### Phase 5: 제재 및 감사 로그 (Week 3)

- [ ] A5. 제재 시스템 구현
  - [ ] A5.1 Ban 서비스 구현
    - 제재 생성 (임시/영구, 사유)
    - 제재 해제
    - 채팅 금지 (게임 허용)
    - 파일: `admin-backend/app/services/ban_service.py`
    - 요구사항: 6.1, 6.2, 6.4, 6.6

  - [ ] A5.2 메인 백엔드 Admin API 연동
    - MainAPIClient 구현
    - ban_user, unban_user 호출
    - 파일: `admin-backend/app/services/main_api_client.py`
    - 요구사항: 11.4

- [ ] A6. 감사 로그 시스템 구현
  - [ ] A6.1 AuditLog 서비스 구현
    - 모든 관리자 액션 기록
    - 조회 API (필터링, 페이지네이션)
    - 파일: `admin-backend/app/services/audit_service.py`
    - 요구사항: 3.5, 4.4, 6.5, 7.4, 10.4

- [ ] A7. 제재 관리 UI 구현
  - [ ] A7.1 제재 목록 페이지 구현
    - 활성 제재 목록
    - 제재 해제 버튼
    - 파일: `admin-frontend/src/app/(dashboard)/bans/page.tsx`
    - 요구사항: 6.3, 6.4

  - [ ] A7.2 제재 생성 다이얼로그 구현
    - 제재 유형, 기간, 사유 입력
    - 확인 다이얼로그
    - 파일: `admin-frontend/src/components/users/BanDialog.tsx`
    - 요구사항: 6.1

---

### Phase 6: 암호화폐 기본 인프라 (Week 5-6)

- [ ] A8. 환율 서비스 구현
  - [ ] A8.1 ExchangeRateService 구현
    - Upbit API 연동 (USDT/KRW)
    - Binance API 폴백
    - Redis 캐싱 (30초 TTL)
    - 파일: `admin-backend/app/services/crypto/exchange_rate.py`
    - 요구사항: 12.3, 15.1

  - [ ] A8.2 환율 히스토리 저장 구현
    - 1분 간격 환율 기록
    - 히스토리 조회 API
    - 파일: `admin-backend/app/services/crypto/exchange_rate.py`
    - 요구사항: 15.2

- [ ] A9. TRON 네트워크 클라이언트 구현
  - [ ] A9.1 TronClient 기본 구현
    - tronpy 라이브러리 연동
    - USDT TRC-20 컨트랙트 연결
    - 잔액 조회, 트랜잭션 조회
    - 파일: `admin-backend/app/services/crypto/tron_client.py`
    - 요구사항: 12.5, 14.1

  - [ ] A9.2 트랜잭션 확인 수 조회 구현
    - 블록 번호 기반 확인 수 계산
    - 20 confirmations 기준 확정
    - 파일: `admin-backend/app/services/crypto/tron_client.py`
    - 요구사항: 12.4

- [ ] A10. 암호화폐 데이터 모델 구현
  - [ ] A10.1 CryptoDeposit 모델 구현
    - 입금 기록 테이블
    - 상태 관리 (pending → confirmed → credited)
    - 파일: `admin-backend/app/models/crypto.py`
    - 요구사항: 12.1, 12.2

  - [ ] A10.2 CryptoWithdrawal 모델 구현
    - 출금 요청 테이블
    - 승인 워크플로우 상태
    - 파일: `admin-backend/app/models/crypto.py`
    - 요구사항: 13.1, 13.2

---

### Phase 7-9: 입출금 및 지갑 관리 (Week 7-8)

- [ ] A11. 입금 관리 시스템
  - [ ] A11.1 DepositMonitor 구현
  - [ ] A11.2 입금 확정 처리 구현
  - [ ] A11.3 입금 관리 API 구현
  - [ ] A11.4 입금 관리 UI 구현

- [ ] A12. 출금 관리 시스템
  - [ ] A12.1 WithdrawalProcessor 구현
  - [ ] A12.2 HSM/KMS 연동 구현
  - [ ] A12.3 출금 승인 워크플로우 구현
  - [ ] A12.4 출금 관리 UI 구현

- [ ] A13. 지갑 관리 시스템
  - [ ] A13.1 WalletManager 구현
  - [ ] A13.2 잔액 경고 시스템 구현
  - [ ] A13.3 암호화폐 통계 서비스 구현
  - [ ] A13.4 지갑 관리 UI 구현

---

### Phase 10: 추가 기능 (Week 9)

- [ ] A14. 방 관리 기능
  - [ ] A14.1 방 목록/상세 API 구현
  - [ ] A14.2 방 강제 종료 API 구현
  - [ ] A14.3 방 관리 UI 구현

- [ ] A15. 핸드 리플레이 기능
  - [ ] A15.1 핸드 검색/상세 API 구현
  - [ ] A15.2 핸드 내보내기 API 구현
  - [ ] A15.3 핸드 리플레이 UI 구현

- [ ] A16. 공지/점검 관리 기능
  - [ ] A16.1 공지/점검 API 구현
  - [ ] A16.2 공지/점검 UI 구현

- [ ] A17. 의심 사용자 관리 기능
  - [ ] A17.1 의심 사용자 API 구현
  - [ ] A17.2 의심 사용자 UI 구현

- [ ] A18. 자산 수동 조정 기능
  - [ ] A18.1 잔액 조정 API 구현
  - [ ] A18.2 잔액 조정 UI 구현

---

### Phase 11: 배포 및 운영 준비 (Week 10)

- [ ] A19. 프로덕션 배포 준비
  - [ ] A19.1 프로덕션 환경 설정
  - [ ] A19.2 Kubernetes 매니페스트 작성
  - [ ] A19.3 모니터링 설정 (Prometheus, Grafana)

- [ ] A20. 보안 검토
  - [ ] A20.1 보안 감사 수행
  - [ ] A20.2 침투 테스트

---

## Part B: 백엔드 보안 강화

### B1. 부정 행위 탐지 시스템 (Week 3-4)

- [ ] B1.1 동일 IP/기기 탐지 시스템
  - 같은 방 입장 차단 로직
  - IP/Device fingerprint 저장
  - 파일: `backend/app/services/anti_collusion.py`

- [ ] B1.2 칩 밀어주기 패턴 모니터링
  - 의심 패턴 정의 (연속 폴드, 비정상 베팅)
  - 실시간 모니터링 서비스
  - 파일: `backend/app/services/chip_dumping_detector.py`

- [ ] B1.3 의심 행위 자동 플래깅
  - SuspiciousActivity 모델
  - 자동 알림 시스템
  - 파일: `backend/app/models/suspicious.py`

### B2. 봇 탐지 시스템 (Week 4)

- [ ] B2.1 행동 패턴 분석
  - 응답 시간 분석
  - 액션 패턴 분석
  - 파일: `backend/app/services/bot_detector.py`

- [ ] B2.2 이상 탐지 알고리즘
  - 통계 기반 이상 탐지
  - 머신러닝 모델 연동 (선택)
  - 파일: `backend/app/services/anomaly_detector.py`

- [ ] B2.3 자동 제재 연동
  - 봇 의심 시 자동 플래깅
  - 관리자 알림
  - 파일: `backend/app/services/auto_ban.py`

### B3. 클라이언트 보안 (Week 4)

- [ ] B3.1 패킷 암호화
  - WebSocket 메시지 암호화
  - 키 교환 프로토콜
  - 파일: `backend/app/ws/encryption.py`

- [ ] B3.2 요청 서명 검증
  - HMAC 서명 검증
  - 타임스탬프 검증
  - 파일: `backend/app/middleware/signature.py`

---

## Part C: 백엔드 기능 확장

### C1. 사용자 관리 확장 (Week 5)

- [ ] C1.1 소셜 로그인 연동
  - Google OAuth 2.0
  - Kakao 로그인
  - 파일: `backend/app/services/social_auth.py`

- [ ] C1.2 성인 인증 / KYC 모듈
  - 본인 인증 API 연동
  - KYC 상태 관리
  - 파일: `backend/app/services/kyc.py`

- [ ] C1.3 아바타 설정 기능
  - 아바타 이미지 업로드
  - S3 연동
  - 파일: `backend/app/services/avatar.py`

- [ ] C1.4 통계 지표 (VPIP, PFR 등)
  - 플레이어 통계 계산
  - 통계 API
  - 파일: `backend/app/services/player_stats.py`

### C2. 인게임 기능 확장 (Week 6)

- [ ] C2.1 플레이어 전용 채팅 구분
  - 채팅 타입 분리
  - 권한 검증
  - 파일: `backend/app/ws/handlers/chat.py`

- [ ] C2.2 이모티콘 시스템
  - 이모티콘 모델
  - 이모티콘 전송 핸들러
  - 파일: `backend/app/ws/handlers/emoticon.py`

- [ ] C2.3 선물하기 기능
  - 선물 모델
  - 선물 전송 로직
  - 파일: `backend/app/services/gift.py`

- [ ] C2.4 핸드 리플레이 기능
  - 핸드 히스토리 조회
  - 리플레이 데이터 생성
  - 파일: `backend/app/services/hand_replay.py`

### C3. 네트워킹 최적화 (Week 6)

- [ ] C3.1 관전자/플레이어 그룹 분리 전송
  - 그룹별 브로드캐스트
  - 메시지 필터링
  - 파일: `backend/app/ws/manager.py`

- [ ] C3.2 중간 입장 시 테이블 동기화
  - Snapshot 생성
  - 상태 복구 로직
  - 파일: `backend/app/ws/handlers/sync.py`

### C4. 데이터베이스 확장 (Week 7)

- [ ] C4.1 핸드 히스토리 로그 (MongoDB)
  - MongoDB 연동
  - 핸드 로그 저장
  - 파일: `backend/app/services/hand_logger.py`

- [ ] C4.2 부정 행위 분석용 상세 로그
  - 상세 액션 로그
  - 분석 쿼리 최적화
  - 파일: `backend/app/services/detailed_logger.py`

---

## 체크포인트

### Week 1 완료 조건
- [ ] 대시보드 메트릭 API 완성
- [ ] 대시보드 UI 렌더링 확인
- [ ] CCU/DAU 차트 실시간 갱신 확인

### Week 2 완료 조건
- [ ] 사용자 검색/필터링 동작 확인
- [ ] 사용자 상세 페이지 모든 탭 로딩 확인

### Week 3 완료 조건
- [ ] 제재 생성/해제 전체 플로우 테스트
- [ ] 감사 로그 기록 확인
- [ ] 메인 시스템 연동 확인

### Week 4 완료 조건
- [ ] 부정 행위 탐지 시스템 동작 확인
- [ ] 봇 탐지 알고리즘 테스트
- [ ] 패킷 암호화 적용 확인

### Week 5-6 완료 조건
- [ ] 환율 API 정상 동작 확인
- [ ] TRON 테스트넷 연동 확인
- [ ] 암호화폐 데이터 모델 마이그레이션 확인

### Week 7-8 완료 조건
- [ ] 입금 감지 → 확정 → 잔액 반영 전체 플로우 테스트
- [ ] 출금 요청 → 승인 → 전송 → 완료 전체 플로우 테스트
- [ ] HSM 서명 보안 검증

### Week 9 완료 조건
- [ ] 모든 추가 기능 통합 테스트
- [ ] E2E 테스트 실행

### Week 10 완료 조건
- [ ] 모든 테스트 통과
- [ ] 보안 감사 완료
- [ ] 문서화 완료

---

## 참고사항

- 각 태스크는 독립적으로 진행 가능하나, 의존성이 있는 경우 순서를 지켜야 함
- 암호화폐 관련 기능은 반드시 테스트넷에서 먼저 검증
- HSM/KMS 연동은 보안팀과 협업하여 진행
- Property-Based 테스트는 선택적으로 진행 (기존 admin-dashboard/tasks.md 참조)
