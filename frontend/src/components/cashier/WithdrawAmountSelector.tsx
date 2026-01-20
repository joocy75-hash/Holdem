'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import RecentTransactions from './RecentTransactions';

interface WithdrawAmountSelectorProps {
  balance: number;
  exchangeRate: string | null;
  onSelect: (amount: number) => void;
  isLoading: boolean;
  disabled?: boolean;
}

const PRESET_AMOUNTS = [
  { krw: 10000, label: '1만원' },
  { krw: 30000, label: '3만원' },
  { krw: 50000, label: '5만원' },
  { krw: 100000, label: '10만원' },
  { krw: 300000, label: '30만원' },
  { krw: 500000, label: '50만원' },
];

export default function WithdrawAmountSelector({
  balance,
  exchangeRate,
  onSelect,
  isLoading,
  disabled = false,
}: WithdrawAmountSelectorProps) {
  const [customAmount, setCustomAmount] = useState<string>('');
  const [selectedPreset, setSelectedPreset] = useState<number | null>(null);

  const rate = exchangeRate ? parseFloat(exchangeRate) : null;

  const calculateUsdt = (krw: number): string => {
    if (!rate) return '-';
    return (krw / rate).toFixed(2);
  };

  const handlePresetClick = (amount: number) => {
    if (disabled) return;
    if (amount <= balance) {
      setSelectedPreset(amount);
      setCustomAmount('');
    }
  };

  const handleCustomChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/[^0-9]/g, '');
    setCustomAmount(value);
    setSelectedPreset(null);
  };

  const handleSubmit = () => {
    const amount = selectedPreset || parseInt(customAmount) || 0;
    if (amount >= 10000 && amount <= balance) {
      onSelect(amount);
    }
  };

  const currentAmount = selectedPreset || parseInt(customAmount) || 0;
  const isValid = !disabled && currentAmount >= 10000 && currentAmount <= balance;

  return (
    <div style={{ padding: '20px', position: 'relative', zIndex: 1 }}>
      {/* 잔액 및 환율 표시 */}
      <div
        className="glass-card"
        style={{
          padding: '18px',
          marginBottom: '16px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '14px' }}>
          <span style={{ color: 'rgba(255,255,255,0.5)', fontSize: '13px' }}>출금 가능 잔액</span>
          <span className="glow-text-gold" style={{ fontSize: '16px', fontWeight: 700 }}>
            {balance.toLocaleString()}원
          </span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: 'rgba(255,255,255,0.5)', fontSize: '13px' }}>현재 환율</span>
          <span style={{ color: 'white', fontSize: '15px', fontWeight: 500 }}>
            1 USDT = {rate ? `${rate.toLocaleString()}원` : '로딩 중...'}
          </span>
        </div>
      </div>

      {/* 24시간 유예 안내 */}
      <div
        className="glass-card"
        style={{
          padding: '14px 16px',
          marginBottom: '20px',
          background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.12) 0%, rgba(220, 38, 38, 0.06) 100%)',
          borderColor: 'rgba(239, 68, 68, 0.25)',
        }}
      >
        <p style={{ color: '#f87171', fontSize: '13px', margin: 0, lineHeight: 1.6 }}>
          환전 요청 후 24시간 보안 대기 기간이 있습니다.
          <br />
          대기 중 언제든 취소할 수 있습니다.
        </p>
      </div>

      {/* 프리셋 금액 버튼 */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '10px',
          marginBottom: '24px',
        }}
      >
        {PRESET_AMOUNTS.map(({ krw, label }) => {
          const isDisabled = krw > balance;
          const isSelected = selectedPreset === krw;

          return (
            <motion.button
              key={krw}
              onClick={() => handlePresetClick(krw)}
              disabled={isDisabled}
              whileHover={!isDisabled ? { scale: 1.03, y: -2 } : {}}
              whileTap={!isDisabled ? { scale: 0.97 } : {}}
              style={{
                padding: '18px 8px',
                background: isSelected
                  ? 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'
                  : 'rgba(255,255,255,0.03)',
                border: isSelected
                  ? 'none'
                  : '1px solid rgba(255,255,255,0.08)',
                borderRadius: '16px',
                cursor: isDisabled ? 'not-allowed' : 'pointer',
                opacity: isDisabled ? 0.35 : 1,
                transition: 'all 0.3s ease',
                boxShadow: isSelected
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
                  textShadow: isSelected ? '0 2px 4px rgba(0,0,0,0.3)' : 'none',
                }}
              >
                {label}
              </p>
              <p
                style={{
                  color: isSelected ? 'rgba(255,255,255,0.85)' : '#fbbf24',
                  fontSize: '12px',
                  margin: '6px 0 0 0',
                  fontWeight: 500,
                }}
              >
                {calculateUsdt(krw)} USDT
              </p>
            </motion.button>
          );
        })}
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
          직접 입력 (최소 10,000원 / 최대 {balance.toLocaleString()}원)
        </label>
        <div style={{ position: 'relative' }}>
          <input
            type="text"
            value={customAmount ? parseInt(customAmount).toLocaleString() : ''}
            onChange={handleCustomChange}
            placeholder="금액 입력"
            className="glass-input"
            disabled={disabled}
            style={{
              width: '100%',
              padding: '18px',
              paddingRight: '50px',
              fontSize: '16px',
              boxSizing: 'border-box',
              opacity: disabled ? 0.5 : 1,
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
              color: parseInt(customAmount) > balance ? '#ef4444' : '#fbbf24',
              fontSize: '14px',
              marginTop: '10px',
              margin: '10px 0 0 0',
              fontWeight: 500,
            }}
          >
            {parseInt(customAmount) > balance
              ? '잔액을 초과했습니다'
              : `= ${calculateUsdt(parseInt(customAmount))} USDT`}
          </motion.p>
        )}
      </div>

      {/* 다음 버튼 */}
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
          `${currentAmount.toLocaleString()}원 환전하기`
        )}
      </motion.button>

      {/* 최근 환전 기록 */}
      <RecentTransactions txType="crypto_withdrawal" title="최근 환전 기록" />
    </div>
  );
}
