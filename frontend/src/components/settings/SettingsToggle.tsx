'use client';

import { motion } from 'framer-motion';

interface SettingsToggleProps {
  label: string;
  description?: string;
  value: boolean;
  onChange: (value: boolean) => void;
  showDivider?: boolean;
}

export default function SettingsToggle({
  label,
  description,
  value,
  onChange,
  showDivider = true,
}: SettingsToggleProps) {
  return (
    <div
      style={{
        padding: '16px 18px',
        borderBottom: showDivider ? '1px solid rgba(255,255,255,0.06)' : 'none',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}
    >
      <div style={{ flex: 1, marginRight: '16px' }}>
        <p style={{ margin: 0, color: 'white', fontSize: '15px', fontWeight: 500 }}>
          {label}
        </p>
        {description && (
          <p style={{ margin: '5px 0 0', color: 'rgba(255,255,255,0.4)', fontSize: '12px', lineHeight: 1.4 }}>
            {description}
          </p>
        )}
      </div>
      <motion.button
        onClick={() => onChange(!value)}
        whileTap={{ scale: 0.9 }}
        style={{
          width: '52px',
          height: '30px',
          borderRadius: '15px',
          background: value
            ? 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)'
            : 'rgba(255,255,255,0.1)',
          border: value ? 'none' : '1px solid rgba(255,255,255,0.1)',
          cursor: 'pointer',
          position: 'relative',
          transition: 'background 0.3s, border 0.3s',
          boxShadow: value ? '0 2px 10px rgba(34, 197, 94, 0.3)' : 'none',
        }}
      >
        <motion.div
          animate={{ x: value ? 22 : 0 }}
          transition={{ type: 'spring', stiffness: 500, damping: 30 }}
          style={{
            position: 'absolute',
            top: '3px',
            left: '3px',
            width: '24px',
            height: '24px',
            borderRadius: '12px',
            background: 'white',
            boxShadow: '0 2px 6px rgba(0,0,0,0.2)',
          }}
        />
      </motion.button>
    </div>
  );
}
