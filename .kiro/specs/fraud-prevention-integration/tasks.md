# 구현 계획: 부정 행위 탐지 시스템 통합

## 개요

이 문서는 admin-backend의 부정 행위 탐지 서비스들을 게임 서버와 통합하는 구현 태스크를 정의합니다. Redis Pub/Sub을 통해 게임 이벤트를 실시간으로 전달하고 분석합니다.

## 태스크

- [x] 1. Game Server - FraudEventPublisher 구현
  - [x] 1.1 FraudEventPublisher 서비스 생성
    - `backend/app/services/fraud_event_publisher.py` 생성
    - Redis Pub/Sub 발행 로직 구현
    - 이벤트 스키마 정의 (Pydantic 모델)
    - _Requirements: 1.1, 1.2, 1.3, 1.4_
  
  - [x] 1.2 FraudEventPublisher 단위 테스트 작성
    - **Property 1: 핸드 완료 이벤트 발행 및 스키마 검증**
    - **Property 2: 플레이어 액션 이벤트 발행 및 스키마 검증**
    - **Validates: Requirements 1.1, 1.2, 2.1, 2.2**

- [x] 2. Game Server - ActionHandler 통합
  - [x] 2.1 ActionHandler에 이벤트 발행 추가
    - `backend/app/ws/handlers/action.py` 수정
    - 핸드 완료 시 `fraud:hand_completed` 이벤트 발행
    - 플레이어 액션 시 `fraud:player_action` 이벤트 발행
    - 응답 시간 측정 로직 추가
    - _Requirements: 1.1, 2.1, 2.3_
  
  - [x] 2.2 봇 플레이어 이벤트 필터링 테스트
    - **Property 3: 봇 플레이어 액션 이벤트 미발행**
    - **Validates: Requirements 2.4**

- [x] 3. Game Server - 플레이어 세션 통계 추적
  - [x] 3.1 플레이어 세션 통계 추적 구현
    - 테이블 입장/퇴장 시 통계 수집
    - 핸드별 베팅/승리 금액 집계
    - 퇴장 시 `fraud:player_stats` 이벤트 발행
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [x] 3.2 세션 통계 정확성 테스트
    - **Property 4: 플레이어 통계 이벤트 발행 및 스키마 검증**
    - **Property 5: 세션 통계 정확성**
    - **Validates: Requirements 3.1, 3.2, 3.3**

- [x] 4. 체크포인트 - Game Server 이벤트 발행 검증
  - 모든 테스트 통과 확인
  - 서버 실행 확인
  - 질문이 있으면 사용자에게 문의


- [x] 5. Admin Backend - FraudEventConsumer 구현
  - [x] 5.1 FraudEventConsumer 서비스 생성
    - `admin-backend/app/services/fraud_event_consumer.py` 생성
    - Redis Pub/Sub 구독 로직 구현
    - 이벤트 유형별 핸들러 구현
    - 기존 탐지 서비스 연동 (ChipDumpingDetector, BotDetector, AnomalyDetector)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [x] 5.2 FraudEventConsumer 단위 테스트 작성
    - **Property 6: 이벤트 유형별 탐지기 호출**
    - **Property 7: 의심 활동 탐지 시 자동 제재 평가**
    - **Validates: Requirements 4.2, 4.3, 4.4, 4.5**

- [x] 6. Admin Backend - 서버 시작 시 Consumer 연동
  - [x] 6.1 main.py에 FraudEventConsumer 시작 로직 추가
    - `admin-backend/app/main.py` 수정
    - 서버 시작 시 Consumer 백그라운드 태스크 시작
    - 서버 종료 시 Consumer 정리
    - _Requirements: 4.1_
  
  - [x] 6.2 Consumer 시작/종료 테스트
    - 서버 시작 시 채널 구독 확인
    - **Validates: Requirements 4.1**

- [x] 7. 체크포인트 - Admin Backend 이벤트 소비 검증
  - 모든 테스트 통과 확인
  - 서버 실행 확인
  - 질문이 있으면 사용자에게 문의

