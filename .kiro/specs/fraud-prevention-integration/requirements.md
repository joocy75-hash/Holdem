# 요구사항 문서

## 소개

본 문서는 부정 행위 탐지 시스템과 게임 서버 간의 통합을 정의합니다. admin-backend에 이미 구현되어 테스트 완료된 부정 행위 탐지 서비스들(ChipDumpingDetector, BotDetector, AnomalyDetector, AutoBanService)을 실제 게임 서버와 연동하여 실시간 부정 행위 탐지 및 자동 제재 시스템을 구축합니다.

### 배경

- **Phase 1 완료**: admin-backend에 부정 행위 탐지 서비스 구현 완료
  - ChipDumpingDetector: 11개 테스트 통과
  - BotDetector: 8개 테스트 통과
  - AnomalyDetector: 8개 테스트 통과
  - AutoBanService: 8개 테스트 통과
- **현재 문제**: 이 서비스들이 실제 게임 서버와 연결되어 있지 않음
- **목표**: Redis Pub/Sub을 통해 게임 서버 이벤트를 admin-backend로 전달하여 실시간 분석 수행

## 용어집

- **Game_Server**: 포커 게임 로직을 처리하는 메인 백엔드 서버 (backend/)
- **Admin_Backend**: 관리자 기능과 부정 행위 탐지를 담당하는 서버 (admin-backend/)
- **Fraud_Event_Consumer**: Redis Pub/Sub 채널을 구독하여 게임 이벤트를 수신하는 서비스
- **Hand_History**: 완료된 핸드의 상세 정보를 저장하는 데이터베이스 모델
- **Redis_Pub_Sub**: 게임 서버와 admin-backend 간 이벤트 전달을 위한 메시징 시스템
- **Chip_Dumping**: 한 플레이어가 의도적으로 다른 플레이어에게 칩을 잃어주는 부정 행위
- **Bot_Detection**: 자동화된 프로그램(봇)을 사용한 플레이 탐지
- **Anomaly_Detection**: 통계적으로 비정상적인 플레이 패턴 탐지
- **Auto_Ban_Service**: 탐지 결과에 따라 자동으로 제재를 적용하는 서비스

## 요구사항

### 요구사항 1: 핸드 완료 이벤트 발행

**사용자 스토리:** 시스템 관리자로서, 모든 완료된 핸드 정보를 분석할 수 있도록 게임 서버가 핸드 완료 이벤트를 발행하기를 원합니다.

#### 수락 기준

1. WHEN 핸드가 완료되면 THE Game_Server SHALL `fraud:hand_completed` Redis 채널로 핸드 결과 이벤트를 발행한다
2. THE 핸드 완료 이벤트 SHALL 다음 정보를 포함한다: hand_id, room_id, 참가자 목록(user_id, cards, bet_amount, won_amount), pot_size, community_cards, timestamp
3. IF Redis 연결이 실패하면 THEN THE Game_Server SHALL 에러를 로깅하고 게임 진행에는 영향을 주지 않는다
4. THE Game_Server SHALL 이벤트 발행을 비동기로 처리하여 게임 응답 시간에 영향을 주지 않는다

### 요구사항 2: 플레이어 액션 타이밍 이벤트 발행

**사용자 스토리:** 시스템 관리자로서, 봇 탐지를 위해 플레이어의 액션 타이밍 데이터를 수집하기를 원합니다.

#### 수락 기준

1. WHEN 플레이어가 액션을 수행하면 THE Game_Server SHALL `fraud:player_action` Redis 채널로 액션 이벤트를 발행한다
2. THE 액션 이벤트 SHALL 다음 정보를 포함한다: user_id, room_id, action_type, amount, response_time_ms, timestamp
3. THE Game_Server SHALL 응답 시간을 턴 시작 시점부터 액션 수신 시점까지의 밀리초 단위로 측정한다
4. IF 봇 플레이어의 액션이면 THEN THE Game_Server SHALL 해당 이벤트를 발행하지 않는다

### 요구사항 3: 플레이어 통계 이벤트 발행

**사용자 스토리:** 시스템 관리자로서, 이상 탐지를 위해 플레이어의 세션 통계를 주기적으로 수집하기를 원합니다.

#### 수락 기준

