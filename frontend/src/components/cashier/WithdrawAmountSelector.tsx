'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';

interface WithdrawAmountSelectorProps {
  balance: number;
  exchangeRate: string | null;
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

const quickSpring = { type: 'spring' as const, stiffness: 400, damping: 20 };

export default function WithdrawAmountSelector({
  balance,
  exchangeRate,
  onSelect,
  isLoading,
}: WithdrawAmountSelectorProps) {
  const [customAmount, setCustomAmount] = useState<string>('');
  const [selectedPreset, setSelectedPreset] = useState<number | null>(null);

  const rate = exchangeRate ? parseFloat(exchangeRate) : null;

  const calculateUsdt = (krw: number): string => {
    if (!rate) return '-';
    return (krw / rate).toFixed(2);
  };

  const handlePresetClick = (amount: number) => {
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
  const isValid = currentAmount >= 10000 && currentAmount <= balance;

  return (
    <div style={{ padding: '20px' }}>
      {/* 잔액 및 환율 표시 */}
      <div
        style={{
          background: 'rgba(255,255,255,0.05)',
          borderRadius: '12px',
          padding: '16px',
          marginBottom: '16px',
          border: '1px solid rgba(255,255,255,0.1)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
          <span style={{ color: '#888', fontSize: '13px' }}>출금 가능 잔액</span>
          <span style={{ color: 'var(--figma-balance-color)', fontSize: '15px', fontWeight: 600 }}>
            {balance.toLocaleString()}원
          </span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: '#888', fontSize: '13px' }}>현재 환율</span>
          <span style={{ color: 'white', fontSize: '15px', fontWeight: 500 }}>
            1 USDT = {rate ? `${rate.toLocaleString()}원` : '로딩 중...'}
          </span>
        </div>
      </div>

      {/* 24시간 유예 안내 */}
      <div
        style={{
          background: 'rgba(239, 68, 68, 0.1)',
          borderRadius: '8px',
          padding: '12px',
          marginBottom: '20px',
          border: '1px solid rgba(239, 68, 68, 0.2)',
        }}
      >
        <p style={{ color: '#f87171', fontSize: '13px', margin: 0, lineHeight: 1.5 }}>
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
          gap: '12px',
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
              whileHover={!isDisabled ? { scale: 1.02 } : {}}
              whileTap={!isDisabled ? { scale: 0.98 } : {}}
              transition={quickSpring}
              style={{
                padding: '16px 8px',
                background: isSelected
                  ? 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'
                  : 'rgba(255,255,255,0.05)',
                border: isSelected
                  ? '2px solid #f59e0b'
                  : '1px solid rgba(255,255,255,0.1)',
                borderRadius: '12px',
                cursor: isDisabled ? 'not-allowed' : 'pointer',
                opacity: isDisabled ? 0.4 : 1,
                transition: 'all 0.2s',
              }}
            >
              <p
                style={{
                  color: 'white',
                  fontWeight: 600,
                  fontSize: '16px',
                  marginBottom: '4px',
                  margin: 0,
                }}
              >
                {label}
              </p>
              <p
                style={{
                  color: isSelected ? 'rgba(255,255,255,0.8)' : 'var(--figma-balance-color)',
                  fontSize: '12px',
                  margin: '4px 0 0 0',
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
            color: '#888',
            fontSize: '12px',
            marginBottom: '8px',
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
            style={{
              width: '100%',
              padding: '16px',
              paddingRight: '40px',
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '12px',
              color: 'white',
              fontSize: '16px',
              outline: 'none',
              boxSizing: 'border-box',
            }}
          />
          <span
            style={{
              position: 'absolute',
              right: '16px',
              top: '50%',
              transform: 'translateY(-50%)',
              color: '#888',
            }}
          >
            원
          </span>
        </div>
        {customAmount && parseInt(customAmount) >= 10000 && (
          <p
            style={{
              color: parseInt(customAmount) > balance ? '#ef4444' : 'var(--figma-balance-color)',
              fontSize: '14px',
              marginTop: '8px',
              margin: '8px 0 0 0',
            }}
          >
            {parseInt(customAmount) > balance
              ? '잔액을 초과했습니다'
              : `= ${calculateUsdt(parseInt(customAmount))} USDT`}
          </p>
        )}
      </div>

      {/* 다음 버튼 */}
      <motion.button
        onClick={handleSubmit}
        disabled={!isValid || isLoading}
        whileHover={isValid && !isLoading ? { scale: 1.02 } : {}}
        whileTap={isValid && !isLoading ? { scale: 0.98 } : {}}
        transition={quickSpring}
        style={{
          width: '100%',
          padding: '18px',
          background: isValid
            ? 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'
            : 'rgba(255,255,255,0.1)',
          border: 'none',
          borderRadius: '12px',
          color: 'white',
          fontWeight: 700,
          fontSize: '18px',
          cursor: isValid && !isLoading ? 'pointer' : 'not-allowed',
          opacity: isValid ? 1 : 0.5,
        }}
      >
        {isLoading ? '처리 중...' : `${currentAmount.toLocaleString()}원 환전하기`}
      </motion.button>
    </div>
  );
}
