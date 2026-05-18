import type { Locale } from '@/domains/conversation/entities';
import { getDisclaimer } from '@/shared/i18n/conversation';

interface DisclaimerBannerProps {
  locale: Locale;
}

export function DisclaimerBanner({ locale }: DisclaimerBannerProps) {
  return (
    <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
      ⚠️ {getDisclaimer(locale)}
    </div>
  );
}
