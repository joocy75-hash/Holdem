# UI 컴포넌트 명세

> 재사용 가능한 UI 컴포넌트 설계

---

## 1. 컴포넌트 계층

```
components/
├── common/           # 공통 컴포넌트
│   ├── Button
│   ├── Modal
│   ├── Toast
│   ├── Loading
│   ├── Avatar
│   └── Card
├── layout/           # 레이아웃 컴포넌트
│   ├── Header
│   ├── ConnectionBanner
│   └── Footer
├── lobby/            # 로비 컴포넌트
│   ├── RoomList
│   ├── RoomCard
│   ├── RoomFilter
│   └── CreateRoomModal
└── table/            # 테이블 컴포넌트
    ├── Table
    ├── Seat
    ├── CommunityCards
    ├── ActionPanel
    ├── PotDisplay
    ├── Timer
    └── Chat
```

---

## 2. 공통 컴포넌트

### 2.1 Button

```typescript
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'danger' | 'ghost';
  size: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  fullWidth?: boolean;
  onClick: () => void;
  children: React.ReactNode;
}
```

| Variant | 용도 | 색상 |
|---------|------|------|
| primary | 주요 액션 | 파란색 |
| secondary | 보조 액션 | 회색 |
| danger | 위험 액션 (Fold) | 빨간색 |
| ghost | 텍스트 버튼 | 투명 |

### 2.2 Modal

```typescript
interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  size?: 'sm' | 'md' | 'lg';
  closeOnOverlay?: boolean;
  children: React.ReactNode;
  footer?: React.ReactNode;
}
```

### 2.3 Toast

```typescript
interface ToastProps {
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;  // ms, default 3000
  action?: {
    label: string;
    onClick: () => void;
  };
}
```

### 2.4 Loading

```typescript
interface LoadingProps {
  type: 'spinner' | 'skeleton' | 'dots';
  size?: 'sm' | 'md' | 'lg';
  text?: string;
}
```

### 2.5 Avatar

```typescript
interface AvatarProps {
  src?: string;
  name: string;
  size: 'sm' | 'md' | 'lg';
  status?: 'online' | 'away' | 'offline';
  showBadge?: boolean;
  badgeContent?: string;
}
```

---

## 3. 레이아웃 컴포넌트

### 3.1 Header

```typescript
interface HeaderProps {
  showBackButton?: boolean;
  title?: string;
  subtitle?: string;
  balance?: number;
  onMenuClick?: () => void;
}
```

### 3.2 ConnectionBanner

```typescript
interface ConnectionBannerProps {
  status: 'connected' | 'reconnecting' | 'disconnected';
  onRetry?: () => void;
}
```

| Status | 메시지 | 색상 |
|--------|--------|------|
| connected | 없음 (숨김) | - |
| reconnecting | "재연결 중..." | 노란색 |
| disconnected | "연결 끊김" + 재시도 버튼 | 빨간색 |

---

## 4. 로비 컴포넌트

### 4.1 RoomCard

```typescript
interface RoomCardProps {
  room: {
    id: string;
    name: string;
    blinds: string;
    maxSeats: number;
    playerCount: number;
    status: 'waiting' | 'playing' | 'full';
  };
  onJoin: (roomId: string) => void;
  onSpectate: (roomId: string) => void;
}
```

### 4.2 RoomFilter

```typescript
interface RoomFilterProps {
  filters: {
    blinds: string | null;
    seats: number | null;
    status: string | null;
  };
  onFilterChange: (filters: Filters) => void;
  onSearch: (query: string) => void;
}
```

### 4.3 CreateRoomModal

```typescript
interface CreateRoomModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (config: RoomConfig) => void;
  isLoading: boolean;
}

interface RoomConfig {
  name: string;
  blinds: { small: number; big: number };
  maxSeats: 2 | 6 | 9;
  buyIn: { min: number; max: number };
}
```

---

## 5. 테이블 컴포넌트

### 5.1 Table

```typescript
interface TableProps {
  tableState: TableState;
  myPosition: number | null;
  isSpectator: boolean;
  onSeatClick: (position: number) => void;
}
```

### 5.2 Seat

```typescript
interface SeatProps {
  position: number;
  seat: SeatState | null;
  isCurrentTurn: boolean;
  isMe: boolean;
  isDealer: boolean;
  showHoleCards: boolean;
  holeCards?: [Card, Card];
  onClick: () => void;
}

interface SeatState {
  player: {
    userId: string;
    nickname: string;
    avatarUrl?: string;
  };
  stack: number;
  betAmount: number;
  status: 'active' | 'folded' | 'all_in' | 'sitting_out';
  lastAction?: {
    type: string;
    amount?: number;
  };
}
```

