'use client';

interface User {
  id: string;
  nickname: string;
  avatarUrl: string | null;
  balance: number;
}

interface LobbyHeaderProps {
  user: User | null;
  onSettingsClick?: () => void;
  onLogout?: () => void;
}

// Gold icon SVG
function GoldIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="12" cy="12" r="10" fill="url(#gold-gradient)" stroke="#d97706" strokeWidth="1.5"/>
      <text x="12" y="16" textAnchor="middle" fill="#92400e" fontSize="10" fontWeight="bold">G</text>
      <defs>
        <linearGradient id="gold-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#fcd34d"/>
          <stop offset="100%" stopColor="#f59e0b"/>
        </linearGradient>
      </defs>
    </svg>
  );
}

// Settings icon SVG
function SettingsIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M12 15a3 3 0 100-6 3 3 0 000 6z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

// Default avatar component
function DefaultAvatar({ nickname }: { nickname: string }) {
  const initial = nickname ? nickname.charAt(0).toUpperCase() : '?';
  return (
    <div className="w-full h-full flex items-center justify-center text-xl font-bold text-[var(--text-primary)]">
      {initial}
    </div>
  );
}

export default function LobbyHeader({ user, onSettingsClick, onLogout }: LobbyHeaderProps) {
  const formatBalance = (balance: number) => {
    if (balance >= 100000000) {
      return `${(balance / 100000000).toFixed(1)}억`;
    }
    if (balance >= 10000) {
      return `${(balance / 10000).toFixed(0)}만`;
    }
    return balance.toLocaleString();
  };

  return (
    <header className="lobby-header" style={{ paddingTop: 'var(--safe-area-top)' }}>
      {/* Left: Avatar */}
      <div className="lobby-avatar">
        {user?.avatarUrl ? (
          <img src={user.avatarUrl} alt={user.nickname} />
        ) : (
          <DefaultAvatar nickname={user?.nickname || ''} />
        )}
      </div>

      {/* Center: Username */}
      <div className="lobby-username">
        {user?.nickname || 'Guest'}
      </div>

      {/* Right: Currency + Settings */}
      <div className="flex items-center gap-3">
        {/* Gold Display */}
        <div className="currency-display currency-gold">
          <GoldIcon />
          <span>{formatBalance(user?.balance || 0)}</span>
        </div>

        {/* Settings Button */}
        <button
          onClick={onSettingsClick || onLogout}
          className="btn-settings"
          aria-label="설정"
        >
          <SettingsIcon />
        </button>
      </div>
    </header>
  );
}
