'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { DetailedStats } from '@/lib/api';

interface DetailedStatsCardProps {
  stats: DetailedStats | null;
  isLoading: boolean;
  isExpanded: boolean;
  onToggle: () => void;
}

interface StatItemProps {
  label: string;
  value: string | number;
  suffix?: string;
  description?: string;
}

function StatItem({ label, value, suffix = '', description }: StatItemProps) {
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
        style={{
          fontSize: '18px',
          fontWeight: 700,
          color: 'white',
          margin: 0,
        }}
      >
        {value}
        {suffix && <span style={{ fontSize: '13px', fontWeight: 500, marginLeft: '2px' }}>{suffix}</span>}
      </p>
      {description && (
        <p
          style={{
            fontSize: '10px',
            color: 'rgba(255,255,255,0.35)',
            margin: '4px 0 0 0',
          }}
        >
          {description}
        </p>
      )}
    </div>
  );
}

const playStyleConfig: Record<string, { color: string; bgColor: string; label: string }> = {
  TAG: { color: '#60a5fa', bgColor: 'rgba(59, 130, 246, 0.15)', label: 'Tight-Aggressive' },
  LAG: { color: '#f97316', bgColor: 'rgba(249, 115, 22, 0.15)', label: 'Loose-Aggressive' },
  Nit: { color: '#a78bfa', bgColor: 'rgba(167, 139, 250, 0.15)', label: 'Tight-Passive' },
  'Calling Station': { color: '#4ade80', bgColor: 'rgba(74, 222, 128, 0.15)', label: 'Loose-Passive' },
  unknown: { color: '#9ca3af', bgColor: 'rgba(156, 163, 175, 0.15)', label: '분석 중' },
};

