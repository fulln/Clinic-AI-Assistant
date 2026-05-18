'use client';

import { ConversationPanel } from '@/features/conversation/components/ConversationPanel';
import { useLocaleStore } from '@/shared/store/localeStore';
import { getSiteCopy } from '@/shared/i18n/site';

export default function ConversationPage() {
  const locale = useLocaleStore((state) => state.locale);
  const copy = getSiteCopy(locale);

  return (
    <div className="grid min-h-0 gap-5 xl:grid-cols-[minmax(0,1fr)_320px]">
      <div className="saas-panel flex h-[calc(100vh-12.5rem)] min-h-0 flex-col overflow-hidden">
        <ConversationPanel />
      </div>
      <aside className="hidden h-[calc(100vh-12.5rem)] min-h-0 xl:flex xl:flex-col xl:gap-4">
        <div className="saas-panel p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">{copy.dashboardConversationPatternLabel}</p>
          <h2 className="mt-3 text-lg font-semibold text-slate-900">{copy.dashboardConversationPatternTitle}</h2>
          <p className="mt-3 text-sm leading-6 text-slate-500">
            {copy.dashboardConversationPatternBody}
          </p>
        </div>
        <div className="saas-muted-panel p-5">
          <p className="text-sm font-semibold text-slate-900">{copy.dashboardConversationPatternIncluded}</p>
          <ul className="mt-3 space-y-3 text-sm text-slate-500">
            <li>{copy.dashboardConversationPatternPointOne}</li>
            <li>{copy.dashboardConversationPatternPointTwo}</li>
            <li>{copy.dashboardConversationPatternPointThree}</li>
          </ul>
        </div>
      </aside>
    </div>
  );
}
