'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { historyApi, HandHistory } from '@/lib/api';
import GameHistoryItem from './GameHistoryItem';

export default function GameHistoryList() {
  const [hands, setHands] = useState<HandHistory[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(true);
  const [offset, setOffset] = useState(0);
  const limit = 20;

  const loadHands = async (reset = false) => {
    try {
      setIsLoading(true);
      const currentOffset = reset ? 0 : offset;
      const response = await historyApi.getGameHistory(limit, currentOffset);
      const newHands = response.data;

      if (reset) {
        setHands(newHands);
        setOffset(limit);
      } else {
        setHands((prev) => [...prev, ...newHands]);
        setOffset((prev) => prev + limit);
      }

      setHasMore(newHands.length === limit);
      setError(null);
    } catch (err) {
      console.error('게임 기록 로딩 실패:', err);
      setError('게임 기록을 불러오는데 실패했습니다');
      // 에러 시 빈 배열 설정
      if (offset === 0) {
        setHands([]);
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadHands(true);
  }, []);

  if (error && hands.length === 0) {
    return (
      <div
        style={{
          padding: '40px 20px',
          textAlign: 'center',
        }}
      >
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
            onClick={() => loadHands(true)}
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

  if (!isLoading && hands.length === 0) {
    return (
      <div
        style={{
          padding: '40px 20px',
          textAlign: 'center',
        }}
      >
        <div
          className="glass-card"
          style={{
            padding: '50px 24px',
          }}
        >
          <div
            style={{
              width: '80px',
              height: '80px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(217, 119, 6, 0.08) 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 24px',
            }}
          >
            <svg width="40" height="40" viewBox="0 0 24 24" fill="rgba(245, 158, 11, 0.6)">
              <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 14l-5-5 1.41-1.41L12 14.17l4.59-4.58L18 11l-6 6z" />
            </svg>
          </div>
          <p style={{ color: 'white', fontSize: '16px', fontWeight: 600, marginBottom: '8px' }}>
            게임 기록이 없습니다
          </p>
          <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '14px', margin: 0, lineHeight: 1.5 }}>
            게임에 참여하면 기록이 표시됩니다
          </p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: '0 20px 20px' }}>
      {hands.map((hand) => (
        <GameHistoryItem key={hand.hand_id} hand={hand} />
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
          onClick={() => loadHands(false)}
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
    </div>
  );
}
