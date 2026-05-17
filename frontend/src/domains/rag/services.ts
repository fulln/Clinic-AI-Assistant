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
  static validateFile(file: File): string | null {
    if (!ALLOWED_TYPES.includes(file.type)) {
      return `不支持的文件类型：${file.type || '未知'}。请上传 PDF、TXT、DOCX 或 Markdown 文件。`;
    }
    if (file.size > MAX_FILE_SIZE_BYTES) {
      return `文件过大（${(file.size / 1024 / 1024).toFixed(1)} MB），最大允许 50 MB。`;
    }
    return null;
  }
}
