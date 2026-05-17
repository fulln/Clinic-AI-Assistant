'use client';

import { useEffect, useRef } from 'react';
import { StreamingMessage } from './StreamingMessage';
import type { Message } from '@/domains/conversation/entities';

interface MessageListProps {
  messages: Message[];
  streamingContent?: string;
  isStreaming?: boolean;
}

export function MessageList({ messages, streamingContent, isStreaming }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length, streamingContent]);

  if (messages.length === 0 && !isStreaming) {
    return (
      <div className="flex flex-1 items-center justify-center text-sm text-gray-400">
        开始与 AI 助手对话
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
              <StreamingMessage
                content={msg.content}
                hasDisclaimer={msg.hasDisclaimer}
              />
            )}
          </div>
        </div>
      ))}

      {isStreaming && streamingContent !== undefined && (
        <div className="flex justify-start">
          <div className="max-w-[75%] rounded-xl border border-gray-200 bg-white px-4 py-3 shadow-sm">
            <StreamingMessage content={streamingContent} isStreaming />
          </div>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
