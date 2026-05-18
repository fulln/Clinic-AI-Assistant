"""Document organizer agent workflow."""
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
            "You are a professional medical document organization AI assistant. "
            "You help physicians organize and format medical notes, discharge summaries, referrals, and similar documents. "
            "You do not provide clinical diagnoses or treatment advice. Reply in English."
        )
    return """你是一位专业的医疗文书整理 AI 助手。
你帮助医师整理、格式化病历摘要、出院记录、转诊函等医疗文书。
你不提供临床诊断或治疗建议。请使用简体中文回复。"""


class DocumentOrganizerWorkflow:
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