1. WHEN 플레이어가 테이블을 떠나면 THE Game_Server SHALL `fraud:player_stats` Redis 채널로 세션 통계 이벤트를 발행한다
2. THE 세션 통계 이벤트 SHALL 다음 정보를 포함한다: user_id, room_id, session_duration_seconds, hands_played, total_bet, total_won, join_time, leave_time
3. THE Game_Server SHALL 세션 중 플레이한 핸드 수와 베팅/승리 금액을 정확히 집계한다

### 요구사항 4: 부정 행위 이벤트 소비자 서비스

**사용자 스토리:** 시스템 관리자로서, 게임 서버에서 발행한 이벤트를 실시간으로 수신하여 부정 행위 분석을 수행하기를 원합니다.

#### 수락 기준

1. THE Fraud_Event_Consumer SHALL 서버 시작 시 `fraud:hand_completed`, `fraud:player_action`, `fraud:player_stats` 채널을 구독한다
2. WHEN `fraud:hand_completed` 이벤트를 수신하면 THE Fraud_Event_Consumer SHALL ChipDumpingDetector를 호출하여 칩 밀어주기 패턴을 분석한다
3. WHEN `fraud:player_action` 이벤트를 수신하면 THE Fraud_Event_Consumer SHALL BotDetector를 호출하여 봇 행동 패턴을 분석한다
4. WHEN `fraud:player_stats` 이벤트를 수신하면 THE Fraud_Event_Consumer SHALL AnomalyDetector를 호출하여 이상 패턴을 분석한다
5. IF 분석 결과 의심 활동이 탐지되면 THEN THE Fraud_Event_Consumer SHALL AutoBanService를 호출하여 자동 제재 평가를 수행한다

### 요구사항 5: 핸드 히스토리 데이터베이스 저장

**사용자 스토리:** 시스템 관리자로서, 완료된 핸드를 데이터베이스에 저장하여 나중에 리플레이하고 부정 행위를 분석할 수 있기를 원합니다.

#### 수락 기준

1. THE Hand_History 모델 SHALL 다음 필드를 포함한다: id, room_id, hand_number, pot_size, community_cards, winner_ids, created_at
2. THE Hand_Participant 모델 SHALL 다음 필드를 포함한다: id, hand_id, user_id, seat, hole_cards, bet_amount, won_amount, final_action
3. WHEN 핸드가 완료되면 THE Game_Server SHALL Hand_History와 Hand_Participant 레코드를 PostgreSQL에 저장한다
4. THE Hand_History_Service SHALL 특정 사용자의 핸드 히스토리를 조회하는 API를 제공한다
5. THE Hand_History_Service SHALL 특정 핸드의 상세 정보(리플레이용)를 조회하는 API를 제공한다

### 요구사항 6: 자동 제재 시스템 통합

**사용자 스토리:** 시스템 관리자로서, 부정 행위가 탐지되면 자동으로 제재가 적용되고 알림을 받기를 원합니다.

#### 수락 기준

1. WHEN 부정 행위 탐지 점수가 임계값을 초과하면 THE Auto_Ban_Service SHALL 해당 사용자를 자동으로 플래깅한다
2. THE Auto_Ban_Service SHALL 심각도에 따라 다른 조치를 취한다: low(모니터링), medium(경고), high(임시 제재)
3. WHEN 자동 제재가 적용되면 THE Admin_Backend SHALL 관리자에게 알림을 전송한다
4. THE Auto_Ban_Service SHALL 모든 자동 제재 결정을 감사 로그에 기록한다
5. WHERE 자동 제재 임계값이 설정 가능하면 THE Admin_Backend SHALL 환경 변수를 통해 임계값을 조정할 수 있다

### 요구사항 7: 실시간 모니터링 대시보드 연동

**사용자 스토리:** 시스템 관리자로서, 부정 행위 탐지 현황을 실시간으로 모니터링하기를 원합니다.

#### 수락 기준

1. THE Admin_Backend SHALL 최근 탐지된 의심 활동 목록을 조회하는 API를 제공한다
2. THE Admin_Backend SHALL 탐지 유형별 통계(칩 밀어주기, 봇, 이상 행동)를 조회하는 API를 제공한다
3. WHEN 새로운 의심 활동이 탐지되면 THE Admin_Backend SHALL WebSocket을 통해 실시간 알림을 전송한다
4. THE Admin_Backend SHALL 의심 활동의 상태(pending, reviewed, dismissed, banned)를 관리하는 API를 제공한다
