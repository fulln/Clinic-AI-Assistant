import { LoginForm } from '@/features/auth/components/LoginForm';

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-sm rounded-xl border border-gray-200 bg-white p-8 shadow-sm">
        <div className="mb-6 text-center">
          <h1 className="text-2xl font-bold text-gray-900">诊所 AI 助手</h1>
          <p className="mt-1 text-sm text-gray-500">请登录您的账户</p>
        </div>
        <LoginForm />
      </div>
    </div>
  );
}
