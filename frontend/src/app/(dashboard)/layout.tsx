'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { LocaleSwitcher } from '@/shared/components/LocaleSwitcher';
import { useLocaleStore } from '@/shared/store/localeStore';
import { getRoleLabel, getSiteCopy } from '@/shared/i18n/site';

function getInitials(name?: string) {
  if (!name) return 'AI';
  return name
    .split(/\s+/)
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const locale = useLocaleStore((state) => state.locale);
  const copy = getSiteCopy(locale);

  const navItems = [
    { href: '/conversation', label: copy.navConversation },
    { href: '/agents', label: copy.navAgents },
    ...(user?.role === 'admin' ? [{ href: '/agent-management', label: copy.navAgentManagement }] : []),
    ...(user?.role === 'doctor' ? [{ href: '/rag', label: copy.navKnowledgeBase }] : []),
  ];

  const pageMeta = pathname.startsWith('/conversation')
    ? { title: copy.navConversation, subtitle: copy.dashboardSubtitleConversation }
    : pathname.startsWith('/agent-management')
      ? { title: copy.navAgentManagement, subtitle: copy.dashboardSubtitleAgentManagement }
      : pathname.startsWith('/agents')
        ? { title: copy.navAgents, subtitle: copy.dashboardSubtitleAgents }
        : pathname.startsWith('/rag')
          ? { title: copy.navKnowledgeBase, subtitle: copy.dashboardSubtitleKnowledgeBase }
          : { title: copy.dashboardOverview, subtitle: copy.dashboardSubtitleConversation };

  return (
    <div className="app-shell flex min-h-screen">
      <aside className="saas-sidebar hidden w-72 flex-shrink-0 flex-col px-5 py-6 lg:flex">
        <div className="flex items-center gap-3 px-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-950 text-sm font-bold text-white shadow-[0_16px_30px_rgba(15,23,42,0.18)]">
            AI
          </div>
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">
              {copy.dashboardWorkspaceStatus}
            </p>
            <p className="text-sm font-semibold text-slate-900">{copy.appName}</p>
          </div>
        </div>

        <div className="saas-muted-panel mt-6 px-4 py-4">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
            {copy.dashboardOverview}
          </p>
          <p className="mt-2 text-sm leading-6 text-slate-600">{pageMeta.subtitle}</p>
        </div>

        <nav className="mt-6 flex-1 space-y-2">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`saas-nav-item ${
                pathname.startsWith(item.href)
                  ? 'saas-nav-item-active'
                  : ''
              }`}
            >
              <span className={`h-2 w-2 rounded-full ${pathname.startsWith(item.href) ? 'bg-white' : 'bg-slate-300'}`} />
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="mt-6 rounded-3xl border border-slate-200/80 bg-white/90 p-4 shadow-sm">
          <LocaleSwitcher className="mb-4" />
          <div className="flex items-center gap-3 rounded-2xl bg-slate-50 px-3 py-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-900 text-xs font-bold text-white">
              {getInitials(user?.displayName)}
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-slate-900">{user?.displayName}</p>
              <p className="text-xs text-slate-500">{user ? getRoleLabel(user.role, locale) : ''}</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="mt-4 w-full rounded-2xl border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
          >
            {copy.logout}
          </button>
        </div>
      </aside>

      <main className="flex min-h-screen flex-1 flex-col overflow-hidden">
        <header className="border-b border-white/60 bg-white/65 px-5 py-4 backdrop-blur-xl sm:px-8">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="saas-pill mb-3">{copy.dashboardOverview}</div>
              <h1 className="text-3xl font-semibold tracking-tight text-slate-950">{pageMeta.title}</h1>
              <p className="mt-2 text-sm leading-6 text-slate-500">{pageMeta.subtitle}</p>
            </div>
            <div className="saas-panel flex items-center gap-3 px-4 py-3">
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">
                  {copy.dashboardWorkspaceStatus}
                </p>
                <p className="text-sm font-semibold text-slate-700">{copy.dashboardWorkspaceHealthy}</p>
              </div>
            </div>
          </div>
        </header>

        <div className="flex-1 overflow-auto px-5 py-5 sm:px-8">
          {children}
        </div>
      </main>
    </div>
  );
}
