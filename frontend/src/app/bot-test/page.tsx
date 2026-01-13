'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/auth';
import { botsApi, tablesApi, BotConfig, BotInfo } from '@/lib/api';

type Strategy = 'random' | 'calculated';

interface Room {
  id: string;
  name: string;
  currentPlayers: number;
  maxSeats: number;
}

export default function BotTestPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, fetchUser } = useAuthStore();

  // State
  const [rooms, setRooms] = useState<Room[]>([]);
  const [selectedRoomId, setSelectedRoomId] = useState<string>('');
  const [bots, setBots] = useState<BotInfo[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Form state
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy>('calculated');
  const [nickname, setNickname] = useState('');
  const [buyIn, setBuyIn] = useState(1000);
  const [aggression, setAggression] = useState(0.5);
  const [tightness, setTightness] = useState(0.5);

  // Polling interval for bot status
  const [pollingId, setPollingId] = useState<NodeJS.Timeout | null>(null);

  useEffect(() => {
    fetchUser();
    fetchRooms();
  }, [fetchUser]);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [authLoading, isAuthenticated, router]);

  // Fetch bots when room changes
  useEffect(() => {
    if (isAuthenticated && selectedRoomId) {
      fetchBots();
      // Start polling
      const id = setInterval(fetchBots, 3000);
      setPollingId(id);
      return () => clearInterval(id);
    }
  }, [isAuthenticated, selectedRoomId]);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingId) clearInterval(pollingId);
    };
  }, [pollingId]);

  const fetchRooms = async () => {
    try {
      const response = await tablesApi.list();
      const roomData = response.data.rooms || response.data;
      setRooms(roomData);
      if (roomData.length > 0 && !selectedRoomId) {
        setSelectedRoomId(roomData[0].id);
      }
    } catch (e) {
      console.error('Failed to fetch rooms:', e);
    }
  };

  const fetchBots = async () => {
    if (!selectedRoomId) return;
    try {
      const response = await botsApi.getRoomBots(selectedRoomId);
      setBots(response.data.bots);
    } catch (e) {
      console.error('Failed to fetch bots:', e);
    }
  };

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 3000);
  };

  const handleAddBot = async () => {
    if (!selectedRoomId) {
      showMessage('error', '먼저 방을 선택하세요');
      return;
    }

    setIsLoading(true);
    try {
      const config: Partial<BotConfig> = {
        strategy: selectedStrategy,
        nickname: nickname.trim() || undefined,
        buyIn,
      };

      if (selectedStrategy === 'calculated') {
        config.aggression = aggression;
        config.tightness = tightness;
      }

      const response = await botsApi.addBot(selectedRoomId, config);
      await fetchBots();
      setNickname('');
      showMessage('success', `봇 "${response.data.nickname}" 추가됨 (포지션: ${response.data.position ?? '-'})`);
    } catch (e: any) {
      showMessage('error', e.response?.data?.detail?.error?.message || '봇 추가 실패');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRemoveBot = async (botId: string) => {
    setIsLoading(true);
    try {
      await botsApi.removeBot(selectedRoomId, botId);
      await fetchBots();
      showMessage('success', '봇 제거됨');
    } catch (e: any) {
      showMessage('error', e.response?.data?.detail?.error?.message || '봇 제거 실패');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearAll = async () => {
    if (!selectedRoomId) return;
    setIsLoading(true);
    try {
      const response = await botsApi.clearRoomBots(selectedRoomId);
      setBots([]);
      showMessage('success', `${response.data.removedCount || 0}개 봇 제거됨`);
    } catch (e: any) {
      showMessage('error', e.response?.data?.detail?.error?.message || '봇 제거 실패');
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickAdd = async (count: number, strategy: Strategy) => {
    if (!selectedRoomId) {
      showMessage('error', '먼저 방을 선택하세요');
      return;
    }

    setIsLoading(true);
    try {
      const response = await botsApi.addMultipleBots(selectedRoomId, count, strategy, buyIn);
      await fetchBots();
      showMessage('success', `${response.data.botIds?.length || count}개 봇 추가됨`);
    } catch (e: any) {
      showMessage('error', e.response?.data?.detail?.error?.message || '봇 추가 실패');
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'playing':
        return 'text-[var(--success)]';
      case 'joining':
        return 'text-[var(--warning)]';
      case 'error':
        return 'text-[var(--error)]';
      default:
        return 'text-[var(--text-secondary)]';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'playing':
        return '플레이 중';
      case 'joining':
        return '참가 중';
      case 'error':
        return '오류';
      default:
        return status;
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-4 border-[var(--primary)] border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="min-h-dvh flex justify-center bg-[#1a1a2e]">
      <div className="w-full max-w-[500px] min-h-dvh flex flex-col bg-[var(--background)]">
        {/* Header */}
        <header className="sticky top-0 z-10 border-b border-[var(--border)] bg-[var(--surface)]" style={{ paddingTop: 'var(--safe-area-top)' }}>
          <div className="px-4 py-3 flex justify-between items-center">
            <div className="flex items-center gap-2">
              <button
                onClick={() => router.push('/lobby')}
                className="text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              >
                ←
              </button>
              <h1 className="text-lg font-bold">봇 컨트롤</h1>
            </div>
            {user && (
              <div className="text-right">
                <p className="text-xs font-medium">{user.nickname}</p>
              </div>
            )}
          </div>
        </header>

        {/* Message Toast */}
        {message && (
          <div className={`mx-4 mt-2 p-3 rounded-lg text-sm animate-fade-in ${
            message.type === 'success'
              ? 'bg-[var(--success)]/10 text-[var(--success)]'
              : 'bg-[var(--error)]/10 text-[var(--error)]'
          }`}>
            {message.text}
          </div>
        )}

        {/* Main Content */}
        <main className="flex-1 px-4 py-4 scroll-container">
          {/* Room Selection */}
          <div className="card p-3 mb-4">
            <label className="block text-xs text-[var(--text-secondary)] mb-1">방 선택</label>
            {rooms.length === 0 ? (
              <div className="text-sm text-[var(--text-secondary)] py-2">
                생성된 방이 없습니다. 먼저 방을 만드세요.
              </div>
            ) : (
              <select
                value={selectedRoomId}
                onChange={(e) => setSelectedRoomId(e.target.value)}
                className="input w-full text-sm"
              >
                {rooms.map((room) => (
                  <option key={room.id} value={room.id}>
                    {room.name} ({room.currentPlayers}/{room.maxSeats})
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Quick Add Buttons */}
          <div className="card p-3 mb-4">
            <label className="block text-xs text-[var(--text-secondary)] mb-2">빠른 추가</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => handleQuickAdd(2, 'random')}
                disabled={isLoading || !selectedRoomId}
                className="btn btn-secondary text-xs py-2"
              >
                랜덤 봇 2개
              </button>
              <button
                onClick={() => handleQuickAdd(2, 'calculated')}
                disabled={isLoading || !selectedRoomId}
                className="btn btn-secondary text-xs py-2"
              >
                계산형 봇 2개
              </button>
              <button
                onClick={() => handleQuickAdd(4, 'calculated')}
                disabled={isLoading || !selectedRoomId}
                className="btn btn-secondary text-xs py-2"
              >
                계산형 봇 4개
              </button>
              <button
                onClick={() => handleQuickAdd(6, 'random')}
                disabled={isLoading || !selectedRoomId}
                className="btn btn-secondary text-xs py-2"
              >
                랜덤 봇 6개
              </button>
            </div>
          </div>

          {/* Add Bot Form */}
          <div className="card p-3 mb-4">
            <h3 className="text-sm font-bold mb-3">봇 추가 (상세)</h3>

            <div className="space-y-3">
              <div>
                <label className="block text-xs text-[var(--text-secondary)] mb-1">전략</label>
                <select
                  value={selectedStrategy}
                  onChange={(e) => setSelectedStrategy(e.target.value as Strategy)}
                  className="input w-full text-sm"
                >
                  <option value="random">Random - 랜덤 액션 선택</option>
                  <option value="calculated">Calculated - Chen Formula + 핸드 강도</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-[var(--text-secondary)] mb-1">닉네임 (선택)</label>
                  <input
                    type="text"
                    value={nickname}
                    onChange={(e) => setNickname(e.target.value)}
                    className="input w-full text-sm"
                    placeholder="자동 생성"
                  />
                </div>
                <div>
                  <label className="block text-xs text-[var(--text-secondary)] mb-1">바이인</label>
                  <input
                    type="number"
                    value={buyIn}
                    onChange={(e) => setBuyIn(Number(e.target.value))}
                    className="input w-full text-sm"
                    min={100}
                    max={10000}
                    step={100}
                  />
                </div>
              </div>

              {selectedStrategy === 'calculated' && (
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-[var(--text-secondary)] mb-1">
                      공격성 ({(aggression * 100).toFixed(0)}%)
                    </label>
                    <input
                      type="range"
                      value={aggression}
                      onChange={(e) => setAggression(Number(e.target.value))}
                      className="w-full"
                      min={0}
                      max={1}
                      step={0.1}
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-[var(--text-secondary)] mb-1">
                      타이트함 ({(tightness * 100).toFixed(0)}%)
                    </label>
                    <input
                      type="range"
                      value={tightness}
                      onChange={(e) => setTightness(Number(e.target.value))}
                      className="w-full"
                      min={0}
                      max={1}
                      step={0.1}
                    />
                  </div>
                </div>
              )}

              <button
                onClick={handleAddBot}
                disabled={isLoading || !selectedRoomId}
                className="btn btn-primary w-full text-sm"
              >
                {isLoading ? '추가 중...' : '봇 추가'}
              </button>
            </div>
          </div>

          {/* Current Bots */}
          <div className="card p-3 mb-4">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-sm font-bold">활성 봇 ({bots.length})</h3>
              {bots.length > 0 && (
                <button
                  onClick={handleClearAll}
                  disabled={isLoading}
                  className="text-xs text-[var(--error)] hover:underline"
                >
                  전체 삭제
                </button>
              )}
            </div>

            {bots.length === 0 ? (
              <p className="text-xs text-[var(--text-secondary)] text-center py-4">
                봇이 없습니다. 위에서 봇을 추가하세요.
              </p>
            ) : (
              <div className="space-y-2">
                {bots.map((bot) => (
                  <div
                    key={bot.botId}
                    className="flex items-center justify-between p-2 rounded bg-[var(--surface-hover)]"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium">{bot.nickname}</p>
                        <span className={`text-xs ${getStatusColor(bot.status)}`}>
                          {getStatusText(bot.status)}
                        </span>
                      </div>
                      <div className="flex gap-3 text-xs text-[var(--text-secondary)]">
                        <span>{bot.strategy}</span>
                        <span>포지션: {bot.position ?? '-'}</span>
                        <span>스택: {bot.stack.toLocaleString()}</span>
                        <span>핸드: {bot.handsPlayed}</span>
                      </div>
                    </div>
                    <button
                      onClick={() => handleRemoveBot(bot.botId)}
                      disabled={isLoading}
                      className="text-[var(--error)] hover:bg-[var(--error)]/10 p-1 rounded ml-2"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Info */}
          <div className="card p-3 bg-[var(--info)]/10 border-[var(--info)]">
            <h3 className="text-sm font-bold text-[var(--info)] mb-2">사용법</h3>
            <ul className="text-xs text-[var(--text-secondary)] space-y-1 list-disc list-inside">
              <li>봇을 추가하면 자동으로 게임에 참여합니다</li>
              <li>봇은 자신의 차례가 되면 전략에 따라 자동으로 플레이합니다</li>
              <li>최소 2명 이상이 있어야 게임이 시작됩니다</li>
              <li>직접 게임에 참여하려면 방에 입장하세요</li>
            </ul>
          </div>
        </main>
      </div>
    </div>
  );
}
