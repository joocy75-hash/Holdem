/**
 * Rooms API Client
 */
import { api } from './api';
import { useAuthStore } from '@/stores/authStore';

// ============================================================================
// Types
// ============================================================================

export type RoomStatus = 'waiting' | 'playing' | 'paused' | 'closed';
export type RoomType = 'cash' | 'tournament';

export interface SeatInfo {
  position: number;
  userId: string | null;
  nickname: string | null;
  stack: number;
  status: string;
  isBot: boolean;
}

export interface Room {
  id: string;
  name: string;
  description: string | null;
  playerCount: number;
  maxPlayers: number;
  smallBlind: number;
  bigBlind: number;
  buyInMin: number;
  buyInMax: number;
  status: RoomStatus;
  isPrivate: boolean;
  roomType: RoomType;
  ownerId: string | null;
  ownerNickname: string | null;
  createdAt: string;
}

export interface RoomDetail extends Room {
  turnTimeout: number;
  seats: SeatInfo[];
  currentHandId: string | null;
  updatedAt: string;
}

export interface PaginatedRooms {
  items: Room[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface CreateRoomData {
  name: string;
  description?: string;
  roomType?: RoomType;
  maxSeats?: 6 | 9;
  smallBlind?: number;
  bigBlind?: number;
  buyInMin?: number;
  buyInMax?: number;
  turnTimeout?: number;
  isPrivate?: boolean;
  password?: string;
}

export interface UpdateRoomData {
  // 기본 정보
  name?: string;
  description?: string;
  isPrivate?: boolean;
  password?: string;
  // 게임 설정
  smallBlind?: number;
  bigBlind?: number;
  buyInMin?: number;
  buyInMax?: number;
  turnTimeout?: number;
  // 테이블 설정 (플레이어 없을 때만)
  maxSeats?: 6 | 9;
}

export interface RefundInfo {
  user_id: string;
  nickname: string;
  amount: number;
  seat: number;
}

export interface ForceCloseResult {
  success: boolean;
  roomId: string;
  roomName: string;
  reason: string;
  refunds: RefundInfo[];
  totalRefunded: number;
  playersAffected: number;
}

export interface CloseRoomResult {
  success: boolean;
  message: string;
  roomId: string;
}

export interface SearchParams {
  status?: RoomStatus;
  search?: string;
  includeClosed?: boolean;
  page?: number;
  pageSize?: number;
}

// ============================================================================
// Helper
// ============================================================================

function getToken(): string | undefined {
  return useAuthStore.getState().accessToken || undefined;
}

// ============================================================================
// API Functions
// ============================================================================

export const roomsApi = {
  /**
   * 방 목록 조회
   */
  async listRooms(params: SearchParams = {}): Promise<PaginatedRooms> {
    const query = new URLSearchParams();
    if (params.status) query.append('status', params.status);
    if (params.search) query.append('search', params.search);
    if (params.includeClosed !== undefined) query.append('includeClosed', String(params.includeClosed));
    query.append('page', String(params.page || 1));
    query.append('pageSize', String(params.pageSize || 20));

    return api.get<PaginatedRooms>(`/api/rooms?${query.toString()}`, { token: getToken() });
  },

  /**
   * 방 상세 조회
   */
  async getRoom(roomId: string): Promise<RoomDetail> {
    return api.get<RoomDetail>(`/api/rooms/${roomId}`, { token: getToken() });
  },

  /**
   * 방 생성
   */
  async createRoom(data: CreateRoomData): Promise<RoomDetail> {
    return api.post<RoomDetail>('/api/rooms', data, { token: getToken() });
  },

  /**
   * 방 수정 (모든 설정 변경 가능)
   */
  async updateRoom(roomId: string, data: UpdateRoomData): Promise<RoomDetail> {
    return api.patch<RoomDetail>(`/api/rooms/${roomId}`, data, { token: getToken() });
  },

  /**
   * 방 종료 (플레이어 없을 때)
   */
  async deleteRoom(roomId: string): Promise<CloseRoomResult> {
    return api.delete<CloseRoomResult>(`/api/rooms/${roomId}`, { token: getToken() });
  },

  /**
   * 방 강제 종료 (플레이어 환불)
   */
  async forceCloseRoom(roomId: string, reason: string): Promise<ForceCloseResult> {
    return api.post<ForceCloseResult>(`/api/rooms/${roomId}/force-close`, { reason }, { token: getToken() });
  },

  /**
   * 시스템 메시지 전송
   */
  async sendMessage(roomId: string, message: string): Promise<{ success: boolean; roomId: string; message: string }> {
    return api.post(`/api/rooms/${roomId}/message`, { message }, { token: getToken() });
  },
};
