'use client';

import { useState, useCallback, memo, useLayoutEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { floatingNumber, CHIP_CONSTANTS } from '@/lib/animations';
import { ChipStack } from './chips';

interface BettingChipsProps {
  amount: number;
  position: { x: number; y: number };
  isAnimating?: boolean;
  animateTo?: { x: number; y: number };
  onAnimationEnd?: () => void;
  showBetAnimation?: boolean;
  betStartPosition?: { x: number; y: number };
  hideLabel?: boolean;
}

// 금액 포맷팅
function formatAmount(amount: number): string {
  if (amount >= 10000) return `+${(amount / 10000).toFixed(1)}만`;
  if (amount >= 1000) return `+${(amount / 1000).toFixed(1)}천`;
  return `+${amount.toLocaleString()}`;
}

// 금액 라벨
const AmountLabel = memo(function AmountLabel({ amount }: { amount: number }) {
  return (
    <div className="mt-1 px-2 py-0.5 bg-black/80 rounded text-white text-[10px] font-bold whitespace-nowrap">
      {amount.toLocaleString()}
    </div>
  );
});

/**
 * 베팅 칩 컴포넌트 (최적화 버전)
 *
 * 미리 생성된 칩 스택 이미지를 사용하여 성능을 최적화합니다.
 * - 기존: 금액에 따라 개별 칩을 계산/렌더링 (최대 15개 DOM 요소)
 * - 변경: 단일 이미지 (1개 DOM 요소)
 */
export function BettingChips({
  amount,
  position,
  isAnimating = false,
  animateTo,
  onAnimationEnd,
  showBetAnimation = false,
  betStartPosition,
  hideLabel = false,
}: BettingChipsProps) {
  const [showFloatingNumber, setShowFloatingNumber] = useState(false);
  const [animationComplete, setAnimationComplete] = useState(false);

  const handleAnimationComplete = useCallback(() => {
    setAnimationComplete(true);
    onAnimationEnd?.();
  }, [onAnimationEnd]);

  const handleFirstChipArrived = useCallback(() => {
    setShowFloatingNumber(true);
  }, []);

  // 이전 상태 추적 (렌더링 중 상태 변경 방지)
  const prevBetStateRef = useRef({ showBetAnimation, amount });

  // 상태 리셋 - useLayoutEffect로 DOM 커밋 전에 동기적으로 실행
  // 새 베팅 애니메이션 시작 시 이전 애니메이션 상태를 즉시 리셋
  // 의도적 state 리셋: 새 베팅 시작 시 이전 애니메이션 상태 초기화 필요
  /* eslint-disable react-hooks/set-state-in-effect */
  useLayoutEffect(() => {
    const prevState = prevBetStateRef.current;
    const hasChanged = showBetAnimation !== prevState.showBetAnimation || amount !== prevState.amount;

    if (hasChanged) {
      prevBetStateRef.current = { showBetAnimation, amount };
      // 새 베팅 애니메이션 시작 시에만 상태 리셋
      if (showBetAnimation && (animationComplete || showFloatingNumber)) {
        setAnimationComplete(false);
        setShowFloatingNumber(false);
      }
    }
  }, [showBetAnimation, amount, animationComplete, showFloatingNumber]);
  /* eslint-enable react-hooks/set-state-in-effect */

  if (amount <= 0) return null;

  // 베팅 애니메이션 모드 (단순 직선 이동)
  if (showBetAnimation && betStartPosition && !animationComplete) {
    return (
      <div className="absolute inset-0 pointer-events-none z-50">
        <AnimatePresence>
          <motion.div
            key="bet-chip"
            className="absolute -translate-x-1/2 -translate-y-1/2"
            style={{ left: betStartPosition.x, top: betStartPosition.y }}
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{
              x: position.x - betStartPosition.x,
              y: position.y - betStartPosition.y,
              opacity: 1,
              scale: 1,
            }}
            transition={{
              duration: CHIP_CONSTANTS.MOVE_DURATION / 1000,
              ease: 'easeOut',
            }}
            onAnimationComplete={() => {
              handleFirstChipArrived();
              handleAnimationComplete();
            }}
          >
            <ChipStack amount={amount} />
          </motion.div>

          {showFloatingNumber && (
            <motion.div
              className="absolute text-xl font-bold text-yellow-400 drop-shadow-lg"
              style={{ left: position.x, top: position.y, transform: 'translate(-50%, -50%)' }}
              variants={floatingNumber}
              initial="initial"
              animate="animate"
              onAnimationComplete={() => setShowFloatingNumber(false)}
            >
              {formatAmount(amount)}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  }

  // 팟 이동 애니메이션 모드 (단순 직선 이동)
  if (isAnimating && animateTo) {
    return (
      <div className="absolute inset-0 pointer-events-none z-50">
        <motion.div
          className="absolute -translate-x-1/2 -translate-y-1/2"
          style={{ left: position.x, top: position.y }}
          initial={{ opacity: 1, scale: 1 }}
          animate={{
            x: animateTo.x - position.x,
            y: animateTo.y - position.y,
            scale: [1, 1, 0.9, 0.8],
            opacity: [1, 1, 1, 0],
          }}
          transition={{ duration: 0.4, ease: 'linear' }}
          onAnimationComplete={handleAnimationComplete}
        >
          <ChipStack amount={amount} />
        </motion.div>
      </div>
    );
  }

  // 정적 표시 (애니메이션 없음 - 가장 빠름)
  return (
    <div
      className="absolute -translate-x-1/2 -translate-y-1/2 flex flex-col items-center z-30"
      style={{ top: position.y, left: position.x }}
    >
      <ChipStack amount={amount} />
      {!hideLabel && <AmountLabel amount={amount} />}
    </div>
  );
}
