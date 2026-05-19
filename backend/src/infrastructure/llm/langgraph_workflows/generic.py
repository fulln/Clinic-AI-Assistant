"""Generic data-driven agent workflow.

Replaces the previous per-agent hardcoded workflows. The agent's behavior
(system prompt, tools, LLM params) is read from the Agent entity. Tool calls
(e.g. RAG retrieval) flow through `LLMAdapter.astream_with_tools`.
"""
from typing import AsyncIterator

from src.domains.agent.entities import Agent
from src.domains.conversation.entities import Locale
from src.domains.conversation.i18n import get_disclaimer
from src.infrastructure.llm.langchain_adapter import LLMAdapter
from src.infrastructure.llm.langgraph_workflows.base_workflow import (
    WorkflowState,
    build_base_nodes,
)
from src.infrastructure.llm.tools import ToolContext, ToolEvent, get_tools_for_agent


_DEFAULT_PROMPT_EN = (
    "You are a helpful AI assistant for a private clinic. Reply in English. "
    "Do not provide clinical diagnoses, prescriptions, or specific treatment plans."
)
_DEFAULT_PROMPT_ZH = (
    "你是一位医疗诊所的 AI 助手。请使用简体中文回复。"
    "不要提供临床诊断、处方或具体治疗方案。"
)


def _resolve_system_prompt(agent: Agent, locale: Locale) -> str:
    if locale == Locale.EN_US:
        return agent.system_prompt_en or agent.system_prompt_zh or _DEFAULT_PROMPT_EN
    return agent.system_prompt_zh or agent.system_prompt_en or _DEFAULT_PROMPT_ZH


class GenericAgentWorkflow:
    def __init__(self, llm: LLMAdapter) -> None:
        self._llm = llm

    async def stream(
        self,
        agent: Agent,
        state: WorkflowState,
        tool_context: ToolContext | None = None,
    ) -> AsyncIterator[str | ToolEvent]:
        context_loader, intent_classifier, _, _ = build_base_nodes(self._llm)
        state = await context_loader(state)
        state = await intent_classifier(state)

        if state["refused"]:
            yield state["refusal_reason"]
            return

        system_content = _resolve_system_prompt(agent, state["locale"])
        messages = [{"role": "system", "content": system_content}] + state["messages"]

        tools = get_tools_for_agent(agent)
        if tools and tool_context is not None:
            async for item in self._llm.astream_with_tools(
                messages,
                tools=tools,
                tool_context=tool_context,
                max_tool_turns=agent.max_tool_turns,
                model=agent.llm_model,
                temperature=agent.llm_temperature,
                max_tokens=agent.llm_max_tokens,
            ):
                yield item
        else:
            async for token in self._llm.astream(
                messages,
                model=agent.llm_model,
                temperature=agent.llm_temperature,
                max_tokens=agent.llm_max_tokens,
            ):
                yield token

        yield f"\n\n{get_disclaimer(state['locale'])}"
