'use client';

import { motion } from 'framer-motion';

export type WalletTab = 'deposit' | 'withdraw';

interface CashierHeaderProps {
  balance: number;
  onBack: () => void;
  showBackButton?: boolean;
  // 탭 관련
  activeTab: WalletTab;
  onTabChange: (tab: WalletTab) => void;
  showTabs?: boolean;
}

const quickSpring = { type: 'spring' as const, stiffness: 400, damping: 20 };

export default function CashierHeader({
  balance,
  onBack,
  showBackButton = false,
  activeTab,
  onTabChange,
  showTabs = true,
}: CashierHeaderProps) {
  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: '50%',
        transform: 'translateX(-50%)',
        width: '390px',
        background: 'var(--figma-gradient-header)',
        zIndex: 100,
        borderBottom: '1px solid rgba(255,255,255,0.1)',
      }}
    >
      {/* 상단 영역: 뒤로가기, 타이틀, 잔액 */}
      <div
        style={{
          height: '56px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 16px',
        }}
      >
        {/* 뒤로가기 버튼 */}
        <motion.button
          onClick={onBack}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          transition={quickSpring}
          style={{
            width: '40px',
            height: '40px',
            background: 'rgba(255,255,255,0.1)',
            border: 'none',
            borderRadius: '8px',
            color: 'white',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z" />
          </svg>
        </motion.button>

        {/* 타이틀 */}
        <h1
          style={{
            fontFamily: 'Paperlogy, sans-serif',
            fontWeight: 600,
            fontSize: '18px',
            color: 'white',
            textShadow: '0 2px 4px rgba(0,0,0,0.3)',
            margin: 0,
          }}
        >
          충전/환전
        </h1>

        {/* 잔액 표시 */}
        <div
          style={{
            background: 'rgba(0,0,0,0.3)',
            padding: '8px 12px',
            borderRadius: '20px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <span
            style={{
              fontWeight: 600,
              fontSize: '14px',
              color: 'var(--figma-balance-color)',
            }}
          >
            {balance.toLocaleString()}
          </span>
        </div>
      </div>

      {/* 탭 영역 */}
      {showTabs && (
        <div
          style={{
            display: 'flex',
            padding: '0 16px 12px',
            gap: '12px',
          }}
        >
          <motion.button
            onClick={() => onTabChange('deposit')}
            whileTap={{ scale: 0.98 }}
            transition={quickSpring}
            style={{
              flex: 1,
              padding: '12px',
              background:
                activeTab === 'deposit'
                  ? 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'
                  : 'rgba(255,255,255,0.1)',
              border: 'none',
              borderRadius: '8px',
              color: 'white',
              fontWeight: 600,
              fontSize: '15px',
              cursor: 'pointer',
              transition: 'background 0.2s',
            }}
          >
            충전
          </motion.button>
          <motion.button
            onClick={() => onTabChange('withdraw')}
            whileTap={{ scale: 0.98 }}
            transition={quickSpring}
            style={{
              flex: 1,
              padding: '12px',
              background:
                activeTab === 'withdraw'
                  ? 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'
                  : 'rgba(255,255,255,0.1)',
              border: 'none',
              borderRadius: '8px',
              color: 'white',
              fontWeight: 600,
              fontSize: '15px',
              cursor: 'pointer',
              transition: 'background 0.2s',
            }}
          >
            환전
          </motion.button>
        </div>
      )}
    </div>
  );
}
