'use client';

export type GameTabType = 'all' | 'tournament' | 'holdem';

interface GameTabsProps {
  activeTab: GameTabType;
  onTabChange: (tab: GameTabType) => void;
}

const tabs: { id: GameTabType; label: string }[] = [
  { id: 'all', label: '전체' },
  { id: 'tournament', label: '토너먼트 채널' },
  { id: 'holdem', label: '홀덤 채널' },
];

// Arrow icon with gradient
function ArrowIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M4.5 2.5L8 6L4.5 9.5"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default function GameTabs({ activeTab, onTabChange }: GameTabsProps) {
  return (
    <div className="game-tabs">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          className={`game-tab ${activeTab === tab.id ? 'active' : ''}`}
        >
          <span>{tab.label}</span>
          <span className="game-tab-arrow">
            <ArrowIcon />
          </span>
        </button>
      ))}
    </div>
  );
}
