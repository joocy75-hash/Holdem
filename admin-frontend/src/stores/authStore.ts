import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { AdminUser } from '@/types';

interface AuthState {
  user: AdminUser | null;
  accessToken: string | null;
  tokenExpiry: number | null;
  isAuthenticated: boolean;
  setAuth: (user: AdminUser, token: string, expiresIn?: number) => void;
  logout: () => void;
  isTokenExpired: () => boolean;
  checkAndRefreshAuth: () => boolean;
}

// Default token expiry: 24 hours (in milliseconds)
const DEFAULT_TOKEN_EXPIRY_MS = 24 * 60 * 60 * 1000;

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      tokenExpiry: null,
      isAuthenticated: false,
      
      setAuth: (user, token, expiresIn = DEFAULT_TOKEN_EXPIRY_MS) => {
        const expiry = Date.now() + expiresIn;
        set({ 
          user, 
          accessToken: token, 
          tokenExpiry: expiry,
          isAuthenticated: true 
        });
      },
      
      logout: () => {
        // Clear all auth state
        set({ 
          user: null, 
          accessToken: null, 
          tokenExpiry: null,
          isAuthenticated: false 
        });
        // Also clear from storage explicitly
        if (typeof window !== 'undefined') {
          localStorage.removeItem('admin-auth');
        }
      },
      
      isTokenExpired: () => {
        const { tokenExpiry } = get();
        if (!tokenExpiry) return true;
        return Date.now() > tokenExpiry;
      },
      
      checkAndRefreshAuth: () => {
        const state = get();
        if (!state.accessToken || !state.user) {
          return false;
        }
        if (state.isTokenExpired()) {
          // Token expired, logout
          state.logout();
          return false;
        }
        return true;
      },
    }),
    {
      name: 'admin-auth',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        accessToken: state.accessToken,
        tokenExpiry: state.tokenExpiry,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
      // Validate stored data on rehydration
      onRehydrateStorage: () => (state) => {
        if (state) {
          // Check if token is expired on app load
          if (state.tokenExpiry && Date.now() > state.tokenExpiry) {
            state.logout();
          }
        }
      },
    }
  )
);
