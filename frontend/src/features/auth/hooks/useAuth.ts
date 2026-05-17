'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/shared/api/client';
import { useAuthStore } from '@/shared/store/authStore';
import { AuthDomainService } from '@/domains/auth/services';
import type { User } from '@/domains/auth/entities';

interface LoginError {
  username?: string;
  password?: string;
  general?: string;
}

export function useAuth() {
  const router = useRouter();
  const { setUser, setToken, clearAuth, user, isAuthenticated } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<LoginError>({});

  async function login(username: string, password: string) {
    const usernameError = AuthDomainService.validateUsername(username);
    const passwordError = AuthDomainService.validatePassword(password);
    if (usernameError || passwordError) {
      setErrors({ username: usernameError ?? undefined, password: passwordError ?? undefined });
      return;
    }
    setErrors({});
    setLoading(true);
    try {
      const { data } = await apiClient.post<{ access_token: string; user: { id: string; username: string; role: string; display_name: string } }>(
        '/api/v1/auth/login',
        { username, password }
      );
      const domainUser: User = {
        id: data.user.id,
        username: data.user.username,
        role: data.user.role as User['role'],
        displayName: data.user.display_name,
      };
      setToken(data.access_token);
      setUser(domainUser);
      router.push('/conversation');
    } catch (err: any) {
      setErrors({ general: err?.response?.data?.detail ?? '登录失败，请重试' });
    } finally {
      setLoading(false);
    }
  }

  async function logout() {
    try {
      await apiClient.post('/api/v1/auth/logout');
    } finally {
      clearAuth();
      router.push('/login');
    }
  }

  async function fetchMe() {
    try {
      const { data } = await apiClient.get<{ id: string; username: string; role: string; display_name: string }>(
        '/api/v1/auth/me'
      );
      const domainUser: User = {
        id: data.id,
        username: data.username,
        role: data.role as User['role'],
        displayName: data.display_name,
      };
      setUser(domainUser);
    } catch {
      clearAuth();
    }
  }

  return { login, logout, fetchMe, loading, errors, user, isAuthenticated };
}
