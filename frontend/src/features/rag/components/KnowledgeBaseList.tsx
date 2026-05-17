'use client';

/**
 * T099 — Expandable knowledge base list with documents.
 */

import { useState } from 'react';
import type { Document, KnowledgeBase } from '@/domains/rag/entities';
import { DocumentStatusBadge } from './DocumentStatusBadge';
import { DocumentUploader } from './DocumentUploader';

interface Props {
  kbs: KnowledgeBase[];
  selectedKbId: string | null;
  documents: Document[];
  onSelectKb: (kbId: string) => void;
  onCreateKb: () => void;
  onDeleteKb: (kbId: string) => void;
  onDeleteDocument: (kbId: string, docId: string) => void;
  onUpload: (kbId: string, file: File) => Promise<void>;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export function KnowledgeBaseList({
  kbs,
  selectedKbId,
  documents,
  onSelectKb,
  onCreateKb,
  onDeleteKb,
  onDeleteDocument,
  onUpload,
}: Props) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-gray-800">知识库列表</h2>
        <button
          type="button"
          onClick={onCreateKb}
          className="text-sm bg-blue-600 text-white px-3 py-1.5 rounded-lg hover:bg-blue-700 transition-colors"
        >
          创建知识库
        </button>
      </div>

      {kbs.length === 0 && (
        <p className="text-sm text-gray-400 py-4 text-center">暂无知识库，请点击上方按钮创建</p>
      )}

      {kbs.map((kb) => {
        const isExpanded = kb.id === selectedKbId;
        return (
          <div key={kb.id} className="border border-gray-200 rounded-lg overflow-hidden">
            {/* KB header */}
            <div
              className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-gray-50"
              onClick={() => onSelectKb(kb.id)}
            >
              <div className="flex items-center gap-2">
                <svg
                  className={`h-4 w-4 text-gray-400 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
                <span className="font-medium text-sm text-gray-800">{kb.name}</span>
                <span className="text-xs text-gray-400">({kb.documentCount} 个文档)</span>
              </div>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteKb(kb.id);
                }}
                className="text-xs text-red-500 hover:text-red-700 px-2 py-1 rounded hover:bg-red-50 transition-colors"
              >
                删除知识库
              </button>
            </div>

            {/* Expanded: document list + uploader */}
            {isExpanded && (
              <div className="border-t border-gray-100 px-4 py-3 space-y-4 bg-gray-50">
                {/* Document list */}
                {documents.length === 0 ? (
                  <p className="text-xs text-gray-400">暂无文档</p>
                ) : (
                  <ul className="space-y-2">
                    {documents.map((doc) => (
                      <li
                        key={doc.id}
                        className="flex items-center justify-between bg-white rounded px-3 py-2 text-sm shadow-sm"
                      >
                        <div className="flex items-center gap-2 min-w-0">
                          <span className="truncate text-gray-700 max-w-xs">{doc.filename}</span>
                          <span className="text-gray-400 text-xs whitespace-nowrap">
                            {formatBytes(doc.fileSizeBytes)}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 ml-2 flex-shrink-0">
                          <DocumentStatusBadge status={doc.status} />
                          <button
                            type="button"
                            onClick={() => onDeleteDocument(kb.id, doc.id)}
                            className="text-xs text-red-400 hover:text-red-600"
                          >
                            删除
                          </button>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}

                {/* Uploader */}
                <DocumentUploader
                  onUpload={(file) => onUpload(kb.id, file)}
                />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
