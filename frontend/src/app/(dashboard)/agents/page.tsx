'use client';

import { useState } from 'react';
import { useAgents } from '@/features/agent-catalog/hooks/useAgents';
import { AgentList } from '@/features/agent-catalog/components/AgentList';
import type { AgentType } from '@/domains/agent/entities';
import { useLocaleStore } from '@/shared/store/localeStore';
import { getSiteCopy } from '@/shared/i18n/site';

type TabValue = 'all' | AgentType;

export default function AgentsPage() {
  const [activeTab, setActiveTab] = useState<TabValue>('all');
  const locale = useLocaleStore((state) => state.locale);
  const copy = getSiteCopy(locale);
  const tabs: { label: string; value: TabValue }[] = [
    { label: copy.agentsTabAll, value: 'all' },
    { label: copy.agentsTabFormal, value: 'formal' },
    { label: copy.agentsTabDemo, value: 'demo' },
  ];

  const { agents, isLoading, error } = useAgents({
    type: activeTab === 'all' ? undefined : activeTab,
  });

  return (
    <div className="space-y-6">
      <div className="saas-panel px-6 py-6">
        <h1 className="text-2xl font-bold text-gray-900">{copy.agentsTitle}</h1>
        <p className="mt-1 text-sm text-gray-500">{copy.agentsSubtitle}</p>
        <div className="mt-6 border-b border-slate-200">
          <nav className="-mb-px flex gap-6" aria-label="Tabs">
            {tabs.map((tab) => (
              <button
                key={tab.value}
                onClick={() => setActiveTab(tab.value)}
                className={[
                  'whitespace-nowrap border-b-2 pb-3 text-sm font-semibold transition',
                  activeTab === tab.value
                    ? 'border-slate-900 text-slate-900'
                    : 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700',
                ].join(' ')}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {isLoading ? (
        <div className="saas-panel flex items-center justify-center py-24">
          <svg
            className="h-8 w-8 animate-spin text-blue-500"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            aria-label={copy.loading}
          >
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
        </div>
      ) : error ? (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {copy.agentsLoadFailed}
        </div>
      ) : (
        <AgentList agents={agents} locale={locale} />
      )}
    </div>
  );
}
