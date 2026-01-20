'use client';

import { motion } from 'framer-motion';

interface EmoticonButtonProps {
  onClick: () => void;
  isActive?: boolean;
  disabled?: boolean;
}

export default function EmoticonButton({
  onClick,
  isActive = false,
  disabled = false,
}: EmoticonButtonProps) {
  return (
    <motion.button
      onClick={onClick}
      disabled={disabled}
      whileHover={!disabled ? { scale: 1.05, y: -2 } : {}}
      whileTap={!disabled ? { scale: 0.95 } : {}}
      style={{
        width: '48px',
        height: '48px',
        borderRadius: '14px',
        border: 'none',
        background: isActive
          ? 'linear-gradient(135deg, rgba(245, 158, 11, 0.3) 0%, rgba(217, 119, 6, 0.2) 100%)'
          : 'rgba(255,255,255,0.08)',
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.5 : 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: isActive
          ? '0 4px 15px rgba(245, 158, 11, 0.2), inset 0 1px 0 rgba(255,255,255,0.1)'
          : '0 2px 8px rgba(0,0,0,0.2)',
        transition: 'all 0.2s ease',
      }}
    >
      <span style={{ fontSize: '24px' }}>
        {isActive ? '😊' : '😀'}
      </span>
    </motion.button>
  );
}
