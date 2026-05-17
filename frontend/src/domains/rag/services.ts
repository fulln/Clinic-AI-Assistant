import type { Locale } from '@/domains/conversation/entities';
import { getSiteCopy } from '@/shared/i18n/site';

/**
 * T095 — RAG domain service: file validation.
 */

const ALLOWED_TYPES: string[] = [
  'application/pdf',
  'text/plain',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/markdown',
];

const MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024; // 50 MB

export class RAGDomainService {
  /**
   * Validate a file before upload.
   * Returns an error message string, or null if the file is valid.
   */
  static validateFile(file: File, locale: Locale): string | null {
    const copy = getSiteCopy(locale);
    if (!ALLOWED_TYPES.includes(file.type)) {
      return copy.ragUnsupportedType(file.type || '');
    }
    if (file.size > MAX_FILE_SIZE_BYTES) {
      return copy.ragFileTooLarge((file.size / 1024 / 1024).toFixed(1));
    }
    return null;
  }
}
