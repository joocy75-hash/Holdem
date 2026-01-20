'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuthStore } from '@/stores/auth';
import HistoryHeader from '@/components/history/HistoryHeader';
import GameHistoryList from '@/components/history/GameHistoryList';
import TransactionList from '@/components/history/TransactionList';
import BottomNavigation from '@/components/lobby/BottomNavigation';

type TabType = 'game' | 'transaction';

export default function HistoryPage() {
  const router = useRouter();
  const { isAuthenticated, fetchUser } = useAuthStore();
  const [activeTab, setActiveTab] = useState<TabType>('game');

  // 인증 체크
  useEffect(() => {
    if (!isAuthenticated) {
      fetchUser().catch(() => router.push('/login'));
    }
  }, [isAuthenticated, fetchUser, router]);

  return (
    <div
      className="page-bg-gradient"
      style={{
        position: 'relative',
        width: '390px',
        minHeight: '858px',
        margin: '0 auto',
      }}
    >
      {/* 노이즈 텍스처 */}
      <div className="noise-overlay" />

      {/* 배경 장식 */}
      <div
        style={{
          position: 'absolute',
          top: '5%',
          right: '-20%',
          width: '300px',
          height: '300px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(245, 158, 11, 0.15) 0%, transparent 70%)',
          filter: 'blur(60px)',
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          bottom: '20%',
          left: '-15%',
          width: '280px',
          height: '280px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(59, 130, 246, 0.12) 0%, transparent 70%)',
          filter: 'blur(50px)',
          pointerEvents: 'none',
        }}
      />

      {/* 헤더 */}
      <HistoryHeader activeTab={activeTab} onTabChange={setActiveTab} />

      {/* 컨텐츠 */}
      <div style={{ paddingTop: '110px', paddingBottom: '120px', position: 'relative', zIndex: 1 }}>
        <AnimatePresence mode="wait">
          {activeTab === 'game' && (
            <motion.div
              key="game"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.2 }}
            >
              <GameHistoryList />
            </motion.div>
          )}

          {activeTab === 'transaction' && (
            <motion.div
              key="transaction"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
            >
              <TransactionList />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* 하단 네비게이션 */}
      <BottomNavigation />
    </div>
  );
}
