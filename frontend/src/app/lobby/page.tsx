'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import LobbyHeader from '@/components/lobby/LobbyHeader';
import BannerCarousel from '@/components/lobby/BannerCarousel';
import GameTabs from '@/components/lobby/GameTabs';
import TournamentCard from '@/components/lobby/TournamentCard';
import HoldemCard from '@/components/lobby/HoldemCard';
import BottomNavigation from '@/components/lobby/BottomNavigation';
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

  useEffect(() => {
    const fetchRooms = async () => {
      try {
        const response = await tablesApi.list();
        setRooms(response.data.rooms || []);
      } catch (error) {
        console.error('방 목록 로드 실패:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchRooms();
  }, []);

  const handleJoinRoom = (roomId: string) => {
    router.push(`/table/${roomId}`);
  };

  // 로딩 중이면 간단한 로딩 표시
  if (loading) {
    return (
      <div
        style={{
          position: 'relative',
          width: '390px',
          minHeight: '858px',
          margin: '0 auto',
          background: 'var(--figma-bg-main)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
        }}
      >
        로딩 중...
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
