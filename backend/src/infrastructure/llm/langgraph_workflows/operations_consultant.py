"""Operations consultant agent workflow."""
from typing import AsyncIterator

from src.domains.conversation.entities import Locale
from src.domains.conversation.i18n import get_disclaimer
from src.infrastructure.llm.langchain_adapter import LLMAdapter
from src.infrastructure.llm.langgraph_workflows.base_workflow import (
    WorkflowState, build_base_nodes
)


def build_system_prompt(locale: Locale) -> str:
    if locale == Locale.EN_US:
        return (
            "You are an operations consulting AI assistant for private clinics. "
            "You help clinic managers with patient reception workflows, appointment management, billing norms, and compliant operations. "
            "You do not provide medical diagnoses or clinical advice. Reply in English."
        )
    return """你是一位私立诊所运营咨询 AI 助手。
你帮助诊所管理者解答：患者接待流程、预约管理、收费规范、合规运营等问题。
你不提供任何医疗诊断或临床建议。请使用简体中文回复。"""


class OperationsConsultantWorkflow:
    def __init__(self, llm: LLMAdapter) -> None:
        self._llm = llm

    async def stream(self, state: WorkflowState) -> AsyncIterator[str]:
        context_loader, intent_classifier, _, _ = build_base_nodes(self._llm)
        state = await context_loader(state)
        state = await intent_classifier(state)

        if state["refused"]:
            yield state["refusal_reason"]
            return

        messages = [{"role": "system", "content": build_system_prompt(state["locale"])}] + state["messages"]
        async for token in self._llm.astream(messages):
            yield token

        yield f"\n\n{get_disclaimer(state['locale'])}"
