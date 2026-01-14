# Requirements Document

## Introduction

홀덤 게임 프론트엔드의 애니메이션 시스템을 Framer Motion 라이브러리로 마이그레이션하고, 5가지 핵심 몰입감 기능을 구현한다. 현재 순수 CSS/JS로 구현된 복잡한 애니메이션 로직을 선언적 API로 교체하여 코드 품질과 사용자 경험을 동시에 개선한다.

### 5가지 핵심 몰입감 기능
1. **카드 쪼기 연출 (The Squeeze/Peek)** - 물리적 저항감과 원근감
2. **베팅 시 칩 이동 및 숫자 상승** - 경쾌한 리듬감
3. **승자 결정 시 팟(Pot) 이동** - 획득의 쾌감 시각화
4. **승자 하이라이트 및 배경 흑백 처리** - 무대 연출
5. **폴드 시 카드 오픈 선택 (Show or Muck)** - 심리전의 여지

## Glossary

- **Framer_Motion**: React용 선언적 애니메이션 라이브러리 (번들 ~40KB gzipped)
- **Motion_Component**: Framer Motion의 `motion.div` 등 애니메이션 가능한 컴포넌트
- **AnimatePresence**: 컴포넌트 마운트/언마운트 시 애니메이션을 처리하는 래퍼
- **useMotionValue**: 애니메이션 값을 추적하는 Framer Motion 훅
- **Drag_Gesture**: 드래그 인터랙션을 처리하는 Framer Motion 기능
- **CardSqueeze**: 카드 쪼기 컴포넌트 (드래그로 카드 공개)
- **ActionButtons**: 폴드/체크/콜/레이즈 액션 버튼 컴포넌트
- **BuyInModal**: 바이인 금액 설정 모달 컴포넌트
- **ChipAnimation**: 칩 이동 애니메이션 컴포넌트
- **PotCollection**: 팟 수거 및 승자 이동 컴포넌트
- **WinnerHighlight**: 승자 하이라이트 및 배경 처리 컴포넌트
- **FoldOptions**: 폴드 시 Show/Muck 선택 컴포넌트
- **Staggered_Motion**: 시간차를 두고 순차적으로 실행되는 애니메이션
- **Ease_In**: 처음 느리게 시작해서 점점 빨라지는 가속 곡선
- **Spring_Physics**: 스프링 물리 기반의 자연스러운 반동 효과

## Requirements

### Requirement 1: Framer Motion 라이브러리 설치 및 환경 구성

**User Story:** As a developer, I want to install Framer Motion and configure it for Next.js 16 + React 19, so that I can use modern animation APIs throughout the project.

#### Acceptance Criteria

1. WHEN `npm install framer-motion` is executed, THE System SHALL install the latest compatible version
2. WHEN the application builds, THE System SHALL compile without errors related to Framer Motion
3. WHEN importing from 'framer-motion', THE System SHALL resolve the module correctly in all components
4. THE System SHALL maintain existing functionality without regression after installation

---

### Requirement 2: 카드 쪼기 연출 (The Squeeze/Peek)

**User Story:** As a player, I want to squeeze my cards with realistic physics, so that I feel the tension and excitement of revealing my hand.

#### Acceptance Criteria

1. WHEN a user drags a card corner upward, THE CardSqueeze_Component SHALL bend the card in 3D space with the top edge fixed
2. WHEN dragging, THE System SHALL show dynamic shadow that becomes softer and wider as the card lifts
3. WHEN dragging, THE System SHALL apply subtle gradient reflection on the card surface to emphasize bending
4. WHEN drag distance is below threshold and released, THE CardSqueeze_Component SHALL snap back with "찰싹" spring physics
5. WHEN drag distance exceeds threshold, THE CardSqueeze_Component SHALL flip the card with "휙" spring animation
6. WHEN a card is being squeezed, THE System SHALL lock other UI interactions
7. THE CardSqueeze_Component SHALL maintain all existing data-testid attributes for E2E tests

---

### Requirement 3: 베팅 시 칩 이동 및 숫자 상승

**User Story:** As a player, I want to see chips fly to the pot with rhythm, so that I feel the impact of my betting action.

#### Acceptance Criteria

1. WHEN a player bets, THE ChipAnimation_Component SHALL animate multiple chip icons with 0.05s staggered delay
2. WHEN chips fly, THE System SHALL use curved bezier path instead of straight line
3. WHEN the first chip reaches center, THE System SHALL display floating bet amount (e.g., +10,000)
4. WHEN displaying bet amount, THE System SHALL animate it floating upward while fading out
5. WHEN chips land, THE System SHALL trigger "찰랑" sound effect synchronization point
6. THE ChipAnimation_Component SHALL support configurable chip count based on bet amount

---

### Requirement 4: 승자 결정 시 팟(Pot) 이동

**User Story:** As a winner, I want to see the pot dramatically fly to me, so that I feel the satisfaction of winning.

#### Acceptance Criteria

