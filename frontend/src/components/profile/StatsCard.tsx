'use client';

import { motion } from 'framer-motion';
import { UserStats } from '@/lib/api';

interface StatsCardProps {
  stats: UserStats | null;
  isLoading: boolean;
}

interface StatItemProps {
  label: string;
  value: string | number;
  suffix?: string;
  highlight?: boolean;
}

function StatItem({ label, value, suffix = '', highlight = false }: StatItemProps) {
  return (
    <div style={{ textAlign: 'center' }}>
      <p
        style={{
          fontSize: '11px',
          color: 'rgba(255,255,255,0.45)',
          margin: '0 0 6px 0',
          fontWeight: 500,
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
        }}
      >
        {label}
      </p>
      <p
        className={highlight ? 'glow-text-gold' : ''}
        style={{
          fontSize: '20px',
          fontWeight: 700,
          color: highlight ? undefined : 'white',
          margin: 0,
        }}
      >
        {value}
        {suffix && <span style={{ fontSize: '14px', fontWeight: 500, marginLeft: '2px' }}>{suffix}</span>}
      </p>
    </div>
  );
}

export default function StatsCard({ stats, isLoading }: StatsCardProps) {
  const winRate = stats && stats.total_hands > 0
    ? ((stats.hands_won / stats.total_hands) * 100).toFixed(1)
    : '0.0';

  return (
    <div
      className="glass-card"
      style={{
        margin: '0 20px 20px',
        padding: '22px',
        position: 'relative',
        zIndex: 1,
      }}
    >
      <h3
        style={{
          fontSize: '16px',
          fontWeight: 600,
          color: 'white',
          margin: '0 0 20px 0',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
        }}
      >
        <div
          style={{
            width: '28px',
            height: '28px',
            borderRadius: '8px',
            background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(37, 99, 235, 0.1) 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="#60a5fa">
            <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z" />
          </svg>
        </div>
        게임 통계
      </h3>

      {isLoading ? (
        <div style={{ textAlign: 'center', padding: '30px 0' }}>
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            style={{
              width: '32px',
              height: '32px',
              border: '3px solid rgba(255,255,255,0.1)',
              borderTopColor: '#fbbf24',
              borderRadius: '50%',
              margin: '0 auto 12px',
            }}
          />
          <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '14px', margin: 0 }}>로딩 중...</p>
        </div>
      ) : (
        <>
          {/* 첫 번째 줄 */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '16px',
              marginBottom: '20px',
            }}
          >
            <StatItem
              label="총 핸드"
              value={stats?.total_hands?.toLocaleString() || '0'}
            />
            <StatItem
              label="승리"
              value={stats?.hands_won?.toLocaleString() || '0'}
            />
            <StatItem
              label="승률"
              value={winRate}
              suffix="%"
              highlight={true}
            />
          </div>

          {/* 구분선 */}
          <div
            style={{
              height: '1px',
              background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent)',
              margin: '20px 0',
            }}
          />

          {/* 두 번째 줄 */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '16px',
            }}
          >
            <StatItem
              label="VPIP"
              value={stats?.vpip?.toFixed(1) || '0.0'}
              suffix="%"
            />
            <StatItem
              label="PFR"
              value={stats?.pfr?.toFixed(1) || '0.0'}
              suffix="%"
            />
            <StatItem
              label="최대 팟"
              value={stats?.biggest_pot?.toLocaleString() || '0'}
            />
          </div>
        </>
      )}
    </div>
  );
}
