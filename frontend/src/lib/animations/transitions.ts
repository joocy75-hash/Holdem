/**
 * Framer Motion Transition Presets
 * 공통 transition 설정 정의
 */

import type { Transition } from 'framer-motion';

// ============================================
// Spring Transitions
// ============================================

/** 기본 스프링 - 자연스러운 움직임 */
export const springTransition: Transition = {
  type: 'spring',
  stiffness: 300,
  damping: 25,
};

/** 부드러운 스프링 - 느린 움직임 */
export const softSpring: Transition = {
  type: 'spring',
  stiffness: 200,
  damping: 30,
};

/** 빠른 스프링 - 빠른 반응 */
export const quickSpring: Transition = {
  type: 'spring',
  stiffness: 500,
  damping: 25,
};

/** "찰싹" Snap-back 스프링 - 카드가 빠르게 원위치로 돌아감 */
export const snapBackSpring: Transition = {
  type: 'spring',
  stiffness: 500,
  damping: 30,
  mass: 0.8,
};

/** "휙" Flip 스프링 - 카드 뒤집기 */
export const flipSpring: Transition = {
  type: 'spring',
  stiffness: 200,
  damping: 20,
  mass: 1,
};

/** 바운시 스프링 - 튀는 효과 */
export const bouncySpring: Transition = {
  type: 'spring',
  stiffness: 400,
  damping: 10,
};

// ============================================
// Tween Transitions
// ============================================

/** 부드러운 트윈 - 일반적인 페이드 */
export const smoothTransition: Transition = {
  type: 'tween',
  duration: 0.3,
  ease: 'easeOut',
};

/** 빠른 트윈 */
export const quickTransition: Transition = {
  type: 'tween',
  duration: 0.15,
  ease: 'easeOut',
};

/** 느린 트윈 - 드라마틱한 효과 */
export const slowTransition: Transition = {
  type: 'tween',
  duration: 0.6,
  ease: 'easeInOut',
};

/** Ease-In 가속 - 처음 느리게, 끝에 빠르게 (팟 이동용) */
export const easeInTransition: Transition = {
  type: 'tween',
  duration: 0.8,
  ease: 'easeIn',
};

/** Ease-Out 감속 - 처음 빠르게, 끝에 느리게 */
export const easeOutTransition: Transition = {
  type: 'tween',
  duration: 0.5,
  ease: 'easeOut',
};

// ============================================
// Stagger Transitions
// ============================================

/** 칩 이동 stagger - 0.05초 간격 */
export const chipStagger: Transition = {
  staggerChildren: 0.05,
  delayChildren: 0,
};

/** 버튼 등장 stagger */
export const buttonStagger: Transition = {
  staggerChildren: 0.08,
  delayChildren: 0.1,
};

/** 카드 배분 stagger */
export const cardDealStagger: Transition = {
  staggerChildren: 0.15,
  delayChildren: 0.2,
};

// ============================================
// Duration Constants
// ============================================

export const DURATIONS = {
  instant: 0.1,
  fast: 0.2,
  normal: 0.3,
  slow: 0.5,
  dramatic: 0.8,
  veryDramatic: 1.2,
} as const;

// ============================================
// Delay Constants
// ============================================

export const DELAYS = {
  none: 0,
  tiny: 0.05,
  small: 0.1,
  medium: 0.2,
  large: 0.4,
} as const;

// ============================================
// Card Animation Constants
// ============================================

export const CARD_CONSTANTS = {
  /** 카드 공개 임계값 (px) */
  REVEAL_THRESHOLD: 80,
  /** 카드 최대 드래그 거리 (px) */
  MAX_DRAG_DISTANCE: 150,
  /** 카드 3D perspective (px) */
  PERSPECTIVE: 1000,
  /** 카드 최대 회전 각도 (deg) */
  MAX_ROTATION: 45,
} as const;

// ============================================
// Chip Animation Constants
// ============================================

export const CHIP_CONSTANTS = {
  /** 칩 이동 시간 (ms) */
  MOVE_DURATION: 600,
  /** 칩 stagger 간격 (ms) */
  STAGGER_DELAY: 50,
  /** 최대 칩 개수 */
  MAX_CHIP_COUNT: 5,
} as const;

// ============================================
// Winner Animation Constants
// ============================================

export const WINNER_CONSTANTS = {
  /** 하이라이트 지속 시간 (ms) */
  HIGHLIGHT_DURATION: 3000,
  /** 복원 애니메이션 시간 (ms) */
  RESTORE_DURATION: 3000,
  /** 팟 이동 시간 (ms) */
  POT_MOVE_DURATION: 800,
} as const;
