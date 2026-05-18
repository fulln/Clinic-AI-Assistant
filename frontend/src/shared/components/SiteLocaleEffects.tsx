'use client';

import { useEffect } from 'react';
import { useLocaleStore } from '@/shared/store/localeStore';
import { getSiteCopy } from '@/shared/i18n/site';
import { detectBrowserLocale } from '@/shared/i18n/conversation';

export function SiteLocaleEffects() {
  const locale = useLocaleStore((state) => state.locale);
  const setLocale = useLocaleStore((state) => state.setLocale);

  useEffect(() => {
    const storedLocale = window.localStorage.getItem('clinic-locale');
    if (!storedLocale) {
      setLocale(detectBrowserLocale());
    }
  }, [setLocale]);

  useEffect(() => {
    const copy = getSiteCopy(locale);
    document.documentElement.lang = locale;
    document.title = copy.metaTitle;

    let description = document.querySelector('meta[name="description"]');
    if (!description) {
      description = document.createElement('meta');
      description.setAttribute('name', 'description');
      document.head.appendChild(description);
    }
    description.setAttribute('content', copy.metaDescription);
  }, [locale]);

  return null;
}