1. WHEN winner is determined, THE PotCollection_Component SHALL first gather all scattered chips to center
2. WHEN chips are gathered, THE System SHALL animate the chip pile toward the winner's seat
3. WHEN moving to winner, THE System SHALL use Ease-In acceleration (slow start, fast finish)
4. WHEN chips reach winner, THE System SHALL trigger pulse effect on winner's avatar
5. THE PotCollection_Component SHALL handle multiple winners (split pot) with divided animations
6. THE PotCollection_Component SHALL complete entire sequence within 2 seconds

---

### Requirement 5: 승자 하이라이트 및 배경 흑백 처리

**User Story:** As a player, I want the winner to be dramatically highlighted, so that the victory moment feels cinematic.

#### Acceptance Criteria

1. WHEN winner is announced, THE WinnerHighlight_Component SHALL apply grayscale filter to all non-winner areas
2. WHEN winner is announced, THE System SHALL darken non-winner player areas
3. WHEN winner is highlighted, THE System SHALL brighten winner's profile above normal
4. WHEN winner is highlighted, THE System SHALL add golden glow border effect around winner
5. WHEN showdown ends, THE System SHALL gradually restore normal colors within 3 seconds
6. THE WinnerHighlight_Component SHALL support multiple winners with equal highlighting

---

### Requirement 6: 폴드 시 카드 오픈 선택 (Show or Muck)

**User Story:** As a player, I want to choose whether to show my folded cards, so that I can use it as a psychological tactic.

#### Acceptance Criteria

1. WHEN fold button is pressed, THE FoldOptions_Component SHALL display overlay buttons on cards
2. THE FoldOptions_Component SHALL provide options: "카드 1 오픈", "카드 2 오픈", "모두 오픈", "그냥 버리기"
3. WHEN "그냥 버리기" is selected, THE System SHALL slide cards face-down to dealer while fading
4. WHEN "오픈" is selected, THE System SHALL flip selected card(s) dramatically and hold for 1-2 seconds
5. WHEN showing cards, THE System SHALL broadcast revealed cards to all players
6. THE FoldOptions_Component SHALL show 3-second countdown timer
7. WHEN timer expires, THE System SHALL auto-execute "그냥 버리기"
8. THE FoldOptions_Component SHALL maintain all data-testid attributes for E2E tests

---

### Requirement 7: ActionButtons 컴포넌트 애니메이션 개선

**User Story:** As a player, I want tactile feedback on action buttons, so that I feel confident my actions are registered.

#### Acceptance Criteria

1. WHEN hovering over an action button, THE ActionButtons_Component SHALL scale up slightly (1.05x) with smooth transition
2. WHEN pressing an action button, THE ActionButtons_Component SHALL scale down (0.95x) for tactile feedback
3. WHEN action buttons appear, THE ActionButtons_Component SHALL animate in with staggered fade effect
4. WHEN action buttons disappear, THE ActionButtons_Component SHALL animate out smoothly
5. THE ActionButtons_Component SHALL maintain all existing click handlers and functionality
6. THE ActionButtons_Component SHALL maintain all existing data-testid attributes for E2E tests

---

### Requirement 8: BuyInModal 컴포넌트 애니메이션 개선

**User Story:** As a player, I want smooth modal transitions, so that the UI feels polished and professional.

#### Acceptance Criteria

1. WHEN the modal opens, THE BuyInModal_Component SHALL animate in from bottom with spring physics
2. WHEN the modal closes, THE BuyInModal_Component SHALL animate out to bottom smoothly
3. WHEN the modal backdrop appears, THE System SHALL fade in with blur effect
4. WHEN the modal backdrop disappears, THE System SHALL fade out smoothly
5. THE BuyInModal_Component SHALL use AnimatePresence for mount/unmount animations
6. THE BuyInModal_Component SHALL maintain all existing form functionality

---

### Requirement 9: 공통 애니메이션 유틸리티 생성

**User Story:** As a developer, I want reusable animation presets, so that I can maintain consistency across components.

#### Acceptance Criteria

1. THE System SHALL provide a `fadeIn` animation variant for component entrance
2. THE System SHALL provide a `fadeOut` animation variant for component exit
3. THE System SHALL provide a `scaleIn` animation variant for popup elements
4. THE System SHALL provide a `slideUp` animation variant for bottom sheets
5. THE System SHALL provide a `spring` transition preset for natural motion
6. THE System SHALL provide a `staggeredChildren` preset for sequential animations
7. THE System SHALL provide a `curvedPath` utility for bezier curve chip movements
8. WHEN using animation utilities, THE System SHALL apply consistent timing across all components

---

### Requirement 10: 기존 E2E 테스트 호환성 유지

**User Story:** As a QA engineer, I want all existing E2E tests to pass after migration, so that we maintain quality assurance.

#### Acceptance Criteria

1. WHEN running card-squeeze E2E tests, THE System SHALL pass all existing test cases
2. WHEN running betting-buttons E2E tests, THE System SHALL pass all existing test cases
3. WHEN running modal-related E2E tests, THE System SHALL pass all existing test cases
4. WHEN running showdown E2E tests, THE System SHALL pass all existing test cases
5. THE System SHALL maintain all data-testid attributes unchanged
6. THE System SHALL maintain all data-* attributes for test assertions
