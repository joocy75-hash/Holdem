'use client';

import { useState, useEffect } from 'react';

interface TournamentCardProps {
  id: string;
  name: string;
  type: 'tournament' | 'bounty';
  status: 'registering' | 'starting' | 'running' | 'finished';
  startTime?: Date;
  prizePool: number;
  buyIn: number;
  playerCount?: number;
  maxPlayers?: number;
  onJoin?: () => void;
  disabled?: boolean;
}

// Trophy icon with gradient - SVG 필터 제거 (CSS drop-shadow로 대체)
function TrophyIcon() {
  return (
    <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="trophy-gold" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#fcd34d"/>
          <stop offset="30%" stopColor="#fbbf24"/>
          <stop offset="70%" stopColor="#f59e0b"/>
          <stop offset="100%" stopColor="#d97706"/>
        </linearGradient>
        <linearGradient id="trophy-shine" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="white" stopOpacity="0"/>
          <stop offset="50%" stopColor="white" stopOpacity="0.3"/>
          <stop offset="100%" stopColor="white" stopOpacity="0"/>
        </linearGradient>
      </defs>
      <g>
        {/* Cup body */}
        <path
          d="M12 8h16v4c0 6-4 10-8 12-4-2-8-6-8-12V8z"
          fill="url(#trophy-gold)"
        />
        {/* Left handle */}
        <path
          d="M12 10c-2 0-4 2-4 4s2 4 4 4"
          stroke="url(#trophy-gold)"
          strokeWidth="2.5"
          fill="none"
        />
        {/* Right handle */}
        <path
          d="M28 10c2 0 4 2 4 4s-2 4-4 4"
          stroke="url(#trophy-gold)"
          strokeWidth="2.5"
          fill="none"
        />
        {/* Base */}
        <rect x="16" y="24" width="8" height="3" fill="url(#trophy-gold)"/>
        <rect x="13" y="27" width="14" height="3" rx="1" fill="url(#trophy-gold)"/>
        {/* Shine effect */}
        <path
          d="M15 10h2v8h-2z"
          fill="url(#trophy-shine)"
        />
      </g>
    </svg>
  );
}

// Bounty target icon with gradient - SVG 필터 제거 (CSS drop-shadow로 대체)
function BountyIcon() {
  return (
    <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="bounty-purple" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#c084fc"/>
          <stop offset="50%" stopColor="#a855f7"/>
          <stop offset="100%" stopColor="#7c3aed"/>
        </linearGradient>
      </defs>
      <g>
        <circle cx="20" cy="20" r="14" stroke="url(#bounty-purple)" strokeWidth="2.5" fill="none"/>
        <circle cx="20" cy="20" r="9" stroke="url(#bounty-purple)" strokeWidth="2" fill="none"/>
        <circle cx="20" cy="20" r="4" fill="url(#bounty-purple)"/>
        {/* Crosshair lines */}
        <line x1="20" y1="4" x2="20" y2="10" stroke="url(#bounty-purple)" strokeWidth="2"/>
        <line x1="20" y1="30" x2="20" y2="36" stroke="url(#bounty-purple)" strokeWidth="2"/>
        <line x1="4" y1="20" x2="10" y2="20" stroke="url(#bounty-purple)" strokeWidth="2"/>
        <line x1="30" y1="20" x2="36" y2="20" stroke="url(#bounty-purple)" strokeWidth="2"/>
      </g>
    </svg>
  );
}

// Prize icon
function PrizeIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="prize-gold" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#fcd34d"/>
          <stop offset="100%" stopColor="#f59e0b"/>
        </linearGradient>
      </defs>
      <path
        d="M9 1l2.5 5 5.5.8-4 3.9 1 5.3-5-2.6-5 2.6 1-5.3-4-3.9 5.5-.8L9 1z"
        fill="url(#prize-gold)"
      />
    </svg>
  );
}

// Gold coin icon
function GoldIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="gold-coin-t" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#fcd34d"/>
          <stop offset="50%" stopColor="#fbbf24"/>
          <stop offset="100%" stopColor="#f59e0b"/>
        </linearGradient>
      </defs>
      <circle cx="8" cy="8" r="7" fill="url(#gold-coin-t)"/>
      <circle cx="8" cy="8" r="5.5" stroke="#d97706" strokeWidth="0.5" fill="none"/>
      <text x="8" y="11" textAnchor="middle" fill="#92400e" fontSize="7" fontWeight="bold">G</text>
    </svg>
  );
}

function formatCountdown(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function formatAmount(amount: number): string {
  if (amount >= 100000000) {
    return `${(amount / 100000000).toFixed(1)}억`;
  }
  if (amount >= 10000) {
    return `${Math.floor(amount / 10000)}만`;
  }
  return amount.toLocaleString();
}

export default function TournamentCard({
  name,
  type,
  status,
  startTime,
  prizePool,
  buyIn,
  onJoin,
  disabled = false,
}: TournamentCardProps) {
  const [countdown, setCountdown] = useState(0);

  useEffect(() => {
    if (!startTime) return;

    const updateCountdown = () => {
      const now = new Date();
      const diff = Math.max(0, Math.floor((startTime.getTime() - now.getTime()) / 1000));
      setCountdown(diff);
    };

    updateCountdown();
    const interval = setInterval(updateCountdown, 1000);
    return () => clearInterval(interval);
  }, [startTime]);

  const statusLabels = {
    registering: '등록 중',
    starting: '시작 예정',
    running: '진행 중',
    finished: '종료',
  };

  const isBounty = type === 'bounty';
  const Icon = isBounty ? BountyIcon : TrophyIcon;
  const typeLabel = isBounty ? '바운티 헌터' : '토너먼트';

  return (
    <div className={`game-card tournament ${isBounty ? 'bounty' : ''}`}>
      {/* Left Section */}
      <div className="game-card-left">
        <div className="game-card-icon">
          <Icon />
        </div>
        <div className="game-card-type">{typeLabel}</div>
        <div className="game-card-badge">{statusLabels[status]}</div>

        {startTime && status === 'registering' && (
          <div className="game-card-timer">
            <div className="game-card-countdown-label">시작 시간까지</div>
            <div className={`game-card-countdown ${countdown < 60 ? 'countdown-active urgent' : ''}`}>
              {formatCountdown(countdown)}
            </div>
          </div>
        )}
      </div>

      {/* Divider */}
      <div className="game-card-divider" />

      {/* Right Section */}
      <div className="game-card-right">
        {/* Title */}
        <div className="game-card-title">{name}</div>

        {/* Prize Pool */}
        <div className="game-card-info">
          <span className="text-[var(--text-muted)]">상금</span>
          <span className="game-card-prize">
            <PrizeIcon />
            <span>{formatAmount(prizePool)}</span>
          </span>
        </div>

        {/* Buy-in Row */}
        <div className="game-card-buyin">
          <div className="game-card-buyin-info">
            <span className="game-card-buyin-label">바이인</span>
            <span className="game-card-buyin-value">
              {buyIn === 0 ? (
                <span className="free-badge">Free</span>
              ) : (
                <>
                  <GoldIcon />
                  <span>{formatAmount(buyIn)}</span>
                </>
              )}
            </span>
          </div>

          <button
            onClick={onJoin}
            disabled={disabled || status === 'finished'}
            className="btn-join"
          >
            <span className="btn-join-arrow">&gt;</span>
            <span>참여하기</span>
          </button>
        </div>
      </div>
    </div>
  );
}
