'use client';

export type NavTab = 'lobby' | 'shop' | 'storage' | 'mission' | 'ranking';

interface BottomNavigationProps {
  activeTab: NavTab;
  onTabChange?: (tab: NavTab) => void;
  badges?: {
    shop?: boolean;
    storage?: number;
    mission?: boolean;
  };
}

// Icon components
function HomeIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M9 22V12h6v10"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function ShopIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4H6z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M3 6h18"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M16 10a4 4 0 01-8 0"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function StorageIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M3.27 6.96L12 12.01l8.73-5.05"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M12 22.08V12"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function MissionIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function RankingIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M8 21V11M12 21V3M16 21v-6"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

const navItems: { id: NavTab; label: string; icon: React.FC }[] = [
  { id: 'lobby', label: '로비', icon: HomeIcon },
  { id: 'shop', label: '상점', icon: ShopIcon },
  { id: 'storage', label: '보관함', icon: StorageIcon },
  { id: 'mission', label: '미션', icon: MissionIcon },
  { id: 'ranking', label: '랭킹', icon: RankingIcon },
];

export default function BottomNavigation({ activeTab, onTabChange, badges }: BottomNavigationProps) {
  const handleTabClick = (tab: NavTab) => {
    if (onTabChange) {
      onTabChange(tab);
    }
  };

  const getBadge = (tabId: NavTab): React.ReactNode => {
    if (!badges) return null;

    switch (tabId) {
      case 'shop':
        return badges.shop ? <span className="nav-badge">N</span> : null;
      case 'storage':
        return badges.storage ? <span className="nav-badge">{badges.storage}</span> : null;
      case 'mission':
        return badges.mission ? <span className="nav-badge">N</span> : null;
      default:
        return null;
    }
  };

  return (
    <nav className="bottom-nav">
      {navItems.map((item) => {
        const Icon = item.icon;
        const isActive = activeTab === item.id;
        const badge = getBadge(item.id);

        return (
          <button
            key={item.id}
            onClick={() => handleTabClick(item.id)}
            className={`bottom-nav-item ${isActive ? 'active' : ''}`}
            aria-label={item.label}
            aria-current={isActive ? 'page' : undefined}
          >
            <span className="bottom-nav-icon">
              <Icon />
            </span>
            <span className="bottom-nav-label">{item.label}</span>
            {badge}
          </button>
        );
      })}
    </nav>
  );
}
