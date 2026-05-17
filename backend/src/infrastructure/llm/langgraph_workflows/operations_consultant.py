"""Operations consultant agent workflow."""
from typing import AsyncIterator

from src.infrastructure.llm.langchain_adapter import LLMAdapter
from src.infrastructure.llm.langgraph_workflows.base_workflow import (
    WorkflowState, build_base_nodes, DISCLAIMER_TEXT
)

SYSTEM_PROMPT = """你是一位私立诊所运营咨询 AI 助手。
你帮助诊所管理者解答：患者接待流程、预约管理、收费规范、合规运营等问题。
你不提供任何医疗诊断或临床建议。"""


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

        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + state["messages"]
        async for token in self._llm.astream(messages):
            yield token

        yield f"\n\n{DISCLAIMER_TEXT}"
