"""T089 — RAG domain services: chunking and vector search."""
from __future__ import annotations

import math
import os
import uuid


class ChunkingService:
    """Simple character-based text chunker (~4 chars per token)."""

    CHARS_PER_TOKEN: int = 4

    def chunk_text(
        self,
        text: str,
        max_tokens: int = 512,
        overlap: int = 50,
    ) -> list[str]:
        """Split *text* into overlapping chunks of at most *max_tokens* tokens."""
        if not text:
            return []

        max_chars = max_tokens * self.CHARS_PER_TOKEN
        overlap_chars = overlap * self.CHARS_PER_TOKEN

        chunks: list[str] = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + max_chars, text_len)
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= text_len:
                break
            start = end - overlap_chars

        return chunks


class VectorSearchService:
    """Embeds a query and delegates similarity search to the vector adapter."""

    def __init__(self, adapter, session) -> None:
        self._adapter = adapter
        self._session = session

    async def search(
        self,
        query_text: str,
        kb_id: uuid.UUID,
        top_k: int,
        openai_client,
    ) -> list[dict]:
        """Embed *query_text* with OpenAI then run pgvector similarity search."""
        embedding_model = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
        embedding_dimensions = os.environ.get("EMBEDDING_DIMENSIONS")
        embedding_request = {
            "model": embedding_model,
            "input": query_text,
        }
        if embedding_dimensions:
            embedding_request["dimensions"] = int(embedding_dimensions)
        response = openai_client.embeddings.create(
            **embedding_request,
        )
        query_embedding: list[float] = response.data[0].embedding

        return await self._adapter.similarity_search(
            self._session,
            query_embedding,
            kb_id,
            top_k,
        )
