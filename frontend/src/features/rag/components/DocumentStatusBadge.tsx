/**
 * T097 — Color-coded document status badge with spinner for processing state.
 */

import type { DocumentStatus } from '@/domains/rag/entities';

interface Props {
  status: DocumentStatus;
}

const statusConfig: Record<
  DocumentStatus,
  { label: string; className: string; showSpinner?: boolean }
> = {
  uploading: {
    label: '上传中',
    className: 'bg-gray-100 text-gray-600',
  },
  processing: {
    label: '处理中',
    className: 'bg-yellow-100 text-yellow-700',
    showSpinner: true,
  },
  ready: {
    label: '就绪',
    className: 'bg-green-100 text-green-700',
  },
  failed: {
    label: '失败',
    className: 'bg-red-100 text-red-700',
  },
};

export function DocumentStatusBadge({ status }: Props) {
  const config = statusConfig[status] ?? statusConfig.failed;

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${config.className}`}
    >
      {config.showSpinner && (
        <svg
          className="animate-spin h-3 w-3"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
          />
        </svg>
      )}
      {config.label}
    </span>
  );
}
