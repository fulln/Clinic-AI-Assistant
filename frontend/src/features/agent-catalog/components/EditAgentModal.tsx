'use client';

import { useEffect, useState } from 'react';
import { Modal } from '@/shared/components/Modal';
import { useLocaleStore } from '@/shared/store/localeStore';
import { getSiteCopy } from '@/shared/i18n/site';
import type { Agent, AgentEditPayload } from '@/domains/agent/entities';

interface EditAgentModalProps {
  agent: Agent | null;
  open: boolean;
  onClose: () => void;
  onSave: (payload: AgentEditPayload) => Promise<void> | void;
  saving: boolean;
}

const ALL_ROLES = ['doctor', 'staff', 'admin'] as const;

const AVAILABLE_TOOLS: { name: string; labelKey: 'agentsToolKnowledgeBase' }[] = [
  { name: 'knowledge_base_search', labelKey: 'agentsToolKnowledgeBase' },
];

function toForm(agent: Agent): AgentEditPayload {
  return {
    name: agent.name,
    description: agent.description,
    agentType: agent.agentType,
    allowedRoles: [...agent.allowedRoles],
    systemPromptEn: agent.systemPromptEn ?? '',
    systemPromptZh: agent.systemPromptZh ?? '',
    tools: [...(agent.tools ?? [])],
    maxToolTurns: agent.maxToolTurns ?? 3,
    llmModel: agent.llmModel ?? '',
    llmTemperature: agent.llmTemperature ?? null,
    llmMaxTokens: agent.llmMaxTokens ?? null,
  };
}

