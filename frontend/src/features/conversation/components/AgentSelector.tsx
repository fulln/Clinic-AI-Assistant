'use client';

import { useEffect, useState } from 'react';
import apiClient from '@/shared/api/client';
import { useAuthStore } from '@/shared/store/authStore';

interface AgentOption {
  id: string;
  name: string;
  agent_type: 'formal' | 'demo';
  allowed_roles: string[];
}

interface AgentSelectorProps {
  value: string | null;
  onChange: (agentId: string) => void;
  disabled?: boolean;
}

export function AgentSelector({ value, onChange, disabled }: AgentSelectorProps) {
  const [agents, setAgents] = useState<AgentOption[]>([]);
  const user = useAuthStore((s) => s.user);

  useEffect(() => {
    apiClient
      .get<{ items: AgentOption[] }>('/api/v1/agents', { params: { status: 'published' } })
      .then(({ data }) => {
        const filtered = data.items.filter(
          (a) => !user || a.allowed_roles.includes(user.role) || user.role === 'admin'
        );
        setAgents(filtered);
      })
      .catch(() => {});
  }, [user]);

  if (agents.length === 0) return null;

  return (
    <select
      value={value ?? ''}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      className="rounded-md border border-gray-300 bg-white px-2 py-1.5 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:opacity-50"
    >
      <option value="">选择智能体</option>
      {agents.map((a) => (
        <option key={a.id} value={a.id}>
          {a.name} {a.agent_type === 'demo' ? '（演示）' : ''}
        </option>
      ))}
    </select>
  );
}
