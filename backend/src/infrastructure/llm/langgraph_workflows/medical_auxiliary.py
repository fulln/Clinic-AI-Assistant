"""Medical auxiliary agent workflow."""
from typing import AsyncIterator

from src.infrastructure.llm.langchain_adapter import LLMAdapter
from src.infrastructure.llm.langgraph_workflows.base_workflow import (
    WorkflowState,
    build_base_nodes,
    should_refuse,
    DISCLAIMER_TEXT,
)

SYSTEM_PROMPT = """你是一位专业的医疗辅助 AI 助手，服务于私立诊所。
你只能提供：医疗辅助对话、常见病症科普、就诊流程指引。
你严格禁止：给出确定性诊断、开具处方、推荐具体用药剂量、制定治疗方案。
每次回复末尾必须包含免责声明。"""


class MedicalAuxiliaryWorkflow:
    def __init__(self, llm: LLMAdapter) -> None:
        self._llm = llm

    async def stream(self, state: WorkflowState) -> AsyncIterator[str]:
        context_loader, intent_classifier, disclaimer_fn, context_saver = build_base_nodes(self._llm)

        state = await context_loader(state)
        state = await intent_classifier(state)

        if state["refused"]:
            yield f"data: {state['refusal_reason']}\n\n"
            return

        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + state["messages"]
        async for token in self._llm.astream(messages):
            yield token

        yield f"\n\n{DISCLAIMER_TEXT}"
