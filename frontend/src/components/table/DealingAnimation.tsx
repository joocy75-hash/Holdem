'use client';

import { useState, useEffect, useRef } from 'react';
import { PlayingCard } from './PlayingCard';

interface DealingAnimationProps {
  isDealing: boolean;
  dealingSequence: { position: number; cardIndex: number }[];
  onDealingComplete: () => void;
  tableCenter: { x: number; y: number };
  playerPositions: Record<number, { x: number; y: number }>;
}

export function DealingAnimation({
  isDealing,
  dealingSequence,
  onDealingComplete,
  tableCenter,
  playerPositions,
}: DealingAnimationProps) {
  const [currentDealIndex, setCurrentDealIndex] = useState(-1);
  const [visibleCards, setVisibleCards] = useState<{ position: number; cardIndex: number; key: string }[]>([]);
  const dealingIdRef = useRef(0); // 현재 딜링 세션 ID (동기적 체크용)

  useEffect(() => {
    if (!isDealing || dealingSequence.length === 0) {
      setCurrentDealIndex(-1);
      setVisibleCards([]);
      dealingIdRef.current = 0;
      return;
    }

    // 새로운 딜링 세션 시작 - 고유 ID 생성
    const newDealingId = Date.now();
    dealingIdRef.current = newDealingId;

    // 이전 카드 즉시 제거
    setVisibleCards([]);
    setCurrentDealIndex(-1);

    console.log('🎴 DealingAnimation 시작:', {
      isDealing,
      sequenceLength: dealingSequence.length,
      dealingId: newDealingId,
      tableCenter,
      playerPositions,
      positionKeys: Object.keys(playerPositions),
    });

    // 딜링 시작
    let index = 0;

    const dealNextCard = () => {
      // 딜링 ID가 변경되었으면 중단 (새 딜링이 시작됨)
      if (dealingIdRef.current !== newDealingId) {
        console.log('🎴 딜링 취소 (새 딜링 시작됨)');
        return;
      }

      if (index >= dealingSequence.length) {
        // 모든 카드 딜링 완료
        console.log('🎴 딜링 완료');
        setTimeout(() => {
          if (dealingIdRef.current === newDealingId) {
            onDealingComplete();
          }
        }, 400);
        return;
      }

      const deal = dealingSequence[index];
      const target = playerPositions[deal.position];
      console.log(`🎴 카드 딜링 [${index}]:`, { deal, target });

      const currentIndex = index;
      const cardKey = `${newDealingId}-${currentIndex}`;

      // 중복 체크 후 추가
      setVisibleCards(prev => {
        if (prev.some(c => c.key === cardKey)) {
          return prev; // 이미 있으면 추가하지 않음
        }
        return [...prev, { ...deal, key: cardKey }];
      });
      setCurrentDealIndex(currentIndex);
      index++;

      // 다음 카드 딜링 (0.15초 간격)
      setTimeout(dealNextCard, 150);
    };

    // 첫 카드 딜링 시작 (약간의 지연으로 상태 정리 시간 확보)
    const startTimer = setTimeout(dealNextCard, 150);

    // Cleanup
    return () => {
      clearTimeout(startTimer);
    };
  }, [isDealing, dealingSequence, onDealingComplete, tableCenter, playerPositions]);

  if (!isDealing) return null;

  console.log('🎴 DealingAnimation 렌더링:', { visibleCards: visibleCards.length, tableCenter });

  return (
    <div className="absolute inset-0 pointer-events-none z-50">
      {visibleCards.map((deal, idx) => {
        const target = playerPositions[deal.position];
        if (!target) return null;

        const deltaX = target.x - tableCenter.x;
        const deltaY = target.y - tableCenter.y;

        return (
          <div
            key={deal.key}
            className="dealing-card animating"
            style={{
              left: tableCenter.x,
              top: tableCenter.y,
              width: '36px',
              height: '50px',
              '--deal-x': `${deltaX}px`,
              '--deal-y': `${deltaY}px`,
              '--deal-rotate': `${(deal.cardIndex === 0 ? -5 : 5)}deg`,
            } as React.CSSProperties}
          >
            <div className="w-full h-full">
              <PlayingCard faceDown />
            </div>
          </div>
        );
      })}
    </div>
  );
}

// 딜링 시퀀스 계산 함수 (SB부터 시계방향, 한 장씩 2바퀴)
export function calculateDealingSequence(
  activePlayers: number[],
  sbPosition: number | null
): { position: number; cardIndex: number }[] {
  if (activePlayers.length === 0) return [];

  // SB부터 시작하도록 정렬
  const sorted = [...activePlayers].sort((a, b) => a - b);
  const sbIndex = sbPosition !== null ? sorted.indexOf(sbPosition) : 0;
  const orderedPlayers = [
    ...sorted.slice(sbIndex),
    ...sorted.slice(0, sbIndex)
  ];

  // 2바퀴 (첫 번째 카드 -> 두 번째 카드)
  const sequence: { position: number; cardIndex: number }[] = [];
  for (let cardIndex = 0; cardIndex < 2; cardIndex++) {
    for (const position of orderedPlayers) {
      sequence.push({ position, cardIndex });
    }
  }
  return sequence;
}
