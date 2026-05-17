'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/features/auth/hooks/useAuth';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const navItems = [
    { href: '/conversation', label: '对话' },
    { href: '/agents', label: '智能体' },
    ...(user?.role === 'doctor' ? [{ href: '/rag', label: '知识库' }] : []),
  ];

  return (
    <div className="flex h-screen bg-gray-50">
      <aside className="w-56 flex-shrink-0 border-r border-gray-200 bg-white flex flex-col">
        <div className="px-4 py-5 border-b border-gray-100">
          <span className="text-sm font-semibold text-gray-800">诊所 AI 助手</span>
        </div>
        <nav className="flex-1 px-2 py-4 space-y-1">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                pathname.startsWith(item.href)
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="px-4 py-4 border-t border-gray-100">
          <p className="text-xs text-gray-500 mb-1">{user?.displayName}</p>
          <p className="text-xs text-gray-400 mb-3">
            {user?.role === 'doctor' ? '医师' : user?.role === 'admin' ? '管理员' : '员工'}
          </p>
          <button
            onClick={logout}
            className="w-full text-left text-xs text-gray-500 hover:text-red-600 transition-colors"
          >
            退出登录
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
