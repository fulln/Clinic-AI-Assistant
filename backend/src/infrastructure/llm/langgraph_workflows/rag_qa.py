"""RAG QA agent workflow — retrieval wired in Phase 6 (T101)."""
from typing import AsyncIterator

from src.infrastructure.llm.langchain_adapter import LLMAdapter
from src.infrastructure.llm.langgraph_workflows.base_workflow import (
    WorkflowState, build_base_nodes, DISCLAIMER_TEXT
)

SYSTEM_PROMPT = """你是一位基于个人知识库的医疗 AI 助手。
当启用知识库时，优先引用知识库内容回答，并标注来源文档名称。
你不提供临床诊断、处方或具体治疗方案。"""


class RagQAWorkflow:
    def __init__(self, llm: LLMAdapter, vector_search_service=None) -> None:
        self._llm = llm
        self._vector_search = vector_search_service

    async def stream(self, state: WorkflowState) -> AsyncIterator[str]:
        context_loader, intent_classifier, _, _ = build_base_nodes(self._llm)
        state = await context_loader(state)
        state = await intent_classifier(state)

        if state["refused"]:
            yield state["refusal_reason"]
            return

        system_content = SYSTEM_PROMPT
        # RAG retrieval (activated in T101 when vector_search_service is wired)
        if state.get("rag_enabled") and state.get("rag_chunks"):
            context_text = "\n\n".join(
                f"[{c.get('filename', '文档')}] {c['content']}"
                for c in state["rag_chunks"]
            )
            system_content += f"\n\n以下是从您的知识库中检索到的相关内容：\n{context_text}"

        messages = [{"role": "system", "content": system_content}] + state["messages"]
        async for token in self._llm.astream(messages):
            yield token

        yield f"\n\n{DISCLAIMER_TEXT}"
