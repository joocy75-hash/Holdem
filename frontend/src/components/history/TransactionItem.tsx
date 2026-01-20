'use client';

import { JSX } from 'react';
import { WalletTransaction } from '@/lib/api';

interface TransactionItemProps {
  transaction: WalletTransaction;
}

const txTypeConfig: Record<string, { label: string; icon: JSX.Element; color: string; gradient: string }> = {
  crypto_deposit: {
    label: '입금',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
        <path d="M20 12l-1.41-1.41L13 16.17V4h-2v12.17l-5.58-5.59L4 12l8 8 8-8z" />
      </svg>
    ),
    color: '#22c55e',
    gradient: 'linear-gradient(135deg, rgba(34, 197, 94, 0.25) 0%, rgba(22, 163, 74, 0.15) 100%)',
  },
  crypto_withdrawal: {
    label: '출금',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
        <path d="M4 12l1.41 1.41L11 7.83V20h2V7.83l5.58 5.59L20 12l-8-8-8 8z" />
      </svg>
    ),
    color: '#ef4444',
    gradient: 'linear-gradient(135deg, rgba(239, 68, 68, 0.25) 0%, rgba(220, 38, 38, 0.15) 100%)',
  },
  buy_in: {
    label: '바이인',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
        <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 14l-5-5 1.41-1.41L12 14.17l4.59-4.58L18 11l-6 6z" />
      </svg>
    ),
    color: '#f59e0b',
    gradient: 'linear-gradient(135deg, rgba(245, 158, 11, 0.25) 0%, rgba(217, 119, 6, 0.15) 100%)',
  },
  cash_out: {
    label: '캐시아웃',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
      </svg>
    ),
    color: '#22c55e',
    gradient: 'linear-gradient(135deg, rgba(34, 197, 94, 0.25) 0%, rgba(22, 163, 74, 0.15) 100%)',
  },
  win: {
    label: '승리',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
        <path d="M19 5h-2V3H7v2H5c-1.1 0-2 .9-2 2v1c0 2.55 1.92 4.63 4.39 4.94.63 1.5 1.98 2.63 3.61 2.96V19H7v2h10v-2h-4v-3.1c1.63-.33 2.98-1.46 3.61-2.96C19.08 12.63 21 10.55 21 8V7c0-1.1-.9-2-2-2z" />
      </svg>
    ),
    color: '#22c55e',
    gradient: 'linear-gradient(135deg, rgba(34, 197, 94, 0.25) 0%, rgba(22, 163, 74, 0.15) 100%)',
  },
  lose: {
    label: '패배',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
        <path d="M16 18l2.29-2.29-4.88-4.88-4 4L2 7.41 3.41 6l6 6 4-4 6.3 6.29L22 12v6z" />
      </svg>
    ),
    color: '#ef4444',
    gradient: 'linear-gradient(135deg, rgba(239, 68, 68, 0.25) 0%, rgba(220, 38, 38, 0.15) 100%)',
  },
  rake: {
    label: '레이크',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
        <path d="M4 10v7h3v-7H4zm6 0v7h3v-7h-3zM2 22h19v-3H2v3zm14-12v7h3v-7h-3zm-4.5-9L2 6v2h19V6l-9.5-5z" />
      </svg>
    ),
    color: '#6b7280',
    gradient: 'linear-gradient(135deg, rgba(107, 114, 128, 0.25) 0%, rgba(75, 85, 99, 0.15) 100%)',
  },
  rakeback: {
    label: '레이크백',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
        <path d="M20 6h-2.18c.11-.31.18-.65.18-1 0-1.66-1.34-3-3-3-1.05 0-1.96.54-2.5 1.35l-.5.67-.5-.68C10.96 2.54 10.05 2 9 2 7.34 2 6 3.34 6 5c0 .35.07.69.18 1H4c-1.11 0-1.99.89-1.99 2L2 19c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2z" />
      </svg>
    ),
    color: '#22c55e',
    gradient: 'linear-gradient(135deg, rgba(34, 197, 94, 0.25) 0%, rgba(22, 163, 74, 0.15) 100%)',
  },
  admin_adjust: {
    label: '관리자 조정',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
        <path d="M19.14 12.94c.04-.31.06-.63.06-.94 0-.31-.02-.63-.06-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.04.31-.06.63-.06.94s.02.63.06.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z" />
      </svg>
    ),
    color: '#3b82f6',
    gradient: 'linear-gradient(135deg, rgba(59, 130, 246, 0.25) 0%, rgba(37, 99, 235, 0.15) 100%)',
  },
  bonus: {
    label: '보너스',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
        <path d="M20 6h-2.18c.11-.31.18-.65.18-1 0-1.66-1.34-3-3-3-1.05 0-1.96.54-2.5 1.35l-.5.67-.5-.68C10.96 2.54 10.05 2 9 2 7.34 2 6 3.34 6 5c0 .35.07.69.18 1H4c-1.11 0-1.99.89-1.99 2L2 19c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2z" />
      </svg>
    ),
    color: '#22c55e',
    gradient: 'linear-gradient(135deg, rgba(34, 197, 94, 0.25) 0%, rgba(22, 163, 74, 0.15) 100%)',
  },
};

