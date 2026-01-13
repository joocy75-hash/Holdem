'use client';

import { useState, useEffect, useMemo, useRef } from 'react';
import { HAND_RANKS, evaluateHand, evaluateDraws } from '@/lib/handEvaluator';

interface Card {
  rank: string;
  suit: string;
}

interface HandRankingGuideProps {
  holeCards: Card[];
  communityCards: Card[];
  isVisible?: boolean;
  position?: 'top' | 'bottom' | 'left' | 'right';
}

// 족보 순위 정보 (낮은 순서부터)
const HAND_RANKINGS = [
  { rank: 1, name: '하이카드', nameEn: 'High Card', color: 'text-gray-400' },
  { rank: 2, name: '원페어', nameEn: 'One Pair', color: 'text-blue-400' },
  { rank: 3, name: '투페어', nameEn: 'Two Pair', color: 'text-blue-500' },
  { rank: 4, name: '트리플', nameEn: 'Three of a Kind', color: 'text-green-400' },
  { rank: 5, name: '스트레이트', nameEn: 'Straight', color: 'text-green-500' },
  { rank: 6, name: '플러시', nameEn: 'Flush', color: 'text-purple-400' },
  { rank: 7, name: '풀하우스', nameEn: 'Full House', color: 'text-purple-500' },
  { rank: 8, name: '포카드', nameEn: 'Four of a Kind', color: 'text-yellow-400' },
  { rank: 9, name: '스트레이트 플러시', nameEn: 'Straight Flush', color: 'text-orange-400' },
  { rank: 10, name: '로얄 플러시', nameEn: 'Royal Flush', color: 'text-red-500' },
];

// 드로우 가능성 분석
function analyzePossibleHands(holeCards: Card[], communityCards: Card[]): number[] {
  const allCards = [...holeCards, ...communityCards];
  const possibleRanks: number[] = [];
  
  if (allCards.length < 2) return possibleRanks;
  
  // 현재 족보 평가
  const currentHand = evaluateHand(allCards);
  if (currentHand) {
    possibleRanks.push(currentHand.rank);
  }
  
  // 드로우 가능성 분석 (플롭/턴에서만)
  if (communityCards.length >= 3 && communityCards.length < 5) {
    const draws = evaluateDraws(allCards);
    
    // 플러시 드로우가 있으면 플러시 가능
    if (draws.includes('플러시 드로우')) {
      possibleRanks.push(HAND_RANKS.FLUSH);
    }
    
    // 스트레이트 드로우가 있으면 스트레이트 가능
    if (draws.includes('오픈엔드 스트레이트 드로우') || draws.includes('거셧 스트레이트 드로우')) {
      possibleRanks.push(HAND_RANKS.STRAIGHT);
    }
  }
  
  return [...new Set(possibleRanks)].sort((a, b) => a - b);
}

/**
 * 피망 스타일 족보 가이드 UI
 * - 현재 족보와 가능한 족보를 실시간으로 표시
 * - 홀카드 2장 받았을 때 현재 족보 표시
 * - 커뮤니티 카드 오픈 시 족보 업데이트
 * - 족보 변경 시 애니메이션
 */
