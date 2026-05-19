"""Registry of available tools.

To add a new tool: implement it in its own module, then register here.
"""
from __future__ import annotations

from src.domains.agent.entities import Agent
from src.infrastructure.llm.tools.base import ToolDefinition
from src.infrastructure.llm.tools.knowledge_base_search import knowledge_base_search


TOOL_REGISTRY: dict[str, ToolDefinition] = {
    knowledge_base_search.name: knowledge_base_search,
}


def get_tools_for_agent(agent: Agent) -> list[ToolDefinition]:
    """Resolve the agent's `tools` slug list to ToolDefinition objects.

    Unknown names are silently dropped so a misconfigured agent does not crash.
    """
    return [TOOL_REGISTRY[name] for name in (agent.tools or []) if name in TOOL_REGISTRY]


def list_available_tool_names() -> list[str]:
    return sorted(TOOL_REGISTRY.keys())
