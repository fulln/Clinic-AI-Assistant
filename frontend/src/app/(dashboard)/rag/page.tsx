'use client';

/**
 * T100 — RAG management page (doctor role only).
 */

import { useState } from 'react';
import { useAuthStore } from '@/shared/store/authStore';
import { useKnowledgeBase } from '@/features/rag/hooks/useKnowledgeBase';
import { KnowledgeBaseList } from '@/features/rag/components/KnowledgeBaseList';

interface CreateKbForm {
  name: string;
  description: string;
}

export default function RagPage() {
  const user = useAuthStore((s) => s.user);

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
          <p className="text-lg font-medium text-gray-600">此功能仅限医师使用</p>
          <p className="text-sm text-gray-400 mt-2">请使用医师账号登录后访问。</p>
        </div>
      </div>
    );
  }

  const handleCreateKb = async () => {
    if (!form.name.trim()) {
      setCreateError('请输入知识库名称');
      return;
    }
    setIsCreating(true);
    setCreateError(null);
    try {
      await createKb(form.name.trim(), form.description.trim() || undefined);
      setShowCreateModal(false);
      setForm({ name: '', description: '' });
    } catch (e: any) {
      setCreateError(e?.response?.data?.detail ?? '创建失败，请重试');
    } finally {
      setIsCreating(false);
    }
  };

  const handleDeleteKb = async (kbId: string) => {
    if (!confirm('确认删除此知识库？该操作不可撤销。')) return;
    await deleteKb(kbId);
  };

  const handleDeleteDocument = async (kbId: string, docId: string) => {
    if (!confirm('确认删除此文档？')) return;
    await deleteDocument(kbId, docId);
  };

  const handleUpload = async (kbId: string, file: File) => {
    await uploadDocument(kbId, file);
  };

  return (
    <div className="max-w-3xl mx-auto py-8 px-4">
      <h1 className="text-xl font-bold text-gray-900 mb-6">RAG 知识库管理</h1>

      <KnowledgeBaseList
        kbs={kbs}
        selectedKbId={selectedKbId}
        documents={documents}
        onSelectKb={(id) => setSelectedKbId(id === selectedKbId ? null : id)}
        onCreateKb={() => setShowCreateModal(true)}
        onDeleteKb={handleDeleteKb}
        onDeleteDocument={handleDeleteDocument}
        onUpload={handleUpload}
      />

      {/* Create KB Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 space-y-4">
            <h2 className="text-base font-semibold text-gray-800">创建知识库</h2>

            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  名称 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="请输入知识库名称"
                  maxLength={100}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">描述</label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  placeholder="可选描述"
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
                取消
              </button>
              <button
                type="button"
                onClick={handleCreateKb}
                disabled={isCreating}
                className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {isCreating ? '创建中…' : '确认创建'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
