# Requirements Document

## Introduction

상용급 온라인 포커 게임의 E2E(End-to-End) 테스트 시스템을 구축합니다. Playwright를 활용하여 인증, 로비, 테이블 입장, 멀티플레이어 베팅 상호작용, 사이드 팟, 재접속 복구, 보안 감사까지 전체 게임 플로우를 자동화 테스트합니다.

## Glossary

- **E2E_Test_System**: Playwright 기반의 End-to-End 테스트 프레임워크
- **Browser_Context**: Playwright에서 독립된 브라우저 세션을 나타내는 단위
- **Player_Session**: 개별 플레이어의 브라우저 컨텍스트와 인증 상태를 포함하는 테스트 세션
- **Table_Page**: 실제 포커 게임이 진행되는 테이블 UI 페이지
- **Lobby_Page**: 테이블 목록을 보여주고 입장할 수 있는 로비 페이지
- **Login_Page**: 사용자 인증을 처리하는 로그인/회원가입 페이지
- **Action_Button**: 폴드, 체크, 콜, 레이즈, 올인 등 게임 액션 버튼
- **Community_Cards**: 테이블 중앙에 공개되는 공용 카드 (플랍, 턴, 리버)
- **Hole_Cards**: 각 플레이어에게 비공개로 배분되는 2장의 카드
- **Pot**: 현재 핸드에서 베팅된 총 금액
- **Main_Pot**: 모든 플레이어가 참여 가능한 기본 팟
- **Side_Pot**: 올인 플레이어 초과 베팅분으로 형성되는 별도 팟
- **Buy_In_Modal**: 테이블 입장 시 바이인 금액을 설정하는 모달
- **Cheat_API**: 테스트 효율화를 위한 관리자 전용 API (덱 주입, 타이머 제어)
- **Server_Authority**: 모든 게임 로직 판정은 서버에서 수행하는 원칙
- **Idempotency**: 동일 요청의 중복 처리 방지 메커니즘
- **Squeeze_Animation**: 모바일에서 카드를 위로 밀어 확인하는 카드 쪼기 애니메이션
- **Hand_Ranking_Guide**: 현재 족보와 가능한 족보를 실시간으로 보여주는 UI
- **Pot_Ratio_Button**: 팟의 일정 비율(1/4, 1/2, 3/4, 전체)로 베팅하는 편의 버튼
- **Winner_Highlight**: 승리 족보에 사용된 5장 카드만 강조하는 시각 효과

## Requirements

### Requirement 1: 인증 플로우 테스트

**User Story:** As a QA engineer, I want to test the authentication flow, so that I can verify users can login and signup correctly.

#### Acceptance Criteria

1. WHEN a user visits the login page THEN THE Login_Page SHALL display email and password input fields
2. WHEN a user enters valid credentials and submits THEN THE E2E_Test_System SHALL verify successful redirect to lobby
3. WHEN a user enters invalid credentials THEN THE Login_Page SHALL display an error message
4. WHEN a user clicks signup toggle THEN THE Login_Page SHALL display nickname and password confirmation fields
5. WHEN a new user completes signup with valid data THEN THE E2E_Test_System SHALL verify account creation and auto-login
6. WHEN a user's token expires THEN THE E2E_Test_System SHALL verify re-authentication flow is triggered
7. WHEN a user logs in from a second device THEN THE E2E_Test_System SHALL verify the first session is terminated

### Requirement 2: 로비 네비게이션 테스트

**User Story:** As a QA engineer, I want to test lobby navigation, so that I can verify users can browse and select tables.

#### Acceptance Criteria

1. WHEN an authenticated user visits the lobby THEN THE Lobby_Page SHALL display available tables list
2. WHEN a user clicks on a table card THEN THE E2E_Test_System SHALL verify navigation to the table page
3. WHEN a user has an active session at a table THEN THE Lobby_Page SHALL display a "계속하기" (continue) banner
4. WHEN a user clicks game tabs (전체/홀덤/토너먼트) THEN THE Lobby_Page SHALL filter displayed content accordingly
5. WHEN a user clicks logout THEN THE E2E_Test_System SHALL verify redirect to login page

### Requirement 3: 테이블 입장 및 바이인 테스트

**User Story:** As a QA engineer, I want to test table joining flow, so that I can verify players can enter tables with proper buy-in.

#### Acceptance Criteria

1. WHEN a player navigates to a table page THEN THE Table_Page SHALL display the poker table UI with seat positions
2. WHEN a player clicks an empty seat THEN THE Buy_In_Modal SHALL appear with min/max buy-in options
3. WHEN a player confirms buy-in within valid range THEN THE E2E_Test_System SHALL verify the player is seated with correct chip stack
4. WHEN a player has insufficient balance THEN THE Buy_In_Modal SHALL display an error message
5. WHEN a player is already seated THEN THE Table_Page SHALL display their hole cards when dealt
6. WHEN two players click the same seat simultaneously THEN THE Server SHALL accept only one player

