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
    <div style={{ padding: '20px', position: 'relative', zIndex: 1 }}>
      {/* 환전 정보 요약 */}
      <div
        className="glass-card"
        style={{
          padding: '20px',
          marginBottom: '20px',
        }}
      >
        <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '12px', marginBottom: '8px', margin: 0 }}>
          환전 금액
        </p>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '10px' }}>
          <span style={{ color: 'white', fontSize: '26px', fontWeight: 700 }}>
            {amount.toLocaleString()}원
          </span>
          <span className="glow-text-gold" style={{ fontSize: '16px', fontWeight: 600 }}>
            = {calculatedUsdt} USDT
          </span>
        </div>
      </div>

      {/* USDT 네트워크 안내 */}
      <div
        className="glass-card"
        style={{
          padding: '18px',
          marginBottom: '20px',
          background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.12) 0%, rgba(22, 163, 74, 0.06) 100%)',
          borderColor: 'rgba(34, 197, 94, 0.25)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '10px' }}>
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #26a17b 0%, #1a8a6a 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '16px',
              fontWeight: 700,
              color: 'white',
              boxShadow: '0 4px 12px rgba(38, 161, 123, 0.4)',
            }}
          >
            ₮
          </div>
          <div>
            <p style={{ color: 'white', fontWeight: 600, margin: 0, fontSize: '15px' }}>USDT (TRC-20)</p>
            <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '12px', margin: '2px 0 0 0' }}>Tron 네트워크</p>
          </div>
        </div>
        <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: '12px', margin: 0, lineHeight: 1.6 }}>
          반드시 TRC-20 네트워크 주소를 입력해주세요. 다른 네트워크로 전송 시 복구가 불가능합니다.
        </p>
      </div>

      {/* 주소 입력 */}
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
          USDT 수신 주소 (TRC-20)
        </label>
        <input
          type="text"
          value={localAddress}
          onChange={handleAddressChange}
          placeholder="T로 시작하는 34자리 주소"
          className="glass-input"
          style={{
            width: '100%',
            padding: '18px',
            fontSize: '14px',
            fontFamily: 'monospace',
            boxSizing: 'border-box',
            borderColor: showAddressError
              ? 'rgba(239, 68, 68, 0.5)'
              : addressValid
              ? 'rgba(34, 197, 94, 0.5)'
              : undefined,
            boxShadow: addressValid
              ? '0 0 15px rgba(34, 197, 94, 0.15)'
              : showAddressError
              ? '0 0 15px rgba(239, 68, 68, 0.15)'
              : undefined,
          }}
        />
        {showAddressError && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            style={{ color: '#ef4444', fontSize: '12px', margin: '10px 0 0 0' }}
          >
            올바른 TRC-20 주소 형식이 아닙니다 (T로 시작, 34자)
          </motion.p>
        )}
        {addressValid && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            style={{ color: '#22c55e', fontSize: '12px', margin: '10px 0 0 0', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="#22c55e">
              <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
            </svg>
            올바른 주소 형식입니다
          </motion.p>
        )}
      </div>

      {/* 에러 메시지 */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card"
          style={{
            padding: '14px',
            marginBottom: '20px',
            background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.12) 0%, rgba(220, 38, 38, 0.06) 100%)',
            borderColor: 'rgba(239, 68, 68, 0.25)',
          }}
        >
          <p style={{ color: '#f87171', fontSize: '13px', margin: 0 }}>{error}</p>
        </motion.div>
      )}

      {/* 버튼 영역 */}
      <div style={{ display: 'flex', gap: '12px' }}>
        <motion.button
          onClick={onBack}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="glass-btn"
          style={{
            flex: 1,
            padding: '16px',
            fontSize: '16px',
            fontWeight: 600,
          }}
        >
          이전
        </motion.button>
        <motion.button
          onClick={handleConfirm}
          disabled={!addressValid || isLoading}
          whileHover={addressValid && !isLoading ? { scale: 1.02 } : {}}
          whileTap={addressValid && !isLoading ? { scale: 0.98 } : {}}
          className={addressValid ? 'gradient-btn-gold' : ''}
          style={{
            flex: 2,
            padding: '16px',
            background: addressValid
              ? undefined
              : 'rgba(255,255,255,0.05)',
            border: addressValid ? undefined : '1px solid rgba(255,255,255,0.1)',
            borderRadius: '16px',
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
