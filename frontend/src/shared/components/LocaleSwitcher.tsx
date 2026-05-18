'use client';

import type { Locale } from '@/domains/conversation/entities';
import { localeOptions } from '@/shared/i18n/conversation';
import { getSiteCopy } from '@/shared/i18n/site';
import { useLocaleStore } from '@/shared/store/localeStore';

interface LocaleSwitcherProps {
  locale?: Locale;
  onChange?: (locale: Locale) => void;
  className?: string;
  compact?: boolean;
  hideLabel?: boolean;
}

export function LocaleSwitcher({
  locale,
  onChange,
  className,
  compact = false,
  hideLabel = false,
}: LocaleSwitcherProps) {
  const storeLocale = useLocaleStore((state) => state.locale);
  const setStoreLocale = useLocaleStore((state) => state.setLocale);
  const activeLocale = locale ?? storeLocale;
  const copy = getSiteCopy(activeLocale);

  const handleChange = (nextLocale: Locale) => {
    setStoreLocale(nextLocale);
    onChange?.(nextLocale);
  };

  return (
    <div className={className}>
      {!hideLabel && (
        <label
          className={`block font-semibold uppercase tracking-[0.18em] text-slate-400 ${
            compact ? 'text-[10px]' : 'text-[11px]'
          }`}
        >
          {copy.language}
        </label>
      )}
      <select
        value={activeLocale}
        onChange={(event) => handleChange(event.target.value as Locale)}
        className={`w-full border border-slate-200 bg-white font-medium text-slate-700 shadow-sm outline-none transition focus:border-blue-400 focus:ring-4 focus:ring-blue-100 ${
          compact
            ? `${hideLabel ? 'mt-0' : 'mt-1'} rounded-xl px-3 py-1.5 text-sm`
            : 'mt-2 rounded-2xl px-3 py-2 text-sm'
        }`}
      >
        {localeOptions.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}
