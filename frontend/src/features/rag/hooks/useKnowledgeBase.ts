'use client';

/**
 * T096 — react-query hook for knowledge base + document management.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback, useState } from 'react';
import apiClient from '@/shared/api/client';
import type { Document, KnowledgeBase } from '@/domains/rag/entities';

// ---- API helpers ----

function mapKb(raw: any): KnowledgeBase {
  return {
    id: raw.id,
    ownerId: raw.owner_id,
    name: raw.name,
    description: raw.description,
    documentCount: raw.document_count,
    createdAt: raw.created_at,
    updatedAt: raw.updated_at,
  };
}

function mapDoc(raw: any): Document {
  return {
    id: raw.id,
    filename: raw.filename,
    fileSizeBytes: raw.file_size_bytes,
    status: raw.status,
    chunkCount: raw.chunk_count,
    errorMessage: raw.error_message ?? undefined,
    createdAt: raw.created_at,
    processedAt: raw.processed_at ?? undefined,
  };
}

async function fetchKbs(): Promise<KnowledgeBase[]> {
  const { data } = await apiClient.get<any[]>('/api/v1/rag/knowledge-bases');
  return data.map(mapKb);
}

async function fetchDocuments(kbId: string): Promise<Document[]> {
  const { data } = await apiClient.get<any[]>(`/api/v1/rag/knowledge-bases/${kbId}/documents`);
  return data.map(mapDoc);
}

// ---- Hook ----

export function useKnowledgeBase() {
  const qc = useQueryClient();
  const [selectedKbId, setSelectedKbId] = useState<string | null>(null);

  // List knowledge bases
  const kbQuery = useQuery<KnowledgeBase[]>({
    queryKey: ['kbs'],
    queryFn: fetchKbs,
  });

  const kbs = kbQuery.data ?? [];
  const selectedKb = kbs.find((kb) => kb.id === selectedKbId) ?? null;

  // List documents for selected KB (poll every 5s when any doc is processing)
  const docQuery = useQuery<Document[]>({
    queryKey: ['docs', selectedKbId],
    queryFn: () => fetchDocuments(selectedKbId!),
    enabled: !!selectedKbId,
    refetchInterval: (query) => {
      const docs = query.state.data;
      if (!docs) return false;
      return docs.some((d) => d.status === 'processing' || d.status === 'uploading') ? 5000 : false;
    },
  });

  const documents = docQuery.data ?? [];

  // Create KB
  const createKbMutation = useMutation({
    mutationFn: async ({ name, description }: { name: string; description?: string }) => {
      const { data } = await apiClient.post('/api/v1/rag/knowledge-bases', { name, description });
      return mapKb(data);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['kbs'] }),
  });

  // Delete KB
  const deleteKbMutation = useMutation({
    mutationFn: async (kbId: string) => {
      await apiClient.delete(`/api/v1/rag/knowledge-bases/${kbId}`);
    },
    onSuccess: (_, kbId) => {
      if (selectedKbId === kbId) setSelectedKbId(null);
      qc.invalidateQueries({ queryKey: ['kbs'] });
    },
  });

  // Upload document
  const uploadDocumentMutation = useMutation({
    mutationFn: async ({ kbId, file }: { kbId: string; file: File }) => {
      const form = new FormData();
      form.append('file', file);
      const { data } = await apiClient.post(
        `/api/v1/rag/knowledge-bases/${kbId}/documents`,
        form,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['docs', selectedKbId] });
      qc.invalidateQueries({ queryKey: ['kbs'] });
    },
  });

  // Delete document
  const deleteDocumentMutation = useMutation({
    mutationFn: async ({ kbId, docId }: { kbId: string; docId: string }) => {
      await apiClient.delete(`/api/v1/rag/knowledge-bases/${kbId}/documents/${docId}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['docs', selectedKbId] });
      qc.invalidateQueries({ queryKey: ['kbs'] });
    },
  });

  const createKb = useCallback(
    (name: string, description?: string) =>
      createKbMutation.mutateAsync({ name, description }),
    [createKbMutation]
  );

  const deleteKb = useCallback(
    (kbId: string) => deleteKbMutation.mutateAsync(kbId),
    [deleteKbMutation]
  );

  const uploadDocument = useCallback(
    (kbId: string, file: File) => uploadDocumentMutation.mutateAsync({ kbId, file }),
    [uploadDocumentMutation]
  );

  const deleteDocument = useCallback(
    (kbId: string, docId: string) => deleteDocumentMutation.mutateAsync({ kbId, docId }),
    [deleteDocumentMutation]
  );

  return {
    kbs,
    selectedKb,
    selectedKbId,
    setSelectedKbId,
    documents,
    isLoadingKbs: kbQuery.isLoading,
    isLoadingDocs: docQuery.isLoading,
    createKb,
    deleteKb,
    uploadDocument,
    deleteDocument,
  };
}
