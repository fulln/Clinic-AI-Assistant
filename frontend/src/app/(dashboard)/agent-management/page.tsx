'use client';

import { useMemo, useState } from 'react';
import { useAuthStore } from '@/shared/store/authStore';
import { useLocaleStore } from '@/shared/store/localeStore';
import { getSiteCopy } from '@/shared/i18n/site';
import { useAgentManagement } from '@/features/agent-catalog/hooks/useAgentManagement';
import type { AgentStatus, AgentType } from '@/domains/agent/entities';

type FilterValue = 'all' | AgentType;

function getStatusLabel(status: AgentStatus, copy: ReturnType<typeof getSiteCopy>) {
  if (status === 'draft') return copy.agentsStatusDraft;
  if (status === 'published') return copy.agentsStatusPublished;
  return copy.agentsStatusArchived;
}

function getStatusClassName(status: AgentStatus) {
  if (status === 'draft') return 'bg-amber-100 text-amber-800';
  if (status === 'published') return 'bg-green-100 text-green-800';
  return 'bg-gray-100 text-gray-700';
}

export default function AgentManagementPage() {
  const user = useAuthStore((state) => state.user);
  const locale = useLocaleStore((state) => state.locale);
  const copy = getSiteCopy(locale);
  const [filter, setFilter] = useState<FilterValue>('all');
  const [actionError, setActionError] = useState<string | null>(null);
  const {
    agents,
    isLoading,
    error,
    publishAgent,
    archiveAgent,
    restoreAgent,
    isPublishing,
    isArchiving,
    isRestoring,
  } =
    useAgentManagement();

  const filteredAgents = useMemo(() => {
    if (filter === 'all') return agents;
    return agents.filter((agent) => agent.agentType === filter);
  }, [agents, filter]);

  if (user?.role !== 'admin') {
    return (
      <div className="mx-auto max-w-4xl px-4 py-10">
        <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
          {copy.agentsManagementForbidden}
        </div>
      </div>
    );
  }

  const handlePublish = async (agentId: string) => {
    setActionError(null);
    try {
      await publishAgent(agentId);
    } catch (error: any) {
      setActionError(error?.response?.data?.detail ?? copy.agentsActionFailed);
    }
  };

  const handleArchive = async (agentId: string) => {
    setActionError(null);
    try {
      await archiveAgent(agentId);
    } catch (error: any) {
      setActionError(error?.response?.data?.detail ?? copy.agentsActionFailed);
    }
  };

  const handleRestore = async (agentId: string) => {
    setActionError(null);
    try {
      await restoreAgent(agentId);
    } catch (error: any) {
      setActionError(error?.response?.data?.detail ?? copy.agentsActionFailed);
    }
  };

  const tabs: Array<{ value: FilterValue; label: string }> = [
    { value: 'all', label: copy.agentsTabAll },
    { value: 'formal', label: copy.agentsTabFormal },
    { value: 'demo', label: copy.agentsTabDemo },
  ];

  return (
    <div className="space-y-6">
      <div className="saas-panel px-6 py-6">
        <h1 className="text-2xl font-bold text-gray-900">{copy.agentsManagementTitle}</h1>
        <p className="mt-1 text-sm text-gray-500">{copy.agentsManagementSubtitle}</p>
        <div className="mt-6 border-b border-slate-200">
          <nav className="-mb-px flex gap-6">
            {tabs.map((tab) => (
              <button
                key={tab.value}
                onClick={() => setFilter(tab.value)}
                className={[
                  'whitespace-nowrap border-b-2 pb-3 text-sm font-semibold transition',
                  filter === tab.value
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

      {actionError && (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{actionError}</div>
      )}

      {isLoading ? (
        <div className="saas-panel px-4 py-6 text-sm text-gray-500">
          {copy.loading}
        </div>
      ) : error ? (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{copy.agentsLoadFailed}</div>
      ) : (
        <div className="overflow-hidden rounded-[1.75rem] border border-white/80 bg-white/92 shadow-[0_18px_60px_rgba(15,23,42,0.08)]">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-slate-50/90">
              <tr className="text-left text-xs font-medium uppercase tracking-wide text-gray-500">
                <th className="px-4 py-3">{copy.agentsTableName}</th>
                <th className="px-4 py-3">{copy.agentsTableSlug}</th>
                <th className="px-4 py-3">{copy.agentsTableType}</th>
                <th className="px-4 py-3">{copy.agentsTableStatus}</th>
                <th className="px-4 py-3">{copy.agentsTableVersion}</th>
                <th className="px-4 py-3">{copy.agentsAllowedRoles}</th>
                <th className="px-4 py-3">{copy.agentsActions}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filteredAgents.map((agent) => (
                <tr key={agent.id} className="align-top">
                  <td className="px-4 py-4">
                    <div className="font-semibold text-slate-900">{agent.name}</div>
                    <div className="mt-1 text-sm leading-6 text-slate-500">{agent.description}</div>
                  </td>
                  <td className="px-4 py-4 text-sm text-slate-600">{agent.slug}</td>
                  <td className="px-4 py-4 text-sm text-slate-600">
                    {agent.agentType === 'demo' ? copy.agentsTabDemo : copy.agentsTabFormal}
                  </td>
                  <td className="px-4 py-4 text-sm">
                    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${getStatusClassName(agent.status)}`}>
                      {getStatusLabel(agent.status, copy)}
                    </span>
                  </td>
                  <td className="px-4 py-4 text-sm text-slate-600">{agent.version ?? copy.agentsNoVersion}</td>
                  <td className="px-4 py-4 text-sm text-slate-600">
                    {agent.allowedRoles.length > 0 ? agent.allowedRoles.join(', ') : '-'}
                  </td>
                  <td className="px-4 py-4">
                    <div className="flex flex-wrap gap-2">
                      {agent.status === 'draft' && (
                        <button
                          type="button"
                          onClick={() => void handlePublish(agent.id)}
                          disabled={isPublishing || isArchiving || isRestoring}
                          className="rounded-2xl bg-slate-900 px-3 py-2 text-xs font-semibold text-white transition hover:bg-slate-800 disabled:opacity-50"
                        >
                          {copy.agentsPublish}
                        </button>
                      )}
                      {agent.status === 'archived' && (
                        <button
                          type="button"
                          onClick={() => void handleRestore(agent.id)}
                          disabled={isPublishing || isArchiving || isRestoring}
                          className="rounded-2xl bg-amber-500 px-3 py-2 text-xs font-semibold text-white transition hover:bg-amber-600 disabled:opacity-50"
                        >
                          {copy.agentsRestoreToDraft}
                        </button>
                      )}
                      {agent.status !== 'archived' && (
                        <button
                          type="button"
                          onClick={() => void handleArchive(agent.id)}
                          disabled={isPublishing || isArchiving || isRestoring}
                          className="rounded-2xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50 disabled:opacity-50"
                        >
                          {copy.agentsArchive}
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {filteredAgents.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-10 text-center text-sm text-gray-500">
                    {copy.agentsEmpty}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
