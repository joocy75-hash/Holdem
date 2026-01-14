/**
 * Framer Motion Animation Variants
 * 공통 애니메이션 variants 정의
 */

import type { Variants, TargetAndTransition } from 'framer-motion';

// ============================================
// Entrance/Exit Variants
// ============================================

export const fadeIn: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
};

export const fadeOut: Variants = {
  initial: { opacity: 1 },
  animate: { opacity: 0 },
  exit: { opacity: 0 },
};

export const scaleIn: Variants = {
  initial: { opacity: 0, scale: 0.9 },
  animate: { opacity: 1, scale: 1 },
  exit: { opacity: 0, scale: 0.9 },
};

export const slideUp: Variants = {
  initial: { opacity: 0, y: '100%' },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: '100%' },
};

export const slideDown: Variants = {
  initial: { opacity: 0, y: '-100%' },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: '-100%' },
};

export const slideLeft: Variants = {
  initial: { opacity: 0, x: '100%' },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: '100%' },
};

export const slideRight: Variants = {
  initial: { opacity: 0, x: '-100%' },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: '-100%' },
};

// ============================================
// Interaction Variants
// ============================================

export const buttonHover: TargetAndTransition = {
  scale: 1.05,
  transition: { type: 'spring', stiffness: 400, damping: 10 },
};

export const buttonTap: TargetAndTransition = {
  scale: 0.95,
};

export const cardHover: TargetAndTransition = {
  scale: 1.02,
  y: -5,
  transition: { type: 'spring', stiffness: 300, damping: 20 },
};

// ============================================
// Staggered Children Variants
// ============================================

export const staggeredContainer: Variants = {
  initial: {},
  animate: {
    transition: {
      staggerChildren: 0.05,
      delayChildren: 0.1,
    },
  },
  exit: {
    transition: {
      staggerChildren: 0.03,
      staggerDirection: -1,
    },
  },
};

export const staggeredItem: Variants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -10 },
};

export const staggeredChip: Variants = {
  initial: { opacity: 0, scale: 0.5 },
  animate: { opacity: 1, scale: 1 },
  exit: { opacity: 0, scale: 0.5 },
};

// ============================================
// Card Animation Variants
// ============================================

export const cardFlip: Variants = {
  initial: { rotateY: 0 },
  flipped: { rotateY: 180 },
};

export const cardReveal: Variants = {
  hidden: { 
    rotateX: 0,
    y: 0,
    boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
  },
  peeking: {
    rotateX: -30,
    y: -20,
    boxShadow: '0 20px 40px rgba(0,0,0,0.4)',
  },
  revealed: {
    rotateX: -180,
    y: 0,
    boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
  },
};

// ============================================
// Winner Highlight Variants
// ============================================

export const winnerGlow: Variants = {
  initial: { 
    boxShadow: '0 0 0 rgba(255, 215, 0, 0)',
    filter: 'brightness(1)',
  },
  highlight: {
    boxShadow: [
      '0 0 20px rgba(255, 215, 0, 0.5)',
      '0 0 40px rgba(255, 215, 0, 0.8)',
      '0 0 20px rgba(255, 215, 0, 0.5)',
    ],
    filter: 'brightness(1.2)',
    transition: {
      boxShadow: {
        repeat: Infinity,
        duration: 1.5,
      },
    },
  },
};

export const loserDim: Variants = {
  initial: { 
    filter: 'grayscale(0) brightness(1)',
  },
  dimmed: {
    filter: 'grayscale(0.8) brightness(0.6)',
    transition: { duration: 0.5 },
  },
  restored: {
    filter: 'grayscale(0) brightness(1)',
    transition: { duration: 3 },
  },
};

// ============================================
// Floating Number Variants
// ============================================

export const floatingNumber: Variants = {
  initial: { 
    opacity: 0, 
    y: 0, 
    scale: 0.5,
  },
  animate: {
    opacity: [0, 1, 1, 0],
    y: [0, -30, -50, -70],
    scale: [0.5, 1.2, 1, 0.8],
    transition: {
      duration: 1.5,
      times: [0, 0.2, 0.6, 1],
    },
  },
};

// ============================================
// Pulse Variants
// ============================================

export const pulse: Variants = {
  initial: { scale: 1 },
  pulse: {
    scale: [1, 1.1, 1],
    transition: {
      duration: 0.4,
      ease: 'easeInOut',
    },
  },
};
