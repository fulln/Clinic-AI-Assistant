import type { AgentType } from '@/domains/agent/entities';
import type { Locale } from '@/domains/conversation/entities';
import { getSiteCopy } from '@/shared/i18n/site';

interface AgentTypeBadgeProps {
  agentType: AgentType;
  locale: Locale;
}

export function AgentTypeBadge({ agentType, locale }: AgentTypeBadgeProps) {
  const copy = getSiteCopy(locale);

  if (agentType === 'demo') {
    return (
      <span className="inline-flex items-center rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-medium text-amber-800">
        {copy.agentsTabDemo}
      </span>
    );
  }

  return (
    <span className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800">
      {copy.agentsTabFormal}
    </span>
  );
}
