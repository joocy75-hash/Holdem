'use client';

import { ReactNode } from 'react';
import { motion } from 'framer-motion';

interface SettingsSectionProps {
  title: string;
  icon?: ReactNode;
  children: ReactNode;
}

export default function SettingsSection({ title, icon, children }: SettingsSectionProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      style={{
        margin: '16px 20px 24px',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          marginBottom: '14px',
          paddingLeft: '4px',
        }}
      >
        {icon && (
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
            {icon}
          </div>
        )}
        <h3
          style={{
            margin: 0,
            fontSize: '13px',
            fontWeight: 600,
            color: 'rgba(255,255,255,0.5)',
            textTransform: 'uppercase',
            letterSpacing: '0.8px',
          }}
        >
          {title}
        </h3>
      </div>
      <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
        {children}
      </div>
    </motion.div>
  );
}
