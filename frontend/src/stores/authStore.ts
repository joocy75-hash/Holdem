import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { UserBasicResponse, LoginRequest, RegisterRequest } from '@/types/api';
import { authApi, userApi } from '@/lib/api/endpoints';
import { tokenManager } from '@/lib/api/client';
import type { AxiosError } from 'axios';

// 네트워크 에러인지 확인하는 헬퍼 함수
function isNetworkError(error: unknown): boolean {
  if (error instanceof Error) {
    // Axios 네트워크 에러 체크
    const axiosError = error as AxiosError;
    if (axiosError.code === 'ERR_NETWORK' || axiosError.message === 'Network Error') {
      return true;
    }
    // status가 0인 경우 (요청이 서버에 도달하지 못함)
    if (axiosError.response === undefined && axiosError.request) {
      return true;
    }
  }
  return false;
}

// HTTP 상태 코드 추출 헬퍼 함수
function getStatusCode(error: unknown): number | null {
  const axiosError = error as AxiosError;
  return axiosError.response?.status ?? null;
}

// API 에러 메시지 추출 헬퍼 함수
function getErrorMessage(error: unknown, defaultMessage: string): string {
  const axiosError = error as AxiosError<{ error?: { message?: string }; detail?: string }>;
  // API 에러 응답에서 메시지 추출
  const apiMessage = axiosError.response?.data?.error?.message ||
                     axiosError.response?.data?.detail;
  if (apiMessage) return apiMessage;
  // 일반 에러 메시지
  if (error instanceof Error) return error.message;
  return defaultMessage;
}

interface AuthState {
  user: UserBasicResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  networkError: boolean; // 네트워크 오류 상태

  // Actions
  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  fetchUser: () => Promise<void>;
  clearError: () => void;
  clearNetworkError: () => void;
  setUser: (user: UserBasicResponse | null) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      networkError: false,

      login: async (credentials) => {
        set({ isLoading: true, error: null, networkError: false });
        try {
          const response = await authApi.login(credentials);
          tokenManager.setTokens(response.tokens.accessToken, response.tokens.refreshToken);

          // Use user from response directly
          set({ user: response.user, isAuthenticated: true, isLoading: false });
        } catch (error) {
          // 네트워크 오류와 일반 오류 구분
          if (isNetworkError(error)) {
            set({
              networkError: true,
              error: '네트워크 연결을 확인해주세요. 잠시 후 다시 시도해주세요.',
              isLoading: false
            });
          } else {
            const message = getErrorMessage(error, '로그인에 실패했습니다');
            set({ error: message, isLoading: false });
          }
          throw error;
        }
      },

      register: async (data) => {
        set({ isLoading: true, error: null, networkError: false });
        try {
          const response = await authApi.register(data);
          tokenManager.setTokens(response.tokens.accessToken, response.tokens.refreshToken);

          // Use user from response directly
          set({ user: response.user, isAuthenticated: true, isLoading: false });
        } catch (error) {
          // 네트워크 오류와 일반 오류 구분
          if (isNetworkError(error)) {
            set({
              networkError: true,
              error: '네트워크 연결을 확인해주세요. 잠시 후 다시 시도해주세요.',
              isLoading: false
            });
          } else {
            const message = getErrorMessage(error, '회원가입에 실패했습니다');
            set({ error: message, isLoading: false });
          }
          throw error;
        }
      },

      logout: async () => {
        try {
          await authApi.logout();
        } catch (error) {
          // 로그아웃 API 에러 로깅 (서버 로그아웃 실패해도 로컬은 정리)
          console.error('[AuthStore] 서버 로그아웃 실패:', error);

          // 네트워크 에러인 경우 사용자에게 알림
          if (isNetworkError(error)) {
            console.warn('[AuthStore] 네트워크 오류로 서버 로그아웃 실패. 로컬 세션만 정리합니다.');
          }
        } finally {
          // 서버 로그아웃 성공/실패와 관계없이 로컬 토큰은 항상 삭제
          tokenManager.clearTokens();
          set({ user: null, isAuthenticated: false, error: null, networkError: false });
        }
      },

      fetchUser: async () => {
        const token = tokenManager.getAccessToken();
        if (!token) {
          set({ user: null, isAuthenticated: false });
          return;
        }

        set({ isLoading: true });
        try {
          const user = await userApi.getMe();
          set({ user, isAuthenticated: true, isLoading: false });
        } catch {
          // Token invalid, clear auth
          tokenManager.clearTokens();
          set({ user: null, isAuthenticated: false, isLoading: false });
        }
      },

      clearError: () => set({ error: null }),

      clearNetworkError: () => set({ networkError: false }),

      setUser: (user) => set({ user, isAuthenticated: !!user }),
    }),
    {
      name: 'holdem-auth',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
