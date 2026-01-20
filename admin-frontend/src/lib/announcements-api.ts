/**
 * Announcements API Client for event/notice management
 */
import { api } from './api';
import { useAuthStore } from '@/stores/authStore';

export type AnnouncementType = 'notice' | 'event' | 'maintenance' | 'urgent';
export type AnnouncementPriority = 'low' | 'normal' | 'high' | 'critical';
export type AnnouncementTarget = 'all' | 'vip' | 'specific_room';

export interface Announcement {
  id: string;
  title: string;
  content: string;
  announcementType: AnnouncementType;
  priority: AnnouncementPriority;
  target: AnnouncementTarget;
  targetRoomId: string | null;
  startTime: string | null;
  endTime: string | null;
  scheduledAt: string | null;
  broadcastedAt: string | null;
  broadcastCount: number;
  createdBy: string;
  createdAt: string | null;
  updatedAt: string | null;
  isActive: boolean;
}

export interface PaginatedAnnouncements {
  items: Announcement[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface CreateAnnouncementRequest {
  title: string;
  content: string;
  announcement_type?: AnnouncementType;
  priority?: AnnouncementPriority;
  target?: AnnouncementTarget;
  target_room_id?: string;
  start_time?: string;
  end_time?: string;
  scheduled_at?: string;
  broadcast_immediately?: boolean;
}

export interface UpdateAnnouncementRequest {
  title?: string;
  content?: string;
  announcement_type?: AnnouncementType;
  priority?: AnnouncementPriority;
  target?: AnnouncementTarget;
  target_room_id?: string;
  start_time?: string;
  end_time?: string;
  scheduled_at?: string;
}

export interface BroadcastResponse {
  success: boolean;
  channel: string | null;
  broadcastCount: number | null;
  error: string | null;
}

export interface AnnouncementTypesResponse {
  types: { value: string; label: string }[];
  priorities: { value: string; label: string }[];
  targets: { value: string; label: string }[];
}

function getToken(): string | undefined {
  return useAuthStore.getState().accessToken || undefined;
}

export interface AnnouncementSearchParams {
  announcementType?: AnnouncementType;
  priority?: AnnouncementPriority;
  target?: AnnouncementTarget;
  includeExpired?: boolean;
  page?: number;
  pageSize?: number;
}

export const announcementsApi = {
  async list(params: AnnouncementSearchParams = {}): Promise<PaginatedAnnouncements> {
    const query = new URLSearchParams();
    if (params.announcementType) query.append('announcement_type', params.announcementType);
    if (params.priority) query.append('priority', params.priority);
    if (params.target) query.append('target', params.target);
    if (params.includeExpired !== undefined) query.append('include_expired', String(params.includeExpired));
    query.append('page', String(params.page || 1));
    query.append('page_size', String(params.pageSize || 20));

    return api.get<PaginatedAnnouncements>(`/api/announcements?${query.toString()}`, { token: getToken() });
  },

  async get(id: string): Promise<Announcement> {
    return api.get<Announcement>(`/api/announcements/${id}`, { token: getToken() });
  },

  async getActive(target?: AnnouncementTarget, roomId?: string): Promise<Announcement[]> {
    const query = new URLSearchParams();
    if (target) query.append('target', target);
    if (roomId) query.append('room_id', roomId);
    const queryStr = query.toString();
    return api.get<Announcement[]>(`/api/announcements/active${queryStr ? '?' + queryStr : ''}`, { token: getToken() });
  },

  async create(data: CreateAnnouncementRequest): Promise<Announcement> {
    return api.post<Announcement>('/api/announcements', data, { token: getToken() });
  },

  async update(id: string, data: UpdateAnnouncementRequest): Promise<Announcement> {
    return api.put<Announcement>(`/api/announcements/${id}`, data, { token: getToken() });
  },

  async delete(id: string): Promise<void> {
    return api.delete(`/api/announcements/${id}`, { token: getToken() });
  },

  async broadcast(id: string): Promise<BroadcastResponse> {
    return api.post<BroadcastResponse>(`/api/announcements/${id}/broadcast`, undefined, { token: getToken() });
  },

  async getTypes(): Promise<AnnouncementTypesResponse> {
    return api.get<AnnouncementTypesResponse>('/api/announcements/types/list', { token: getToken() });
  },
};
