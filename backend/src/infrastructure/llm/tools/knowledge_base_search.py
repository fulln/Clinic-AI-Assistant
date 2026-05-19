"""Knowledge-base search tool.

Wraps the existing pgvector similarity-search path so any agent can call it
via LLM tool-calling. Returns a formatted snippet string to the LLM AND
populates `ToolContext.collected_artifacts` with structured chunk data so
the streaming layer can surface them to the UI.
"""
from __future__ import annotations

import json

from src.domains.conversation.entities import Locale
from src.infrastructure.llm.embeddings import embed_query
from src.infrastructure.llm.tools.base import ToolContext, ToolDefinition


RAG_SCORE_THRESHOLD = 0.5
_DEFAULT_TOP_K = 5
_MAX_TOP_K = 10

_NO_KB_MSG_EN = "The user has no knowledge base set up yet."
_NO_KB_MSG_ZH = "该用户尚未创建任何知识库。"
_NO_HITS_MSG_EN = "No relevant content found in the knowledge base."
_NO_HITS_MSG_ZH = "未在知识库中找到相关内容。"


def _format_artifact(index: int, chunk: dict, kb_name: str | None) -> dict:
    content = str(chunk.get("content") or "")
    return {
        "type": "rag_chunk",
        "title": f"{index}. {chunk.get('filename', '知识库文档')}",
        "subtitle": kb_name,
        "score": round(float(chunk.get("similarity_score", 0)), 4),
        "content": content[:500],
        "document_id": chunk.get("document_id"),
        "chunk_id": chunk.get("chunk_id"),
    }


def _format_for_llm(chunks: list[dict], locale: Locale) -> str:
    fallback_filename = "Document" if locale == Locale.EN_US else "文档"
    parts = []
    for chunk in chunks:
        filename = chunk.get("filename", fallback_filename)
        content = str(chunk.get("content") or "").strip()
        parts.append(f"[{filename}] {content}")
    return "\n\n".join(parts)


async def _handler(arguments: dict, ctx: ToolContext) -> str:
    locale = ctx.locale
    if ctx.rag_repo is None:
        return _NO_KB_MSG_EN if locale == Locale.EN_US else _NO_KB_MSG_ZH

    query = str(arguments.get("query") or "").strip()
    if not query:
        return "Tool error: empty query." if locale == Locale.EN_US else "工具错误：query 为空。"

    requested_top_k = int(arguments.get("top_k") or _DEFAULT_TOP_K)
    top_k = max(1, min(requested_top_k, _MAX_TOP_K))

    kbs = await ctx.rag_repo.find_by_owner(ctx.user_id)
    if not kbs:
        return _NO_KB_MSG_EN if locale == Locale.EN_US else _NO_KB_MSG_ZH

    query_embedding = embed_query(query)
    per_kb_limit = max(top_k, 3)
    all_results: list[tuple[dict, str]] = []  # (chunk, kb_name)

    for kb in kbs:
        results = await ctx.rag_repo.similarity_search(
            query_embedding=query_embedding,
            kb_id=kb.id,
            top_k=per_kb_limit,
        )
        for result in results:
            if float(result.get("similarity_score", 0)) <= RAG_SCORE_THRESHOLD:
                continue
            result["knowledge_base_id"] = str(kb.id)
            result["knowledge_base_name"] = kb.name
            all_results.append((result, kb.name))

    all_results.sort(key=lambda pair: pair[0]["similarity_score"], reverse=True)
    top_pairs = all_results[:top_k]

    if not top_pairs:
        return _NO_HITS_MSG_EN if locale == Locale.EN_US else _NO_HITS_MSG_ZH

    # Push artifacts onto the side-channel for the SSE layer to consume.
    ctx.collected_artifacts.extend(
        _format_artifact(idx, chunk, kb_name)
        for idx, (chunk, kb_name) in enumerate(top_pairs, start=1)
    )

    return _format_for_llm([chunk for chunk, _ in top_pairs], locale)


knowledge_base_search = ToolDefinition(
    name="knowledge_base_search",
    description=(
        "Search the doctor's personal knowledge base for content relevant to the user's "
        "question. Use this when the user asks about uploaded documents, clinical protocols, "
        "or anything that would benefit from grounding in their own files. Returns formatted "
        "excerpts that you must read and synthesize into your answer, citing the source "
        "document names."
    ),
    parameters_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "Search query, ideally a self-contained phrase derived from the user's "
                    "question (not the raw user message)."
                ),
            },
            "top_k": {
                "type": "integer",
                "description": f"How many chunks to return. Default {_DEFAULT_TOP_K}, max {_MAX_TOP_K}.",
                "default": _DEFAULT_TOP_K,
                "minimum": 1,
                "maximum": _MAX_TOP_K,
            },
        },
        "required": ["query"],
    },
    handler=_handler,
)