### Requirement 4: 멀티플레이어 상호작용 테스트

**User Story:** As a QA engineer, I want to test multi-player interactions, so that I can verify betting actions are synchronized across players.

#### Acceptance Criteria

1. WHEN Player A performs a raise action THEN THE E2E_Test_System SHALL verify Player B's UI reflects the updated pot and current bet
2. WHEN it is a player's turn THEN THE Table_Page SHALL highlight the active player and display action buttons
3. WHEN a player folds THEN THE E2E_Test_System SHALL verify the player's cards are hidden and status shows "FOLD"
4. WHEN a player calls THEN THE E2E_Test_System SHALL verify chip deduction and pot increase
5. WHEN all players complete betting round THEN THE E2E_Test_System SHALL verify phase transition (preflop → flop → turn → river)

### Requirement 5: 게임 진행 및 카드 표시 테스트

**User Story:** As a QA engineer, I want to test game progression, so that I can verify cards are dealt and displayed correctly.

#### Acceptance Criteria

1. WHEN a hand starts THEN THE Table_Page SHALL display 2 hole cards to each active player
2. WHEN flop phase begins THEN THE Table_Page SHALL display 3 community cards
3. WHEN turn phase begins THEN THE Table_Page SHALL display 4 community cards
4. WHEN river phase begins THEN THE Table_Page SHALL display 5 community cards
5. WHEN showdown occurs THEN THE Table_Page SHALL reveal all remaining players' hole cards

### Requirement 6: 승패 판정 및 팟 분배 테스트

**User Story:** As a QA engineer, I want to test winner determination, so that I can verify correct hand evaluation and pot distribution.

#### Acceptance Criteria

1. WHEN showdown completes THEN THE E2E_Test_System SHALL verify the winner is correctly identified with "WIN" badge
2. WHEN a player wins THEN THE E2E_Test_System SHALL verify their chip stack increases by the pot amount
3. WHEN a hand ends THEN THE E2E_Test_System SHALL verify a new hand can start with updated chip stacks

### Requirement 7: 타이머 및 자동 폴드 테스트

**User Story:** As a QA engineer, I want to test turn timer functionality, so that I can verify automatic actions when time expires.

#### Acceptance Criteria

1. WHEN a player's turn begins THEN THE Table_Page SHALL display a countdown timer
2. WHEN the timer reaches zero THEN THE E2E_Test_System SHALL verify automatic fold action is triggered
3. WHEN a player acts before timeout THEN THE E2E_Test_System SHALL verify timer stops and turn passes
4. WHEN comparing server and client timers THEN THE E2E_Test_System SHALL verify synchronization within ±1 second

### Requirement 8: 테이블 퇴장 테스트

**User Story:** As a QA engineer, I want to test table leaving flow, so that I can verify players can exit cleanly.

#### Acceptance Criteria

1. WHEN a player clicks leave table button THEN THE E2E_Test_System SHALL verify redirect to lobby
2. WHEN a player leaves mid-hand THEN THE E2E_Test_System SHALL verify automatic fold and seat becomes empty
3. WHEN a player leaves THEN THE E2E_Test_System SHALL verify their remaining chips are returned to balance

### Requirement 9: 블라인드 및 버튼 이동 테스트

**User Story:** As a QA engineer, I want to test dealer button and blind positions, so that I can verify poker rules are correctly applied.

#### Acceptance Criteria

1. WHEN a hand ends THEN THE Table_Page SHALL move the dealer button clockwise
2. WHEN dealer button moves THEN THE Table_Page SHALL position SB and BB correctly relative to dealer
3. WHEN only 2 players remain (Heads-up) THEN THE Table_Page SHALL apply special rule: dealer=SB, opponent=BB
4. WHEN a player leaves mid-game THEN THE Table_Page SHALL skip their position for button movement

### Requirement 10: 사이드 팟 테스트

**User Story:** As a QA engineer, I want to test side pot creation and distribution, so that I can verify all-in scenarios are handled correctly.

#### Acceptance Criteria

1. WHEN a player goes all-in THEN THE E2E_Test_System SHALL verify main pot and side pot are correctly separated
2. WHEN multiple players go all-in with different amounts THEN THE E2E_Test_System SHALL verify multiple side pots are created
3. WHEN showdown occurs with side pots THEN THE E2E_Test_System SHALL verify each pot is awarded to the correct winner
4. WHEN pot cannot be evenly split (odd chip) THEN THE E2E_Test_System SHALL verify the extra chip goes to the player closest to dealer's left

### Requirement 11: 서버 권위 및 보안 테스트

**User Story:** As a QA engineer, I want to test server authority and security, so that I can verify the game is protected against cheating.

#### Acceptance Criteria

