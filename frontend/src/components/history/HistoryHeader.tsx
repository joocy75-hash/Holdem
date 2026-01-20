'use client';

import { motion } from 'framer-motion';

type TabType = 'game' | 'transaction';

interface HistoryHeaderProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
}

export default function HistoryHeader({ activeTab, onTabChange }: HistoryHeaderProps) {
  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: '50%',
        transform: 'translateX(-50%)',
        width: '390px',
        background: 'linear-gradient(180deg, rgba(15, 23, 42, 0.98) 0%, rgba(15, 23, 42, 0.92) 100%)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        zIndex: 100,
        borderBottom: '1px solid rgba(255,255,255,0.08)',
      }}
    >
      {/* 타이틀 */}
      <div
        style={{
          height: '60px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <h1
          style={{
            fontWeight: 700,
            fontSize: '18px',
            color: 'white',
            textShadow: '0 2px 8px rgba(0,0,0,0.3)',
            letterSpacing: '0.5px',
            margin: 0,
          }}
        >
          기록
        </h1>
      </div>

      {/* 탭 */}
      <div
        style={{
          display: 'flex',
          padding: '0 20px 14px',
          gap: '12px',
        }}
      >
        <motion.button
          onClick={() => onTabChange('game')}
          whileTap={{ scale: 0.95 }}
          whileHover={{ scale: 1.02 }}
          style={{
            flex: 1,
            padding: '12px',
            background: activeTab === 'game'
              ? 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'
              : 'rgba(255,255,255,0.06)',
            border: activeTab === 'game'
              ? 'none'
              : '1px solid rgba(255,255,255,0.08)',
            borderRadius: '12px',
            color: 'white',
            fontSize: '14px',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.3s ease',
            boxShadow: activeTab === 'game'
              ? '0 4px 15px rgba(245, 158, 11, 0.3), inset 0 1px 0 rgba(255,255,255,0.2)'
              : 'none',
          }}
        >
          <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 14l-5-5 1.41-1.41L12 14.17l4.59-4.58L18 11l-6 6z" />
            </svg>
            게임 기록
          </span>
        </motion.button>
        <motion.button
          onClick={() => onTabChange('transaction')}
          whileTap={{ scale: 0.95 }}
          whileHover={{ scale: 1.02 }}
          style={{
            flex: 1,
            padding: '12px',
            background: activeTab === 'transaction'
              ? 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'
              : 'rgba(255,255,255,0.06)',
            border: activeTab === 'transaction'
              ? 'none'
              : '1px solid rgba(255,255,255,0.08)',
            borderRadius: '12px',
            color: 'white',
            fontSize: '14px',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.3s ease',
            boxShadow: activeTab === 'transaction'
              ? '0 4px 15px rgba(245, 158, 11, 0.3), inset 0 1px 0 rgba(255,255,255,0.2)'
              : 'none',
          }}
        >
          <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M21 18v1c0 1.1-.9 2-2 2H5c-1.11 0-2-.9-2-2V5c0-1.1.89-2 2-2h14c1.1 0 2 .9 2 2v1h-9c-1.11 0-2 .9-2 2v8c0 1.1.89 2 2 2h9zm-9-2h10V8H12v8zm4-2.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z" />
            </svg>
            거래 내역
          </span>
        </motion.button>
      </div>
    </div>
  );
}
