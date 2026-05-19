"""Embedding helpers shared between the RAG tool and other consumers."""
from __future__ import annotations

import os


def embed_query(query: str) -> list[float]:
    """Embed a single query string using the configured embedding provider.

    Reads `EMBEDDING_API_KEY` / `EMBEDDING_BASE_URL` / `EMBEDDING_MODEL` /
    `EMBEDDING_DIMENSIONS` from the environment, falling back to the
    OpenAI-compatible vars used elsewhere.
    """
    import openai

    api_key = os.environ.get("EMBEDDING_API_KEY") or os.environ["OPENAI_API_KEY"]
    base_url = os.environ.get("EMBEDDING_BASE_URL") or os.environ.get("OPENAI_BASE_URL")
    model = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
    dimensions = os.environ.get("EMBEDDING_DIMENSIONS")

    client = openai.OpenAI(api_key=api_key, base_url=base_url)
    payload: dict = {"model": model, "input": query}
    if dimensions:
        payload["dimensions"] = int(dimensions)
    response = client.embeddings.create(**payload)
    return response.data[0].embedding
