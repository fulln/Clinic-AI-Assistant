/**
 * T094 — RAG domain entities (TypeScript).
 */

export type DocumentStatus = 'uploading' | 'processing' | 'ready' | 'failed';

export interface KnowledgeBase {
  id: string;
  ownerId: string;
  name: string;
  description?: string;
  documentCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface Document {
  id: string;
  filename: string;
  fileSizeBytes: number;
  status: DocumentStatus;
  chunkCount: number;
  errorMessage?: string;
  createdAt: string;
  processedAt?: string;
}
