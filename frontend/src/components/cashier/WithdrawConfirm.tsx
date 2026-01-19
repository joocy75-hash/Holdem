'use client';

import { motion } from 'framer-motion';
import { WithdrawResponse } from '@/lib/api';

interface WithdrawConfirmProps {
  amount: number;
  calculatedUsdt: string | null;
  address: string;
  exchangeRate: string | null;
  onConfirm: () => void;
  onBack: () => void;
  isLoading: boolean;
  error: string | null;
  // 완료 후 표시
  isComplete: boolean;
  transaction: WithdrawResponse | null;
  onDone: () => void;
}

const quickSpring = { type: 'spring' as const, stiffness: 400, damping: 20 };

export default function WithdrawConfirm({
  amount,
  calculatedUsdt,
  address,
  exchangeRate,
  onConfirm,
  onBack,
  isLoading,
  error,
  isComplete,
  transaction,
  onDone,
}: WithdrawConfirmProps) {
  // 완료 화면
  if (isComplete && transaction) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        {/* 성공 아이콘 */}
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', stiffness: 200, damping: 15 }}
          style={{
            width: '80px',
            height: '80px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '40px auto 24px',
          }}
        >
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none">
            <path
              d="M9 12l2 2 4-4"
              stroke="white"
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </motion.div>

        <h2 style={{ color: 'white', fontSize: '24px', fontWeight: 700, marginBottom: '8px' }}>
          환전 요청 완료
        </h2>
        <p style={{ color: '#888', fontSize: '14px', marginBottom: '32px' }}>
          24시간 보안 대기 후 자동 처리됩니다
        </p>

        {/* 요청 정보 */}
        <div
          style={{
            background: 'rgba(255,255,255,0.05)',
            borderRadius: '12px',
            padding: '20px',
            marginBottom: '24px',
            textAlign: 'left',
            border: '1px solid rgba(255,255,255,0.1)',
          }}
        >
          <div style={{ marginBottom: '16px' }}>
            <p style={{ color: '#888', fontSize: '12px', margin: '0 0 4px 0' }}>환전 금액</p>
            <p style={{ color: 'white', fontSize: '18px', fontWeight: 600, margin: 0 }}>
              {transaction.krw_amount.toLocaleString()}원
              <span style={{ color: 'var(--figma-balance-color)', fontSize: '14px', marginLeft: '8px' }}>
                = {transaction.crypto_amount} USDT
              </span>
            </p>
          </div>
          <div style={{ marginBottom: '16px' }}>
            <p style={{ color: '#888', fontSize: '12px', margin: '0 0 4px 0' }}>수신 주소</p>
            <p
              style={{
                color: 'white',
                fontSize: '13px',
                fontFamily: 'monospace',
                margin: 0,
                wordBreak: 'break-all',
              }}
            >
              {transaction.crypto_address}
            </p>
          </div>
          <div>
            <p style={{ color: '#888', fontSize: '12px', margin: '0 0 4px 0' }}>상태</p>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div
                style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: '#f59e0b',
                }}
              />
              <span style={{ color: '#f59e0b', fontSize: '14px', fontWeight: 500 }}>
                24시간 보안 대기 중
              </span>
            </div>
          </div>
        </div>

        {/* 안내 */}
        <div
          style={{
            background: 'rgba(59, 130, 246, 0.1)',
            borderRadius: '8px',
            padding: '12px',
            marginBottom: '24px',
            border: '1px solid rgba(59, 130, 246, 0.2)',
          }}
        >
          <p style={{ color: '#60a5fa', fontSize: '13px', margin: 0, lineHeight: 1.5 }}>
            거래 내역에서 진행 상황을 확인할 수 있습니다.
            <br />
            대기 중에는 언제든 취소가 가능합니다.
          </p>
        </div>

        <motion.button
          onClick={onDone}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          transition={quickSpring}
          style={{
            width: '100%',
            padding: '18px',
            background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
            border: 'none',
            borderRadius: '12px',
            color: 'white',
            fontWeight: 700,
            fontSize: '18px',
            cursor: 'pointer',
          }}
        >
          확인
        </motion.button>
      </div>
    );
  }

  // 확인 화면
  return (
    <div style={{ padding: '20px' }}>
      <h2 style={{ color: 'white', fontSize: '20px', fontWeight: 700, marginBottom: '20px' }}>
        환전 정보 확인
      </h2>

      {/* 환전 상세 정보 */}
      <div
        style={{
          background: 'rgba(255,255,255,0.05)',
          borderRadius: '12px',
          padding: '20px',
          marginBottom: '20px',
          border: '1px solid rgba(255,255,255,0.1)',
        }}
      >
        <div style={{ marginBottom: '16px', paddingBottom: '16px', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ color: '#888', fontSize: '14px' }}>환전 금액</span>
            <span style={{ color: 'white', fontSize: '16px', fontWeight: 600 }}>
              {amount.toLocaleString()}원
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: '#888', fontSize: '14px' }}>수령 금액</span>
            <span style={{ color: 'var(--figma-balance-color)', fontSize: '16px', fontWeight: 600 }}>
              {calculatedUsdt} USDT
            </span>
          </div>
        </div>

        <div style={{ marginBottom: '16px' }}>
          <p style={{ color: '#888', fontSize: '12px', margin: '0 0 8px 0' }}>적용 환율</p>
          <p style={{ color: 'white', fontSize: '14px', margin: 0 }}>
            1 USDT = {exchangeRate ? parseFloat(exchangeRate).toLocaleString() : '-'}원
          </p>
        </div>

        <div>
          <p style={{ color: '#888', fontSize: '12px', margin: '0 0 8px 0' }}>수신 주소 (TRC-20)</p>
          <p
            style={{
              color: 'white',
              fontSize: '13px',
              fontFamily: 'monospace',
              margin: 0,
              wordBreak: 'break-all',
              background: 'rgba(255,255,255,0.05)',
              padding: '12px',
              borderRadius: '8px',
            }}
          >
            {address}
          </p>
        </div>
      </div>

      {/* 24시간 유예 경고 */}
      <div
        style={{
          background: 'rgba(239, 68, 68, 0.1)',
          borderRadius: '8px',
          padding: '16px',
          marginBottom: '20px',
          border: '1px solid rgba(239, 68, 68, 0.2)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
          <div
            style={{
              width: '24px',
              height: '24px',
              borderRadius: '50%',
              background: 'rgba(239, 68, 68, 0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <span style={{ color: '#f87171', fontSize: '14px' }}>!</span>
          </div>
          <div>
            <p style={{ color: '#f87171', fontWeight: 600, fontSize: '14px', margin: '0 0 4px 0' }}>
              24시간 보안 대기
            </p>
            <p style={{ color: '#fca5a5', fontSize: '13px', margin: 0, lineHeight: 1.5 }}>
              환전 요청 후 24시간 동안 보안 검토 기간이 있습니다.
              이 기간 동안 요청을 취소할 수 있습니다.
            </p>
          </div>
        </div>
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
          disabled={isLoading}
          whileHover={!isLoading ? { scale: 1.02 } : {}}
          whileTap={!isLoading ? { scale: 0.98 } : {}}
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
            cursor: isLoading ? 'not-allowed' : 'pointer',
            opacity: isLoading ? 0.5 : 1,
          }}
        >
          이전
        </motion.button>
        <motion.button
          onClick={onConfirm}
          disabled={isLoading}
          whileHover={!isLoading ? { scale: 1.02 } : {}}
          whileTap={!isLoading ? { scale: 0.98 } : {}}
          transition={quickSpring}
          style={{
            flex: 2,
            padding: '16px',
            background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
            border: 'none',
            borderRadius: '12px',
            color: 'white',
            fontWeight: 700,
            fontSize: '16px',
            cursor: isLoading ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
          }}
        >
          {isLoading ? (
            <>
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
            </>
          ) : (
            '환전 요청하기'
          )}
        </motion.button>
      </div>
    </div>
  );
}