export function EditAgentModal({ agent, open, onClose, onSave, saving }: EditAgentModalProps) {
  const locale = useLocaleStore((state) => state.locale);
  const copy = getSiteCopy(locale);
  const [form, setForm] = useState<AgentEditPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open && agent) {
      setForm(toForm(agent));
      setError(null);
    }
    if (!open) {
      setForm(null);
    }
  }, [open, agent]);

  if (!form || !agent) {
    return <Modal open={open} onClose={onClose} title={copy.agentsEditTitle} size="lg"><div /></Modal>;
  }

  const handleRoleToggle = (role: string) => {
    setForm((prev) => {
      if (!prev) return prev;
      const has = prev.allowedRoles.includes(role);
      return {
        ...prev,
        allowedRoles: has ? prev.allowedRoles.filter((r) => r !== role) : [...prev.allowedRoles, role],
      };
    });
  };

  const handleToolToggle = (toolName: string) => {
    setForm((prev) => {
      if (!prev) return prev;
      const has = prev.tools.includes(toolName);
      return {
        ...prev,
        tools: has ? prev.tools.filter((t) => t !== toolName) : [...prev.tools, toolName],
      };
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form) return;
    setError(null);
    const payload: AgentEditPayload = {
      ...form,
      systemPromptEn: form.systemPromptEn?.trim() ? form.systemPromptEn : null,
      systemPromptZh: form.systemPromptZh?.trim() ? form.systemPromptZh : null,
      llmModel: form.llmModel?.toString().trim() ? form.llmModel : null,
      llmTemperature: form.llmTemperature === null || Number.isNaN(form.llmTemperature) ? null : Number(form.llmTemperature),
      llmMaxTokens: form.llmMaxTokens === null || Number.isNaN(form.llmMaxTokens) ? null : Number(form.llmMaxTokens),
    };
    try {
      await onSave(payload);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? copy.agentsSaveFailed);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title={copy.agentsEditTitle} size="lg">
      <form onSubmit={handleSubmit} className="space-y-4 text-sm">
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">
            {copy.agentsFieldName}
          </label>
          <input
            value={form.name}
            onChange={(e) => setForm((p) => p && { ...p, name: e.target.value })}
            className="w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-slate-400 focus:outline-none"
            required
          />
        </div>

        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">
            {copy.agentsFieldDescription}
          </label>
          <textarea
            value={form.description}
            onChange={(e) => setForm((p) => p && { ...p, description: e.target.value })}
            rows={2}
            className="w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-slate-400 focus:outline-none"
            required
          />
        </div>

        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">
            {copy.agentsFieldSystemPromptZh}
          </label>
          <textarea
            value={form.systemPromptZh ?? ''}
            onChange={(e) => setForm((p) => p && { ...p, systemPromptZh: e.target.value })}
            rows={6}
            className="w-full rounded-lg border border-slate-200 px-3 py-2 font-mono text-xs focus:border-slate-400 focus:outline-none"
          />
        </div>

        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">
            {copy.agentsFieldSystemPromptEn}
          </label>
          <textarea
            value={form.systemPromptEn ?? ''}
            onChange={(e) => setForm((p) => p && { ...p, systemPromptEn: e.target.value })}
            rows={6}
            className="w-full rounded-lg border border-slate-200 px-3 py-2 font-mono text-xs focus:border-slate-400 focus:outline-none"
          />
        </div>

        <div className="flex flex-wrap items-center gap-4">
          <div>
            <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">
              {copy.agentsFieldTools}
            </span>
            <div className="flex flex-wrap gap-3">
              {AVAILABLE_TOOLS.map((tool) => (
                <label key={tool.name} className="flex items-center gap-2 text-sm text-slate-700">
                  <input
                    type="checkbox"
                    checked={form.tools.includes(tool.name)}
                    onChange={() => handleToolToggle(tool.name)}
                    className="h-4 w-4 rounded border-slate-300"
                  />
                  {copy[tool.labelKey]}
                </label>
              ))}
            </div>
          </div>
          <div className="w-40">
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">
              {copy.agentsFieldMaxToolTurns}
            </label>
            <input
              type="number"
              min={1}
              max={10}
              step={1}
              value={form.maxToolTurns}
              onChange={(e) =>
                setForm((p) => p && {
                  ...p,
                  maxToolTurns: e.target.value === '' ? 3 : Math.max(1, Number(e.target.value)),
                })
              }
              className="w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-slate-400 focus:outline-none"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">
              {copy.agentsFieldLlmModel}
            </label>
            <input
              value={form.llmModel ?? ''}
              onChange={(e) => setForm((p) => p && { ...p, llmModel: e.target.value })}
              placeholder={copy.agentsLlmModelPlaceholder}
              className="w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-slate-400 focus:outline-none"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">
              {copy.agentsFieldLlmTemperature}
            </label>
            <input
              type="number"
              min={0}
              max={2}
              step={0.1}
              value={form.llmTemperature ?? ''}
              onChange={(e) =>
                setForm((p) => p && {
                  ...p,
                  llmTemperature: e.target.value === '' ? null : Number(e.target.value),
                })
              }
              className="w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-slate-400 focus:outline-none"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">
              {copy.agentsFieldLlmMaxTokens}
            </label>
            <input
              type="number"
              min={1}
              step={1}
              value={form.llmMaxTokens ?? ''}
              onChange={(e) =>
                setForm((p) => p && {
                  ...p,
                  llmMaxTokens: e.target.value === '' ? null : Number(e.target.value),
                })
              }
              placeholder={copy.agentsLlmMaxTokensPlaceholder}
              className="w-full rounded-lg border border-slate-200 px-3 py-2 focus:border-slate-400 focus:outline-none"
            />
          </div>
        </div>

        <div>
          <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">
            {copy.agentsAllowedRoles}
          </span>
          <div className="flex flex-wrap gap-3">
            {ALL_ROLES.map((role) => (
              <label key={role} className="flex items-center gap-2 text-sm text-slate-700">
                <input
                  type="checkbox"
                  checked={form.allowedRoles.includes(role)}
                  onChange={() => handleRoleToggle(role)}
                  className="h-4 w-4 rounded border-slate-300"
                />
                {role}
              </label>
            ))}
          </div>
        </div>

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">{error}</div>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:border-slate-300"
            disabled={saving}
          >
            {copy.cancel}
          </button>
          <button
            type="submit"
            className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-50"
            disabled={saving}
          >
            {saving ? copy.agentsSaving : copy.agentsSave}
          </button>
        </div>
      </form>
    </Modal>
  );
}
