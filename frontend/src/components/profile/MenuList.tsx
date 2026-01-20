'use client';

import { motion } from 'framer-motion';

interface MenuListProps {
  onEditProfile: () => void;
  onChangePassword: () => void;
  onLogout: () => void;
}

interface MenuItemProps {
  icon: React.ReactNode;
  iconBg: string;
  label: string;
  onClick: () => void;
  color?: string;
  isLast?: boolean;
}

function MenuItem({ icon, iconBg, label, onClick, color = 'white', isLast = false }: MenuItemProps) {
  return (
    <motion.button
      onClick={onClick}
      whileHover={{ backgroundColor: 'rgba(255,255,255,0.05)' }}
      whileTap={{ scale: 0.98 }}
      style={{
        width: '100%',
        padding: '16px 18px',
        background: 'transparent',
        border: 'none',
        borderBottom: isLast ? 'none' : '1px solid rgba(255,255,255,0.06)',
        display: 'flex',
        alignItems: 'center',
        gap: '14px',
        cursor: 'pointer',
        color,
        transition: 'background 0.2s',
      }}
    >
      <div
        style={{
          width: '36px',
          height: '36px',
          borderRadius: '10px',
          background: iconBg,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {icon}
      </div>
      <span style={{ fontSize: '15px', flex: 1, textAlign: 'left', fontWeight: 500 }}>{label}</span>
      <svg width="18" height="18" viewBox="0 0 24 24" fill="rgba(255,255,255,0.3)">
        <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z" />
      </svg>
    </motion.button>
  );
}

export default function MenuList({ onEditProfile, onChangePassword, onLogout }: MenuListProps) {
  return (
    <div
      className="glass-card"
      style={{
        margin: '0 20px 20px',
        overflow: 'hidden',
        padding: 0,
        position: 'relative',
        zIndex: 1,
      }}
    >
      <MenuItem
        icon={
          <svg width="18" height="18" viewBox="0 0 24 24" fill="white">
            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
          </svg>
        }
        iconBg="linear-gradient(135deg, rgba(59, 130, 246, 0.25) 0%, rgba(37, 99, 235, 0.15) 100%)"
        label="프로필 수정"
        onClick={onEditProfile}
      />

      <MenuItem
        icon={
          <svg width="18" height="18" viewBox="0 0 24 24" fill="white">
            <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z" />
          </svg>
        }
        iconBg="linear-gradient(135deg, rgba(139, 92, 246, 0.25) 0%, rgba(124, 58, 237, 0.15) 100%)"
        label="비밀번호 변경"
        onClick={onChangePassword}
      />

      <MenuItem
        icon={
          <svg width="18" height="18" viewBox="0 0 24 24" fill="white">
            <path d="M13 3h-2v10h2V3zm4.83 2.17l-1.42 1.42C17.99 7.86 19 9.81 19 12c0 3.87-3.13 7-7 7s-7-3.13-7-7c0-2.19 1.01-4.14 2.58-5.42L6.17 5.17C4.23 6.82 3 9.26 3 12c0 4.97 4.03 9 9 9s9-4.03 9-9c0-2.74-1.23-5.18-3.17-6.83z" />
          </svg>
        }
        iconBg="linear-gradient(135deg, rgba(239, 68, 68, 0.25) 0%, rgba(220, 38, 38, 0.15) 100%)"
        label="로그아웃"
        onClick={onLogout}
        color="#f87171"
        isLast={true}
      />
    </div>
  );
}
