'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';

interface WithdrawAddressInputProps {
  amount: number;
  calculatedUsdt: string | null;
  address: string;
  onAddressChange: (address: string) => void;
  onConfirm: () => void;
  onBack: () => void;
  isLoading: boolean;
  error: string | null;
}

const quickSpring = { type: 'spring' as const, stiffness: 400, damping: 20 };

export default function WithdrawAddressInput({
  amount,
  calculatedUsdt,
  address,
  onAddressChange,
  onConfirm,
  onBack,
  isLoading,
  error,
}: WithdrawAddressInputProps) {
  const [localAddress, setLocalAddress] = useState(address);

  // USDT TRC-20 주소 형식 검증 (T로 시작, 34자)
  const isValidAddress = (addr: string): boolean => {
    return /^T[a-zA-Z0-9]{33}$/.test(addr);
  };

  const handleAddressChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.trim();
    setLocalAddress(value);
    onAddressChange(value);
  };

  const handleConfirm = () => {
    if (isValidAddress(localAddress)) {
      onConfirm();
    }
  };

  const addressValid = isValidAddress(localAddress);
  const showAddressError = localAddress.length > 0 && !addressValid && localAddress.length >= 34;

  return (
    <div style={{ padding: '20px' }}>
      {/* 환전 정보 요약 */}
      <div
        style={{
          background: 'rgba(255,255,255,0.05)',
          borderRadius: '12px',
          padding: '16px',
          marginBottom: '20px',
          border: '1px solid rgba(255,255,255,0.1)',
        }}
      >
        <p style={{ color: '#888', fontSize: '12px', marginBottom: '8px', margin: 0 }}>
          환전 금액
        </p>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
          <span style={{ color: 'white', fontSize: '24px', fontWeight: 700 }}>
            {amount.toLocaleString()}원
          </span>
          <span style={{ color: 'var(--figma-balance-color)', fontSize: '16px' }}>
            = {calculatedUsdt} USDT
          </span>
        </div>
      </div>

      {/* USDT 네트워크 안내 */}
      <div
        style={{
          background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(34, 197, 94, 0.05) 100%)',
          borderRadius: '12px',
          padding: '16px',
          marginBottom: '20px',
          border: '1px solid rgba(34, 197, 94, 0.2)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              background: '#26a17b',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '14px',
              fontWeight: 700,
              color: 'white',
            }}
          >
            ₮
          </div>
          <div>
            <p style={{ color: 'white', fontWeight: 600, margin: 0 }}>USDT (TRC-20)</p>
            <p style={{ color: '#888', fontSize: '12px', margin: '2px 0 0 0' }}>Tron 네트워크</p>
          </div>
        </div>
        <p style={{ color: '#888', fontSize: '12px', margin: 0 }}>
          반드시 TRC-20 네트워크 주소를 입력해주세요. 다른 네트워크로 전송 시 복구가 불가능합니다.
        </p>
      </div>

      {/* 주소 입력 */}
      <div style={{ marginBottom: '24px' }}>
        <label
          style={{
            display: 'block',
            color: '#888',
            fontSize: '12px',
            marginBottom: '8px',
          }}
        >
          USDT 수신 주소 (TRC-20)
        </label>
        <input
          type="text"
          value={localAddress}
          onChange={handleAddressChange}
          placeholder="T로 시작하는 34자리 주소"
          style={{
            width: '100%',
            padding: '16px',
            background: 'rgba(255,255,255,0.05)',
            border: showAddressError
              ? '1px solid #ef4444'
              : addressValid
              ? '1px solid #22c55e'
              : '1px solid rgba(255,255,255,0.1)',
            borderRadius: '12px',
            color: 'white',
            fontSize: '14px',
            fontFamily: 'monospace',
            outline: 'none',
            boxSizing: 'border-box',
          }}
        />
        {showAddressError && (
          <p style={{ color: '#ef4444', fontSize: '12px', margin: '8px 0 0 0' }}>
            올바른 TRC-20 주소 형식이 아닙니다 (T로 시작, 34자)
          </p>
        )}
        {addressValid && (
          <p style={{ color: '#22c55e', fontSize: '12px', margin: '8px 0 0 0' }}>
            올바른 주소 형식입니다
          </p>
        )}
      </div>

      {/* 에러 메시지 */}
      {error && (
        <div
          style={{
            background: 'rgba(239, 68, 68, 0.1)',
            borderRadius: '8px',
            padding: '12px',
            marginBottom: '20px',
            border: '1px solid rgba(239, 68, 68, 0.2)',
          }}
        >
          <p style={{ color: '#f87171', fontSize: '13px', margin: 0 }}>{error}</p>
        </div>
      )}

      {/* 버튼 영역 */}
      <div style={{ display: 'flex', gap: '12px' }}>
        <motion.button
          onClick={onBack}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          transition={quickSpring}
          style={{
            flex: 1,
            padding: '16px',
            background: 'rgba(255,255,255,0.1)',
            border: 'none',
            borderRadius: '12px',
            color: 'white',
            fontWeight: 600,
            fontSize: '16px',
            cursor: 'pointer',
          }}
        >
          이전
        </motion.button>
        <motion.button
          onClick={handleConfirm}
          disabled={!addressValid || isLoading}
          whileHover={addressValid && !isLoading ? { scale: 1.02 } : {}}
          whileTap={addressValid && !isLoading ? { scale: 0.98 } : {}}
          transition={quickSpring}
          style={{
            flex: 2,
            padding: '16px',
            background: addressValid
              ? 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'
              : 'rgba(255,255,255,0.1)',
            border: 'none',
            borderRadius: '12px',
            color: 'white',
            fontWeight: 700,
            fontSize: '16px',
            cursor: addressValid && !isLoading ? 'pointer' : 'not-allowed',
            opacity: addressValid ? 1 : 0.5,
          }}
        >
          {isLoading ? '처리 중...' : '다음'}
        </motion.button>
      </div>
    </div>
  );
}
