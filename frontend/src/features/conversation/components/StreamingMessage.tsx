'use client';

import { DisclaimerBanner } from './DisclaimerBanner';

interface StreamingMessageProps {
  content: string;
  isStreaming?: boolean;
  hasDisclaimer?: boolean;
}

export function StreamingMessage({ content, isStreaming, hasDisclaimer }: StreamingMessageProps) {
  // Strip the disclaimer text from content display if we show it separately
  const DISCLAIMER = '本内容仅供辅助参考，不构成医疗诊断或治疗建议，请遵医嘱。';
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
        <DisclaimerBanner />
      )}
    </div>
  );
}