- [x] 8. Game Server - HandParticipant 모델 및 저장
  - [x] 8.1 HandParticipant 모델 추가
    - `backend/app/models/hand.py` 수정
    - HandParticipant 모델 정의
    - Hand 모델과 관계 설정
    - _Requirements: 5.1, 5.2_
  
  - [x] 8.2 Alembic 마이그레이션 생성
    - `backend/alembic/versions/xxx_add_hand_participants.py` 생성
    - hand_participants 테이블 생성
    - _Requirements: 5.1, 5.2_
  
  - [x] 8.3 HandHistoryService 구현
    - `backend/app/services/hand_history.py` 생성
    - 핸드 완료 시 DB 저장 로직
    - 사용자별 핸드 히스토리 조회
    - 핸드 상세 정보 조회 (리플레이용)
    - _Requirements: 5.3, 5.4, 5.5_
  
  - [x] 8.4 HandHistoryService 테스트
    - **Property 8: 핸드 히스토리 저장**
    - **Validates: Requirements 5.3**

- [x] 9. 체크포인트 - 핸드 히스토리 저장 검증
  - 마이그레이션 적용 확인
  - 모든 테스트 통과 확인
  - 질문이 있으면 사용자에게 문의


- [x] 10. Admin Backend - 자동 제재 시스템 강화
  - [x] 10.1 AutoBanService 감사 로그 연동
    - `admin-backend/app/services/auto_ban.py` 수정
    - 모든 자동 제재 결정을 감사 로그에 기록
    - 심각도별 조치 로직 명확화
    - _Requirements: 6.1, 6.2, 6.4_
  
  - [x] 10.2 자동 제재 로직 테스트
    - **Property 9: 탐지 점수 기반 자동 조치**
    - **Property 10: 자동 제재 감사 로그**
    - **Validates: Requirements 6.1, 6.2, 6.4**
  
  - [x] 10.3 관리자 알림 연동
    - 자동 제재 시 관리자 알림 전송
    - 기존 notify_admins 메서드 활용
    - _Requirements: 6.3_
  
  - [x] 10.4 관리자 알림 테스트
    - **Property 11: 자동 제재 시 관리자 알림**
    - **Validates: Requirements 6.3**

- [x] 11. Admin Backend - 모니터링 API 구현
  - [x] 11.1 부정 행위 모니터링 API 생성
    - `admin-backend/app/api/fraud.py` 생성
    - GET /api/fraud/suspicious - 의심 활동 목록 조회
    - GET /api/fraud/statistics - 탐지 유형별 통계
    - PATCH /api/fraud/suspicious/{id} - 상태 업데이트
    - _Requirements: 7.1, 7.2, 7.4_
  
  - [x] 11.2 모니터링 API 테스트
    - API 엔드포인트 통합 테스트
    - **Validates: Requirements 7.1, 7.2, 7.4**

- [x] 12. 체크포인트 - 자동 제재 및 모니터링 검증
  - 모든 테스트 통과 확인
  - 서버 실행 확인
  - 질문이 있으면 사용자에게 문의

- [x] 13. 통합 테스트 및 문서화
  - [x] 13.1 전체 파이프라인 통합 테스트
    - 게임 액션 → Redis 이벤트 → 탐지 → 제재 흐름 테스트
    - 실제 Redis 연동 테스트
    - _Requirements: 전체_
  
  - [x] 13.2 WORK_PROGRESS.md 생성
    - `.kiro/specs/fraud-prevention-integration/WORK_PROGRESS.md` 생성
    - 작업 진행 현황 추적 문서

- [x] 14. 최종 체크포인트 - 전체 시스템 검증
  - 모든 단위 테스트 통과
  - 통합 테스트 통과
  - backend 서버 실행 확인
  - admin-backend 서버 실행 확인
  - 질문이 있으면 사용자에게 문의

## 참고 사항

- 모든 테스트 태스크는 필수입니다
- 각 체크포인트에서 테스트 통과 및 서버 실행을 확인합니다
- 기존 탐지 서비스(ChipDumpingDetector, BotDetector, AnomalyDetector, AutoBanService)는 이미 구현 및 테스트 완료 상태입니다
