import Link from 'next/link';
import type { Agent } from '@/domains/agent/entities';
import { AgentTypeBadge } from './AgentTypeBadge';
import type { Locale } from '@/domains/conversation/entities';
import { getSiteCopy } from '@/shared/i18n/site';

interface AgentCardProps {
  agent: Agent;
  locale: Locale;
}

export function AgentCard({ agent, locale }: AgentCardProps) {
  const copy = getSiteCopy(locale);

  return (
    <div className="group flex h-full flex-col gap-4 rounded-[1.5rem] border border-white/80 bg-white/90 p-6 shadow-[0_18px_50px_rgba(15,23,42,0.08)] transition duration-200 hover:-translate-y-1 hover:shadow-[0_24px_70px_rgba(15,23,42,0.12)]">
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-lg font-semibold leading-snug text-slate-900">{agent.name}</h3>
        <AgentTypeBadge agentType={agent.agentType} locale={locale} />
      </div>

      <p className="line-clamp-3 text-sm leading-6 text-slate-500">{agent.description}</p>

      {agent.capabilities.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {agent.capabilities.map((cap) => (
            <span
              key={cap}
              className="inline-block rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600"
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
            className="inline-flex items-center rounded-2xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-1"
          >
            {copy.agentsDemoEnter}
          </Link>
        </div>
      )}
    </div>
  );
}
