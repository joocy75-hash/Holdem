'use client';

import { useState, useCallback, useRef, useEffect } from 'react';

interface Card {
  rank: string;
  suit: string;
}

interface CardSqueezeProps {
  cards: Card[];
  onRevealComplete?: (cardIndex: number) => void;
  disabled?: boolean;
  className?: string;
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

// 드래그 임계값 (픽셀)
const REVEAL_THRESHOLD = 80;
const SNAP_BACK_DURATION = 300;

/**
 * 피망 스타일 카드 쪼기 컴포넌트
 * - 드래그로 카드 점진적 공개
 * - 임계값 미달 시 Snap Back
 * - 쪼기 중 다른 UI 잠금
 */
export default function CardSqueeze({
  cards,
  onRevealComplete,
  disabled = false,
  className = '',
}: CardSqueezeProps) {
  const [revealedCards, setRevealedCards] = useState<Set<number>>(new Set());
  const [activeCardIndex, setActiveCardIndex] = useState<number | null>(null);
  const [dragProgress, setDragProgress] = useState(0);
  const [isSnappingBack, setIsSnappingBack] = useState(false);
  
  const containerRef = useRef<HTMLDivElement>(null);
  const startYRef = useRef<number>(0);
  const isDraggingRef = useRef(false);

  // UI 잠금 상태 전파
  useEffect(() => {
    if (activeCardIndex !== null) {
      document.body.setAttribute('data-ui-locked', 'true');
    } else {
      document.body.removeAttribute('data-ui-locked');
    }
    return () => {
      document.body.removeAttribute('data-ui-locked');
    };
  }, [activeCardIndex]);

  // 드래그 시작
  const handleDragStart = useCallback((index: number, clientY: number) => {
    if (disabled || revealedCards.has(index)) return;
    
    setActiveCardIndex(index);
    startYRef.current = clientY;
    isDraggingRef.current = true;
    setDragProgress(0);
  }, [disabled, revealedCards]);

  // 드래그 중
  const handleDragMove = useCallback((clientY: number) => {
    if (!isDraggingRef.current || activeCardIndex === null) return;
    
    const deltaY = startYRef.current - clientY;
    const progress = Math.max(0, Math.min(1, deltaY / REVEAL_THRESHOLD));
    setDragProgress(progress);
  }, [activeCardIndex]);

  // 드래그 종료
  const handleDragEnd = useCallback(() => {
    if (!isDraggingRef.current || activeCardIndex === null) return;
    
    isDraggingRef.current = false;
    
    if (dragProgress >= 1) {
      // 임계값 도달 - 카드 공개
      setRevealedCards(prev => new Set([...prev, activeCardIndex]));
      onRevealComplete?.(activeCardIndex);
      setActiveCardIndex(null);
      setDragProgress(0);
    } else {
      // 임계값 미달 - Snap Back
      setIsSnappingBack(true);
      setTimeout(() => {
        setDragProgress(0);
        setActiveCardIndex(null);
        setIsSnappingBack(false);
      }, SNAP_BACK_DURATION);
    }
  }, [activeCardIndex, dragProgress, onRevealComplete]);

  // 마우스 이벤트 핸들러
  const handleMouseDown = (index: number) => (e: React.MouseEvent) => {
    e.preventDefault();
    handleDragStart(index, e.clientY);
  };

  // 터치 이벤트 핸들러
  const handleTouchStart = (index: number) => (e: React.TouchEvent) => {
    handleDragStart(index, e.touches[0].clientY);
  };

  // 전역 이벤트 리스너
  useEffect(() => {
    const handleGlobalMouseMove = (e: MouseEvent) => {
      handleDragMove(e.clientY);
    };
    
    const handleGlobalMouseUp = () => {
      handleDragEnd();
    };
    
    const handleGlobalTouchMove = (e: TouchEvent) => {
      if (isDraggingRef.current) {
        e.preventDefault();
        handleDragMove(e.touches[0].clientY);
      }
    };
    
    const handleGlobalTouchEnd = () => {
      handleDragEnd();
    };

    document.addEventListener('mousemove', handleGlobalMouseMove);
    document.addEventListener('mouseup', handleGlobalMouseUp);
    document.addEventListener('touchmove', handleGlobalTouchMove, { passive: false });
    document.addEventListener('touchend', handleGlobalTouchEnd);

    return () => {
      document.removeEventListener('mousemove', handleGlobalMouseMove);
      document.removeEventListener('mouseup', handleGlobalMouseUp);
      document.removeEventListener('touchmove', handleGlobalTouchMove);
      document.removeEventListener('touchend', handleGlobalTouchEnd);
    };
  }, [handleDragMove, handleDragEnd]);

  // 카드 렌더링
  const renderCard = (card: Card, index: number) => {
    const isRevealed = revealedCards.has(index);
    const isActive = activeCardIndex === index;
    const suitLower = card.suit.toLowerCase();
    const suitSymbol = SUIT_SYMBOLS[suitLower] || card.suit;
    const suitColor = SUIT_COLORS[suitLower] || 'text-gray-900';
    
    // 공개 진행률 계산
    const revealProgress = isRevealed ? 1 : (isActive ? dragProgress : 0);
    const maskHeight = `${(1 - revealProgress) * 100}%`;

    return (
      <div
        key={index}
        className={`
          relative w-[70px] h-[100px] rounded-xl cursor-pointer
          select-none touch-none
          transition-transform duration-200
          ${isActive ? 'scale-105 z-10' : ''}
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        `}
        onMouseDown={handleMouseDown(index)}
        onTouchStart={handleTouchStart(index)}
        data-testid={`hole-card-${index}`}
        data-revealed={isRevealed ? 'true' : 'false'}
      >
        {/* 카드 뒷면 */}
        <div 
          className={`
            absolute inset-0 rounded-xl
            bg-gradient-to-br from-blue-800 to-blue-900
            border-2 border-blue-600
            shadow-lg
            ${isSnappingBack && isActive ? 'transition-all duration-300' : ''}
          `}
          style={{
            clipPath: `inset(0 0 ${100 - parseFloat(maskHeight)}% 0)`,
          }}
        >
          {/* 카드 뒷면 패턴 */}
          <div className="absolute inset-2 rounded-lg border border-blue-500/30 bg-blue-700/20">
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-8 h-8 rounded-full border-2 border-blue-400/50" />
            </div>
          </div>
        </div>

        {/* 카드 앞면 (점진적 공개) */}
        <div 
          className={`
            absolute inset-0 rounded-xl bg-white
            border-2 border-gray-200
            shadow-lg overflow-hidden
            ${isSnappingBack && isActive ? 'transition-all duration-300' : ''}
          `}
          style={{
            clipPath: `inset(${maskHeight} 0 0 0)`,
          }}
        >
          {/* 카드 내용 */}
          <div className={`
            flex flex-col items-center justify-center h-full
            font-bold ${suitColor}
          `}>
            <span className="text-2xl leading-none">{card.rank}</span>
            <span className="text-3xl leading-none mt-1">{suitSymbol}</span>
          </div>

          {/* 코너 표시 */}
          <div className={`absolute top-1 left-1.5 text-xs ${suitColor}`}>
            <div className="leading-none font-bold">{card.rank}</div>
            <div className="leading-none text-sm">{suitSymbol}</div>
          </div>
          <div className={`absolute bottom-1 right-1.5 text-xs ${suitColor} rotate-180`}>
            <div className="leading-none font-bold">{card.rank}</div>
            <div className="leading-none text-sm">{suitSymbol}</div>
          </div>
        </div>

        {/* 드래그 힌트 */}
        {!isRevealed && !isActive && (
          <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-[10px] text-gray-400 whitespace-nowrap animate-pulse">
            ↑ 드래그하여 공개
          </div>
        )}

        {/* 진행률 표시 */}
        {isActive && (
          <div className="absolute -right-2 top-0 bottom-0 w-1 bg-gray-700 rounded-full overflow-hidden">
            <div 
              className="absolute bottom-0 w-full bg-gradient-to-t from-green-500 to-green-400 transition-all duration-75"
              style={{ height: `${revealProgress * 100}%` }}
            />
          </div>
        )}

        {/* 공개 완료 효과 */}
        {isRevealed && (
          <div className="absolute inset-0 rounded-xl ring-2 ring-yellow-400/50 animate-pulse-once pointer-events-none" />
        )}
      </div>
    );
  };

  return (
    <div 
      ref={containerRef}
      className={`flex gap-4 ${className}`}
      data-testid="my-hole-cards"
    >
      {cards.map((card, index) => renderCard(card, index))}
    </div>
  );
}
