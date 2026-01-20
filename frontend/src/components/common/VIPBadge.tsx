'use client';

/**
 * VIP 등급 배지 컴포넌트
 *
 * 아바타 옆이나 닉네임 옆에 표시되는 작은 VIP 레벨 아이콘
 */

export type VIPLevel = 'bronze' | 'silver' | 'gold' | 'platinum' | 'diamond';

export type VIPBadgeSize = 'xs' | 'sm' | 'md' | 'lg';

export interface VIPBadgeProps {
  /** VIP 레벨 */
  level: VIPLevel | string;
  /** 크기 */
  size?: VIPBadgeSize;
  /** 아바타 위에 오버레이로 표시할지 여부 */
  overlay?: boolean;
  /** 텍스트 라벨 표시 여부 */
  showLabel?: boolean;
  /** 추가 className */
  className?: string;
}

// 레벨별 설정
const LEVEL_CONFIG: Record<VIPLevel, {
  icon: string;
  color: string;
  bgColor: string;
  borderColor: string;
  label: string;
  glowColor: string;
}> = {
  bronze: {
    icon: '🥉',
    color: '#CD7F32',
    bgColor: 'rgba(205, 127, 50, 0.15)',
    borderColor: 'rgba(205, 127, 50, 0.4)',
    label: 'Bronze',
    glowColor: 'rgba(205, 127, 50, 0.3)',
  },
  silver: {
    icon: '🥈',
    color: '#C0C0C0',
    bgColor: 'rgba(192, 192, 192, 0.15)',
    borderColor: 'rgba(192, 192, 192, 0.4)',
    label: 'Silver',
    glowColor: 'rgba(192, 192, 192, 0.3)',
  },
  gold: {
    icon: '🥇',
    color: '#FFD700',
    bgColor: 'rgba(255, 215, 0, 0.15)',
    borderColor: 'rgba(255, 215, 0, 0.4)',
    label: 'Gold',
    glowColor: 'rgba(255, 215, 0, 0.3)',
  },
  platinum: {
    icon: '💎',
    color: '#E5E4E2',
    bgColor: 'rgba(229, 228, 226, 0.15)',
    borderColor: 'rgba(229, 228, 226, 0.4)',
    label: 'Platinum',
    glowColor: 'rgba(229, 228, 226, 0.3)',
  },
  diamond: {
    icon: '👑',
    color: '#B9F2FF',
    bgColor: 'rgba(185, 242, 255, 0.15)',
    borderColor: 'rgba(185, 242, 255, 0.4)',
    label: 'Diamond',
    glowColor: 'rgba(185, 242, 255, 0.4)',
  },
};

// 크기별 설정
const SIZE_CONFIG: Record<VIPBadgeSize, {
  width: number;
  height: number;
  fontSize: number;
  labelFontSize: number;
  padding: string;
}> = {
  xs: { width: 14, height: 14, fontSize: 8, labelFontSize: 8, padding: '1px' },
  sm: { width: 18, height: 18, fontSize: 10, labelFontSize: 9, padding: '2px' },
  md: { width: 22, height: 22, fontSize: 12, labelFontSize: 10, padding: '3px' },
  lg: { width: 28, height: 28, fontSize: 14, labelFontSize: 11, padding: '4px' },
};

export function VIPBadge({
  level,
  size = 'sm',
  overlay = false,
  showLabel = false,
  className = '',
}: VIPBadgeProps) {
  const normalizedLevel = level.toLowerCase() as VIPLevel;
  const config = LEVEL_CONFIG[normalizedLevel] || LEVEL_CONFIG.bronze;
  const sizeConfig = SIZE_CONFIG[size];

  if (overlay) {
    // 아바타 오버레이 모드 (우하단 작은 배지)
    return (
      <div
        className={className}
        style={{
          position: 'absolute',
          bottom: -2,
          right: -2,
          width: sizeConfig.width,
          height: sizeConfig.height,
          borderRadius: '50%',
          background: `linear-gradient(135deg, ${config.bgColor} 0%, ${config.borderColor} 100%)`,
          border: `1.5px solid ${config.borderColor}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: sizeConfig.fontSize,
          boxShadow: `0 2px 6px ${config.glowColor}`,
          zIndex: 10,
        }}
        title={config.label}
      >
        {config.icon}
      </div>
    );
  }

  if (showLabel) {
    // 라벨과 함께 표시 (인라인)
    return (
      <div
        className={className}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '4px',
          padding: `2px 6px 2px 4px`,
          borderRadius: '10px',
          background: config.bgColor,
          border: `1px solid ${config.borderColor}`,
        }}
      >
        <span style={{ fontSize: sizeConfig.fontSize }}>{config.icon}</span>
        <span
          style={{
            fontSize: sizeConfig.labelFontSize,
            fontWeight: 600,
            color: config.color,
            textShadow: `0 0 4px ${config.glowColor}`,
          }}
        >
          {config.label}
        </span>
      </div>
    );
  }

  // 아이콘만 표시 (인라인)
  return (
    <span
      className={className}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: sizeConfig.width,
        height: sizeConfig.height,
        fontSize: sizeConfig.fontSize,
      }}
      title={config.label}
    >
      {config.icon}
    </span>
  );
}

/**
 * VIP 레벨 유효성 검사
 */
export function isValidVIPLevel(level: string): level is VIPLevel {
  return ['bronze', 'silver', 'gold', 'platinum', 'diamond'].includes(level.toLowerCase());
}

/**
 * VIP 레벨 설정 조회
 */
export function getVIPConfig(level: string) {
  const normalizedLevel = level.toLowerCase() as VIPLevel;
  return LEVEL_CONFIG[normalizedLevel] || LEVEL_CONFIG.bronze;
}

export default VIPBadge;
