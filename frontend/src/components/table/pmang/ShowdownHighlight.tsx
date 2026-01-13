'use client';

import { useState, useEffect, useMemo } from 'react';
import { evaluateHand, HandResult } from '@/lib/handEvaluator';

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
 * 하이라이트된 카드 컴포넌트
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
  const [isRevealed, setIsRevealed] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setIsRevealed(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);

  const suitLower = card.suit.toLowerCase();
  const suitSymbol = SUIT_SYMBOLS[suitLower] || card.suit;
  const suitColor = SUIT_COLORS[suitLower] || 'text-gray-900';

  return (
    <div
      className={`
        relative w-[44px] h-[62px] rounded-lg
        transition-all duration-500 ease-out
        ${isRevealed ? 'opacity-100 scale-100' : 'opacity-0 scale-75'}
        ${isWinning 
          ? 'ring-2 ring-yellow-400 shadow-lg shadow-yellow-400/50 z-10' 
          : 'opacity-40 grayscale'
        }
      `}
      style={{ transitionDelay: `${delay}ms` }}
    >
      {/* 카드 배경 */}
      <div className={`
        absolute inset-0 rounded-lg bg-white
        ${isWinning ? 'bg-gradient-to-br from-white to-yellow-50' : ''}
      `} />

      {/* 카드 내용 */}
      <div className={`
        relative flex flex-col items-center justify-center h-full
        font-bold ${suitColor}
      `}>
        <span className="text-lg leading-none">{card.rank}</span>
        <span className="text-xl leading-none">{suitSymbol}</span>
      </div>

      {/* 승리 카드 글로우 효과 */}
      {isWinning && (
        <div className="absolute inset-0 rounded-lg animate-pulse-glow pointer-events-none" />
      )}
    </div>
  );
}

/**
 * 피망 스타일 쇼다운 하이라이트
 * - 승리 족보 5장만 밝게 강조
 * - 비사용 카드 딤 처리
 * - 스플릿 팟 시 각 승자 개별 하이라이트
 */
export default function ShowdownHighlight({
  winners,
  communityCards,
  isActive,
  onAnimationComplete,
}: ShowdownHighlightProps) {
  const [currentWinnerIndex, setCurrentWinnerIndex] = useState(0);
  const [showWinnerBanner, setShowWinnerBanner] = useState(false);

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
        // 모든 승자 표시 완료
        setTimeout(() => {
          onAnimationComplete?.();
        }, 2000);
      }
    }, 4000);

    return () => {
      clearTimeout(bannerTimer);
      clearTimeout(nextWinnerTimer);
    };
  }, [isActive, currentWinnerIndex, winnersWithHands.length, onAnimationComplete]);

  // 리셋 - requestAnimationFrame 사용하여 cascading render 방지
  useEffect(() => {
    if (!isActive) {
      requestAnimationFrame(() => {
        setCurrentWinnerIndex(0);
        setShowWinnerBanner(false);
      });
    }
  }, [isActive]);

  if (!isActive || !currentWinner) {
    return null;
  }

  const { holeCards, winningCards, handResult, amount } = currentWinner;
  const isSplitPot = winnersWithHands.length > 1;

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 animate-fade-in"
      data-testid="showdown-highlight"
    >
      <div className="relative max-w-lg w-full mx-4">
        {/* 승자 배너 */}
        {showWinnerBanner && (
          <div className="absolute -top-16 left-1/2 -translate-x-1/2 animate-bounce-in">
            <div className="px-6 py-3 bg-gradient-to-r from-yellow-500 via-yellow-400 to-yellow-500 rounded-xl shadow-2xl shadow-yellow-500/50">
              <div className="text-center">
                <div className="text-black font-bold text-xl">
                  🏆 {isSplitPot ? `승자 ${currentWinnerIndex + 1}/${winnersWithHands.length}` : 'WINNER!'}
                </div>
                <div className="text-black/80 text-sm font-semibold">
                  +{amount.toLocaleString()} 칩
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 메인 카드 디스플레이 */}
        <div className="bg-gray-900/95 backdrop-blur-md rounded-2xl p-6 border border-yellow-500/30 shadow-2xl">
          {/* 족보 이름 */}
          <div className="text-center mb-4">
            <div className="text-yellow-400 font-bold text-2xl animate-pulse">
              {handResult?.name || ''}
            </div>
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
                <div
                  key={i}
                  className={`w-2 h-2 rounded-full transition-all duration-300 ${
                    i === currentWinnerIndex 
                      ? 'bg-yellow-400 scale-125' 
                      : i < currentWinnerIndex 
                        ? 'bg-yellow-400/50' 
                        : 'bg-gray-600'
                  }`}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
