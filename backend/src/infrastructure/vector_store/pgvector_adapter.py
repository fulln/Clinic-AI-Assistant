"""T087 — pgvector similarity search adapter."""
from __future__ import annotations

import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class PgVectorAdapter:
    """Low-level vector similarity search using pgvector's cosine distance operator."""

    async def similarity_search(
        self,
        session: AsyncSession,
        query_embedding: list[float],
        kb_id: uuid.UUID,
        top_k: int = 5,
    ) -> list[dict]:
        """Return the *top_k* most similar chunks within *kb_id*.

        Returns list of dicts with keys:
            chunk_id, document_id, filename, content, similarity_score, metadata
        """
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
        result = await session.execute(
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
