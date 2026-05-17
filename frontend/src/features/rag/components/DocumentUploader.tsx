'use client';

/**
 * T098 — Drag-and-drop + click-to-select document uploader.
 */

import { useCallback, useRef, useState } from 'react';
import { RAGDomainService } from '@/domains/rag/services';

interface Props {
  onUpload: (file: File) => Promise<void>;
  disabled?: boolean;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export function DocumentUploader({ onUpload, disabled = false }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const handleFile = (file: File) => {
    const error = RAGDomainService.validateFile(file);
    setValidationError(error);
    setSelectedFile(error ? null : file);
  };

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragging(false);
      if (disabled) return;
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [disabled]
  );

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (!disabled) setIsDragging(true);
  };

  const handleDragLeave = () => setIsDragging(false);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const handleUpload = async () => {
    if (!selectedFile || isUploading) return;
    setIsUploading(true);
    try {
      await onUpload(selectedFile);
      setSelectedFile(null);
      if (inputRef.current) inputRef.current.value = '';
    } finally {
      setIsUploading(false);
    }
  };

  const isUploadDisabled = disabled || isUploading || !selectedFile;

  return (
    <div className="space-y-3">
      {/* Drop zone */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => !disabled && inputRef.current?.click()}
        className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors
          ${isDragging ? 'border-blue-400 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.txt,.docx,.md"
          className="hidden"
          onChange={handleInputChange}
          disabled={disabled}
        />
        <p className="text-sm text-gray-500">
          拖拽文件至此或
          <span className="text-blue-600 font-medium"> 点击选择文件</span>
        </p>
        <p className="text-xs text-gray-400 mt-1">支持 PDF、TXT、DOCX、Markdown，最大 50 MB</p>
      </div>

      {/* Selected file info */}
      {selectedFile && (
        <div className="flex items-center justify-between bg-gray-50 rounded px-3 py-2 text-sm">
          <span className="truncate text-gray-700 max-w-xs">{selectedFile.name}</span>
          <span className="text-gray-400 ml-2 whitespace-nowrap">
            {formatBytes(selectedFile.size)}
          </span>
        </div>
      )}

      {/* Validation error */}
      {validationError && (
        <p className="text-xs text-red-600">{validationError}</p>
      )}

      {/* Upload button */}
      <button
        type="button"
        onClick={handleUpload}
        disabled={isUploadDisabled}
        className={`w-full py-2 px-4 rounded-lg text-sm font-medium transition-colors
          ${
            isUploadDisabled
              ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }
        `}
      >
        {isUploading ? '上传中…' : '上传文件'}
      </button>
    </div>
  );
}