### 5.3 CommunityCards

```typescript
interface CommunityCardsProps {
  cards: Card[];
  phase: 'preflop' | 'flop' | 'turn' | 'river' | 'showdown';
  winningCards?: Card[];  // 쇼다운 시 하이라이트
}

interface Card {
  rank: string;  // '2'-'9', 'T', 'J', 'Q', 'K', 'A'
  suit: 'c' | 'd' | 'h' | 's';
}
```

### 5.4 ActionPanel

```typescript
interface ActionPanelProps {
  allowedActions: ValidAction[];
  currentBet: number;
  myBet: number;
  myStack: number;
  pot: number;
  minRaise: number;
  disabled: boolean;
  onAction: (action: ActionRequest) => void;
}

interface ValidAction {
  type: 'fold' | 'check' | 'call' | 'bet' | 'raise' | 'all_in';
  minAmount?: number;
  maxAmount?: number;
}
```

### 5.5 PotDisplay

```typescript
interface PotDisplayProps {
  mainPot: number;
  sidePots: { amount: number; eligiblePlayers: number[] }[];
}
```

### 5.6 Timer

```typescript
interface TimerProps {
  deadline: Date;
  warningThreshold?: number;  // 초, default 10
  criticalThreshold?: number; // 초, default 5
  onTimeout?: () => void;
}
```

### 5.7 Chat

```typescript
interface ChatProps {
  messages: ChatMessage[];
  onSend: (message: string) => void;
  disabled?: boolean;
}

interface ChatMessage {
  id: string;
  type: 'user' | 'system';
  sender?: string;
  content: string;
  timestamp: Date;
}
```

---

## 6. 카드 컴포넌트

### 6.1 PlayingCard

```typescript
interface PlayingCardProps {
  card: Card | null;  // null이면 뒷면
  size: 'sm' | 'md' | 'lg';
  highlighted?: boolean;
  disabled?: boolean;
}
```

### 6.2 카드 크기

| Size | 너비 | 높이 |
|------|------|------|
| sm | 40px | 56px |
| md | 60px | 84px |
| lg | 80px | 112px |

### 6.3 카드 색상

| Suit | 색상 |
|------|------|
| ♠ (Spades) | 검정 |
| ♣ (Clubs) | 검정 |
| ♥ (Hearts) | 빨강 |
| ♦ (Diamonds) | 빨강 |

---

## 7. 상태 표시 컴포넌트

### 7.1 PlayerStatus

```typescript
interface PlayerStatusProps {
  status: 'active' | 'folded' | 'all_in' | 'sitting_out' | 'disconnected';
}
```

| Status | 표시 | 스타일 |
|--------|------|--------|
| active | 없음 | 기본 |
| folded | "FOLD" | 흐리게 |
| all_in | "ALL-IN" | 강조 |
| sitting_out | "자리비움" | 흐리게 |
| disconnected | "연결 끊김" | 점선 테두리 |

### 7.2 ActionBadge

```typescript
interface ActionBadgeProps {
  action: 'fold' | 'check' | 'call' | 'bet' | 'raise' | 'all_in';
  amount?: number;
}
```

---

## 8. 디자인 토큰

### 8.1 색상

```css
:root {
  /* Primary */
  --color-primary: #3B82F6;
  --color-primary-hover: #2563EB;
  
  /* Status */
  --color-success: #10B981;
  --color-warning: #F59E0B;
  --color-danger: #EF4444;
  
  /* Neutral */
  --color-bg: #1F2937;
  --color-surface: #374151;
  --color-text: #F9FAFB;
  --color-text-muted: #9CA3AF;
  
  /* Table */
  --color-table-felt: #166534;
  --color-table-border: #14532D;
}
```

### 8.2 간격

```css
:root {
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
}
```

### 8.3 타이포그래피

```css
:root {
  --font-family: 'Inter', sans-serif;
  --font-size-xs: 12px;
  --font-size-sm: 14px;
  --font-size-md: 16px;
  --font-size-lg: 18px;
  --font-size-xl: 24px;
}
```

---

## 관련 문서

- [30-ui-ia.md](./30-ui-ia.md) - UI 정보 아키텍처
- [31-table-ui-spec.md](./31-table-ui-spec.md) - 테이블 UI 스펙
- [32-lobby-ui-spec.md](./32-lobby-ui-spec.md) - 로비 UI 스펙
