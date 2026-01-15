'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { AvailableAction } from '@/types/websocket';
import {
  buttonHover,
  buttonTap,
  staggeredContainer,
  staggeredItem,
  scaleIn,
  springTransition,
} from '@/lib/animations';

interface ActionButtonsProps {
  allowedActions: AvailableAction[];
  myStack: number;
  minRaiseAmount: number;
  maxRaiseAmount: number;
  callAmount: number;
  raiseAmount: number;
  onRaiseAmountChange: (amount: number) => void;
  onFold: () => void;
  onCheck: () => void;
  onCall: () => void;
  onRaise: () => void;
  onAllIn: () => void;
}

export function ActionButtons({
  allowedActions,
  myStack: _myStack,
  minRaiseAmount,
  maxRaiseAmount,
  callAmount,
  raiseAmount,
  onRaiseAmountChange,
  onFold,
  onCheck,
  onCall,
  onRaise,
  onAllIn,
}: ActionButtonsProps) {
  // 향후 기능 확장용 (현재 미사용)
  void _myStack;
  
  const [showRaiseSlider, setShowRaiseSlider] = useState(false);

  // 서버에서 받은 allowedActions 기반으로 액션 정보 추출
  const canFold = allowedActions.some(a => a.type === 'fold');
  const canCheck = allowedActions.some(a => a.type === 'check');
  const canCall = allowedActions.some(a => a.type === 'call');
  const canBet = allowedActions.some(a => a.type === 'bet');
  const canRaise = allowedActions.some(a => a.type === 'raise');

  const handleRaiseConfirm = () => {
    onRaise();
    setShowRaiseSlider(false);
  };

  // 버튼 목록 생성
  const buttons = [];
  if (canFold) buttons.push({ key: 'fold', action: onFold, img: '/assets/ui/btn_fold.png?v=3', alt: '폴드', label: '폴드', testId: 'fold-button' });
  if (canCheck) buttons.push({ key: 'check', action: onCheck, img: '/assets/ui/btn_check.png?v=3', alt: '체크', label: '체크', testId: 'check-button' });
  if (canCall) buttons.push({ key: 'call', action: onCall, img: '/assets/ui/btn_call.png?v=3', alt: '콜', label: `콜${callAmount > 0 ? `(${callAmount.toLocaleString()})` : ''}`, testId: 'call-button' });
  if (canBet || canRaise) buttons.push({ key: 'raise', action: () => setShowRaiseSlider(!showRaiseSlider), img: '/assets/ui/btn_raise.png?v=3', alt: '레이즈', label: `레이즈(${raiseAmount.toLocaleString()})`, testId: 'raise-button' });
  if (canRaise || canBet || canCall) buttons.push({ key: 'allin', action: onAllIn, img: '/assets/ui/btn_allin.png?v=3', alt: '올인', label: '올인', testId: 'allin-button' });

  return (
    <div className="absolute -top-12 left-0 right-0 flex flex-col items-center gap-2">
      {/* 레이즈 슬라이더 팝업 */}
      <AnimatePresence>
        {showRaiseSlider && (canBet || canRaise) && (
          <motion.div 
            className="absolute bottom-full left-1/2 mb-2 bg-black/90 border border-white/20 rounded-lg p-4 min-w-[280px] z-[100]"
            variants={scaleIn}
            initial="initial"
            animate="animate"
            exit="exit"
            style={{ x: '-50%' }}
          >
            <div className="flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <span className="text-white text-sm">레이즈 금액</span>
                <motion.button
                  onClick={() => setShowRaiseSlider(false)}
                  className="text-white/60 hover:text-white text-xl leading-none"
                  whileHover={{ scale: 1.2 }}
                  whileTap={{ scale: 0.9 }}
                >
                  ×
                </motion.button>
              </div>
              <input
                type="range"
                min={minRaiseAmount}
                max={maxRaiseAmount}
                value={raiseAmount}
                onChange={(e) => onRaiseAmountChange(parseInt(e.target.value))}
                className="w-full"
                data-testid="raise-slider"
              />
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={raiseAmount}
                  onChange={(e) => onRaiseAmountChange(parseInt(e.target.value) || minRaiseAmount)}
                  className="flex-1 bg-white/10 border border-white/20 rounded px-3 py-2 text-white text-center"
                  min={minRaiseAmount}
                  max={maxRaiseAmount}
                  data-testid="raise-input"
                />
                <motion.button
                  onClick={handleRaiseConfirm}
                  disabled={raiseAmount < minRaiseAmount}
                  className="bg-yellow-500 hover:bg-yellow-400 disabled:bg-gray-500 text-black font-bold px-4 py-2 rounded transition-colors"
                  whileHover={buttonHover}
                  whileTap={buttonTap}
                >
                  확인
                </motion.button>
              </div>
              {/* 퀵 버튼 */}
              <motion.div 
                className="flex gap-2"
                variants={staggeredContainer}
                initial="initial"
                animate="animate"
              >
                {[
                  { label: '최소', value: minRaiseAmount },
                  { label: '1/2', value: Math.floor((minRaiseAmount + maxRaiseAmount) / 2) },
                  { label: '3/4', value: Math.floor(maxRaiseAmount * 0.75) },
                  { label: 'MAX', value: maxRaiseAmount },
                ].map((btn) => (
                  <motion.button
                    key={btn.label}
                    onClick={() => onRaiseAmountChange(btn.value)}
                    className="flex-1 bg-white/10 hover:bg-white/20 text-white text-xs py-1 rounded"
                    variants={staggeredItem}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    {btn.label}
                  </motion.button>
                ))}
              </motion.div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 액션 버튼 영역 */}
      <AnimatePresence mode="wait">
        {buttons.length > 0 && (
          <motion.div 
            className="flex gap-2 justify-center items-center"
            variants={staggeredContainer}
            initial="initial"
            animate="animate"
            exit="exit"
          >
            {buttons.map((btn, index) => (
              <motion.button
                key={btn.key}
                onClick={btn.action}
                className="relative"
                variants={staggeredItem}
                whileHover={buttonHover}
                whileTap={buttonTap}
                transition={{ ...springTransition, delay: index * 0.05 }}
                data-testid={btn.testId}
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={btn.img} alt={btn.alt} className="h-[53px]" />
                <span className="absolute inset-0 flex items-center justify-center text-white font-bold text-sm drop-shadow-[0_2px_2px_rgba(0,0,0,0.8)]">
                  {btn.label}
                </span>
              </motion.button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

interface WaitingStateProps {
  currentTurnPosition: number | null;
  phase: string | null;
  seatedPlayerCount: number;
  onStartGame: () => void;
}

export function WaitingState({
  currentTurnPosition,
  phase,
  seatedPlayerCount,
  onStartGame,
}: WaitingStateProps) {
  if (currentTurnPosition !== null) {
    return (
      <motion.div 
        className="flex flex-col items-center justify-center h-full"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
      >
        <p className="text-[var(--text-secondary)] text-sm">
          다른 플레이어의 차례를 기다리는 중...
        </p>
      </motion.div>
    );
  }

  if (phase === 'waiting' || !phase) {
    return (
      <motion.div 
        className="flex flex-col items-center justify-center h-full gap-2"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={springTransition}
      >
        <p className="text-[var(--text-secondary)] text-sm">
          참가자: {seatedPlayerCount}명
        </p>
        <motion.button
          onClick={onStartGame}
          disabled={seatedPlayerCount < 2}
          className="px-6 py-2 rounded-lg font-bold text-black bg-gradient-to-r from-yellow-400 via-yellow-500 to-amber-500 hover:from-yellow-300 hover:via-yellow-400 hover:to-amber-400 disabled:from-gray-500 disabled:via-gray-600 disabled:to-gray-700 disabled:text-gray-400 disabled:cursor-not-allowed shadow-lg transition-all duration-200"
          whileHover={seatedPlayerCount >= 2 ? buttonHover : undefined}
          whileTap={seatedPlayerCount >= 2 ? buttonTap : undefined}
        >
          게임 시작
        </motion.button>
        {seatedPlayerCount < 2 && (
          <motion.p 
            className="text-xs text-[var(--text-muted)]"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            2명 이상이 필요합니다
          </motion.p>
        )}
      </motion.div>
    );
  }

  return (
    <motion.div 
      className="flex flex-col items-center justify-center h-full"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <p className="text-[var(--text-secondary)] text-sm">
        게임 진행 중...
      </p>
    </motion.div>
  );
}

// eslint-disable-next-line @typescript-eslint/no-empty-object-type
interface SpectatorStateProps {}

export function SpectatorState({}: SpectatorStateProps) {
  return (
    <motion.div 
      className="text-center"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <p className="text-[var(--text-secondary)] text-sm">
        관전 중 - 위 프로필을 클릭하여 참여하세요
      </p>
    </motion.div>
  );
}
