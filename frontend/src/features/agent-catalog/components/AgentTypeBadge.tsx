import type { AgentType } from '@/domains/agent/entities';

interface AgentTypeBadgeProps {
  agentType: AgentType;
}

export function AgentTypeBadge({ agentType }: AgentTypeBadgeProps) {
  if (agentType === 'demo') {
    return (
      <span className="inline-flex items-center rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-medium text-amber-800">
        演示
      </span>
    );
  }

  return (
    <span className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800">
      正式
    </span>
  );
}
