'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  EMOTICON_CATEGORIES,
  getEmoticonsByCategory,
  EmoticonCategory,
  Emoticon,
} from '@/constants/emoticons';

interface EmoticonPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (emoticon: Emoticon) => void;
  disabled?: boolean;
}

export default function EmoticonPanel({
  isOpen,
  onClose,
  onSelect,
  disabled = false,
}: EmoticonPanelProps) {
  const [activeCategory, setActiveCategory] = useState<EmoticonCategory>('basic');

  const emoticons = getEmoticonsByCategory(activeCategory);

  const handleSelect = (emoticon: Emoticon) => {
    if (disabled) return;
    onSelect(emoticon);
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* 배경 오버레이 */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            style={{
              position: 'fixed',
              inset: 0,
              zIndex: 100,
            }}
          />

          {/* 패널 */}
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
            className="glass-card"
            style={{
              position: 'absolute',
              bottom: '100%',
              left: '50%',
              transform: 'translateX(-50%)',
              marginBottom: '12px',
              width: '320px',
              padding: '12px',
              zIndex: 101,
              borderRadius: '16px',
              boxShadow: '0 -4px 30px rgba(0,0,0,0.4)',
            }}
          >
            {/* 카테고리 탭 */}
            <div
              style={{
                display: 'flex',
                gap: '6px',
                marginBottom: '12px',
                paddingBottom: '10px',
                borderBottom: '1px solid rgba(255,255,255,0.08)',
                overflowX: 'auto',
              }}
            >
              {EMOTICON_CATEGORIES.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => setActiveCategory(cat.id)}
                  style={{
                    flex: '0 0 auto',
                    padding: '8px 12px',
                    borderRadius: '10px',
                    border: 'none',
                    background:
                      activeCategory === cat.id
                        ? 'linear-gradient(135deg, rgba(245, 158, 11, 0.3) 0%, rgba(217, 119, 6, 0.2) 100%)'
                        : 'rgba(255,255,255,0.05)',
                    color: activeCategory === cat.id ? '#fbbf24' : 'rgba(255,255,255,0.6)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    fontSize: '12px',
                    fontWeight: 500,
                    transition: 'all 0.2s ease',
                  }}
                >
                  <span style={{ fontSize: '16px' }}>{cat.icon}</span>
                  {cat.name}
                </button>
              ))}
            </div>

            {/* 이모티콘 그리드 */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(5, 1fr)',
                gap: '8px',
                maxHeight: '200px',
                overflowY: 'auto',
              }}
            >
              {emoticons.map((emoticon) => (
                <motion.button
                  key={emoticon.id}
                  onClick={() => handleSelect(emoticon)}
                  disabled={disabled}
                  whileHover={{ scale: 1.1, y: -2 }}
                  whileTap={{ scale: 0.9 }}
                  style={{
                    width: '52px',
                    height: '52px',
                    borderRadius: '12px',
                    border: 'none',
                    background: 'rgba(255,255,255,0.05)',
                    cursor: disabled ? 'not-allowed' : 'pointer',
                    opacity: disabled ? 0.5 : 1,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '2px',
                    transition: 'background 0.2s ease',
                  }}
                >
                  <span style={{ fontSize: '24px' }}>{emoticon.emoji}</span>
                  <span
                    style={{
                      fontSize: '9px',
                      color: 'rgba(255,255,255,0.5)',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      maxWidth: '48px',
                    }}
                  >
                    {emoticon.name}
                  </span>
                </motion.button>
              ))}
            </div>

            {/* 하단 힌트 */}
            <p
              style={{
                margin: '10px 0 0',
                textAlign: 'center',
                fontSize: '11px',
                color: 'rgba(255,255,255,0.35)',
              }}
            >
              클릭하여 이모티콘 전송
            </p>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
