'use client';

import type { GamePhase } from '@/types/websocket';

interface GameInfoProps {
  phase: GamePhase | string;
  smallBlind: number;
  bigBlind: number;
  pot: number;
  isConnected: boolean;
}

export function GameInfo({
  phase,
  smallBlind,
  bigBlind,
  pot,
  isConnected,
}: GameInfoProps) {
  return (
    <div className="flex items-center gap-4">
      <div className="text-center" data-testid="game-phase" data-phase={phase || 'waiting'}>
        <div className="text-xs text-[var(--text-muted)]">페이즈</div>
        <div className="text-sm font-bold uppercase">
          {phase || 'waiting'}
        </div>
      </div>
      <div className="text-center">
        <div className="text-xs text-[var(--text-muted)]">블라인드</div>
        <div className="text-sm font-bold">
          {smallBlind || 0} / {bigBlind || 0}
        </div>
      </div>
      <div className="text-center">
        <div className="text-xs text-[var(--text-muted)]">팟</div>
        <div className="text-sm font-bold text-[var(--accent)] tabular-nums">
          {pot.toLocaleString()}
        </div>
      </div>
      <div
        className={`badge ${
          isConnected ? 'badge-success' : 'badge-error'
        }`}
      >
        {isConnected ? 'Connected' : 'Disconnected'}
      </div>
    </div>
  );
}

interface CountdownOverlayProps {
  countdown: number | null;
}

export function CountdownOverlay({ countdown }: CountdownOverlayProps) {
  if (countdown === null) return null;

  return (
    <div className="absolute inset-0 flex items-center justify-center bg-black/50 z-20">
      <div className="text-center animate-pulse">
        <div className="text-6xl font-bold text-white mb-4 drop-shadow-lg">
          {countdown}
        </div>
        <div className="text-xl text-white/80 drop-shadow-lg">
          게임이 곧 시작됩니다!
        </div>
      </div>
    </div>
  );
}

interface ShowdownIntroOverlayProps {
  isVisible: boolean;
}

export function ShowdownIntroOverlay({ isVisible }: ShowdownIntroOverlayProps) {
  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 animate-fade-in px-4">
      <div className="text-center max-w-full">
        <h1 className="text-[clamp(2.5rem,12vw,6rem)] font-black text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 via-red-500 to-yellow-400 animate-showdown-text drop-shadow-[0_0_30px_rgba(255,200,0,0.8)]">
          SHOWDOWN!
        </h1>
        <div className="mt-4 text-white/80 text-lg md:text-xl animate-pulse">
          카드를 공개합니다
        </div>
      </div>
    </div>
  );
}