export default function DetailedStatsCard({ stats, isLoading, isExpanded, onToggle }: DetailedStatsCardProps) {
  const styleConfig = stats?.play_style
    ? playStyleConfig[stats.play_style.style] || playStyleConfig.unknown
    : playStyleConfig.unknown;

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
      {/* 헤더 - 토글 버튼 */}
      <button
        onClick={onToggle}
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          padding: 0,
        }}
      >
        <h3
          style={{
            fontSize: '16px',
            fontWeight: 600,
            color: 'white',
            margin: 0,
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
              background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(217, 119, 6, 0.1) 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="#fbbf24">
              <path d="M3.5 18.49l6-6.01 4 4L22 6.92l-1.41-1.41-7.09 7.97-4-4L2 16.99z" />
            </svg>
          </div>
          상세 통계
        </h3>
        <motion.div
          animate={{ rotate: isExpanded ? 180 : 0 }}
          transition={{ duration: 0.2 }}
          style={{
            width: '28px',
            height: '28px',
            borderRadius: '8px',
            background: 'rgba(255,255,255,0.05)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="rgba(255,255,255,0.5)">
            <path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6z" />
          </svg>
        </motion.div>
      </button>

      {/* 확장 컨텐츠 */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            style={{ overflow: 'hidden' }}
          >
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
                <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '14px', margin: 0 }}>
                  상세 통계 로딩 중...
                </p>
              </div>
            ) : stats ? (
              <div style={{ marginTop: '20px' }}>
                {/* 플레이 스타일 배지 */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '12px',
                    padding: '16px',
                    background: styleConfig.bgColor,
                    borderRadius: '12px',
                    marginBottom: '20px',
                    border: `1px solid ${styleConfig.color}30`,
                  }}
                >
                  <span style={{ fontSize: '32px' }}>{stats.play_style?.emoji || '🎴'}</span>
                  <div>
                    <p
                      style={{
                        margin: 0,
                        fontWeight: 700,
                        fontSize: '18px',
                        color: styleConfig.color,
                      }}
                    >
                      {stats.play_style?.style || 'Unknown'}
                    </p>
                    <p
                      style={{
                        margin: '4px 0 0 0',
                        fontSize: '12px',
                        color: 'rgba(255,255,255,0.5)',
                      }}
                    >
                      {stats.play_style?.description || styleConfig.label}
                    </p>
                  </div>
                </div>

                {/* 구분선 */}
                <div
                  style={{
                    height: '1px',
                    background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent)',
                    margin: '16px 0',
                  }}
                />

                {/* 프리플롭 지표 */}
                <p
                  style={{
                    fontSize: '12px',
                    color: 'rgba(255,255,255,0.4)',
                    margin: '0 0 12px 0',
                    fontWeight: 600,
                  }}
                >
                  프리플롭 지표
                </p>
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(3, 1fr)',
                    gap: '12px',
                    marginBottom: '20px',
                  }}
                >
                  <StatItem
                    label="VPIP"
                    value={stats.vpip?.toFixed(1) || '0.0'}
                    suffix="%"
                    description="참여율"
                  />
                  <StatItem
                    label="PFR"
                    value={stats.pfr?.toFixed(1) || '0.0'}
                    suffix="%"
                    description="레이즈율"
                  />
                  <StatItem
                    label="3-Bet"
                    value={stats.three_bet?.toFixed(1) || '0.0'}
                    suffix="%"
                    description="3벳 빈도"
                  />
                </div>

                {/* 구분선 */}
                <div
                  style={{
                    height: '1px',
                    background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent)',
                    margin: '16px 0',
                  }}
                />

                {/* 공격성 지표 */}
                <p
                  style={{
                    fontSize: '12px',
                    color: 'rgba(255,255,255,0.4)',
                    margin: '0 0 12px 0',
                    fontWeight: 600,
                  }}
                >
                  공격성 지표
                </p>
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(2, 1fr)',
                    gap: '12px',
                    marginBottom: '20px',
                  }}
                >
                  <StatItem
                    label="AF"
                    value={stats.af?.toFixed(2) || '0.00'}
                    description="(Bet+Raise)/Call"
                  />
                  <StatItem
                    label="Agg Freq"
                    value={stats.agg_freq?.toFixed(1) || '0.0'}
                    suffix="%"
                    description="공격 빈도"
                  />
                </div>

                {/* 구분선 */}
                <div
                  style={{
                    height: '1px',
                    background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent)',
                    margin: '16px 0',
                  }}
                />

                {/* 쇼다운 지표 */}
                <p
                  style={{
                    fontSize: '12px',
                    color: 'rgba(255,255,255,0.4)',
                    margin: '0 0 12px 0',
                    fontWeight: 600,
                  }}
                >
                  쇼다운 지표
                </p>
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(2, 1fr)',
                    gap: '12px',
                    marginBottom: '20px',
                  }}
                >
                  <StatItem
                    label="WTSD"
                    value={stats.wtsd?.toFixed(1) || '0.0'}
                    suffix="%"
                    description="쇼다운 진행률"
                  />
                  <StatItem
                    label="WSD"
                    value={stats.wsd?.toFixed(1) || '0.0'}
                    suffix="%"
                    description="쇼다운 승률"
                  />
                </div>

                {/* 구분선 */}
                <div
                  style={{
                    height: '1px',
                    background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent)',
                    margin: '16px 0',
                  }}
                />

                {/* 수익성 지표 */}
                <p
                  style={{
                    fontSize: '12px',
                    color: 'rgba(255,255,255,0.4)',
                    margin: '0 0 12px 0',
                    fontWeight: 600,
                  }}
                >
                  수익성 지표
                </p>
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(2, 1fr)',
                    gap: '12px',
                  }}
                >
                  <StatItem
                    label="Win Rate"
                    value={stats.win_rate?.toFixed(1) || '0.0'}
                    suffix="%"
                    description="전체 승률"
                  />
                  <StatItem
                    label="BB/100"
                    value={stats.bb_per_100?.toFixed(2) || '0.00'}
                    description="100핸드당 BB"
                  />
                </div>
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '30px 0' }}>
                <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '14px', margin: 0 }}>
                  통계 데이터가 없습니다
                </p>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
