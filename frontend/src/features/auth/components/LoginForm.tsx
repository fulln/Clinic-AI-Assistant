'use client';

import { useState } from 'react';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { useLocaleStore } from '@/shared/store/localeStore';
import { getSiteCopy } from '@/shared/i18n/site';

export function LoginForm() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const { login, loading, errors } = useAuth();
  const locale = useLocaleStore((state) => state.locale);
  const copy = getSiteCopy(locale);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await login(username, password);
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-sm space-y-5">
      <div>
        <label htmlFor="username" className="mb-2 block text-sm font-semibold text-slate-700">
          {copy.authUsername}
        </label>
        <input
          id="username"
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoComplete="username"
          className="w-full rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3 text-sm text-slate-900 shadow-sm outline-none transition focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-100"
          placeholder={copy.authUsernamePlaceholder}
          disabled={loading}
        />
        {errors.username && <p className="mt-1 text-xs text-red-600">{errors.username}</p>}
      </div>

      <div>
        <label htmlFor="password" className="mb-2 block text-sm font-semibold text-slate-700">
          {copy.authPassword}
        </label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
          className="w-full rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3 text-sm text-slate-900 shadow-sm outline-none transition focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-100"
          placeholder={copy.authPasswordPlaceholder}
          disabled={loading}
        />
        {errors.password && <p className="mt-1 text-xs text-red-600">{errors.password}</p>}
      </div>

      {errors.general && (
        <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{errors.general}</p>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-2xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white shadow-[0_12px_32px_rgba(15,23,42,0.18)] transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? copy.authLoggingIn : copy.authLogin}
      </button>
    </form>
  );
}
