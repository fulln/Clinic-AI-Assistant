"""T086 — SQLAlchemy async implementation of IKnowledgeBaseRepository."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.rag.entities import Document, DocumentChunk, DocumentStatus, KnowledgeBase
from src.domains.rag.repository import IKnowledgeBaseRepository
from src.infrastructure.db.models import (
    DocumentChunkModel,
    DocumentModel,
    KnowledgeBaseModel,
)


class KnowledgeBaseRepository(IKnowledgeBaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # KnowledgeBase
    # ------------------------------------------------------------------

    async def find_by_id(self, kb_id: uuid.UUID) -> KnowledgeBase | None:
        result = await self._session.execute(
            select(KnowledgeBaseModel).where(KnowledgeBaseModel.id == kb_id)
        )
        row = result.scalar_one_or_none()
        return self._kb_to_domain(row) if row else None

    async def find_by_owner(self, owner_id: uuid.UUID) -> list[KnowledgeBase]:
        result = await self._session.execute(
            select(KnowledgeBaseModel)
            .where(KnowledgeBaseModel.owner_id == owner_id)
            .order_by(KnowledgeBaseModel.created_at.desc())
        )
        return [self._kb_to_domain(r) for r in result.scalars().all()]

    async def save_kb(self, kb: KnowledgeBase) -> KnowledgeBase:
        result = await self._session.execute(
            select(KnowledgeBaseModel).where(KnowledgeBaseModel.id == kb.id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = KnowledgeBaseModel(
                id=kb.id,
                owner_id=kb.owner_id,
                name=kb.name,
                description=kb.description,
                document_count=kb.document_count,
                created_at=kb.created_at,
                updated_at=kb.updated_at,
            )
            self._session.add(row)
        else:
            row.name = kb.name
            row.description = kb.description
            row.document_count = kb.document_count
            row.updated_at = datetime.utcnow()
        await self._session.flush()
        return kb

    async def delete_kb(self, kb_id: uuid.UUID) -> None:
        result = await self._session.execute(
            select(KnowledgeBaseModel).where(KnowledgeBaseModel.id == kb_id)
        )
        row = result.scalar_one_or_none()
        if row:
            await self._session.delete(row)
            await self._session.flush()

    # ------------------------------------------------------------------
    # Document
    # ------------------------------------------------------------------

    async def save_document(self, document: Document) -> Document:
        result = await self._session.execute(
            select(DocumentModel).where(DocumentModel.id == document.id)
        )
        existing = result.scalar_one_or_none()
        is_new = existing is None
        if is_new:
            row = DocumentModel(
                id=document.id,
                knowledge_base_id=document.kb_id,
                filename=document.filename,
                file_size_bytes=document.file_size_bytes,
                mime_type=document.mime_type,
                status=document.status.value,
                chunk_count=document.chunk_count,
                error_message=document.error_message,
                created_at=document.created_at,
                processed_at=document.processed_at,
            )
            self._session.add(row)
        else:
            existing.status = document.status.value
            existing.chunk_count = document.chunk_count
            existing.error_message = document.error_message
            existing.processed_at = document.processed_at
        await self._session.flush()

        # Increment document_count on KB only when creating a new row
        if is_new:
            kb_result = await self._session.execute(
                select(KnowledgeBaseModel).where(
                    KnowledgeBaseModel.id == document.kb_id
                )
            )
            kb_row = kb_result.scalar_one_or_none()
            if kb_row:
                kb_row.document_count = (kb_row.document_count or 0) + 1
                kb_row.updated_at = datetime.utcnow()
                await self._session.flush()

        return document

    async def find_document_by_id(self, document_id: uuid.UUID) -> Document | None:
        result = await self._session.execute(
            select(DocumentModel).where(DocumentModel.id == document_id)
        )
        row = result.scalar_one_or_none()
        return self._doc_to_domain(row) if row else None

    async def find_documents_by_kb(self, kb_id: uuid.UUID) -> list[Document]:
        result = await self._session.execute(
            select(DocumentModel)
            .where(DocumentModel.knowledge_base_id == kb_id)
            .order_by(DocumentModel.created_at.desc())
        )
        return [self._doc_to_domain(r) for r in result.scalars().all()]

    async def update_document_status(
        self,
        document_id: uuid.UUID,
        status: DocumentStatus,
        *,
        chunk_count: int | None = None,
        error_message: str | None = None,
        processed_at=None,
    ) -> None:
        result = await self._session.execute(
            select(DocumentModel).where(DocumentModel.id == document_id)
        )
        row = result.scalar_one_or_none()
        if not row:
            return
        row.status = status.value
        if chunk_count is not None:
            row.chunk_count = chunk_count
        if error_message is not None:
            row.error_message = error_message
        if processed_at is not None:
            row.processed_at = processed_at
        await self._session.flush()

    async def delete_document(self, document_id: uuid.UUID) -> None:
        result = await self._session.execute(
            select(DocumentModel).where(DocumentModel.id == document_id)
        )
        row = result.scalar_one_or_none()
        if row:
            kb_id = row.knowledge_base_id
            await self._session.delete(row)
            await self._session.flush()
            # Decrement document_count
            kb_result = await self._session.execute(
                select(KnowledgeBaseModel).where(KnowledgeBaseModel.id == kb_id)
            )
            kb_row = kb_result.scalar_one_or_none()
            if kb_row and kb_row.document_count > 0:
                kb_row.document_count -= 1
                kb_row.updated_at = datetime.utcnow()
                await self._session.flush()

    # ------------------------------------------------------------------
    # Chunks
    # ------------------------------------------------------------------

    async def save_chunks(self, chunks: list[DocumentChunk]) -> None:
        for chunk in chunks:
            row = DocumentChunkModel(
                id=chunk.id,
                document_id=chunk.document_id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                embedding=chunk.embedding,
                token_count=chunk.token_count,
                chunk_metadata=chunk.metadata,
            )
            self._session.add(row)
        await self._session.flush()

    # ------------------------------------------------------------------
    # Vector search
    # ------------------------------------------------------------------

    async def similarity_search(
        self,
        query_embedding: list[float],
        kb_id: uuid.UUID,
        top_k: int = 5,
    ) -> list[dict]:
        sql = text(
            """
            SELECT
                dc.id          AS chunk_id,
                dc.document_id AS document_id,
                d.filename     AS filename,
                dc.content     AS content,
                dc.metadata    AS metadata,
                1 - (dc.embedding <=> CAST(:query_vec AS vector)) AS score
            FROM document_chunks dc
            JOIN documents d ON d.id = dc.document_id
            WHERE d.knowledge_base_id = :kb_id
              AND d.status = 'ready'
            ORDER BY score DESC
            LIMIT :top_k
            """
        )
        result = await self._session.execute(
            sql,
            {
                "query_vec": str(query_embedding),
                "kb_id": str(kb_id),
                "top_k": top_k,
            },
        )
        rows = result.mappings().all()
        return [
            {
                "chunk_id": str(r["chunk_id"]),
                "document_id": str(r["document_id"]),
                "filename": r["filename"],
                "content": r["content"],
                "similarity_score": float(r["score"]),
                "metadata": r["metadata"] or {},
            }
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Mappers
    # ------------------------------------------------------------------

    @staticmethod
    def _kb_to_domain(row: KnowledgeBaseModel) -> KnowledgeBase:
        return KnowledgeBase(
            id=row.id,
            owner_id=row.owner_id,
            name=row.name,
            description=row.description,
            document_count=row.document_count,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _doc_to_domain(row: DocumentModel) -> Document:
        return Document(
            id=row.id,
            kb_id=row.knowledge_base_id,
            filename=row.filename,
            file_size_bytes=row.file_size_bytes,
            mime_type=row.mime_type,
            status=DocumentStatus(row.status),
            chunk_count=row.chunk_count,
            error_message=row.error_message,
            created_at=row.created_at,
            processed_at=row.processed_at,
        )
