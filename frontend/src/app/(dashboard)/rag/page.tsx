'use client';

/**
 * T100 — RAG management page (doctor role only).
 */

import { useState } from 'react';
import { useAuthStore } from '@/shared/store/authStore';
import { useKnowledgeBase } from '@/features/rag/hooks/useKnowledgeBase';
import { KnowledgeBaseList } from '@/features/rag/components/KnowledgeBaseList';
import { useLocaleStore } from '@/shared/store/localeStore';
import { getSiteCopy } from '@/shared/i18n/site';

interface CreateKbForm {
  name: string;
  description: string;
}

export default function RagPage() {
  const user = useAuthStore((s) => s.user);
  const locale = useLocaleStore((state) => state.locale);
  const copy = getSiteCopy(locale);

  const {
    kbs,
    selectedKbId,
    setSelectedKbId,
    documents,
    createKb,
    deleteKb,
    uploadDocument,
    deleteDocument,
  } = useKnowledgeBase();

  // Create KB modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [form, setForm] = useState<CreateKbForm>({ name: '', description: '' });
  const [createError, setCreateError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  if (!user || user.role !== 'doctor') {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <p className="text-lg font-medium text-gray-600">{copy.ragDoctorOnlyTitle}</p>
          <p className="text-sm text-gray-400 mt-2">{copy.ragDoctorOnlySubtitle}</p>
        </div>
      </div>
    );
  }

  const handleCreateKb = async () => {
    if (!form.name.trim()) {
      setCreateError(copy.ragNamePlaceholder);
      return;
    }
    setIsCreating(true);
    setCreateError(null);
    try {
      await createKb(form.name.trim(), form.description.trim() || undefined);
      setShowCreateModal(false);
      setForm({ name: '', description: '' });
    } catch (e: any) {
      setCreateError(e?.response?.data?.detail ?? copy.ragCreateFailed);
    } finally {
      setIsCreating(false);
    }
  };

  const handleDeleteKb = async (kbId: string) => {
    if (!confirm(copy.ragDeleteKbConfirm)) return;
    await deleteKb(kbId);
  };

  const handleDeleteDocument = async (kbId: string, docId: string) => {
    if (!confirm(copy.ragDeleteDocConfirm)) return;
    await deleteDocument(kbId, docId);
  };

  const handleUpload = async (kbId: string, file: File) => {
    await uploadDocument(kbId, file);
  };

  return (
    <div className="space-y-6">
      <div className="saas-panel px-6 py-6">
        <h1 className="text-xl font-bold text-gray-900">{copy.ragTitle}</h1>
        <p className="mt-2 text-sm leading-6 text-slate-500">{copy.dashboardSubtitleKnowledgeBase}</p>
      </div>

      <div className="saas-panel px-6 py-6">
        <KnowledgeBaseList
          kbs={kbs}
          selectedKbId={selectedKbId}
          documents={documents}
          onSelectKb={(id) => setSelectedKbId(id === selectedKbId ? null : id)}
          onCreateKb={() => setShowCreateModal(true)}
          onDeleteKb={handleDeleteKb}
          onDeleteDocument={handleDeleteDocument}
          onUpload={handleUpload}
          locale={locale}
        />
      </div>

      {/* Create KB Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 space-y-4">
            <h2 className="text-base font-semibold text-gray-800">{copy.ragCreateTitle}</h2>

            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {copy.ragName} <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder={copy.ragNamePlaceholder}
                  maxLength={100}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{copy.ragDescription}</label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  placeholder={copy.ragDescriptionPlaceholder}
                  rows={3}
                  maxLength={300}
                />
              </div>
            </div>

            {createError && (
              <p className="text-xs text-red-600">{createError}</p>
            )}

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => {
                  setShowCreateModal(false);
                  setForm({ name: '', description: '' });
                  setCreateError(null);
                }}
                className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                {copy.cancel}
              </button>
              <button
                type="button"
                onClick={handleCreateKb}
                disabled={isCreating}
                className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {isCreating ? copy.ragCreateSubmitting : copy.ragCreateConfirm}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
