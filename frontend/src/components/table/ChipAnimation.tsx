'use client';

import { useState, useCallback, memo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  floatingNumber,
  CHIP_CONSTANTS,
  calculateCurvedPath,
  pathToKeyframes,
  Point,
} from '@/lib/animations';
import { ChipStack } from './chips';

interface ChipAnimationProps {
  /** 베팅 금액 */
  amount: number;
  /** 시작 위치 (플레이어 좌석) */
  startPosition: Point;
  /** 끝 위치 (테이블 중앙) */
  endPosition: Point;
  /** 애니메이션 시작 트리거 */
  isAnimating: boolean;
  /** 애니메이션 완료 콜백 (사운드 트리거용) */
  onAnimationComplete?: () => void;
  /** 첫 칩 도착 콜백 (숫자 팝업용) */
  onFirstChipArrived?: () => void;
  /** 고유 키 (외부에서 제어) */
  animationKey?: number;
}

// 금액 포맷팅
function formatAmount(amount: number): string {
  if (amount >= 10000) {
    return `+${(amount / 10000).toFixed(1)}만`;
  }
  if (amount >= 1000) {
    return `+${(amount / 1000).toFixed(1)}천`;
  }
  return `+${amount.toLocaleString()}`;
}

/**
 * 베팅 칩 이동 애니메이션 컴포넌트
 * - 단일 칩 스택 이미지 이동 (성능 최적화)
 * - 곡선 경로 (베지어 곡선)
 * - Floating Number 효과
 * - 효과음 동기화 포인트
 */
function ChipAnimationComponent({
  amount,
  startPosition,
  endPosition,
  isAnimating,
  onAnimationComplete,
  onFirstChipArrived,
  animationKey = 0,
}: ChipAnimationProps) {
  const [showFloatingNumber, setShowFloatingNumber] = useState(false);
  const [lastAnimationKey, setLastAnimationKey] = useState(animationKey);

  // animationKey가 변경되면 floating number 리셋
  if (animationKey !== lastAnimationKey) {
    setLastAnimationKey(animationKey);
    if (showFloatingNumber) {
      setShowFloatingNumber(false);
    }
  }

  // 곡선 경로 계산
  const path = calculateCurvedPath(startPosition, endPosition, {
    curvature: 0.25,
    direction: 'up',
  });
  const keyframes = pathToKeyframes(path);

  // 칩 도착 처리
  const handleChipArrived = useCallback(() => {
    setShowFloatingNumber(true);
    onFirstChipArrived?.();
    onAnimationComplete?.();
  }, [onFirstChipArrived, onAnimationComplete]);

  if (!isAnimating || amount <= 0) return null;

  return (
    <div className="absolute inset-0 pointer-events-none z-50">
      <AnimatePresence>
        {/* 단일 칩 스택 이미지 */}
        <motion.div
          key={`${animationKey}-chip`}
          className="absolute"
          style={{
            left: startPosition.x - 16,
            top: startPosition.y - 16,
          }}
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{
            x: keyframes.x.map((x) => x - startPosition.x),
            y: keyframes.y.map((y) => y - startPosition.y),
            opacity: 1,
            scale: 1,
          }}
          transition={{
            duration: CHIP_CONSTANTS.MOVE_DURATION / 1000,
            ease: [0.25, 0.1, 0.25, 1],
          }}
          onAnimationComplete={handleChipArrived}
        >
          <ChipStack amount={amount} />
        </motion.div>

        {/* Floating Number */}
        {showFloatingNumber && (
          <motion.div
            key={`${animationKey}-number`}
            className="absolute text-2xl font-bold text-yellow-400 drop-shadow-lg"
            style={{
              left: endPosition.x,
              top: endPosition.y,
              transform: 'translate(-50%, -50%)',
            }}
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

export default memo(ChipAnimationComponent);

/**
 * 칩 애니메이션 훅 - 컴포넌트에서 쉽게 사용
 */
export function useChipAnimation() {
  const [animationState, setAnimationState] = useState<{
    isAnimating: boolean;
    amount: number;
    startPosition: Point;
    endPosition: Point;
    key: number;
  } | null>(null);

  const triggerAnimation = useCallback(
    (amount: number, startPosition: Point, endPosition: Point) => {
      setAnimationState((prev) => ({
        isAnimating: true,
        amount,
        startPosition,
        endPosition,
        key: (prev?.key ?? 0) + 1,
      }));
    },
    []
  );

  const stopAnimation = useCallback(() => {
    setAnimationState(null);
  }, []);

  return {
    animationState,
    triggerAnimation,
    stopAnimation,
  };
}
