'use client';

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { User } from '@/domains/auth/entities';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  setUser: (user: User) => void;
  setToken: (token: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      isAuthenticated: false,

      setUser: (user) => set({ user, isAuthenticated: true }),

      setToken: (token) => {
        if (typeof window !== 'undefined') window.__authToken = token;
        set({ accessToken: token });
      },

      clearAuth: () => {
        if (typeof window !== 'undefined') delete window.__authToken;
        set({ user: null, accessToken: null, isAuthenticated: false });
      },
    }),
    {
      name: 'clinic-auth',
      storage: createJSONStorage(() => sessionStorage),
      partialize: (state) => ({ user: state.user, accessToken: state.accessToken }),
      onRehydrateStorage: () => (state) => {
        if (state?.accessToken && typeof window !== 'undefined') {
          window.__authToken = state.accessToken;
          state.isAuthenticated = true;
        }
      },
    }
  )
);
