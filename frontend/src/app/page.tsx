'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/auth';

export default function Home() {
  const router = useRouter();
  const { isAuthenticated, isLoading, fetchUser } = useAuthStore();

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  useEffect(() => {
    if (!isLoading) {
      if (isAuthenticated) {
        router.push('/lobby');
      } else {
        router.push('/login');
      }
    }
  }, [isLoading, isAuthenticated, router]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center animate-fade-in">
        <h1 className="text-4xl font-bold text-gradient mb-4">POKER HOLDEM</h1>
        <div className="flex justify-center gap-2 mb-8">
          {['♠', '♥', '♦', '♣'].map((suit, i) => (
            <div
              key={suit}
              className={`w-12 h-16 rounded-lg flex items-center justify-center text-2xl font-bold ${
                i % 2 === 0
                  ? 'bg-white text-black'
                  : 'bg-white text-[var(--suit-red)]'
              }`}
            >
              {suit}
            </div>
          ))}
        </div>
        <div className="animate-spin h-8 w-8 border-4 border-[var(--primary)] border-t-transparent rounded-full mx-auto" />
        <p className="mt-4 text-[var(--text-secondary)]">로딩 중...</p>
      </div>
    </div>
  );
}
