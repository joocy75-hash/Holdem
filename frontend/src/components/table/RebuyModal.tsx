'use client';

import { useState } from 'react';

interface RebuyModalProps {
  isOpen: boolean;
  onRebuy: (amount: number) => void;
  onLeave: () => void;
  onSpectate: () => void;
  minBuyIn: number;
  maxBuyIn: number;
  defaultBuyIn: number;
}

export function RebuyModal({
  isOpen,
  onRebuy,
  onLeave,
  onSpectate,
  minBuyIn,
  maxBuyIn,
  defaultBuyIn,
}: RebuyModalProps) {
  const [rebuyAmount, setRebuyAmount] = useState(defaultBuyIn);

  if (!isOpen) return null;

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setRebuyAmount(Number(e.target.value));
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center">
      {/* 반투명 배경 */}
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />

      {/* 모달 컨테이너 */}
      <div className="relative w-[340px] bg-gradient-to-b from-[#1a1a2e] to-[#16213e] rounded-2xl shadow-2xl border border-[#4a4a6a]/50 overflow-hidden">
        {/* 헤더 */}
        <div className="px-6 py-4 bg-gradient-to-r from-red-600/20 to-orange-600/20 border-b border-white/10">
          <h2 className="text-xl font-bold text-white text-center">
            칩이 부족합니다
          </h2>
          <p className="text-sm text-gray-400 text-center mt-1">
            다음 핸드에 참여하려면 리바이가 필요합니다
          </p>
        </div>

        {/* 본문 */}
        <div className="p-6 space-y-6">
          {/* 리바이 금액 선택 */}
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">리바이 금액</span>
              <span className="text-lg font-bold text-[var(--accent)]">
                {rebuyAmount.toLocaleString()}
              </span>
            </div>

            {/* 슬라이더 */}
            <input
              type="range"
              min={minBuyIn}
              max={maxBuyIn}
              step={100}
              value={rebuyAmount}
              onChange={handleSliderChange}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-green-500"
            />

            {/* 최소/최대 표시 */}
            <div className="flex justify-between text-xs text-gray-500">
              <span>{minBuyIn.toLocaleString()}</span>
              <span>{maxBuyIn.toLocaleString()}</span>
            </div>
          </div>

          {/* 버튼들 */}
          <div className="space-y-3">
            {/* 리바이 버튼 (강조) */}
            <button
              onClick={() => onRebuy(rebuyAmount)}
              className="w-full py-3 px-4 bg-gradient-to-r from-green-600 to-green-500 hover:from-green-500 hover:to-green-400 text-white font-bold rounded-xl shadow-lg shadow-green-500/30 transition-all duration-200 transform hover:scale-[1.02]"
            >
              리바이 ({rebuyAmount.toLocaleString()})
            </button>

            {/* 구분선 */}
            <div className="flex items-center gap-3">
              <div className="flex-1 h-px bg-gray-600" />
              <span className="text-xs text-gray-500">또는</span>
              <div className="flex-1 h-px bg-gray-600" />
            </div>

            {/* 나가기 / 구경하기 버튼 */}
            <div className="flex gap-3">
              <button
                onClick={onLeave}
                className="flex-1 py-2.5 px-4 bg-gray-700 hover:bg-gray-600 text-gray-300 font-medium rounded-xl transition-colors"
              >
                나가기
              </button>
              <button
                onClick={onSpectate}
                className="flex-1 py-2.5 px-4 bg-gray-700 hover:bg-gray-600 text-gray-300 font-medium rounded-xl transition-colors"
              >
                구경하기
              </button>
            </div>
          </div>
        </div>

        {/* 푸터 안내문 */}
        <div className="px-6 py-3 bg-black/30 border-t border-white/5">
          <p className="text-xs text-gray-500 text-center">
            구경하기를 선택하면 칩 없이 게임을 관전할 수 있습니다
          </p>
        </div>
      </div>
    </div>
  );
}
