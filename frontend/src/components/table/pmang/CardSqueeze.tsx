'use client';

import { useState, useCallback, useEffect } from 'react';
import { motion, useMotionValue, useTransform, PanInfo, AnimatePresence } from 'framer-motion';
import { 
  CARD_CONSTANTS, 
  snapBackSpring, 
  flipSpring,
} from '@/lib/animations';

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

const { REVEAL_THRESHOLD, PERSPECTIVE, MAX_ROTATION } = CARD_CONSTANTS;

/**
 * 피망 스타일 카드 쪼기 컴포넌트 (Framer Motion 버전)
 * - 3D 휘어짐 효과 (상단 고정, 하단 들어올림)
 * - 동적 그림자 및 광택 효과
 * - "찰싹" Snap-back / "휙" Flip 물리 효과
 * - 드래그 중 UI 잠금
 */
export default function CardSqueeze({
  cards,
  onRevealComplete,
  disabled = false,
  className = '',
}: CardSqueezeProps) {
  const [revealedCards, setRevealedCards] = useState<Set<number>>(new Set());
  const [activeCardIndex, setActiveCardIndex] = useState<number | null>(null);

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

  // 카드 공개 처리
  const handleReveal = useCallback((index: number) => {
    setRevealedCards(prev => new Set([...prev, index]));
    onRevealComplete?.(index);
    setActiveCardIndex(null);
  }, [onRevealComplete]);

  // 드래그 시작
  const handleDragStart = useCallback((index: number) => {
    if (disabled || revealedCards.has(index)) return;
    setActiveCardIndex(index);
  }, [disabled, revealedCards]);

  // 드래그 종료
  const handleDragEnd = useCallback((index: number, info: PanInfo) => {
    if (info.offset.y < -REVEAL_THRESHOLD) {
      // 임계값 초과 - 카드 공개 ("휙")
      handleReveal(index);
    } else {
      // 임계값 미달 - Snap back ("찰싹")
      setActiveCardIndex(null);
    }
  }, [handleReveal]);

  return (
    <div 
      className={`flex gap-4 ${className}`}
      style={{ perspective: PERSPECTIVE }}
      data-testid="my-hole-cards"
    >
      {cards.map((card, index) => (
        <SqueezeCard
          key={index}
          card={card}
          index={index}
          isRevealed={revealedCards.has(index)}
          isActive={activeCardIndex === index}
          isOtherActive={activeCardIndex !== null && activeCardIndex !== index}
          disabled={disabled}
          onDragStart={() => handleDragStart(index)}
          onDragEnd={(info) => handleDragEnd(index, info)}
        />
      ))}
    </div>
  );
}

interface SqueezeCardProps {
  card: Card;
  index: number;
  isRevealed: boolean;
  isActive: boolean;
  isOtherActive: boolean;
  disabled: boolean;
  onDragStart: () => void;
  onDragEnd: (info: PanInfo) => void;
}

