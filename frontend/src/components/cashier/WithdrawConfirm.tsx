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
      <div style={{ padding: '20px', textAlign: 'center', position: 'relative', zIndex: 1 }}>
        {/* 성공 아이콘 */}
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', stiffness: 200, damping: 15 }}
          style={{
            width: '90px',
            height: '90px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '40px auto 28px',
            boxShadow: '0 8px 30px rgba(34, 197, 94, 0.4), 0 0 60px rgba(34, 197, 94, 0.2)',
          }}
        >
          <svg width="44" height="44" viewBox="0 0 24 24" fill="none">
            <motion.path
              d="M9 12l2 2 4-4"
              stroke="white"
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ delay: 0.3, duration: 0.4 }}
            />
          </svg>
        </motion.div>

        <motion.h2
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          style={{ color: 'white', fontSize: '26px', fontWeight: 700, marginBottom: '8px' }}
        >
          환전 요청 완료
        </motion.h2>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          style={{ color: 'rgba(255,255,255,0.5)', fontSize: '14px', marginBottom: '32px' }}
        >
          24시간 보안 대기 후 자동 처리됩니다
        </motion.p>

        {/* 요청 정보 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="glass-card"
          style={{
            padding: '22px',
            marginBottom: '24px',
            textAlign: 'left',
          }}
        >
          <div style={{ marginBottom: '18px' }}>
            <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '12px', margin: '0 0 6px 0' }}>환전 금액</p>
            <p style={{ color: 'white', fontSize: '20px', fontWeight: 700, margin: 0 }}>
              {transaction.krw_amount.toLocaleString()}원
              <span className="glow-text-gold" style={{ fontSize: '14px', marginLeft: '10px' }}>
                = {transaction.crypto_amount} USDT
              </span>
            </p>
          </div>
          <div style={{ marginBottom: '18px' }}>
            <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '12px', margin: '0 0 6px 0' }}>수신 주소</p>
            <p
              style={{
                color: 'white',
                fontSize: '13px',
                fontFamily: 'monospace',
                margin: 0,
                wordBreak: 'break-all',
                background: 'rgba(255,255,255,0.05)',
                padding: '10px 12px',
                borderRadius: '8px',
              }}
            >
              {transaction.crypto_address}
            </p>
          </div>
          <div>
            <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '12px', margin: '0 0 6px 0' }}>상태</p>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 1.5, repeat: Infinity }}
                style={{
                  width: '10px',
                  height: '10px',
                  borderRadius: '50%',
                  background: '#f59e0b',
                  boxShadow: '0 0 10px rgba(245, 158, 11, 0.5)',
                }}
              />
              <span style={{ color: '#fbbf24', fontSize: '14px', fontWeight: 600 }}>
                24시간 보안 대기 중
              </span>
            </div>
          </div>
        </motion.div>

        {/* 안내 */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="glass-card"
          style={{
            padding: '16px',
            marginBottom: '24px',
            background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.12) 0%, rgba(37, 99, 235, 0.06) 100%)',
            borderColor: 'rgba(59, 130, 246, 0.25)',
          }}
        >
          <p style={{ color: '#60a5fa', fontSize: '13px', margin: 0, lineHeight: 1.6 }}>
            거래 내역에서 진행 상황을 확인할 수 있습니다.
            <br />
            대기 중에는 언제든 취소가 가능합니다.
          </p>
        </motion.div>

        <motion.button
          onClick={onDone}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="gradient-btn-gold"
          style={{
            width: '100%',
            padding: '18px',
            fontSize: '18px',
            fontWeight: 700,
          }}
        >
          확인
        </motion.button>
      </div>
    );
  }

  // 확인 화면
  return (
    <div style={{ padding: '20px', position: 'relative', zIndex: 1 }}>
      <h2
        style={{ color: 'white', fontSize: '22px', fontWeight: 700, marginBottom: '24px' }}
      >
        환전 정보 확인
      </h2>

      {/* 환전 상세 정보 */}
      <div
        className="glass-card"
        style={{
          padding: '22px',
          marginBottom: '20px',
        }}
      >
        <div style={{ marginBottom: '18px', paddingBottom: '18px', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
            <span style={{ color: 'rgba(255,255,255,0.5)', fontSize: '14px' }}>환전 금액</span>
            <span style={{ color: 'white', fontSize: '17px', fontWeight: 700 }}>
              {amount.toLocaleString()}원
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'rgba(255,255,255,0.5)', fontSize: '14px' }}>수령 금액</span>
            <span className="glow-text-gold" style={{ fontSize: '17px', fontWeight: 700 }}>
              {calculatedUsdt} USDT
            </span>
          </div>
        </div>

        <div style={{ marginBottom: '18px' }}>
          <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '12px', margin: '0 0 8px 0' }}>적용 환율</p>
          <p style={{ color: 'white', fontSize: '15px', margin: 0, fontWeight: 500 }}>
            1 USDT = {exchangeRate ? parseFloat(exchangeRate).toLocaleString() : '-'}원
          </p>
        </div>

        <div>
          <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '12px', margin: '0 0 8px 0' }}>수신 주소 (TRC-20)</p>
          <p
            style={{
              color: 'white',
              fontSize: '13px',
              fontFamily: 'monospace',
              margin: 0,
              wordBreak: 'break-all',
              background: 'rgba(255,255,255,0.05)',
              padding: '12px 14px',
              borderRadius: '10px',
            }}
          >
            {address}
          </p>
        </div>
      </div>

      {/* 24시간 유예 경고 */}
      <div
        className="glass-card"
        style={{
          padding: '18px',
          marginBottom: '20px',
          background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.12) 0%, rgba(220, 38, 38, 0.06) 100%)',
          borderColor: 'rgba(239, 68, 68, 0.25)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '14px' }}>
          <div
            style={{
              width: '28px',
              height: '28px',
              borderRadius: '50%',
              background: 'rgba(239, 68, 68, 0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <span style={{ color: '#f87171', fontSize: '16px', fontWeight: 700 }}>!</span>
          </div>
          <div>
            <p style={{ color: '#f87171', fontWeight: 600, fontSize: '15px', margin: '0 0 6px 0' }}>
              24시간 보안 대기
            </p>
            <p style={{ color: '#fca5a5', fontSize: '13px', margin: 0, lineHeight: 1.6 }}>
              환전 요청 후 24시간 동안 보안 검토 기간이 있습니다.
              이 기간 동안 요청을 취소할 수 있습니다.
            </p>
          </div>
        </div>
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
          disabled={isLoading}
          whileHover={!isLoading ? { scale: 1.02 } : {}}
          whileTap={!isLoading ? { scale: 0.98 } : {}}
          className="glass-btn"
          style={{
            flex: 1,
            padding: '16px',
            fontSize: '16px',
            fontWeight: 600,
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
          className="gradient-btn-gold"
          style={{
            flex: 2,
            padding: '16px',
            fontSize: '16px',
            fontWeight: 700,
            cursor: isLoading ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '10px',
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
