'use client';

import type { Locale } from '@/domains/conversation/entities';
import { getDisclaimer } from '@/shared/i18n/conversation';
import { DisclaimerBanner } from './DisclaimerBanner';

interface StreamingMessageProps {
  content: string;
  locale: Locale;
  isStreaming?: boolean;
  hasDisclaimer?: boolean;
}

export function StreamingMessage({ content, locale, isStreaming, hasDisclaimer }: StreamingMessageProps) {
  // Strip the disclaimer text from content display if we show it separately
  const DISCLAIMER = getDisclaimer(locale);
  const displayContent = content.replace(`\n\n${DISCLAIMER}`, '').replace(DISCLAIMER, '').trim();

  return (
    <div className="space-y-2">
      <div className="whitespace-pre-wrap text-sm text-gray-800 leading-relaxed">
        {displayContent}
        {isStreaming && (
          <span className="inline-block w-0.5 h-4 bg-gray-500 ml-0.5 animate-pulse align-middle" />
        )}
      </div>
      {(hasDisclaimer || content.includes(DISCLAIMER)) && !isStreaming && (
        <DisclaimerBanner locale={locale} />
      )}
    </div>
  );
}
