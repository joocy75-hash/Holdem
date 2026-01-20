'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { historyApi, WalletTransaction } from '@/lib/api';
import TransactionItem from './TransactionItem';

const filterOptions = [
  { value: '', label: '전체' },
  { value: 'crypto_deposit', label: '입금' },
  { value: 'crypto_withdrawal', label: '출금' },
  { value: 'buy_in', label: '바이인' },
  { value: 'cash_out', label: '캐시아웃' },
];

export default function TransactionList() {
  const [transactions, setTransactions] = useState<WalletTransaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState('');
  const [hasMore, setHasMore] = useState(true);
  const [offset, setOffset] = useState(0);
  const limit = 20;

  const loadTransactions = async (reset = false, txType?: string) => {
    try {
      setIsLoading(true);
      const currentOffset = reset ? 0 : offset;
      const response = await historyApi.getTransactions(
        txType || undefined,
        limit,
        currentOffset
      );
      const newTransactions = response.data;

      if (reset) {
        setTransactions(newTransactions);
        setOffset(limit);
      } else {
        setTransactions((prev) => [...prev, ...newTransactions]);
        setOffset((prev) => prev + limit);
      }

      setHasMore(newTransactions.length === limit);
      setError(null);
    } catch (err) {
      console.error('거래 내역 로딩 실패:', err);
      setError('거래 내역을 불러오는데 실패했습니다');
      if (offset === 0) {
        setTransactions([]);
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadTransactions(true, filter);
  }, [filter]);

  const handleFilterChange = (newFilter: string) => {
    setFilter(newFilter);
    setOffset(0);
  };

  if (error && transactions.length === 0) {
    return (
      <div style={{ padding: '40px 20px', textAlign: 'center' }}>
        <div
          className="glass-card"
          style={{
            padding: '40px 24px',
          }}
        >
          <div
            style={{
              width: '64px',
              height: '64px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(220, 38, 38, 0.1) 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 20px',
            }}
          >
            <svg width="32" height="32" viewBox="0 0 24 24" fill="#ef4444">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
            </svg>
          </div>
          <p style={{ color: 'rgba(255,255,255,0.7)', marginBottom: '20px', fontSize: '15px' }}>{error}</p>
          <motion.button
            onClick={() => loadTransactions(true, filter)}
            whileTap={{ scale: 0.95 }}
            whileHover={{ scale: 1.02 }}
            className="glass-btn"
            style={{
              padding: '12px 28px',
              fontSize: '14px',
              fontWeight: 600,
            }}
          >
            다시 시도
          </motion.button>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* 필터 */}
      <div
        style={{
          padding: '0 20px 16px',
          display: 'flex',
          gap: '8px',
          overflowX: 'auto',
          msOverflowStyle: 'none',
          scrollbarWidth: 'none',
        }}
      >
        {filterOptions.map((option) => (
          <motion.button
            key={option.value}
            onClick={() => handleFilterChange(option.value)}
            whileTap={{ scale: 0.95 }}
            whileHover={{ scale: 1.03 }}
            style={{
              padding: '10px 18px',
              background:
                filter === option.value
                  ? 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'
                  : 'rgba(255,255,255,0.05)',
              border: filter === option.value
                ? 'none'
                : '1px solid rgba(255,255,255,0.1)',
              borderRadius: '20px',
              color: 'white',
              fontSize: '13px',
              fontWeight: 600,
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              boxShadow: filter === option.value
                ? '0 4px 12px rgba(245, 158, 11, 0.3)'
                : 'none',
              transition: 'all 0.3s ease',
            }}
          >
            {option.label}
          </motion.button>
        ))}
      </div>

      {/* 리스트 */}
      <div style={{ padding: '0 20px 20px' }}>
        {!isLoading && transactions.length === 0 ? (
          <div
            className="glass-card"
            style={{ padding: '50px 24px', textAlign: 'center' }}
          >
            <div
              style={{
                width: '80px',
                height: '80px',
                borderRadius: '50%',
                background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(37, 99, 235, 0.08) 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 24px',
              }}
            >
              <svg width="40" height="40" viewBox="0 0 24 24" fill="rgba(59, 130, 246, 0.6)">
                <path d="M21 18v1c0 1.1-.9 2-2 2H5c-1.11 0-2-.9-2-2V5c0-1.1.89-2 2-2h14c1.1 0 2 .9 2 2v1h-9c-1.11 0-2 .9-2 2v8c0 1.1.89 2 2 2h9zm-9-2h10V8H12v8zm4-2.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z" />
              </svg>
            </div>
            <p style={{ color: 'white', fontSize: '16px', fontWeight: 600, marginBottom: '8px' }}>
              거래 내역이 없습니다
            </p>
            <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '14px', margin: 0 }}>
              {filter ? '해당 유형의 거래가 없습니다' : '충전 또는 환전하면 내역이 표시됩니다'}
            </p>
          </div>
        ) : (
          <>
            {transactions.map((tx) => (
              <TransactionItem key={tx.id} transaction={tx} />
            ))}

            {isLoading && (
              <div style={{ textAlign: 'center', padding: '24px' }}>
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  style={{
                    width: '32px',
                    height: '32px',
                    border: '3px solid rgba(245, 158, 11, 0.2)',
                    borderTopColor: '#f59e0b',
                    borderRadius: '50%',
                    margin: '0 auto 12px',
                  }}
                />
                <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '14px', margin: 0 }}>로딩 중...</p>
              </div>
            )}

            {!isLoading && hasMore && (
              <motion.button
                onClick={() => loadTransactions(false, filter)}
                whileTap={{ scale: 0.98 }}
                whileHover={{ scale: 1.01, y: -2 }}
                className="glass-btn"
                style={{
                  width: '100%',
                  padding: '14px',
                  fontSize: '14px',
                  fontWeight: 600,
                  marginTop: '12px',
                }}
              >
                더 보기
              </motion.button>
            )}
          </>
        )}
      </div>
    </div>
  );
}