function SqueezeCard({
  card,
  index,
  isRevealed,
  isActive,
  isOtherActive,
  disabled,
  onDragStart,
  onDragEnd,
}: SqueezeCardProps) {
  // 드래그 Y 값 추적 - 항상 호출
  const dragY = useMotionValue(0);
  
  // 현재 진행률 상태 (E2E 테스트용)
  const [currentProgress, setCurrentProgress] = useState(0);
  
  // 드래그 Y 값 변경 시 진행률 업데이트
  useEffect(() => {
    const unsubscribe = dragY.on('change', (latest) => {
      const prog = Math.max(0, Math.min(100, (-latest / REVEAL_THRESHOLD) * 100));
      setCurrentProgress(Math.round(prog));
    });
    return () => unsubscribe();
  }, [dragY]);
  
  // 드래그 진행률 (0-1) - 항상 호출
  const progress = useTransform(dragY, [0, -REVEAL_THRESHOLD], [0, 1]);
  
  // 3D 회전 각도 (상단 고정, 하단 들어올림) - 항상 호출
  const rotateX = useTransform(dragY, [0, -REVEAL_THRESHOLD], [0, -MAX_ROTATION]);
  
  // 동적 그림자 (드래그할수록 더 넓고 부드러워짐) - 항상 호출
  const shadowBlur = useTransform(dragY, [0, -REVEAL_THRESHOLD], [4, 30]);
  const shadowY = useTransform(dragY, [0, -REVEAL_THRESHOLD], [2, 20]);
  const shadowOpacity = useTransform(dragY, [0, -REVEAL_THRESHOLD], [0.2, 0.5]);
  
  // 광택 효과 (그라데이션 위치) - 항상 호출
  const glossPosition = useTransform(dragY, [0, -REVEAL_THRESHOLD], [100, 30]);
  
  // 카드 스케일 (드래그 중 약간 확대) - 항상 호출
  const scale = useTransform(dragY, [0, -REVEAL_THRESHOLD / 2], [1, 1.05]);
  
  // 클립 패스 - 항상 호출
  const clipPath = useTransform(progress, v => `inset(${(1 - v) * 100}% 0 0 0)`);
  
  // 그림자 필터 - 항상 호출
  const shadowFilter = useTransform(shadowBlur, v => `blur(${v}px)`);
  
  // 광택 그라데이션 - 항상 호출
  const glossGradient = useTransform(
    glossPosition,
    v => `linear-gradient(180deg, rgba(255,255,255,0.3) 0%, rgba(255,255,255,0) ${v}%)`
  );
  
  // 진행률 높이 - 항상 호출
  const progressHeight = useTransform(progress, v => `${v * 100}%`);

  const suitLower = card.suit.toLowerCase();
  const suitSymbol = SUIT_SYMBOLS[suitLower] || card.suit;
  const suitColor = SUIT_COLORS[suitLower] || 'text-gray-900';

  // 공개된 카드
  if (isRevealed) {
    return (
      <motion.div
        className="relative w-[70px] h-[100px]"
        initial={{ rotateY: 0 }}
        animate={{ rotateY: 180 }}
        transition={flipSpring}
        style={{ transformStyle: 'preserve-3d' }}
        data-testid={`hole-card-${index}`}
        data-revealed="true"
      >
        {/* 카드 앞면 (뒤집힌 상태) */}
        <motion.div 
          className="absolute inset-0 rounded-xl bg-white border-2 border-gray-200 shadow-lg overflow-hidden"
          style={{ 
            backfaceVisibility: 'hidden',
            rotateY: 180,
          }}
        >
          <CardFace card={card} suitSymbol={suitSymbol} suitColor={suitColor} />
        </motion.div>
        
        {/* 공개 완료 효과 */}
        <motion.div 
          className="absolute inset-0 rounded-xl ring-2 ring-yellow-400/50 pointer-events-none"
          initial={{ opacity: 0 }}
          animate={{ opacity: [0, 1, 0.5] }}
          transition={{ duration: 0.6 }}
        />
      </motion.div>
    );
  }

  // 드래그 가능한 카드
  return (
    <motion.div
      className={`
        relative w-[70px] h-[100px] cursor-pointer select-none touch-none
        ${disabled || isOtherActive ? 'opacity-50 cursor-not-allowed pointer-events-none' : ''}
      `}
      style={{ 
        transformStyle: 'preserve-3d',
        transformOrigin: 'center top', // 상단 고정
      }}
      drag={!disabled && !isOtherActive ? 'y' : false}
      dragConstraints={{ top: -REVEAL_THRESHOLD * 1.5, bottom: 0 }}
      dragElastic={0.1}
      onDragStart={onDragStart}
      onDragEnd={(_, info) => onDragEnd(info)}
      whileDrag={{ zIndex: 10 }}
      data-testid={`hole-card-${index}`}
      data-revealed="false"
      data-reveal-percent={currentProgress}
    >
      {/* 3D 카드 컨테이너 */}
      <motion.div
        className="absolute inset-0"
        style={{
          rotateX,
          scale,
          transformStyle: 'preserve-3d',
          transformOrigin: 'center top',
        }}
      >
        {/* 동적 그림자 */}
        <motion.div
          className="absolute inset-0 rounded-xl bg-black/20"
          style={{
            filter: shadowFilter,
            y: shadowY,
            opacity: shadowOpacity,
            transform: 'translateZ(-10px)',
          }}
        />

        {/* 카드 뒷면 */}
        <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-blue-800 to-blue-900 border-2 border-blue-600 shadow-lg overflow-hidden">
          {/* 카드 뒷면 패턴 */}
          <div className="absolute inset-2 rounded-lg border border-blue-500/30 bg-blue-700/20">
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-8 h-8 rounded-full border-2 border-blue-400/50" />
            </div>
          </div>
          
          {/* 광택 효과 (그라데이션 오버레이) */}
          <motion.div
            className="absolute inset-0 pointer-events-none"
            style={{ background: glossGradient }}
          />
        </div>

        {/* 카드 앞면 미리보기 (드래그 시 점진적 공개) */}
        <motion.div
          className="absolute inset-0 rounded-xl bg-white border-2 border-gray-200 overflow-hidden"
          style={{ clipPath }}
        >
          <CardFace card={card} suitSymbol={suitSymbol} suitColor={suitColor} />
        </motion.div>
      </motion.div>

      {/* 드래그 힌트 */}
      <AnimatePresence>
        {!isActive && (
          <motion.div 
            className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-[10px] text-gray-400 whitespace-nowrap"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.span
              animate={{ y: [0, -3, 0] }}
              transition={{ repeat: Infinity, duration: 1.5 }}
            >
              ↑ 드래그하여 공개
            </motion.span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 진행률 표시 */}
      <AnimatePresence>
        {isActive && (
          <motion.div 
            className="absolute -right-2 top-0 bottom-0 w-1 bg-gray-700 rounded-full overflow-hidden"
            initial={{ opacity: 0, x: 5 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 5 }}
            transition={snapBackSpring}
          >
            <motion.div 
              className="absolute bottom-0 w-full bg-gradient-to-t from-green-500 to-green-400"
              style={{ height: progressHeight }}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// 카드 앞면 컴포넌트
function CardFace({ 
  card, 
  suitSymbol, 
  suitColor 
}: { 
  card: Card; 
  suitSymbol: string; 
  suitColor: string;
}) {
  return (
    <>
      {/* 카드 중앙 내용 */}
      <div className={`flex flex-col items-center justify-center h-full font-bold ${suitColor}`}>
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
    </>
  );
}
