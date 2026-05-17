"""T085 — RAG repository interfaces (ABCs)."""
from __future__ import annotations

import abc
import uuid

from src.domains.rag.entities import Document, DocumentChunk, DocumentStatus, KnowledgeBase


class IKnowledgeBaseRepository(abc.ABC):
    # ----- KnowledgeBase -----

    @abc.abstractmethod
    async def find_by_id(self, kb_id: uuid.UUID) -> KnowledgeBase | None:
        ...

    @abc.abstractmethod
    async def find_by_owner(self, owner_id: uuid.UUID) -> list[KnowledgeBase]:
        ...

    @abc.abstractmethod
    async def save_kb(self, kb: KnowledgeBase) -> KnowledgeBase:
        ...

    @abc.abstractmethod
    async def delete_kb(self, kb_id: uuid.UUID) -> None:
        ...

    # ----- Document -----

    @abc.abstractmethod
    async def save_document(self, document: Document) -> Document:
        ...

    @abc.abstractmethod
    async def find_document_by_id(self, document_id: uuid.UUID) -> Document | None:
        ...

    @abc.abstractmethod
    async def find_documents_by_kb(self, kb_id: uuid.UUID) -> list[Document]:
        ...

    @abc.abstractmethod
    async def update_document_status(
        self,
        document_id: uuid.UUID,
        status: DocumentStatus,
        *,
        chunk_count: int | None = None,
        error_message: str | None = None,
        processed_at=None,
    ) -> None:
        ...

    @abc.abstractmethod
    async def delete_document(self, document_id: uuid.UUID) -> None:
        ...

    # ----- Chunks -----

    @abc.abstractmethod
    async def save_chunks(self, chunks: list[DocumentChunk]) -> None:
        ...

    # ----- Vector search -----

    @abc.abstractmethod
    async def similarity_search(
        self,
        query_embedding: list[float],
        kb_id: uuid.UUID,
        top_k: int = 5,
    ) -> list[dict]:
        """Return list of dicts with keys: chunk_id, document_id, filename,
        content, similarity_score, metadata."""
        ...
