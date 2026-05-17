"""Health educator agent workflow."""
from typing import AsyncIterator

from src.infrastructure.llm.langchain_adapter import LLMAdapter
from src.infrastructure.llm.langgraph_workflows.base_workflow import (
    WorkflowState, build_base_nodes, DISCLAIMER_TEXT
)

SYSTEM_PROMPT = """你是一位健康科普 AI 助手，服务于私立诊所患者教育。
你提供：常见疾病预防知识、健康生活方式建议、慢性病自我管理科普。
你严格禁止提供个体化诊断、处方或具体用药建议。"""


class HealthEducatorWorkflow:
    def __init__(self, llm: LLMAdapter) -> None:
        self._llm = llm

    async def stream(self, state: WorkflowState) -> AsyncIterator[str]:
        context_loader, intent_classifier, _, _ = build_base_nodes(self._llm)
        state = await context_loader(state)
        state = await intent_classifier(state)

        if state["refused"]:
            yield state["refusal_reason"]
            return

        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + state["messages"]
        async for token in self._llm.astream(messages):
            yield token

        yield f"\n\n{DISCLAIMER_TEXT}"
