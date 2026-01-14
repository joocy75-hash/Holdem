'use client';

import { useState, useEffect } from 'react';

// 턴 타이머 설정 (서버와 동기화)
export const DEFAULT_TURN_TIME = 15; // 기본 턴 시간 15초 (UTG는 20초)
export const COUNTDOWN_START = 10; // 카운트다운 표시 시작 (마지막 10초)

interface TurnTimerProps {
  isActive: boolean;
  turnStartTime: number | null;
  turnTime?: number;
  isCurrentUser: boolean;
  onAutoFold?: () => void;
  children: React.ReactNode;
}

export function TurnTimer({
  isActive,
  turnStartTime,
  turnTime = DEFAULT_TURN_TIME,
  isCurrentUser,
  onAutoFold,
  children,
}: TurnTimerProps) {
  const [timeRemaining, setTimeRemaining] = useState<number | null>(null);
  const [showCountdown, setShowCountdown] = useState(false);

  useEffect(() => {
    if (!isActive || !turnStartTime) {
      const resetTimer = setTimeout(() => {
        setTimeRemaining(null);
        setShowCountdown(false);
      }, 0);
      return () => clearTimeout(resetTimer);
    }

    // 클라이언트 시간 기준으로 타이머 시작
    const clientTurnStartTime = Date.now();
    const turnTimeMs = (turnTime || DEFAULT_TURN_TIME) * 1000;
    let autoFoldTriggered = false;

    console.log(`⏱️ Timer started: ${turnTime}s`);

    const updateTimer = () => {
      const elapsed = Date.now() - clientTurnStartTime;
      const remaining = turnTimeMs - elapsed;

      // 시간 초과 시 자동 폴드
      if (remaining <= 0) {
        setTimeRemaining(0);
        setShowCountdown(false);
        if (isCurrentUser && onAutoFold && !autoFoldTriggered) {
          autoFoldTriggered = true;
          console.log('⏰ Auto-fold triggered by timer');
          onAutoFold();
        }
        return;
      }

      setTimeRemaining(remaining / 1000);
      // 마지막 10초부터 카운트다운 표시
      setShowCountdown(remaining <= COUNTDOWN_START * 1000);
    };

    const initTimer = setTimeout(updateTimer, 0);
    const interval = setInterval(updateTimer, 100);

    return () => {
      clearTimeout(initTimer);
      clearInterval(interval);
    };
  }, [isActive, turnStartTime, turnTime, isCurrentUser, onAutoFold]);

  // 타이머 진행률 계산 (10초 기준)
  const timerProgress = timeRemaining !== null && showCountdown
    ? Math.max(0, (timeRemaining / COUNTDOWN_START) * 100)
    : 100;

  return (
    <div className="relative" data-testid={isActive ? "turn-timer" : undefined} data-time-remaining={isActive ? Math.ceil(timeRemaining || 0) : undefined}>
      {/* SVG 원형 프로그레스 바 (턴일 때만) */}
      {isActive && (
        <svg
          className="absolute -inset-1 w-[calc(100%+8px)] h-[calc(100%+8px)] -rotate-90"
          viewBox="0 0 100 100"
        >
          {/* 배경 원 (턴 표시) */}
          <circle
            cx="50"
            cy="50"
            r="46"
            fill="none"
            stroke={showCountdown ? "rgba(255,255,255,0.2)" : "var(--accent)"}
            strokeWidth="4"
          />
          {/* 진행 원 (카운트다운 타이머) */}
          {showCountdown && (
            <circle
              cx="50"
              cy="50"
              r="46"
              fill="none"
              stroke={
                timerProgress > 40
                  ? '#22c55e'  // 녹색
                  : timerProgress > 20
                    ? '#f59e0b'  // 황색
                    : '#ef4444'  // 빨강
              }
              strokeWidth="4"
              strokeLinecap="round"
              strokeDasharray={`${(timerProgress / 100) * 289} 289`}
              className="transition-all duration-100"
            />
          )}
        </svg>
      )}

      {/* 자식 컴포넌트 (아바타 등) */}
      {children}

      {/* 카운트다운 숫자 (우측 상단 뱃지) */}
      {isActive && showCountdown && (
        <div
          className={`absolute -top-1 -right-1 w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${
            timerProgress > 40
              ? 'bg-green-500 text-white'
              : timerProgress > 20
                ? 'bg-yellow-500 text-black'
                : 'bg-red-500 text-white'
          }`}
          data-testid="timeout-indicator"
        >
          {Math.ceil(timeRemaining || 0)}
        </div>
      )}
    </div>
  );
}
