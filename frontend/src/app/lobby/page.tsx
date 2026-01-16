'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import LobbyHeader from '@/components/lobby/LobbyHeader';
import BannerCarousel from '@/components/lobby/BannerCarousel';
import GameTabs from '@/components/lobby/GameTabs';
import TournamentCard from '@/components/lobby/TournamentCard';
import HoldemCard from '@/components/lobby/HoldemCard';
import BottomNavigation from '@/components/lobby/BottomNavigation';
// import QuickJoinButton from '@/components/lobby/QuickJoinButton'; // 임시 숨김
import { tablesApi } from '@/lib/api';

interface Room {
  id: string;
  name: string;
  blinds: string;
  maxSeats: number;
  playerCount: number;
  status: string;
  isPrivate: boolean;
  buyInMin: number;
  buyInMax: number;
}

export default function LobbyPage() {
  const router = useRouter();
  const [rooms, setRooms] = useState<Room[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRooms = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await tablesApi.list();
      setRooms(response.data.rooms || []);
    } catch (err) {
      const errorMessage = err instanceof Error 
        ? err.message 
        : '방 목록을 불러오는데 실패했습니다';
      setError(errorMessage);
      console.error('방 목록 로드 실패:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRooms();
  }, [fetchRooms]);

  const handleJoinRoom = (roomId: string) => {
    router.push(`/table/${roomId}`);
  };

  const handleRetry = () => {
    fetchRooms();
  };

  // 에러 상태 UI
  if (error) {
    return (
      <div
        style={{
          position: 'relative',
          width: '390px',
          minHeight: '858px',
          margin: '0 auto',
          background: 'var(--figma-bg-main)',
        }}
      >
        {/* 헤더 */}
        <div style={{ position: 'absolute', left: 0, top: 0, zIndex: 1 }}>
          <LobbyHeader />
        </div>

        {/* 에러 메시지 */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="flex flex-col items-center gap-4 p-6 text-center">
            <div className="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center">
              <svg 
                className="w-8 h-8 text-red-500" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" 
                />
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary mb-2">
                연결 오류
              </h3>
              <p className="text-sm text-text-secondary mb-4">
                {error}
              </p>
            </div>
            <button
              onClick={handleRetry}
              className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
            >
              다시 시도
            </button>
          </div>
        </div>

        {/* 하단 네비게이션 */}
        <BottomNavigation />
      </div>
    );
  }

  // 로딩 중이면 스켈레톤 UI 표시
  if (loading) {
    return (
      <div
        style={{
          position: 'relative',
          width: '390px',
          minHeight: '858px',
          margin: '0 auto',
          background: 'var(--figma-bg-main)',
        }}
      >
        {/* 헤더 스켈레톤 */}
        <div style={{ padding: '16px' }}>
          <div className="flex justify-between items-center mb-4">
            <div className="w-24 h-8 bg-surface animate-pulse rounded-md" />
            <div className="flex gap-2">
              <div className="w-8 h-8 bg-surface animate-pulse rounded-full" />
              <div className="w-8 h-8 bg-surface animate-pulse rounded-full" />
            </div>
          </div>
        </div>

        {/* 배너 스켈레톤 */}
        <div style={{ position: 'absolute', left: '8px', top: '156px', right: '8px' }}>
          <div className="w-full h-[180px] bg-surface animate-pulse rounded-xl" />
        </div>

        {/* 탭 스켈레톤 */}
        <div style={{ position: 'absolute', left: '10px', top: '380px' }}>
          <div className="flex gap-4">
            <div className="w-16 h-8 bg-surface animate-pulse rounded-md" />
            <div className="w-16 h-8 bg-surface animate-pulse rounded-md" />
            <div className="w-16 h-8 bg-surface animate-pulse rounded-md" />
          </div>
        </div>

        {/* 카드 스켈레톤들 */}
        <div style={{ position: 'absolute', left: '10px', top: '414px', right: '10px' }}>
          <div className="w-full h-[120px] bg-surface animate-pulse rounded-xl mb-4" />
          <div className="w-full h-[120px] bg-surface animate-pulse rounded-xl" />
        </div>

        {/* 중앙 로딩 인디케이터 */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="flex flex-col items-center gap-3">
            <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            <span className="text-text-secondary text-sm">테이블 목록 로딩 중...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        position: 'relative',
        width: '390px',
        minHeight: '858px',
        margin: '0 auto',
        background: 'var(--figma-bg-main)',
      }}
    >
      {/* 배경 이미지 (opacity 50%) - 맨 뒤 레이어 */}
      <div
        style={{
          position: 'absolute',
          left: '2px',
          top: '88px',
          width: '388px',
          height: '687px',
          opacity: 0.5,
          pointerEvents: 'none',
          zIndex: 0,
        }}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="https://www.figma.com/api/mcp/asset/8f7b90fa-8a33-4ede-997d-20831e008a85"
          alt="background"
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* 헤더 (0-148px) */}
      <div style={{ position: 'absolute', left: 0, top: 0, zIndex: 1 }}>
        <LobbyHeader />
      </div>

      {/* 배너 (156-348px) */}
      <div style={{ position: 'absolute', left: '8px', top: '156px', zIndex: 1 }}>
        <BannerCarousel />
      </div>

      {/* 게임 탭 (380px) */}
      <div style={{ position: 'absolute', left: '10px', top: '380px', zIndex: 1 }}>
        <GameTabs />
      </div>

      {/* 빠른 입장 버튼 - 임시 숨김 처리
      <div style={{ position: 'absolute', right: '10px', top: '350px', zIndex: 2 }}>
        <QuickJoinButton />
      </div>
      */}

      {/* 토너먼트 카드 (414px) */}
      <div style={{ position: 'absolute', left: '10px', top: '414px', zIndex: 1 }}>
        {rooms.length > 0 ? (
          <TournamentCard
            roomId={rooms[0].id}
            name={rooms[0].name}
            buyIn={rooms[0].buyInMin}
            onJoin={handleJoinRoom}
          />
        ) : (
          <TournamentCard />
        )}
      </div>

      {/* 홀덤 카드 (546px) */}
      <div style={{ position: 'absolute', left: '10px', top: '546px', zIndex: 1 }}>
        {rooms.length > 1 ? (
          <HoldemCard
            roomId={rooms[1].id}
            name={rooms[1].name}
            maxSeats={rooms[1].maxSeats}
            buyIn={rooms[1].buyInMin}
            onJoin={handleJoinRoom}
          />
        ) : (
          <HoldemCard />
        )}
      </div>

      {/* 하단 네비게이션 (fixed) */}
      <BottomNavigation />
    </div>
  );
}
