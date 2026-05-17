'use client';

import type { Locale } from '@/domains/conversation/entities';
import { localeOptions } from '@/shared/i18n/conversation';
import { getSiteCopy } from '@/shared/i18n/site';
import { useLocaleStore } from '@/shared/store/localeStore';

interface LocaleSwitcherProps {
  locale?: Locale;
  onChange?: (locale: Locale) => void;
  className?: string;
}

export function LocaleSwitcher({ locale, onChange, className }: LocaleSwitcherProps) {
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
      <label className="block text-xs font-medium text-gray-500">{copy.language}</label>
      <select
        value={activeLocale}
        onChange={(event) => handleChange(event.target.value as Locale)}
        className="mt-1 w-full rounded-md border border-gray-300 bg-white px-2 py-1.5 text-sm text-gray-700"
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
