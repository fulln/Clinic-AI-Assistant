import Link from 'next/link';
import type { Agent } from '@/domains/agent/entities';
import { AgentTypeBadge } from './AgentTypeBadge';

interface AgentCardProps {
  agent: Agent;
}

export function AgentCard({ agent }: AgentCardProps) {
  return (
    <div className="flex flex-col gap-3 rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition hover:shadow-md">
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-base font-semibold text-gray-900 leading-snug">{agent.name}</h3>
        <AgentTypeBadge agentType={agent.agentType} />
      </div>

      <p className="line-clamp-2 text-sm text-gray-500">{agent.description}</p>

      {agent.capabilities.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {agent.capabilities.map((cap) => (
            <span
              key={cap}
              className="inline-block rounded-md bg-gray-100 px-2 py-0.5 text-xs text-gray-600"
            >
              {cap}
            </span>
          ))}
        </div>
      )}

      {agent.agentType === 'demo' && (
        <div className="mt-auto pt-2">
          <Link
            href={`/agents/${agent.id}`}
            className="inline-flex items-center rounded-lg bg-amber-500 px-4 py-2 text-sm font-medium text-white transition hover:bg-amber-600 focus:outline-none focus:ring-2 focus:ring-amber-400 focus:ring-offset-1"
          >
            进入演示
          </Link>
        </div>
      )}
    </div>
  );
}
