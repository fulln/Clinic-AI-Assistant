"""AgentDispatcher routes conversation messages to the generic agent workflow.

Each agent is fully data-driven: its system prompt, tools, RAG behavior, and
LLM params live on the Agent entity itself (loaded from the database). The
dispatcher just wraps the agent and the user message context into a
WorkflowState and streams the result.
"""
from typing import AsyncIterator

from src.domains.agent.entities import Agent
from src.domains.conversation.entities import Locale
from src.infrastructure.llm.langchain_adapter import LLMAdapter
from src.infrastructure.llm.langgraph_workflows.base_workflow import WorkflowState
from src.infrastructure.llm.langgraph_workflows.generic import GenericAgentWorkflow
from src.infrastructure.llm.tools.base import ToolContext, ToolEvent


class AgentDispatcher:
    def __init__(
        self,
        llm: LLMAdapter,
        workflow: GenericAgentWorkflow | None = None,
    ) -> None:
        self._llm = llm
        self._workflow = workflow or GenericAgentWorkflow(llm)

    async def dispatch(
        self,
        agent: Agent,
        messages: list[dict],
        session_context: dict,
        user_role: str,
        locale: Locale,
        tool_context: ToolContext | None = None,
    ) -> AsyncIterator[str | ToolEvent]:
        state: WorkflowState = {
            "messages": messages,
            "session_context": session_context,
            "agent_id": str(agent.id),
            "user_role": user_role,
            "locale": locale,
            "rag_enabled": False,
            "rag_chunks": [],
            "response_tokens": [],
            "has_disclaimer": False,
            "refused": False,
            "refusal_reason": "",
        }
        return self._workflow.stream(agent, state, tool_context=tool_context)
