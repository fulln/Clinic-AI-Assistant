'use client';

import { useState } from 'react';
import { useAgents } from '@/features/agent-catalog/hooks/useAgents';
import { AgentList } from '@/features/agent-catalog/components/AgentList';
import type { AgentType } from '@/domains/agent/entities';

type TabValue = 'all' | AgentType;

const TABS: { label: string; value: TabValue }[] = [
  { label: '全部', value: 'all' },
  { label: '正式', value: 'formal' },
  { label: '演示', value: 'demo' },
];

export default function AgentsPage() {
  const [activeTab, setActiveTab] = useState<TabValue>('all');

  const { agents, isLoading, error } = useAgents({
    type: activeTab === 'all' ? undefined : activeTab,
  });

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">智能体目录</h1>
        <p className="mt-1 text-sm text-gray-500">浏览并使用可用的 AI 智能体</p>
      </div>

      {/* Tabs */}
      <div className="mb-6 border-b border-gray-200">
        <nav className="-mb-px flex gap-6" aria-label="Tabs">
          {TABS.map((tab) => (
            <button
              key={tab.value}
              onClick={() => setActiveTab(tab.value)}
              className={[
                'whitespace-nowrap border-b-2 pb-3 text-sm font-medium transition',
                activeTab === tab.value
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700',
              ].join(' ')}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <svg
            className="h-8 w-8 animate-spin text-blue-500"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            aria-label="加载中"
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
        <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
          加载智能体失败，请稍后重试。
        </div>
      ) : (
        <AgentList agents={agents} />
      )}
    </div>
  );
}
