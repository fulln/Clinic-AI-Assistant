"""Tool definitions for agents (data-driven tool calling)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from src.domains.conversation.entities import Locale
from src.domains.rag.repository import IKnowledgeBaseRepository


@dataclass
class ToolContext:
    """Runtime context passed to every tool handler.

    Tools should NEVER reach beyond this struct — anything they need must be
    declared here. This keeps tools testable and side-effect-explicit.
    """

    user_id: uuid.UUID
    user_role: str
    locale: Locale
    rag_repo: IKnowledgeBaseRepository | None = None
    # Side-channel for tools to surface UI artifacts (e.g. RAG chunks) to the
    # streaming layer. Tools append dicts; the SSE layer pops them.
    collected_artifacts: list[dict] = field(default_factory=list)


@dataclass
class ToolEvent:
    """Emitted by the LLM adapter after a tool call completes.

    Used by the streaming layer to surface progress to the client.
    """

    name: str
    arguments: dict
    result: str
    artifacts: list[dict] = field(default_factory=list)


@dataclass
class ToolDefinition:
    """A tool an agent can declare in `Agent.tools`."""

    name: str
    description: str
    parameters_schema: dict  # OpenAI JSON-Schema function parameters
    handler: Callable[[dict, ToolContext], Awaitable[str]]

    def to_openai_spec(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema,
            },
        }
