'use client';

import { LoginForm } from '@/features/auth/components/LoginForm';
import { useLocaleStore } from '@/shared/store/localeStore';
import { getSiteCopy } from '@/shared/i18n/site';

export default function LoginPage() {
  const locale = useLocaleStore((state) => state.locale);
  const copy = getSiteCopy(locale);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-sm rounded-xl border border-gray-200 bg-white p-8 shadow-sm">
        <div className="mb-6">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900">{copy.authLoginTitle}</h1>
            <p className="mt-1 text-sm text-gray-500">{copy.authLoginSubtitle}</p>
          </div>
        </div>
        <LoginForm />
      </div>
    </div>
  );
}