const statusLabels: Record<string, { label: string; color: string }> = {
  pending: { label: '대기중', color: '#f59e0b' },
  processing: { label: '처리중', color: '#3b82f6' },
  completed: { label: '완료', color: '#22c55e' },
  failed: { label: '실패', color: '#ef4444' },
  cancelled: { label: '취소', color: '#6b7280' },
};

const defaultTypeConfig = {
  label: '기타',
  icon: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
      <circle cx="12" cy="12" r="4" />
    </svg>
  ),
  color: '#6b7280',
  gradient: 'linear-gradient(135deg, rgba(107, 114, 128, 0.25) 0%, rgba(75, 85, 99, 0.15) 100%)',
};

export default function TransactionItem({ transaction }: TransactionItemProps) {
  const typeConfig = txTypeConfig[transaction.tx_type] || {
    ...defaultTypeConfig,
    label: transaction.tx_type,
  };
  const statusInfo = statusLabels[transaction.status] || {
    label: transaction.status,
    color: '#6b7280',
  };

  const isPositive = transaction.krw_amount > 0;

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('ko-KR', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div
      className="glass-card"
      style={{
        padding: '16px',
        marginBottom: '12px',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
        }}
      >
        {/* 왼쪽: 아이콘 + 정보 */}
        <div style={{ display: 'flex', gap: '14px' }}>
          <div
            style={{
              width: '44px',
              height: '44px',
              borderRadius: '12px',
              background: typeConfig.gradient,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: typeConfig.color,
              flexShrink: 0,
            }}
          >
            {typeConfig.icon}
          </div>
          <div>
            <p
              style={{
                margin: 0,
                fontWeight: 600,
                color: 'white',
                fontSize: '15px',
              }}
            >
              {typeConfig.label}
            </p>
            <p
              style={{
                margin: '5px 0 0',
                color: 'rgba(255,255,255,0.4)',
                fontSize: '12px',
              }}
            >
              {formatDate(transaction.created_at)}
            </p>
            {transaction.crypto_type && (
              <p
                style={{
                  margin: '5px 0 0',
                  color: 'rgba(255,255,255,0.35)',
                  fontSize: '11px',
                  fontFamily: 'monospace',
                }}
              >
                {transaction.crypto_amount} {transaction.crypto_type.toUpperCase()}
              </p>
            )}
          </div>
        </div>

        {/* 오른쪽: 금액 + 상태 */}
        <div style={{ textAlign: 'right' }}>
          <p
            className={isPositive ? 'glow-text-green' : ''}
            style={{
              margin: 0,
              fontWeight: 700,
              fontSize: '17px',
              color: isPositive ? '#4ade80' : '#f87171',
            }}
          >
            {isPositive ? '+' : ''}{transaction.krw_amount.toLocaleString()}
          </p>
          <p
            style={{
              margin: '6px 0 0',
              fontSize: '11px',
              color: statusInfo.color,
              fontWeight: 500,
            }}
          >
            {statusInfo.label}
          </p>
          {transaction.status === 'completed' && (
            <p
              style={{
                margin: '4px 0 0',
                color: 'rgba(255,255,255,0.3)',
                fontSize: '11px',
              }}
            >
              잔액: {transaction.krw_balance_after.toLocaleString()}원
            </p>
          )}
        </div>
      </div>

      {/* 설명 */}
      {transaction.description && (
        <div
          style={{
            margin: '14px 0 0',
            padding: '10px 12px',
            background: 'rgba(255,255,255,0.03)',
            borderRadius: '8px',
            border: '1px solid rgba(255,255,255,0.05)',
          }}
        >
          <p
            style={{
              margin: 0,
              color: 'rgba(255,255,255,0.5)',
              fontSize: '12px',
              lineHeight: 1.5,
            }}
          >
            {transaction.description}
          </p>
        </div>
      )}
    </div>
  );
}
