'use client';

import { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { evaluateHand, HandResult } from '@/lib/handEvaluator';
import {
  winnerGlow,
  loserDim,
  scaleIn,
  springTransition,
  WINNER_CONSTANTS,
} from '@/lib/animations';

interface Card {
  rank: string;
  suit: string;
}

interface Winner {
  position: number;
  holeCards: Card[];
  amount: number;
  handResult?: HandResult;
}

interface ShowdownHighlightProps {
  winners: Winner[];
  communityCards: Card[];
  isActive: boolean;
  onAnimationComplete?: () => void;
}

// 슈트 심볼 매핑
const SUIT_SYMBOLS: Record<string, string> = {
  hearts: '♥', h: '♥',
  diamonds: '♦', d: '♦',
  clubs: '♣', c: '♣',
  spades: '♠', s: '♠',
};

// 슈트 색상 매핑
const SUIT_COLORS: Record<string, string> = {
  hearts: 'text-red-500', h: 'text-red-500',
  diamonds: 'text-red-500', d: 'text-red-500',
  clubs: 'text-gray-900', c: 'text-gray-900',
  spades: 'text-gray-900', s: 'text-gray-900',
};

// 카드가 승리 족보에 포함되는지 확인
function isWinningCard(card: Card, winningCards: Card[]): boolean {
  return winningCards.some(
    wc => wc.rank === card.rank && wc.suit.toLowerCase() === card.suit.toLowerCase()
  );
}

/**
 * 하이라이트된 카드 컴포넌트 (Framer Motion 버전)
 */
function HighlightedCard({
  card,
  isWinning,
  delay = 0,
}: {
  card: Card;
  isWinning: boolean;
  delay?: number;
}) {
  const suitLower = card.suit.toLowerCase();
  const suitSymbol = SUIT_SYMBOLS[suitLower] || card.suit;
  const suitColor = SUIT_COLORS[suitLower] || 'text-gray-900';

  return (
    <motion.div
      className="relative w-[44px] h-[62px] rounded-lg"
      initial={{ opacity: 0, scale: 0.75 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ 
        ...springTransition,
        delay: delay / 1000,
      }}
    >
      {/* 카드 배경 */}
      <motion.div 
        className="absolute inset-0 rounded-lg bg-white"
        variants={isWinning ? winnerGlow : loserDim}
        initial="initial"
        animate={isWinning ? "highlight" : "dimmed"}
        style={{
          background: isWinning 
            ? 'linear-gradient(135deg, white 0%, #FEF3C7 100%)' 
            : 'white',
        }}
      />

      {/* 승리 카드 글로우 효과 */}
      {isWinning && (
        <motion.div 
          className="absolute inset-0 rounded-lg pointer-events-none"
          animate={{
            boxShadow: [
              '0 0 10px rgba(255, 215, 0, 0.3)',
              '0 0 20px rgba(255, 215, 0, 0.6)',
              '0 0 10px rgba(255, 215, 0, 0.3)',
            ],
          }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
      )}

      {/* 비승리 카드 딤 효과 */}
      {!isWinning && (
        <motion.div 
          className="absolute inset-0 rounded-lg bg-black/40 pointer-events-none"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: delay / 1000 + 0.3 }}
        />
      )}

      {/* 카드 내용 */}
      <div className={`
        relative flex flex-col items-center justify-center h-full
        font-bold ${suitColor}
        ${!isWinning ? 'opacity-60' : ''}
      `}>
        <span className="text-lg leading-none">{card.rank}</span>
        <span className="text-xl leading-none">{suitSymbol}</span>
      </div>
    </motion.div>
  );
}

/**
 * 피망 스타일 쇼다운 하이라이트 (Framer Motion 버전)
 * - 승리 족보 5장만 밝게 강조 (금색 글로우)
 * - 비사용 카드 딤 처리 (grayscale + darken)
 * - 스플릿 팟 시 각 승자 개별 하이라이트
 * - 3초 후 점진적 복원
 */
