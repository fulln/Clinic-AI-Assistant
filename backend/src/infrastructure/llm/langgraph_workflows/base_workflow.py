"""Shared LangGraph workflow nodes used by all agents."""
from typing import Any, AsyncIterator, TypedDict

from langgraph.graph import StateGraph, END

from src.domains.conversation.entities import DISCLAIMER_TEXT
from src.infrastructure.llm.langchain_adapter import LLMAdapter

# Intent patterns that must be refused (Constitution Principle I)
REFUSED_INTENTS = [
    "诊断", "确诊", "处方", "开药", "用药剂量", "治疗方案", "病历",
    "diagnos", "prescri", "medication dosage", "treatment plan",
]


class WorkflowState(TypedDict):
    messages: list[dict]
    session_context: dict
    agent_id: str
    user_role: str
    rag_enabled: bool
    rag_chunks: list[dict]
    response_tokens: list[str]
    has_disclaimer: bool
    refused: bool
    refusal_reason: str


def build_base_nodes(llm: LLMAdapter):
    async def context_loader(state: WorkflowState) -> WorkflowState:
        """Loads session context into messages if available."""
        return state

    async def intent_classifier(state: WorkflowState) -> WorkflowState:
        """Refuses diagnostic/prescription requests (Constitution Principle I)."""
        last_user_msg = next(
            (m["content"] for m in reversed(state["messages"]) if m["role"] == "user"),
            "",
        )
        for pattern in REFUSED_INTENTS:
            if pattern in last_user_msg.lower():
                state["refused"] = True
                state["refusal_reason"] = "该请求超出本平台服务范围，请咨询执业医师。"
                return state
        state["refused"] = False
        return state

    async def disclaimer(state: WorkflowState) -> WorkflowState:
        """Appends mandatory medical disclaimer to response."""
        state["has_disclaimer"] = True
        if state["response_tokens"]:
            state["response_tokens"].append(f"\n\n{DISCLAIMER_TEXT}")
        return state

    async def context_saver(state: WorkflowState) -> WorkflowState:
        """Persists final state (handled externally via checkpointer)."""
        return state

    return context_loader, intent_classifier, disclaimer, context_saver


def should_refuse(state: WorkflowState) -> str:
    return "refused" if state.get("refused") else "continue"
