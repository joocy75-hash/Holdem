'use client';

import { motion } from 'framer-motion';
import { VIPStatusResponse } from '@/lib/api';

interface VIPCardProps {
  vipStatus: VIPStatusResponse | null;
  isLoading: boolean;
}

// VIP 레벨별 스타일 설정
const vipLevelConfig: Record<string, {
  color: string;
  bgGradient: string;
  icon: string;
  borderColor: string;
}> = {
  bronze: {
    color: '#cd7f32',
    bgGradient: 'linear-gradient(135deg, rgba(205, 127, 50, 0.15) 0%, rgba(139, 69, 19, 0.1) 100%)',
    icon: '🥉',
    borderColor: 'rgba(205, 127, 50, 0.3)',
  },
  silver: {
    color: '#c0c0c0',
    bgGradient: 'linear-gradient(135deg, rgba(192, 192, 192, 0.15) 0%, rgba(128, 128, 128, 0.1) 100%)',
    icon: '🥈',
    borderColor: 'rgba(192, 192, 192, 0.3)',
  },
  gold: {
    color: '#ffd700',
    bgGradient: 'linear-gradient(135deg, rgba(255, 215, 0, 0.15) 0%, rgba(218, 165, 32, 0.1) 100%)',
    icon: '🥇',
    borderColor: 'rgba(255, 215, 0, 0.3)',
  },
  platinum: {
    color: '#e5e4e2',
    bgGradient: 'linear-gradient(135deg, rgba(229, 228, 226, 0.2) 0%, rgba(180, 180, 180, 0.1) 100%)',
    icon: '💎',
    borderColor: 'rgba(229, 228, 226, 0.3)',
  },
  diamond: {
    color: '#b9f2ff',
    bgGradient: 'linear-gradient(135deg, rgba(185, 242, 255, 0.2) 0%, rgba(0, 191, 255, 0.1) 100%)',
    icon: '👑',
    borderColor: 'rgba(185, 242, 255, 0.3)',
  },
};

export default function VIPCard({ vipStatus, isLoading }: VIPCardProps) {
  const levelConfig = vipStatus
    ? vipLevelConfig[vipStatus.level] || vipLevelConfig.bronze
    : vipLevelConfig.bronze;

  return (
    <div
      className="glass-card"
      style={{
        margin: '0 20px 20px',
        padding: '22px',
        position: 'relative',
        zIndex: 1,
        background: levelConfig.bgGradient,
        border: `1px solid ${levelConfig.borderColor}`,
      }}
    >
      {isLoading ? (
        <div style={{ textAlign: 'center', padding: '20px 0' }}>
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
            VIP 정보 로딩 중...
          </p>
        </div>
      ) : vipStatus ? (
        <>
          {/* 헤더: VIP 레벨 배지 */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '20px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ fontSize: '36px' }}>{levelConfig.icon}</span>
              <div>
                <p
                  style={{
                    margin: 0,
                    fontWeight: 700,
                    fontSize: '22px',
                    color: levelConfig.color,
                    textShadow: `0 0 8px ${levelConfig.color}30`,
                  }}
                >
                  {vipStatus.display_name}
                </p>
                <p
                  style={{
                    margin: '4px 0 0 0',
                    fontSize: '12px',
                    color: 'rgba(255,255,255,0.5)',
                  }}
                >
                  VIP 등급
                </p>
              </div>
            </div>

            {/* 레이크백 비율 */}
            <div
              style={{
                background: 'rgba(255,255,255,0.08)',
                padding: '10px 16px',
                borderRadius: '12px',
                textAlign: 'center',
              }}
            >
              <p
                style={{
                  margin: 0,
                  fontWeight: 700,
                  fontSize: '20px',
                  color: '#4ade80',
                }}
              >
                {vipStatus.rakeback_pct.toFixed(0)}%
              </p>
              <p
                style={{
                  margin: '2px 0 0 0',
                  fontSize: '10px',
                  color: 'rgba(255,255,255,0.45)',
                  textTransform: 'uppercase',
                }}
              >
                레이크백
              </p>
            </div>
          </div>

          {/* 진행도 바 */}
          {vipStatus.next_level && (
            <>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '8px',
                }}
              >
                <p
                  style={{
                    margin: 0,
                    fontSize: '12px',
                    color: 'rgba(255,255,255,0.5)',
                  }}
                >
                  다음 레벨까지
                </p>
                <p
                  style={{
                    margin: 0,
                    fontSize: '12px',
                    color: 'rgba(255,255,255,0.7)',
                  }}
                >
                  {vipStatus.rake_to_next.toLocaleString()}원 남음
                </p>
              </div>

              <div
                style={{
                  height: '8px',
                  background: 'rgba(255,255,255,0.1)',
                  borderRadius: '4px',
                  overflow: 'hidden',
                  marginBottom: '12px',
                }}
              >
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(vipStatus.progress_pct, 100)}%` }}
                  transition={{ duration: 0.8, ease: 'easeOut' }}
                  style={{
                    height: '100%',
                    background: `linear-gradient(90deg, ${levelConfig.color}, ${levelConfig.color}80)`,
                    borderRadius: '4px',
                  }}
                />
              </div>

              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <p
                  style={{
                    margin: 0,
                    fontSize: '11px',
                    color: 'rgba(255,255,255,0.4)',
                  }}
                >
                  총 레이크: {vipStatus.total_rake_paid.toLocaleString()}원
                </p>
                <p
                  style={{
                    margin: 0,
                    fontSize: '11px',
                    color: levelConfig.color,
                    fontWeight: 600,
                  }}
                >
                  → {vipStatus.next_level.charAt(0).toUpperCase() + vipStatus.next_level.slice(1)}
                </p>
              </div>
            </>
          )}

          {/* 최고 레벨 도달 시 */}
          {!vipStatus.next_level && (
            <div
              style={{
                textAlign: 'center',
                padding: '10px',
                background: 'rgba(255,255,255,0.05)',
                borderRadius: '8px',
              }}
            >
              <p
                style={{
                  margin: 0,
                  fontSize: '14px',
                  color: levelConfig.color,
                  fontWeight: 600,
                }}
              >
                최고 등급 달성!
              </p>
              <p
                style={{
                  margin: '4px 0 0 0',
                  fontSize: '12px',
                  color: 'rgba(255,255,255,0.5)',
                }}
              >
                총 레이크: {vipStatus.total_rake_paid.toLocaleString()}원
              </p>
            </div>
          )}
        </>
      ) : (
        <div style={{ textAlign: 'center', padding: '20px 0' }}>
          <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '14px', margin: 0 }}>
            VIP 정보를 불러올 수 없습니다
          </p>
        </div>
      )}
    </div>
  );
}
