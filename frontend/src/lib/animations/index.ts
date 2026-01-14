/**
 * Animation Utilities - 통합 Export
 * 
 * 사용 예시:
 * import { fadeIn, springTransition, calculateCurvedPath } from '@/lib/animations';
 */

// Variants
export {
  // Entrance/Exit
  fadeIn,
  fadeOut,
  scaleIn,
  slideUp,
  slideDown,
  slideLeft,
  slideRight,
  // Interactions
  buttonHover,
  buttonTap,
  cardHover,
  // Staggered
  staggeredContainer,
  staggeredItem,
  staggeredChip,
  // Card
  cardFlip,
  cardReveal,
  // Winner
  winnerGlow,
  loserDim,
  // Effects
  floatingNumber,
  pulse,
} from './variants';

// Transitions
export {
  // Springs
  springTransition,
  softSpring,
  quickSpring,
  snapBackSpring,
  flipSpring,
  bouncySpring,
  // Tweens
  smoothTransition,
  quickTransition,
  slowTransition,
  easeInTransition,
  easeOutTransition,
  // Staggers
  chipStagger,
  buttonStagger,
  cardDealStagger,
  // Constants
  DURATIONS,
  DELAYS,
  CARD_CONSTANTS,
  CHIP_CONSTANTS,
  WINNER_CONSTANTS,
} from './transitions';

// Paths
export {
  calculateCurvedPath,
  calculateArcPath,
  calculateCircularPath,
  createChipToTablePath,
  createPotToWinnerPath,
  generateScatteredPositions,
  pathToKeyframes,
} from './paths';

export type { Point, CurvedPathOptions } from './paths';
