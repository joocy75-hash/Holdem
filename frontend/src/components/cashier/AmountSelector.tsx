'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import RecentTransactions from './RecentTransactions';

interface AmountSelectorProps {
  exchangeRate: string | null;
  balance: number;
  onSelect: (amount: number) => void;
  isLoading: boolean;
}

const PRESET_AMOUNTS = [
  { krw: 10000, label: '1만원' },
  { krw: 30000, label: '3만원' },
  { krw: 50000, label: '5만원' },
  { krw: 100000, label: '10만원' },
  { krw: 300000, label: '30만원' },
  { krw: 500000, label: '50만원' },
];

export default function AmountSelector({
  exchangeRate,
  balance,
  onSelect,
  isLoading,
}: AmountSelectorProps) {
  const [customAmount, setCustomAmount] = useState<string>('');
  const [selectedPreset, setSelectedPreset] = useState<number | null>(null);

  const rate = exchangeRate ? parseFloat(exchangeRate) : null;

  const calculateUsdt = (krw: number): string => {
    if (!rate) return '-';
    return (krw / rate).toFixed(2);
  };

  const handlePresetClick = (amount: number) => {
    setSelectedPreset(amount);
    setCustomAmount('');
  };

  const handleCustomChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/[^0-9]/g, '');
    setCustomAmount(value);
    setSelectedPreset(null);
  };

  const handleSubmit = () => {
    const amount = selectedPreset || parseInt(customAmount) || 0;
    if (amount >= 10000) {
      onSelect(amount);
    }
  };

  const currentAmount = selectedPreset || parseInt(customAmount) || 0;
  const isValid = currentAmount >= 10000;

  return (
    <div style={{ padding: '20px', position: 'relative', zIndex: 1 }}>
      {/* 내 잔액 표시 - Glass Card */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.2 }}
        className="glass-card"
        style={{
          padding: '20px',
          marginBottom: '24px',
          textAlign: 'center',
        }}
      >
        <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '12px', marginBottom: '4px', margin: 0 }}>
          내 잔액
        </p>
        <p
          className="glow-text-gold"
          style={{
            fontSize: '28px',
            fontWeight: 700,
            margin: '8px 0 0 0',
          }}
        >
          {balance.toLocaleString()}
        </p>
      </motion.div>

      {/* 프리셋 금액 버튼 */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '10px',
          marginBottom: '24px',
        }}
      >
        {PRESET_AMOUNTS.map(({ krw, label }) => (
          <motion.button
            key={krw}
            onClick={() => handlePresetClick(krw)}
            whileHover={{ scale: 1.03, y: -2 }}
            whileTap={{ scale: 0.97 }}
            style={{
              padding: '18px 8px',
              background:
                selectedPreset === krw
                  ? 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'
                  : 'rgba(255,255,255,0.03)',
              border:
                selectedPreset === krw
                  ? 'none'
                  : '1px solid rgba(255,255,255,0.08)',
              borderRadius: '16px',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              boxShadow:
                selectedPreset === krw
                  ? '0 8px 25px rgba(245, 158, 11, 0.35), inset 0 1px 0 rgba(255,255,255,0.2)'
                  : '0 4px 15px rgba(0,0,0,0.2)',
              backdropFilter: 'blur(10px)',
            }}
          >
            <p
              style={{
                color: 'white',
                fontWeight: 700,
                fontSize: '16px',
                marginBottom: '4px',
                margin: 0,
                textShadow: selectedPreset === krw ? '0 2px 4px rgba(0,0,0,0.3)' : 'none',
              }}
            >
              {label}
            </p>
            <p
              style={{
                color: selectedPreset === krw ? 'rgba(255,255,255,0.85)' : '#fbbf24',
                fontSize: '12px',
                margin: '6px 0 0 0',
                fontWeight: 500,
              }}
            >
              {calculateUsdt(krw)} USDT
            </p>
          </motion.button>
        ))}
      </div>

      {/* 직접 입력 */}
      <div style={{ marginBottom: '24px' }}>
        <label
          style={{
            display: 'block',
            color: 'rgba(255,255,255,0.5)',
            fontSize: '12px',
            marginBottom: '10px',
            fontWeight: 500,
          }}
        >
          직접 입력 (최소 10,000원)
        </label>
        <div style={{ position: 'relative' }}>
          <input
            type="text"
            value={customAmount ? parseInt(customAmount).toLocaleString() : ''}
            onChange={handleCustomChange}
            placeholder="금액 입력"
            className="glass-input"
            style={{
              width: '100%',
              padding: '18px',
              paddingRight: '50px',
              fontSize: '16px',
              boxSizing: 'border-box',
            }}
          />
          <span
            style={{
              position: 'absolute',
              right: '18px',
              top: '50%',
              transform: 'translateY(-50%)',
              color: 'rgba(255,255,255,0.4)',
              fontWeight: 500,
            }}
          >
            원
          </span>
        </div>
        {customAmount && parseInt(customAmount) >= 10000 && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            style={{
              color: '#fbbf24',
              fontSize: '14px',
              marginTop: '10px',
              margin: '10px 0 0 0',
              fontWeight: 500,
            }}
          >
            = {calculateUsdt(parseInt(customAmount))} USDT
          </motion.p>
        )}
      </div>

      {/* 충전 버튼 */}
      <motion.button
        onClick={handleSubmit}
        disabled={!isValid || isLoading}
        whileHover={isValid && !isLoading ? { scale: 1.02, y: -2 } : {}}
        whileTap={isValid && !isLoading ? { scale: 0.98 } : {}}
        style={{
          width: '100%',
          padding: '18px',
          borderRadius: '16px',
          color: 'white',
          fontWeight: 700,
          fontSize: '18px',
          cursor: isValid && !isLoading ? 'pointer' : 'not-allowed',
          opacity: isValid ? 1 : 0.5,
          background: isValid
            ? 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'
            : 'rgba(255,255,255,0.05)',
          border: isValid ? 'none' : '1px solid rgba(255,255,255,0.1)',
          boxShadow: isValid
            ? '0 4px 15px rgba(245, 158, 11, 0.4), inset 0 1px 0 rgba(255,255,255,0.2)'
            : 'none',
        }}
      >
        {isLoading ? (
          <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px' }}>
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
              style={{
                width: '20px',
                height: '20px',
                border: '2px solid rgba(255,255,255,0.3)',
                borderTopColor: 'white',
                borderRadius: '50%',
              }}
            />
            처리 중...
          </span>
        ) : (
          `${currentAmount.toLocaleString()}원 충전하기`
        )}
      </motion.button>

      {/* 최근 충전 기록 */}
      <RecentTransactions txType="crypto_deposit" title="최근 충전 기록" />
    </div>
  );
}
