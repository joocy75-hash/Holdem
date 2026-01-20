'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { historyApi, WalletTransaction } from '@/lib/api';

interface RecentTransactionsProps {
  txType: 'crypto_deposit' | 'crypto_withdrawal';
  title: string;
  refreshTrigger?: number;
}

const statusLabels: Record<string, { label: string; color: string }> = {
  pending: { label: '대기중', color: '#f59e0b' },
  processing: { label: '처리중', color: '#3b82f6' },
  completed: { label: '완료', color: '#22c55e' },
  failed: { label: '실패', color: '#ef4444' },
  cancelled: { label: '취소', color: '#6b7280' },
};

export default function RecentTransactions({ txType, title, refreshTrigger }: RecentTransactionsProps) {
  const [transactions, setTransactions] = useState<WalletTransaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadTransactions = async () => {
      try {
        setIsLoading(true);
        const response = await historyApi.getTransactions(txType, 5, 0);
        setTransactions(response.data);
      } catch (error) {
        console.error('거래 내역 로딩 실패:', error);
        setTransactions([]);
      } finally {
        setIsLoading(false);
      }
    };

    loadTransactions();
  }, [txType, refreshTrigger]);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('ko-KR', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (isLoading) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        style={{ padding: '20px', textAlign: 'center' }}
      >
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          style={{
            width: '24px',
            height: '24px',
            border: '2px solid rgba(245, 158, 11, 0.2)',
            borderTopColor: '#f59e0b',
            borderRadius: '50%',
            margin: '0 auto',
          }}
        />
      </motion.div>
    );
  }

  if (transactions.length === 0) {
    return (
      <div style={{ marginTop: '24px' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginBottom: '12px',
          }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="rgba(255,255,255,0.4)">
            <path d="M13 3c-4.97 0-9 4.03-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42C8.27 19.99 10.51 21 13 21c4.97 0 9-4.03 9-9s-4.03-9-9-9zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z" />
          </svg>
          <span style={{ color: 'rgba(255,255,255,0.5)', fontSize: '13px', fontWeight: 600 }}>
            {title}
          </span>
        </div>
        <div
          className="glass-card"
          style={{
            padding: '24px',
            textAlign: 'center',
          }}
        >
          <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '13px', margin: 0 }}>
            아직 {txType === 'crypto_deposit' ? '충전' : '환전'} 기록이 없습니다
          </p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ marginTop: '24px' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          marginBottom: '12px',
        }}
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="rgba(255,255,255,0.4)">
          <path d="M13 3c-4.97 0-9 4.03-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42C8.27 19.99 10.51 21 13 21c4.97 0 9-4.03 9-9s-4.03-9-9-9zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z" />
        </svg>
        <span style={{ color: 'rgba(255,255,255,0.5)', fontSize: '13px', fontWeight: 600 }}>
          {title}
        </span>
      </div>

      <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
        {transactions.map((tx, index) => {
          const statusInfo = statusLabels[tx.status] || { label: tx.status, color: '#6b7280' };
          const isPositive = tx.krw_amount > 0;

          return (
            <div
              key={tx.id}
              style={{
                padding: '14px 16px',
                borderBottom: index < transactions.length - 1 ? '1px solid rgba(255,255,255,0.06)' : 'none',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <div>
                <p style={{ margin: 0, color: 'rgba(255,255,255,0.5)', fontSize: '12px' }}>
                  {formatDate(tx.created_at)}
                </p>
                {tx.crypto_amount && tx.crypto_type && (
                  <p style={{ margin: '4px 0 0', color: 'rgba(255,255,255,0.35)', fontSize: '11px' }}>
                    {tx.crypto_amount} {tx.crypto_type.toUpperCase()}
                  </p>
                )}
              </div>
              <div style={{ textAlign: 'right' }}>
                <p
                  style={{
                    margin: 0,
                    color: isPositive ? '#4ade80' : '#f87171',
                    fontSize: '15px',
                    fontWeight: 700,
                  }}
                >
                  {isPositive ? '+' : ''}{tx.krw_amount.toLocaleString()}원
                </p>
                <p
                  style={{
                    margin: '4px 0 0',
                    color: statusInfo.color,
                    fontSize: '11px',
                    fontWeight: 500,
                  }}
                >
                  {statusInfo.label}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
