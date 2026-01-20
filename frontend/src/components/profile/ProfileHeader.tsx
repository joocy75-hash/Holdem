'use client';

import { motion } from 'framer-motion';
import { UserProfile } from '@/lib/api';
import { Avatar } from '@/components/common';
import { VIPBadge } from '@/components/common/VIPBadge';

interface ProfileHeaderProps {
  user: UserProfile | null;
  vipLevel?: string | null;
  onEditClick: () => void;
}

export default function ProfileHeader({ user, vipLevel, onEditClick }: ProfileHeaderProps) {
  return (
    <div
      style={{
        padding: '28px 20px',
        textAlign: 'center',
        position: 'relative',
        zIndex: 1,
      }}
    >
      {/* 아바타 */}
      <div
        style={{
          position: 'relative',
          display: 'inline-block',
          margin: '0 auto 20px',
        }}
      >
        {/* 아바타 글로우 효과 */}
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: '100px',
            height: '100px',
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(139, 92, 246, 0.3) 0%, transparent 70%)',
            filter: 'blur(15px)',
          }}
        />
        <Avatar
          avatarId={user?.avatar_url ?? null}
          size="xl"
          nickname={user?.nickname}
          showVIPBadge={false}
        />
        {/* 편집 버튼 */}
        <motion.button
          onClick={onEditClick}
          whileHover={{ scale: 1.15 }}
          whileTap={{ scale: 0.9 }}
          style={{
            position: 'absolute',
            bottom: 0,
            right: 0,
            width: '36px',
            height: '36px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
            border: '3px solid rgba(15, 23, 42, 0.9)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 15px rgba(245, 158, 11, 0.4)',
          }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="white">
            <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z" />
          </svg>
        </motion.button>
      </div>

      {/* 닉네임 + VIP 배지 */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '8px',
          margin: '0 0 8px 0',
        }}
      >
        <h2
          style={{
            fontSize: '26px',
            fontWeight: 700,
            color: 'white',
            margin: 0,
            textShadow: '0 2px 10px rgba(0,0,0,0.3)',
          }}
        >
          {user?.nickname || '로딩 중...'}
        </h2>
        {vipLevel && <VIPBadge level={vipLevel} size="md" showLabel />}
      </div>

      {/* 이메일 */}
      <p
        style={{
          fontSize: '14px',
          color: 'rgba(255,255,255,0.5)',
          margin: '0 0 20px 0',
        }}
      >
        {user?.email || ''}
      </p>

      {/* 잔액 */}
      <div
        className="glass-card"
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '10px',
          padding: '14px 28px',
          background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.12) 0%, rgba(217, 119, 6, 0.06) 100%)',
          borderColor: 'rgba(245, 158, 11, 0.2)',
        }}
      >
        <span style={{ color: 'rgba(255,255,255,0.5)', fontSize: '14px' }}>잔액</span>
        <span
          className="glow-text-gold"
          style={{
            fontSize: '22px',
            fontWeight: 700,
          }}
        >
          {user?.balance?.toLocaleString() || '0'}
        </span>
        <span style={{ color: 'rgba(255,255,255,0.5)', fontSize: '14px' }}>원</span>
      </div>
    </div>
  );
}
