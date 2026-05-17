'use client';

import { useState, useRef, KeyboardEvent } from 'react';
import type { Locale } from '@/domains/conversation/entities';
import { t } from '@/shared/i18n/conversation';

interface MessageInputProps {
  onSend: (content: string) => void;
  locale: Locale;
  disabled?: boolean;
}

export function MessageInput({ onSend, locale, disabled }: MessageInputProps) {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const copy = t(locale);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = 'auto';
      el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
    }
  };

  return (
    <div className="border-t border-slate-200 bg-white/92 px-5 py-4 backdrop-blur">
      <div className="flex items-end gap-3 rounded-[1.5rem] border border-slate-200 bg-slate-50 px-4 py-3 shadow-inner focus-within:border-blue-400 focus-within:ring-4 focus-within:ring-blue-100">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder={disabled ? copy.placeholderStreaming : copy.placeholderReady}
          disabled={disabled}
          rows={1}
          maxLength={4000}
          className="flex-1 resize-none bg-transparent text-sm leading-6 text-slate-800 outline-none placeholder:text-slate-400 disabled:opacity-50"
        />
        <button
          onClick={handleSend}
          disabled={disabled || !value.trim()}
          className="rounded-2xl bg-slate-900 px-4 py-2 text-xs font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {copy.send}
        </button>
      </div>
      <p className="mt-2 text-right text-xs text-slate-400">{value.length}/4000</p>
    </div>
  );
}
