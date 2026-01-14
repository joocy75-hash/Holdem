# Design Document: Framer Motion Migration

## Overview

이 문서는 홀덤 게임 프론트엔드의 애니메이션 시스템을 Framer Motion으로 마이그레이션하는 기술 설계를 정의한다. 현재 순수 CSS/JS 기반의 복잡한 애니메이션 로직을 Framer Motion의 선언적 API로 교체하여 코드 복잡도를 66% 이상 감소시키고, 일관된 애니메이션 패턴을 확립한다.

## Architecture

```
frontend/src/
├── lib/
│   └── animations/
│       ├── variants.ts      # 공통 애니메이션 variants
│       ├── transitions.ts   # 공통 transition presets
│       └── index.ts         # 통합 export
├── components/
│   └── table/
│       ├── pmang/
│       │   └── CardSqueeze.tsx  # Framer Motion 적용
│       ├── ActionButtons.tsx     # Framer Motion 적용
│       └── BuyInModal.tsx        # Framer Motion 적용
```

## Components and Interfaces

### 1. Animation Utilities (`lib/animations/`)

```typescript
// variants.ts
export const fadeIn = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 }
};

export const scaleIn = {
  initial: { opacity: 0, scale: 0.9 },
  animate: { opacity: 1, scale: 1 },
  exit: { opacity: 0, scale: 0.9 }
};

export const slideUp = {
  initial: { opacity: 0, y: '100%' },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: '100%' }
};

export const buttonHover = {
  scale: 1.05,
  transition: { type: 'spring', stiffness: 400, damping: 10 }
};

export const buttonTap = {
  scale: 0.95
};

// transitions.ts
export const springTransition = {
  type: 'spring',
  stiffness: 300,
  damping: 25
};

export const smoothTransition = {
  type: 'tween',
  duration: 0.3,
  ease: 'easeOut'
};
```

### 2. CardSqueeze Component (Refactored)

```typescript
// 기존: 150줄 → 리팩토링 후: ~50줄
interface CardSqueezeProps {
  cards: Card[];
  onRevealComplete?: (cardIndex: number) => void;
  disabled?: boolean;
  className?: string;
}

// Framer Motion 핵심 구현
const CardSqueeze = ({ cards, onRevealComplete, disabled }: CardSqueezeProps) => {
  const [revealedCards, setRevealedCards] = useState<Set<number>>(new Set());
  
  const handleDragEnd = (index: number, info: PanInfo) => {
    if (info.offset.y < -REVEAL_THRESHOLD) {
      setRevealedCards(prev => new Set([...prev, index]));
      onRevealComplete?.(index);
    }
  };

  return (
    <div className="flex gap-4">
      {cards.map((card, index) => (
        <motion.div
          key={index}
          drag={!revealedCards.has(index) && !disabled ? 'y' : false}
          dragConstraints={{ top: -REVEAL_THRESHOLD, bottom: 0 }}
          dragElastic={0.1}
          onDragEnd={(_, info) => handleDragEnd(index, info)}
          whileDrag={{ scale: 1.05, zIndex: 10 }}
          data-testid={`hole-card-${index}`}
          data-revealed={revealedCards.has(index)}
        >
          <CardContent card={card} isRevealed={revealedCards.has(index)} />
        </motion.div>
      ))}
    </div>
  );
};
```

### 3. ActionButtons Component (Enhanced)

```typescript
// Framer Motion 적용
const ActionButton = ({ onClick, children, testId, imageSrc, alt }) => (
  <motion.button
    onClick={onClick}
    whileHover={{ scale: 1.05 }}
    whileTap={{ scale: 0.95 }}
    transition={{ type: 'spring', stiffness: 400, damping: 17 }}
    data-testid={testId}
  >
    <img src={imageSrc} alt={alt} />
    {children}
  </motion.button>
);

// AnimatePresence로 버튼 그룹 등장/퇴장
<AnimatePresence mode="wait">
  {showButtons && (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      transition={{ staggerChildren: 0.05 }}
    >
      {/* 버튼들 */}
    </motion.div>
  )}
</AnimatePresence>
```

### 4. BuyInModal Component (Enhanced)

```typescript
// AnimatePresence + motion 조합
<AnimatePresence>
  {isOpen && (
    <>
      {/* Backdrop */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal Content */}
      <motion.div
        initial={{ opacity: 0, y: '100%' }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: '100%' }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        className="fixed bottom-0 left-0 right-0 bg-surface rounded-t-2xl"
      >
        {/* Modal content */}
      </motion.div>
    </>
  )}
</AnimatePresence>
```

## Data Models

### Animation Variant Type

```typescript
interface AnimationVariant {
  initial?: TargetAndTransition;
  animate?: TargetAndTransition;
  exit?: TargetAndTransition;
  whileHover?: TargetAndTransition;
  whileTap?: TargetAndTransition;
  whileDrag?: TargetAndTransition;
}

interface TransitionPreset {
  type: 'spring' | 'tween';
  stiffness?: number;
  damping?: number;
  duration?: number;
  ease?: string;
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Drag Threshold Consistency
*For any* card drag interaction, if the drag offset exceeds -80px (REVEAL_THRESHOLD), the card SHALL be revealed; otherwise, it SHALL snap back to original position.
**Validates: Requirements 2.2, 2.3**

### Property 2: Animation State Preservation
*For any* component using Framer Motion, the data-testid and data-* attributes SHALL remain unchanged after animation completes.
**Validates: Requirements 2.7, 3.6, 6.4, 6.5**

### Property 3: Button Interaction Feedback
*For any* action button, hover state SHALL apply scale(1.05) and tap state SHALL apply scale(0.95) consistently.
**Validates: Requirements 3.1, 3.2**

### Property 4: Modal Animation Sequence
*For any* modal open/close action, the backdrop and content SHALL animate in correct sequence (backdrop first on open, content first on close).
**Validates: Requirements 4.1, 4.2, 4.3, 4.4**

## Error Handling

1. **Framer Motion Import Errors**: 빌드 시 모듈 해석 실패 시 명확한 에러 메시지 출력
2. **Animation Interruption**: 애니메이션 중 컴포넌트 언마운트 시 메모리 누수 방지 (AnimatePresence 사용)
3. **Drag Gesture Conflicts**: 터치 디바이스에서 스크롤과 드래그 충돌 방지 (dragConstraints 설정)
4. **SSR Compatibility**: Next.js SSR 환경에서 Framer Motion 호환성 확보 ('use client' 지시어)

## Testing Strategy

### Unit Tests
- Animation variant 객체의 올바른 구조 검증
- Transition preset 값 범위 검증

### Integration Tests (E2E)
- CardSqueeze 드래그 → 공개 시나리오
- ActionButtons 호버/클릭 피드백
- BuyInModal 열기/닫기 애니메이션

### Property-Based Tests
- 드래그 임계값 일관성 테스트 (다양한 드래그 거리에 대해)
- 애니메이션 완료 후 DOM 상태 검증

### Test Configuration
- 최소 100회 반복 실행 (Property-Based Tests)
- Playwright E2E 테스트 기존 스펙 유지