export default function ShowdownHighlight({
  winners,
  communityCards,
  isActive,
  onAnimationComplete,
}: ShowdownHighlightProps) {
  const [currentWinnerIndex, setCurrentWinnerIndex] = useState(0);
  const [showWinnerBanner, setShowWinnerBanner] = useState(false);
  const [isRestoring, setIsRestoring] = useState(false);

  // 각 승자의 핸드 결과 계산
  const winnersWithHands = useMemo(() => {
    return winners.map(winner => {
      const allCards = [...winner.holeCards, ...communityCards];
      const handResult = evaluateHand(allCards);
      return {
        ...winner,
        handResult,
        winningCards: handResult?.bestFive || [],
      };
    });
  }, [winners, communityCards]);

  // 현재 표시 중인 승자
  const currentWinner = winnersWithHands[currentWinnerIndex];

  // 애니메이션 시퀀스
  useEffect(() => {
    if (!isActive || winnersWithHands.length === 0) return;

    // 승자 배너 표시
    const bannerTimer = setTimeout(() => {
      setShowWinnerBanner(true);
    }, 500);

    // 다음 승자로 전환 (스플릿 팟)
    const nextWinnerTimer = setTimeout(() => {
      if (currentWinnerIndex < winnersWithHands.length - 1) {
        setShowWinnerBanner(false);
        setTimeout(() => {
          setCurrentWinnerIndex(prev => prev + 1);
        }, 300);
      } else {
        // 복원 시작
        setIsRestoring(true);
        // 모든 승자 표시 완료
        setTimeout(() => {
          onAnimationComplete?.();
        }, WINNER_CONSTANTS.RESTORE_DURATION);
      }
    }, 4000);

    return () => {
      clearTimeout(bannerTimer);
      clearTimeout(nextWinnerTimer);
    };
  }, [isActive, currentWinnerIndex, winnersWithHands.length, onAnimationComplete]);

  // 리셋
  useEffect(() => {
    if (!isActive) {
      requestAnimationFrame(() => {
        setCurrentWinnerIndex(0);
        setShowWinnerBanner(false);
        setIsRestoring(false);
      });
    }
  }, [isActive]);

  if (!isActive || !currentWinner) {
    return null;
  }

  const { holeCards, winningCards, handResult, amount } = currentWinner;
  const isSplitPot = winnersWithHands.length > 1;

  return (
    <AnimatePresence>
      <motion.div 
        className="fixed inset-0 z-50 flex items-center justify-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.3 }}
        data-testid="showdown-highlight"
      >
        {/* 배경 흑백 처리 */}
        <motion.div 
          className="absolute inset-0 bg-black/60"
          initial={{ backdropFilter: 'grayscale(0) brightness(1)' }}
          animate={{ 
            backdropFilter: isRestoring 
              ? 'grayscale(0) brightness(1)' 
              : 'grayscale(0.5) brightness(0.7)',
          }}
          transition={{ 
            duration: isRestoring 
              ? WINNER_CONSTANTS.RESTORE_DURATION / 1000 
              : 0.5,
          }}
        />

        <motion.div 
          className="relative max-w-lg w-full mx-4"
          variants={scaleIn}
          initial="initial"
          animate="animate"
          exit="exit"
        >
          {/* 승자 배너 */}
          <AnimatePresence>
            {showWinnerBanner && (
              <motion.div 
                className="absolute -top-16 left-1/2"
                initial={{ opacity: 0, y: 20, x: '-50%' }}
                animate={{ opacity: 1, y: 0, x: '-50%' }}
                exit={{ opacity: 0, y: -20, x: '-50%' }}
                transition={springTransition}
              >
                <motion.div 
                  className="px-6 py-3 bg-gradient-to-r from-yellow-500 via-yellow-400 to-yellow-500 rounded-xl shadow-2xl"
                  animate={{
                    boxShadow: [
                      '0 10px 40px rgba(234, 179, 8, 0.3)',
                      '0 10px 60px rgba(234, 179, 8, 0.5)',
                      '0 10px 40px rgba(234, 179, 8, 0.3)',
                    ],
                  }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  <div className="text-center">
                    <div className="text-black font-bold text-xl">
                      🏆 {isSplitPot ? `승자 ${currentWinnerIndex + 1}/${winnersWithHands.length}` : 'WINNER!'}
                    </div>
                    <motion.div 
                      className="text-black/80 text-sm font-semibold"
                      initial={{ scale: 1 }}
                      animate={{ scale: [1, 1.1, 1] }}
                      transition={{ duration: 0.5, delay: 0.3 }}
                    >
                      +{amount.toLocaleString()} 칩
                    </motion.div>
                  </div>
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* 메인 카드 디스플레이 */}
          <motion.div 
            className="bg-gray-900/95 backdrop-blur-md rounded-2xl p-6 border border-yellow-500/30 shadow-2xl"
            variants={winnerGlow}
            initial="initial"
            animate="highlight"
          >
            {/* 족보 이름 */}
            <div className="text-center mb-4">
              <motion.div 
                className="text-yellow-400 font-bold text-2xl"
                animate={{ 
                  textShadow: [
                    '0 0 10px rgba(250, 204, 21, 0.5)',
                    '0 0 20px rgba(250, 204, 21, 0.8)',
                    '0 0 10px rgba(250, 204, 21, 0.5)',
                  ],
                }}
                transition={{ duration: 1.5, repeat: Infinity }}
              >
                {handResult?.name || ''}
              </motion.div>
              <div className="text-gray-400 text-sm">
                {handResult?.description || ''}
              </div>
            </div>

            {/* 홀카드 */}
            <div className="mb-4">
              <div className="text-xs text-gray-500 mb-2 text-center">홀카드</div>
              <div className="flex justify-center gap-2">
                {holeCards.map((card, i) => (
                  <HighlightedCard
                    key={`hole-${i}`}
                    card={card}
                    isWinning={isWinningCard(card, winningCards)}
                    delay={i * 150}
                  />
                ))}
              </div>
            </div>

            {/* 커뮤니티 카드 */}
            <div>
              <div className="text-xs text-gray-500 mb-2 text-center">커뮤니티 카드</div>
              <div className="flex justify-center gap-2">
                {communityCards.map((card, i) => (
                  <HighlightedCard
                    key={`community-${i}`}
                    card={card}
                    isWinning={isWinningCard(card, winningCards)}
                    delay={300 + i * 150}
                  />
                ))}
              </div>
            </div>

            {/* 승리 족보 5장 표시 */}
            <div className="mt-6 pt-4 border-t border-gray-700">
              <div className="text-xs text-gray-500 mb-2 text-center">승리 족보 (Best 5)</div>
              <div className="flex justify-center gap-1">
                {winningCards.map((card, i) => (
                  <HighlightedCard
                    key={`winning-${i}`}
                    card={card}
                    isWinning={true}
                    delay={800 + i * 100}
                  />
                ))}
              </div>
            </div>

            {/* 스플릿 팟 인디케이터 */}
            {isSplitPot && (
              <div className="mt-4 flex justify-center gap-1">
                {winnersWithHands.map((_, i) => (
                  <motion.div
                    key={i}
                    className="w-2 h-2 rounded-full"
                    initial={{ scale: 1, backgroundColor: '#4B5563' }}
                    animate={{ 
                      scale: i === currentWinnerIndex ? 1.25 : 1,
                      backgroundColor: i <= currentWinnerIndex ? '#FACC15' : '#4B5563',
                    }}
                    transition={{ duration: 0.3 }}
                  />
                ))}
              </div>
            )}
          </motion.div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
