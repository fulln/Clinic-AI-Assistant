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
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{copy.agentsManagementTitle}</h1>
        <p className="mt-1 text-sm text-gray-500">{copy.agentsManagementSubtitle}</p>
      </div>

      <div className="mb-6 border-b border-gray-200">
        <nav className="-mb-px flex gap-6">
          {tabs.map((tab) => (
            <button
              key={tab.value}
              onClick={() => setFilter(tab.value)}
              className={[
                'whitespace-nowrap border-b-2 pb-3 text-sm font-medium transition',
                filter === tab.value
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700',
              ].join(' ')}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {actionError && (
        <div className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{actionError}</div>
      )}

      {isLoading ? (
        <div className="rounded-lg border border-gray-200 bg-white px-4 py-6 text-sm text-gray-500">
          {copy.loading}
        </div>
      ) : error ? (
        <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{copy.agentsLoadFailed}</div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr className="text-left text-xs font-medium uppercase tracking-wide text-gray-500">
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Slug</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Version</th>
                <th className="px-4 py-3">{copy.agentsAllowedRoles}</th>
                <th className="px-4 py-3">{copy.agentsActions}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filteredAgents.map((agent) => (
                <tr key={agent.id} className="align-top">
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-900">{agent.name}</div>
                    <div className="mt-1 text-sm text-gray-500">{agent.description}</div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{agent.slug}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {agent.agentType === 'demo' ? copy.agentsTabDemo : copy.agentsTabFormal}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${getStatusClassName(agent.status)}`}>
                      {getStatusLabel(agent.status, copy)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{agent.version ?? copy.agentsNoVersion}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {agent.allowedRoles.length > 0 ? agent.allowedRoles.join(', ') : '-'}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      {agent.status === 'draft' && (
                        <button
                          type="button"
                          onClick={() => void handlePublish(agent.id)}
                          disabled={isPublishing || isArchiving || isRestoring}
                          className="rounded-md bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                        >
                          {copy.agentsPublish}
                        </button>
                      )}
                      {agent.status === 'archived' && (
                        <button
                          type="button"
                          onClick={() => void handleRestore(agent.id)}
                          disabled={isPublishing || isArchiving || isRestoring}
                          className="rounded-md bg-amber-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-amber-700 disabled:opacity-50"
                        >
                          {copy.agentsRestoreToDraft}
                        </button>
                      )}
                      {agent.status !== 'archived' && (
                        <button
                          type="button"
                          onClick={() => void handleArchive(agent.id)}
                          disabled={isPublishing || isArchiving || isRestoring}
                          className="rounded-md bg-gray-800 px-3 py-1.5 text-xs font-medium text-white hover:bg-gray-900 disabled:opacity-50"
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