export default function HandRankingGuide({
  holeCards,
  communityCards,
  isVisible = true,
  position = 'right',
}: HandRankingGuideProps) {
  const [isAnimating, setIsAnimating] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  
  // 이전 랭크 추적용 ref
  const previousRankRef = useRef<number | null>(null);

  // 현재 핸드 분석
  const handAnalysis = useMemo(() => {
    if (holeCards.length === 0) return null;
    const allCards = [...holeCards, ...communityCards];
    return evaluateHand(allCards);
  }, [holeCards, communityCards]);

  // 드로우 가능성 분석
  const draws = useMemo(() => {
    if (holeCards.length === 0 || communityCards.length < 3 || communityCards.length >= 5) {
      return [];
    }
    const allCards = [...holeCards, ...communityCards];
    return evaluateDraws(allCards);
  }, [holeCards, communityCards]);

  // 가능한 족보 분석
  const possibleRanks = useMemo(() => {
    return analyzePossibleHands(holeCards, communityCards);
  }, [holeCards, communityCards]);

  // 족보 변경 감지 및 애니메이션 - requestAnimationFrame 사용
  useEffect(() => {
    if (handAnalysis && handAnalysis.rank !== previousRankRef.current) {
      if (previousRankRef.current !== null && handAnalysis.rank > previousRankRef.current) {
        // 족보가 상승했을 때 애니메이션 - 다음 프레임에서 실행
        requestAnimationFrame(() => {
          setIsAnimating(true);
          setTimeout(() => setIsAnimating(false), 1000);
        });
      }
      previousRankRef.current = handAnalysis.rank;
    }
  }, [handAnalysis]);

  if (!isVisible || holeCards.length === 0) {
    return null;
  }

  const positionClasses = {
    top: 'top-4 left-1/2 -translate-x-1/2',
    bottom: 'bottom-4 left-1/2 -translate-x-1/2',
    left: 'left-4 top-1/2 -translate-y-1/2',
    right: 'right-2 top-[15%]',
  };

  return (
    <div
      className={`absolute ${positionClasses[position]} z-30 transition-all duration-300`}
      data-testid="hand-ranking-guide"
    >
      {/* 컴팩트 뷰 (기본) */}
      <div
        className={`
          bg-black/80 backdrop-blur-md rounded-xl border border-purple-500/30
          shadow-lg shadow-purple-500/20 cursor-pointer
          transition-all duration-300 hover:border-purple-500/50
          ${isAnimating ? 'animate-hand-upgrade' : ''}
        `}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {/* 현재 족보 표시 */}
        <div className="px-3 py-2">
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-400">현재 족보</span>
            {draws.length > 0 && (
              <span className="px-1.5 py-0.5 bg-cyan-500/20 text-cyan-400 text-[10px] rounded">
                드로우
              </span>
            )}
          </div>
          <div 
            className={`text-sm font-bold mt-0.5 ${
              handAnalysis ? HAND_RANKINGS.find(h => h.rank === handAnalysis.rank)?.color : 'text-white'
            }`}
            data-testid="current-hand-rank"
            data-rank={handAnalysis?.rank}
          >
            {handAnalysis?.name || '분석 중...'}
          </div>
          {handAnalysis?.description && (
            <div className="text-xs text-gray-400 mt-0.5">
              {handAnalysis.description}
            </div>
          )}
          
          {/* 드로우 표시 */}
          {draws.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {draws.map((draw, i) => (
                <span
                  key={i}
                  className="px-2 py-0.5 bg-cyan-500/20 text-cyan-400 text-xs rounded-full"
                >
                  {draw}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* 확장 뷰 (클릭 시) */}
        {isExpanded && (
          <div className="border-t border-purple-500/20 px-4 py-3 animate-slide-down">
            <div className="text-xs text-gray-400 mb-2">족보 순위</div>
            <div className="space-y-1">
              {HAND_RANKINGS.slice().reverse().map((hand) => {
                const isCurrent = handAnalysis?.rank === hand.rank;
                const isPossible = possibleRanks.includes(hand.rank);
                
                return (
                  <div
                    key={hand.rank}
                    className={`
                      flex items-center justify-between px-2 py-1 rounded
                      transition-all duration-200
                      ${isCurrent ? 'bg-purple-500/30 border border-purple-500/50' : ''}
                      ${isPossible && !isCurrent ? 'bg-cyan-500/10' : ''}
                      ${!isCurrent && !isPossible ? 'opacity-40' : ''}
                    `}
                  >
                    <span className={`text-xs ${hand.color}`}>
                      {hand.name}
                    </span>
                    <div className="flex items-center gap-1">
                      {isCurrent && (
                        <span className="text-[10px] text-purple-400 font-bold">현재</span>
                      )}
                      {isPossible && !isCurrent && (
                        <span className="text-[10px] text-cyan-400">가능</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* 족보 상승 애니메이션 오버레이 */}
      {isAnimating && (
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute inset-0 bg-gradient-to-t from-yellow-500/30 to-transparent animate-pulse rounded-xl" />
          <div className="absolute -top-8 left-1/2 -translate-x-1/2 text-yellow-400 font-bold text-sm animate-float-up">
            ↑ 족보 상승!
          </div>
        </div>
      )}
    </div>
  );
}
