'use client';

import { useEffect, useRef } from 'react';
import { StreamingMessage } from './StreamingMessage';
import type { Locale, Message } from '@/domains/conversation/entities';
import type { StreamProgress } from '../hooks/useSSEStream';
import { normalizeLocale, t } from '@/shared/i18n/conversation';

interface MessageListProps {
  locale: Locale;
  messages: Message[];
  streamingContent?: string;
  isStreaming?: boolean;
  progressSteps?: StreamProgress[];
}

export function MessageList({
  locale,
  messages,
  streamingContent,
  isStreaming,
  progressSteps = [],
}: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const copy = t(locale);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length, streamingContent, progressSteps.length]);

  if (messages.length === 0 && !isStreaming) {
    return (
      <div className="flex flex-1 items-center justify-center text-sm text-gray-400">
        {copy.emptyState}
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col gap-4 overflow-y-auto px-4 py-4">
      {messages.map((msg) => (
        <div
          key={msg.id}
          className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          <div
            className={`max-w-[75%] rounded-xl px-4 py-3 text-sm ${
              msg.role === 'user'
                ? 'bg-blue-600 text-white'
                : 'bg-white border border-gray-200 shadow-sm'
            }`}
          >
            {msg.role === 'user' ? (
              <p className="whitespace-pre-wrap">{msg.content}</p>
            ) : (
              <>
                <ProgressTrace
                  steps={msg.progressSteps ?? []}
                  locale={normalizeLocale(msg.metadata?.locale ?? locale)}
                />
                <StreamingMessage
                  content={msg.content}
                  locale={normalizeLocale(msg.metadata?.disclaimer_locale ?? msg.metadata?.locale ?? locale)}
                  hasDisclaimer={msg.hasDisclaimer}
                />
              </>
            )}
          </div>
        </div>
      ))}

      {isStreaming && streamingContent !== undefined && (
        <div className="flex justify-start">
          <div className="max-w-[75%] rounded-xl border border-gray-200 bg-white px-4 py-3 shadow-sm">
            <ProgressTrace steps={progressSteps} locale={locale} />
            <StreamingMessage content={streamingContent} locale={locale} isStreaming />
          </div>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}

function ProgressTrace({ steps, locale }: { steps: StreamProgress[]; locale: Locale }) {
  if (steps.length === 0) return null;

  return (
    <details open className="mb-3 rounded-md border border-blue-100 bg-blue-50 px-3 py-2 text-xs text-blue-800">
      <summary className="cursor-pointer font-medium">{t(locale).progressTrace}</summary>
      <div className="mt-2 space-y-1">
        {steps.map((step, index) => (
          <div key={`${step.stage}-${index}`} className="space-y-2">
            <div className="flex gap-2">
              <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-blue-500" />
              <span>{step.message}</span>
            </div>
            {(step.artifacts ?? []).length > 0 && (
              <div className="ml-4 space-y-2">
                {step.artifacts?.map((artifact, artifactIndex) => (
                  <div
                    key={`${artifact.chunk_id ?? artifactIndex}`}
                    className="rounded border border-blue-100 bg-white px-2 py-2 text-blue-950"
                  >
                    <div className="flex flex-wrap items-center gap-2 font-medium">
                      <span>{artifact.title}</span>
                      {artifact.score !== undefined && artifact.score !== null && (
                        <span className="text-[11px] font-normal text-blue-600">
                          score {artifact.score}
                        </span>
                      )}
                    </div>
                    {artifact.subtitle && (
                      <div className="mt-0.5 text-[11px] text-blue-600">{artifact.subtitle}</div>
                    )}
                    <div className="mt-1 whitespace-pre-wrap text-[11px] leading-relaxed text-gray-700">
                      {artifact.content}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </details>
  );
}
