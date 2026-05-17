import type { Locale } from '@/domains/conversation/entities';
import { getSiteCopy } from '@/shared/i18n/site';

export class AuthDomainService {
  static validateUsername(username: string, locale: Locale): string | null {
    const copy = getSiteCopy(locale);
    if (!username.trim()) return copy.authUsernameRequired;
    if (username.trim().length < 3) return copy.authUsernameMin;
    return null;
  }

  static validatePassword(password: string, locale: Locale): string | null {
    const copy = getSiteCopy(locale);
    if (!password) return copy.authPasswordRequired;
    return null;
  }
}
