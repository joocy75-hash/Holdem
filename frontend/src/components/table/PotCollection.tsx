'use client';

import { useState, useCallback, memo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  easeInTransition,
  pulse,
  calculateCurvedPath,
  pathToKeyframes,
  Point,
  WINNER_CONSTANTS,
} from '@/lib/animations';
import { ChipStack } from './chips';

interface Winner {
  position: number;
  amount: number;
  seatPosition: Point;
}

interface PotCollectionProps {
  /** 총 팟 금액 */
  potAmount: number;
  /** 테이블 중앙 위치 */
  tableCenter: Point;
  /** 승자 정보 (복수 가능 - split pot) */
  winners: Winner[];
  /** 애니메이션 시작 트리거 */
  isAnimating: boolean;
  /** 애니메이션 완료 콜백 */
  onAnimationComplete?: () => void;
  /** 칩 수거 완료 콜백 */
  onChipsGathered?: () => void;
}

type AnimationPhase = 'idle' | 'gathering' | 'moving' | 'complete';

/**
 * 팟 수거 및 승자 이동 애니메이션 컴포넌트
 * - 단일 칩 스택 이미지 사용 (성능 최적화)
 * - 중앙 → 승자 좌석 이동 (Ease-In 가속)
 * - Split pot 지원 (여러 승자)
 */
function PotCollectionComponent({
  potAmount,
  tableCenter,
  winners,
  isAnimating,
  onAnimationComplete,
  onChipsGathered,
}: PotCollectionProps) {
  const [phase, setPhase] = useState<AnimationPhase>('idle');

  // 애니메이션 시작 감지
  const [lastIsAnimating, setLastIsAnimating] = useState(isAnimating);
  if (isAnimating !== lastIsAnimating) {
    setLastIsAnimating(isAnimating);
    if (isAnimating) {
      setPhase('gathering');
    } else {
      setPhase('idle');
    }
  }

  // 수거 완료 처리
  const handleGatherComplete = useCallback(() => {
    setPhase('moving');
    onChipsGathered?.();
  }, [onChipsGathered]);

  // 이동 완료 처리
  const handleMoveComplete = useCallback(() => {
    setPhase('complete');
    onAnimationComplete?.();
  }, [onAnimationComplete]);

  if (!isAnimating && phase === 'idle') return null;

  return (
    <div className="absolute inset-0 pointer-events-none z-50">
      <AnimatePresence mode="wait">
        {/* Phase 1: 중앙에 팟 표시 후 곧바로 이동 단계로 */}
        {phase === 'gathering' && (
          <GatheringChips
            key="gathering"
            tableCenter={tableCenter}
            potAmount={potAmount}
            onComplete={handleGatherComplete}
          />
        )}

        {/* Phase 2: 중앙에서 승자들에게 이동 */}
        {phase === 'moving' && winners.length > 0 && (
          <MovingToWinners
            key="moving"
            tableCenter={tableCenter}
            winners={winners}
            onComplete={handleMoveComplete}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

export default memo(PotCollectionComponent);

// 칩 수거 애니메이션 (중앙 집결 표시)
const GatheringChips = memo(function GatheringChips({
  tableCenter,
  potAmount,
  onComplete,
}: {
  tableCenter: Point;
  potAmount: number;
  onComplete: () => void;
}) {
  return (
    <motion.div
      className="absolute"
      style={{
        left: tableCenter.x - 16,
        top: tableCenter.y - 16,
      }}
      initial={{ opacity: 0, scale: 0.5 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      onAnimationComplete={() => {
        setTimeout(onComplete, 100);
      }}
    >
      <ChipStack amount={potAmount} />
    </motion.div>
  );
});

// 승자에게 이동 애니메이션
const MovingToWinners = memo(function MovingToWinners({
  tableCenter,
  winners,
  onComplete,
}: {
  tableCenter: Point;
  winners: Winner[];
  onComplete: () => void;
}) {
  const [completedWinners, setCompletedWinners] = useState(0);

  const handleWinnerComplete = useCallback(() => {
    setCompletedWinners((prev) => {
      const next = prev + 1;
      if (next >= winners.length) {
        setTimeout(onComplete, 100);
      }
      return next;
    });
  }, [winners.length, onComplete]);

  // completedWinners is used for tracking animation progress
  void completedWinners;

  return (
    <>
      {winners.map((winner, winnerIndex) => (
        <WinnerChipAnimation
          key={`winner-${winnerIndex}`}
          tableCenter={tableCenter}
          winner={winner}
          delay={winnerIndex * 0.2}
          onComplete={
            winnerIndex === winners.length - 1 ? handleWinnerComplete : undefined
          }
        />
      ))}
    </>
  );
});

// 개별 승자 칩 애니메이션
const WinnerChipAnimation = memo(function WinnerChipAnimation({
  tableCenter,
  winner,
  delay,
  onComplete,
}: {
  tableCenter: Point;
  winner: Winner;
  delay: number;
  onComplete?: () => void;
}) {
  const [showPulse, setShowPulse] = useState(false);

  const path = calculateCurvedPath(tableCenter, winner.seatPosition, {
    curvature: 0.2,
    direction: 'up',
  });
  const keyframes = pathToKeyframes(path);

  const handleAnimationComplete = useCallback(() => {
    setShowPulse(true);
    onComplete?.();
  }, [onComplete]);

  return (
    <>
      {/* 단일 칩 스택 이미지 이동 */}
      <motion.div
        className="absolute"
        initial={{
          x: tableCenter.x - 16,
          y: tableCenter.y - 16,
          scale: 0.8,
        }}
        animate={{
          x: keyframes.x.map((x) => x - 16),
          y: keyframes.y.map((y) => y - 16),
          scale: 1,
        }}
        transition={{
          ...easeInTransition,
          duration: WINNER_CONSTANTS.POT_MOVE_DURATION / 1000,
          delay,
        }}
        onAnimationComplete={handleAnimationComplete}
      >
        <ChipStack amount={winner.amount} />
      </motion.div>

      {/* 승자 위치 펄스 효과 */}
      {showPulse && (
        <motion.div
          className="absolute w-16 h-16 rounded-full"
          style={{
            left: winner.seatPosition.x - 32,
            top: winner.seatPosition.y - 32,
            background:
              'radial-gradient(circle, rgba(255,215,0,0.5) 0%, transparent 70%)',
          }}
          variants={pulse}
          initial="initial"
          animate="pulse"
        />
      )}

      {/* 금액 표시 */}
      {showPulse && (
        <motion.div
          className="absolute text-lg font-bold text-yellow-400 drop-shadow-lg"
          style={{
            left: winner.seatPosition.x,
            top: winner.seatPosition.y - 40,
            transform: 'translateX(-50%)',
          }}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          +{winner.amount.toLocaleString()}
        </motion.div>
      )}
    </>
  );
});