1. WHEN a player attempts action out of turn THEN THE Server SHALL reject the action
2. WHEN a folded player attempts to bet THEN THE Server SHALL reject the action
3. WHEN the same action_id is sent twice THEN THE Server SHALL process it only once (idempotency)
4. WHEN a spectator joins THEN THE E2E_Test_System SHALL verify opponent hole cards are NOT included in WebSocket messages

### Requirement 12: 재접속 및 복구 테스트

**User Story:** As a QA engineer, I want to test reconnection and recovery, so that I can verify game state is preserved after disconnection.

#### Acceptance Criteria

1. WHEN a player refreshes the browser mid-game THEN THE E2E_Test_System SHALL verify game state (cards, pot, phase) is restored
2. WHEN network disconnects and reconnects THEN THE E2E_Test_System SHALL verify WebSocket reconnection and state sync
3. WHEN messages arrive out of order THEN THE E2E_Test_System SHALL verify client renders correct final state using sequence numbers
4. WHEN server restarts mid-hand THEN THE E2E_Test_System SHALL verify hand is recovered from snapshot (pot, timer, cards)

### Requirement 13: 부하 테스트

**User Story:** As a QA engineer, I want to test system under load, so that I can verify stability with multiple concurrent tables.

#### Acceptance Criteria

1. WHEN 10 tables run simultaneously THEN THE E2E_Test_System SHALL verify no event loss
2. WHEN 100+ tables run simultaneously THEN THE E2E_Test_System SHALL measure and verify acceptable response times
3. WHEN many WebSocket connections are active THEN THE E2E_Test_System SHALL verify connection stability

### Requirement 14: 족보 안내 및 승률 계산 UI 테스트 (피망 스타일)

**User Story:** As a QA engineer, I want to test hand ranking guide UI, so that I can verify real-time hand information is displayed correctly.

#### Acceptance Criteria

1. WHEN hole cards are dealt THEN THE Table_Page SHALL display current hand ranking in the guide UI
2. WHEN community cards are revealed THEN THE Table_Page SHALL update hand ranking guide to reflect new possibilities
3. WHEN hand ranking changes (e.g., pair to two pair) THEN THE Table_Page SHALL animate the ranking change
4. WHEN comparing guide UI data with actual cards THEN THE E2E_Test_System SHALL verify 100% accuracy

### Requirement 15: 베팅 버튼 편의성 테스트 (피망 스타일)

**User Story:** As a QA engineer, I want to test betting convenience buttons, so that I can verify pot-based calculations are accurate.

#### Acceptance Criteria

1. WHEN a player clicks "1/4 Pot" button THEN THE Table_Page SHALL calculate and display exactly 25% of current pot
2. WHEN a player clicks "1/2 Pot" button THEN THE Table_Page SHALL calculate and display exactly 50% of current pot
3. WHEN a player clicks "3/4 Pot" button THEN THE Table_Page SHALL calculate and display exactly 75% of current pot
4. WHEN a player clicks "Pot" button THEN THE Table_Page SHALL calculate and display exactly 100% of current pot
5. WHEN pot amount changes during betting round THEN THE Table_Page SHALL recalculate button amounts in real-time
6. WHEN calculated amount exceeds player's stack THEN THE Table_Page SHALL cap the amount to player's remaining chips

### Requirement 16: 쇼다운 하이라이트 테스트 (피망 스타일)

**User Story:** As a QA engineer, I want to test winner highlight effects, so that I can verify winning hand cards are correctly emphasized.

#### Acceptance Criteria

1. WHEN showdown completes THEN THE Table_Page SHALL highlight only the 5 cards that form the winning hand
2. WHEN winner is determined THEN THE Table_Page SHALL dim non-winning cards (both community and hole cards not used)
3. WHEN multiple winners exist (split pot) THEN THE Table_Page SHALL highlight each winner's winning hand separately
4. WHEN comparing highlighted cards with actual winning hand THEN THE E2E_Test_System SHALL verify 100% accuracy

### Requirement 17: 카드 쪼기(Squeeze) 애니메이션 테스트

**User Story:** As a QA engineer, I want to test card squeeze animation, so that I can verify the mobile-friendly card reveal interaction works correctly.

#### Acceptance Criteria

1. WHEN a player drags card upward THEN THE Table_Page SHALL reveal card proportionally to drag distance
2. WHEN drag distance exceeds threshold THEN THE Table_Page SHALL fully flip the card
3. WHEN player releases drag before threshold THEN THE Table_Page SHALL snap card back to face-down position
4. WHEN card is being squeezed THEN THE Table_Page SHALL show smooth transition between back and front
5. WHEN squeeze animation is in progress THEN THE Table_Page SHALL lock other UI interactions (betting buttons)
6. WHEN card reveal completes THEN THE Table_Page SHALL unlock UI interactions
7. WHEN testing at various drag angles THEN THE E2E_Test_System SHALL verify no graphical glitches or premature card exposure
