'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface WaitlistJoinModalProps {
  isOpen: boolean;
  onClose: () => void;
  onJoin: (buyIn: number) => void;
  roomName: string;
  minBuyIn: number;
  maxBuyIn: number;
  currentWaitlistCount: number;
  userBalance: number;
  isLoading: boolean;
}

export default function WaitlistJoinModal({
  isOpen,
  onClose,
  onJoin,
  roomName,
  minBuyIn,
  maxBuyIn,
  currentWaitlistCount,
  userBalance,
  isLoading,
}: WaitlistJoinModalProps) {
  const [buyIn, setBuyIn] = useState<number>(minBuyIn);
  const [error, setError] = useState<string | null>(null);

  const handleBuyInChange = (value: number) => {
    setBuyIn(Math.max(minBuyIn, Math.min(maxBuyIn, value)));
    setError(null);
  };

  const handleSubmit = () => {
    if (buyIn < minBuyIn || buyIn > maxBuyIn) {
      setError(`바이인은 ${minBuyIn.toLocaleString()} ~ ${maxBuyIn.toLocaleString()} 범위여야 합니다`);
      return;
    }

    if (buyIn > userBalance) {
      setError('잔액이 부족합니다');
      return;
    }

    onJoin(buyIn);
  };

  const presetAmounts = [
    { label: '최소', value: minBuyIn },
    { label: '1/2', value: Math.floor((minBuyIn + maxBuyIn) / 2) },
    { label: '최대', value: maxBuyIn },
  ];

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 200,
            padding: '20px',
          }}
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            onClick={(e) => e.stopPropagation()}
            style={{
              width: '100%',
              maxWidth: '350px',
              background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
              borderRadius: '16px',
              padding: '24px',
              border: '1px solid rgba(255,255,255,0.1)',
            }}
          >
            {/* 헤더 */}
            <div style={{ textAlign: 'center', marginBottom: '24px' }}>
              <span style={{ fontSize: '48px', display: 'block', marginBottom: '12px' }}>
                ⏳
              </span>
              <h3
                style={{
                  fontSize: '20px',
                  fontWeight: 700,
                  color: 'white',
                  margin: '0 0 8px 0',
                }}
              >
                대기열 등록
              </h3>
              <p
                style={{
                  fontSize: '14px',
                  color: 'rgba(255,255,255,0.5)',
                  margin: 0,
                }}
              >
                {roomName}
              </p>
            </div>

            {/* 대기 인원 안내 */}
            <div
              style={{
                background: 'rgba(59, 130, 246, 0.1)',
                border: '1px solid rgba(59, 130, 246, 0.2)',
                borderRadius: '12px',
                padding: '14px',
                marginBottom: '20px',
                textAlign: 'center',
              }}
            >
              <p
                style={{
                  margin: 0,
                  fontSize: '14px',
                  color: 'rgba(255,255,255,0.7)',
                }}
              >
                현재 대기 인원:{' '}
                <span style={{ color: '#3b82f6', fontWeight: 700 }}>
                  {currentWaitlistCount}명
                </span>
              </p>
              <p
                style={{
                  margin: '8px 0 0 0',
                  fontSize: '12px',
                  color: 'rgba(255,255,255,0.5)',
                }}
              >
                자리가 나면 순서대로 자동 착석됩니다
              </p>
            </div>

            {/* 바이인 선택 */}
            <div style={{ marginBottom: '20px' }}>
              <label
                style={{
                  display: 'block',
                  fontSize: '13px',
                  color: 'rgba(255,255,255,0.6)',
                  marginBottom: '10px',
                }}
              >
                바이인 금액 (자리가 나면 이 금액으로 착석)
              </label>

              {/* 프리셋 버튼 */}
              <div
                style={{
                  display: 'flex',
                  gap: '8px',
                  marginBottom: '12px',
                }}
              >
                {presetAmounts.map((preset) => (
                  <motion.button
                    key={preset.label}
                    onClick={() => handleBuyInChange(preset.value)}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    disabled={preset.value > userBalance}
                    style={{
                      flex: 1,
                      padding: '10px',
                      background:
                        buyIn === preset.value
                          ? 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'
                          : 'rgba(255,255,255,0.05)',
                      border:
                        buyIn === preset.value
                          ? 'none'
                          : '1px solid rgba(255,255,255,0.1)',
                      borderRadius: '8px',
                      color: preset.value > userBalance ? 'rgba(255,255,255,0.3)' : 'white',
                      fontSize: '13px',
                      fontWeight: 600,
                      cursor: preset.value > userBalance ? 'not-allowed' : 'pointer',
                      opacity: preset.value > userBalance ? 0.5 : 1,
                    }}
                  >
                    <div>{preset.label}</div>
                    <div style={{ fontSize: '11px', marginTop: '4px', opacity: 0.8 }}>
                      {preset.value.toLocaleString()}
                    </div>
                  </motion.button>
                ))}
              </div>

              {/* 슬라이더 */}
              <input
                type="range"
                min={minBuyIn}
                max={Math.min(maxBuyIn, userBalance)}
                value={buyIn}
                onChange={(e) => handleBuyInChange(Number(e.target.value))}
                style={{
                  width: '100%',
                  marginBottom: '8px',
                  accentColor: '#f59e0b',
                }}
              />

              {/* 현재 금액 표시 */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  fontSize: '12px',
                  color: 'rgba(255,255,255,0.5)',
                }}
              >
                <span>최소: {minBuyIn.toLocaleString()}</span>
                <span
                  style={{
                    color: '#f59e0b',
                    fontWeight: 700,
                    fontSize: '14px',
                  }}
                >
                  {buyIn.toLocaleString()}원
                </span>
                <span>최대: {maxBuyIn.toLocaleString()}</span>
              </div>
            </div>

            {/* 잔액 정보 */}
            <div
              style={{
                background: 'rgba(255,255,255,0.03)',
                borderRadius: '8px',
                padding: '12px',
                marginBottom: '16px',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  fontSize: '13px',
                }}
              >
                <span style={{ color: 'rgba(255,255,255,0.5)' }}>내 잔액</span>
                <span style={{ color: 'white', fontWeight: 600 }}>
                  {userBalance.toLocaleString()}원
                </span>
              </div>
            </div>

            {/* 에러 메시지 */}
            {error && (
              <div
                style={{
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  borderRadius: '8px',
                  padding: '12px',
                  marginBottom: '16px',
                }}
              >
                <p
                  style={{
                    color: '#ef4444',
                    fontSize: '13px',
                    margin: 0,
                    textAlign: 'center',
                  }}
                >
                  {error}
                </p>
              </div>
            )}

            {/* 버튼 */}
            <div style={{ display: 'flex', gap: '12px' }}>
              <motion.button
                onClick={onClose}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                disabled={isLoading}
                style={{
                  flex: 1,
                  padding: '14px',
                  background: 'rgba(255,255,255,0.1)',
                  border: 'none',
                  borderRadius: '10px',
                  color: 'white',
                  fontSize: '15px',
                  fontWeight: 600,
                  cursor: isLoading ? 'not-allowed' : 'pointer',
                  opacity: isLoading ? 0.5 : 1,
                }}
              >
                취소
              </motion.button>
              <motion.button
                onClick={handleSubmit}
                disabled={isLoading || buyIn > userBalance}
                whileHover={{ scale: isLoading ? 1 : 1.02 }}
                whileTap={{ scale: isLoading ? 1 : 0.98 }}
                style={{
                  flex: 1,
                  padding: '14px',
                  background:
                    isLoading || buyIn > userBalance
                      ? 'rgba(255,255,255,0.2)'
                      : 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
                  border: 'none',
                  borderRadius: '10px',
                  color: 'white',
                  fontSize: '15px',
                  fontWeight: 600,
                  cursor: isLoading || buyIn > userBalance ? 'not-allowed' : 'pointer',
                  opacity: isLoading || buyIn > userBalance ? 0.7 : 1,
                  boxShadow:
                    isLoading || buyIn > userBalance
                      ? 'none'
                      : '0 4px 15px rgba(245, 158, 11, 0.3)',
                }}
              >
                {isLoading ? (
                  <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                    <motion.span
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                      style={{ display: 'inline-block' }}
                    >
                      ⏳
                    </motion.span>
                    등록 중...
                  </span>
                ) : (
                  '대기열 등록'
                )}
              </motion.button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
