/**
 * Deposits API Client for TON/USDT deposit management
 */
import { api } from './api';
import { useAuthStore } from '@/stores/authStore';

export interface DepositListItem {
  id: string;
  userId: string;
  telegramId: number | null;
  requestedKrw: number;
  calculatedUsdt: number;
  exchangeRate: number;
  memo: string;
  status: 'pending' | 'confirmed' | 'expired' | 'cancelled';
  expiresAt: string;
  createdAt: string;
  confirmedAt: string | null;
  txHash: string | null;
}

export interface DepositDetail extends DepositListItem {
  qrData: string;
  isExpired: boolean;
  remainingSeconds: number;
}

export interface PaginatedDeposits {
  items: DepositListItem[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface DepositStats {
  totalPending: number;
  totalConfirmed: number;
  totalExpired: number;
  totalCancelled: number;
  totalUsdtConfirmed: number;
  totalKrwConfirmed: number;
  todayConfirmedCount: number;
  todayConfirmedUsdt: number;
}

function getToken(): string | undefined {
  return useAuthStore.getState().accessToken || undefined;
}

export interface DepositSearchParams {
  status?: string;
  userId?: string;
  page?: number;
  pageSize?: number;
}

export const depositsApi = {
  async listDeposits(params: DepositSearchParams = {}): Promise<PaginatedDeposits> {
    const query = new URLSearchParams();
    if (params.status) query.append('status', params.status);
    if (params.userId) query.append('user_id', params.userId);
    query.append('page', String(params.page || 1));
    query.append('page_size', String(params.pageSize || 20));
    
    return api.get<PaginatedDeposits>(`/api/admin/deposits?${query.toString()}`, { token: getToken() });
  },

  async getDeposit(depositId: string): Promise<DepositDetail> {
    return api.get<DepositDetail>(`/api/admin/deposits/${depositId}`, { token: getToken() });
  },

  async getStats(): Promise<DepositStats> {
    return api.get<DepositStats>('/api/admin/deposits/stats', { token: getToken() });
  },

  async getPendingCount(): Promise<{ pendingCount: number }> {
    return api.get<{ pendingCount: number }>('/api/admin/deposits/pending/count', { token: getToken() });
  },

  async approveDeposit(depositId: string, txHash: string, note?: string): Promise<{ status: string; depositId: string }> {
    return api.post<{ status: string; depositId: string }>(
      `/api/admin/deposits/${depositId}/approve`,
      { tx_hash: txHash, note },
      { token: getToken() }
    );
  },

  async rejectDeposit(depositId: string, reason: string): Promise<{ status: string; depositId: string }> {
    return api.post<{ status: string; depositId: string }>(
      `/api/admin/deposits/${depositId}/reject`,
      { reason },
      { token: getToken() }
    );
  },
};
