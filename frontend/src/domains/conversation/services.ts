import type { Locale } from './entities';
import { t } from '@/shared/i18n/conversation';

export class ConversationDomainService {
  static validateMessageContent(content: string, locale: Locale): string | null {
    const copy = t(locale);
    if (!content.trim()) return copy.validationEmpty;
    if (content.length > 4000) return copy.validationTooLong(content.length);
    return null;
  }
}
