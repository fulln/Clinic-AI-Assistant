"""Medical auxiliary agent workflow."""
from typing import AsyncIterator

from src.infrastructure.llm.langchain_adapter import LLMAdapter
from src.infrastructure.llm.langgraph_workflows.base_workflow import (
    WorkflowState,
    build_base_nodes,
)
from src.domains.conversation.entities import Locale
from src.domains.conversation.i18n import get_disclaimer


def build_system_prompt(locale: Locale) -> str:
    if locale == Locale.EN_US:
        return (
            "You are a professional medical auxiliary AI assistant for a private clinic. "
            "You may only provide medical auxiliary dialogue, general symptom education, and visit-process guidance. "
            "You must not provide definitive diagnoses, prescriptions, specific medication dosages, or treatment plans. "
            "Reply in English."
        )
    return """你是一位专业的医疗辅助 AI 助手，服务于私立诊所。
你只能提供：医疗辅助对话、常见病症科普、就诊流程指引。
你严格禁止：给出确定性诊断、开具处方、推荐具体用药剂量、制定治疗方案。
请使用简体中文回复。"""


class MedicalAuxiliaryWorkflow:
    def __init__(self, llm: LLMAdapter) -> None:
        self._llm = llm

    async def stream(self, state: WorkflowState) -> AsyncIterator[str]:
        context_loader, intent_classifier, disclaimer_fn, context_saver = build_base_nodes(self._llm)

        state = await context_loader(state)
        state = await intent_classifier(state)

        if state["refused"]:
            yield state["refusal_reason"]
            return

        messages = [{"role": "system", "content": build_system_prompt(state["locale"])}] + state["messages"]
        async for token in self._llm.astream(messages):
            yield token

        yield f"\n\n{get_disclaimer(state['locale'])}"
