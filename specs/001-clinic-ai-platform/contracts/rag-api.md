# Contract: RAG Knowledge Base API

**Base path**: `/api/v1/rag`
**Auth**: Bearer token required; all endpoints require `role = doctor` unless noted

---

## POST /api/v1/rag/knowledge-bases

Create a new personal knowledge base. **Doctor role only.**

**Request**
```json
{
  "name": "string (required, max 100 chars)",
  "description": "string (optional, max 300 chars)"
}
```

**Response 201**
```json
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "document_count": 0,
  "created_at": "2026-05-17T10:00:00Z"
}
```

---

## GET /api/v1/rag/knowledge-bases

List current doctor's knowledge bases.

**Response 200**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "string",
      "description": "string",
      "document_count": 5,
      "created_at": "2026-05-17T10:00:00Z"
    }
  ]
}
```

---

## POST /api/v1/rag/knowledge-bases/{kb_id}/documents

Upload a document for vectorization. **Multipart form data.**

**Request** (`Content-Type: multipart/form-data`):
- `file`: binary (max 50MB; supported types: PDF, TXT, DOCX, MD)

**Response 202**: Document accepted for async processing.
```json
{
  "document_id": "uuid",
  "filename": "clinical_guide.pdf",
  "file_size_bytes": 2048000,
  "status": "processing",
  "created_at": "2026-05-17T10:00:00Z"
}
```

---

## GET /api/v1/rag/knowledge-bases/{kb_id}/documents

List documents in a knowledge base with processing status.

**Response 200**
```json
{
  "items": [
    {
      "id": "uuid",
      "filename": "string",
      "file_size_bytes": 2048000,
      "status": "uploading | processing | ready | failed",
      "chunk_count": 45,
      "error_message": "string | null",
      "created_at": "2026-05-17T10:00:00Z",
      "processed_at": "2026-05-17T10:01:30Z"
    }
  ]
}
```

---

## DELETE /api/v1/rag/knowledge-bases/{kb_id}/documents/{document_id}

Delete a document and its vector embeddings.

**Response 204**: Document and all `DocumentChunk` records (including embeddings) deleted.

---

## DELETE /api/v1/rag/knowledge-bases/{kb_id}

Delete an entire knowledge base and all its documents/embeddings.

**Response 204**: Cascading delete of all documents and chunks.

---

## POST /api/v1/rag/query

Direct RAG query against doctor's knowledge base (without starting a full conversation). **Doctor role only.**

**Request**
```json
{
  "knowledge_base_id": "uuid",
  "query": "string (required, max 1000 chars)",
  "top_k": 5
}
```

**Response 200**
```json
{
  "results": [
    {
      "chunk_id": "uuid",
      "document_id": "uuid",
      "filename": "clinical_guide.pdf",
      "content": "string (chunk text)",
      "similarity_score": 0.92,
      "metadata": { "page_number": 12 }
    }
  ],
  "query_embedding_tokens": 15
}
```
