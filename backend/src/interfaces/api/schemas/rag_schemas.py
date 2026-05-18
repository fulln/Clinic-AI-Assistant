"""T092 — Pydantic v2 schemas for RAG endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class CreateKnowledgeBaseRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=300)


class KnowledgeBaseResponse(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    description: Optional[str] = None
    document_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentUploadResponse(BaseModel):
    document_id: uuid.UUID
    filename: str
    file_size_bytes: int
    status: str
    created_at: datetime


class DocumentListItem(BaseModel):
    id: uuid.UUID
    filename: str
    file_size_bytes: int
    status: str
    chunk_count: int
    error_message: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RAGQueryRequest(BaseModel):
    knowledge_base_id: uuid.UUID
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(5, ge=1, le=20)


class RAGQueryResult(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    content: str
    similarity_score: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class RAGQueryResponse(BaseModel):
    results: list[RAGQueryResult]
    query_embedding_tokens: int = 0
