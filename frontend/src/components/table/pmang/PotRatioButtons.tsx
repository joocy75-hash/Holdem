'use client';

import { useState, useCallback, useMemo } from 'react';

interface PotRatioButtonsProps {
  potAmount: number;
  playerStack: number;
  minBet: number;
  currentBet?: number;
  onBetSelect: (amount: number) => void;
  disabled?: boolean;
  className?: string;
}

// 팟 비율 버튼 설정
const POT_RATIOS = [
  { ratio: 0.25, label: '1/4' },
  { ratio: 0.5, label: '1/2' },
  { ratio: 0.75, label: '3/4' },
  { ratio: 1, label: 'Pot' },
];

/**
 * 피망 스타일 베팅 편의 버튼
 * - 1/4 Pot, 1/2 Pot, 3/4 Pot, Pot 버튼
 * - 팟 금액에 따른 실시간 계산
 * - 스택 초과 시 자동 조정 (올인 표시)
 */
export default function PotRatioButtons({
  potAmount,
  playerStack,
  minBet,
  currentBet = 0,
  onBetSelect,
  disabled = false,
  className = '',
}: PotRatioButtonsProps) {
  const [selectedRatio, setSelectedRatio] = useState<number | null>(null);
  const [hoveredRatio, setHoveredRatio] = useState<number | null>(null);

  // 각 비율에 대한 베팅 금액 계산
  const betAmounts = useMemo(() => {
    return POT_RATIOS.map(({ ratio }) => {
      // 팟 비율 베팅 = (현재 팟 + 콜 금액) * 비율
      const effectivePot = potAmount + currentBet;
      let amount = Math.floor(effectivePot * ratio);
      
      // 최소 베팅 금액 보장
      amount = Math.max(amount, minBet);
      
      // 스택 초과 시 올인 금액으로 조정
      const isAllIn = amount >= playerStack;
      const finalAmount = isAllIn ? playerStack : amount;
      
      return {
        ratio,
        amount: finalAmount,
        isAllIn,
        isDisabled: finalAmount < minBet || playerStack <= 0,
      };
    });
  }, [potAmount, playerStack, minBet, currentBet]);

  // 버튼 클릭 핸들러
  const handleClick = useCallback((ratio: number, amount: number) => {
    if (disabled) return;
    setSelectedRatio(ratio);
    onBetSelect(amount);
    
    // 선택 효과 후 리셋
    setTimeout(() => setSelectedRatio(null), 300);
  }, [disabled, onBetSelect]);

  // 금액 포맷팅
  const formatAmount = (amount: number): string => {
    if (amount >= 1000000) {
      return `${(amount / 1000000).toFixed(1)}M`;
    }
    if (amount >= 1000) {
      return `${(amount / 1000).toFixed(1)}K`;
    }
    return amount.toLocaleString();
  };

  return (
    <div 
      className={`flex gap-2 ${className}`}
      data-testid="pot-ratio-buttons"
    >
      {POT_RATIOS.map(({ ratio, label }, index) => {
        const { amount, isAllIn, isDisabled } = betAmounts[index];
        const isSelected = selectedRatio === ratio;
        const isHovered = hoveredRatio === ratio;
        
        return (
          <button
            key={ratio}
            onClick={() => handleClick(ratio, amount)}
            onMouseEnter={() => setHoveredRatio(ratio)}
            onMouseLeave={() => setHoveredRatio(null)}
            disabled={disabled || isDisabled}
            className={`
              relative flex flex-col items-center justify-center
              min-w-[60px] h-[52px] px-3 py-1.5
              rounded-lg font-semibold text-sm
              transition-all duration-200 ease-out
              border-2
              ${isSelected 
                ? 'bg-orange-500 border-orange-400 text-white scale-95 shadow-lg shadow-orange-500/30' 
                : isHovered
                  ? 'bg-orange-500/20 border-orange-500/50 text-orange-400'
                  : 'bg-gray-800/80 border-gray-600/50 text-gray-300 hover:border-orange-500/30'
              }
              ${isDisabled || disabled
                ? 'opacity-40 cursor-not-allowed'
                : 'cursor-pointer active:scale-95'
              }
            `}
            data-testid={`pot-ratio-${ratio}`}
          >
            {/* 비율 라벨 */}
            <span className={`text-xs font-bold ${isAllIn ? 'text-red-400' : ''}`}>
              {isAllIn ? 'ALL IN' : label}
            </span>
            
            {/* 금액 표시 */}
            <span className={`text-[10px] ${isAllIn ? 'text-red-300' : 'text-gray-400'}`}>
              {formatAmount(amount)}
            </span>

            {/* 선택 시 반짝임 효과 */}
            {isSelected && (
              <div className="absolute inset-0 rounded-lg bg-white/20 animate-ping-once" />
            )}

            {/* 호버 시 툴팁 */}
            {isHovered && !isSelected && (
              <div className="absolute -top-10 left-1/2 -translate-x-1/2 px-2 py-1 bg-black/90 text-white text-xs rounded whitespace-nowrap z-10 animate-fade-in">
                {amount.toLocaleString()} 칩
                <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-black/90 rotate-45" />
              </div>
            )}
          </button>
        );
      })}

      {/* 올인 버튼 (별도) */}
      <button
        onClick={() => handleClick(999, playerStack)}
        onMouseEnter={() => setHoveredRatio(999)}
        onMouseLeave={() => setHoveredRatio(null)}
        disabled={disabled || playerStack <= 0}
        className={`
          relative flex flex-col items-center justify-center
          min-w-[60px] h-[52px] px-3 py-1.5
          rounded-lg font-bold text-sm
          transition-all duration-200 ease-out
          border-2
          ${selectedRatio === 999
            ? 'bg-red-600 border-red-500 text-white scale-95 shadow-lg shadow-red-500/30'
            : hoveredRatio === 999
              ? 'bg-red-600/20 border-red-500/50 text-red-400'
              : 'bg-gradient-to-b from-red-600/80 to-red-700/80 border-red-500/50 text-white hover:from-red-500/80 hover:to-red-600/80'
          }
          ${disabled || playerStack <= 0
            ? 'opacity-40 cursor-not-allowed'
            : 'cursor-pointer active:scale-95'
          }
        `}
        data-testid="pot-ratio-allin"
      >
        <span className="text-xs font-bold">ALL IN</span>
        <span className="text-[10px] text-red-200">
          {formatAmount(playerStack)}
        </span>
      </button>
    </div>
  );
}
