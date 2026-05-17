"""AgentDispatcher routes conversation messages to the correct LangGraph workflow."""
import uuid
from typing import AsyncIterator

from src.infrastructure.llm.langchain_adapter import LLMAdapter
from src.infrastructure.llm.langgraph_workflows.base_workflow import WorkflowState
from src.infrastructure.llm.langgraph_workflows.medical_auxiliary import MedicalAuxiliaryWorkflow
from src.infrastructure.llm.langgraph_workflows.document_organizer import DocumentOrganizerWorkflow
from src.infrastructure.llm.langgraph_workflows.operations_consultant import OperationsConsultantWorkflow
from src.infrastructure.llm.langgraph_workflows.health_educator import HealthEducatorWorkflow
from src.infrastructure.llm.langgraph_workflows.rag_qa import RagQAWorkflow


class AgentDispatcher:
    def __init__(self, llm: LLMAdapter) -> None:
        self._llm = llm
        self._workflows = {
            "medical_auxiliary": MedicalAuxiliaryWorkflow(llm),
            "document_organizer": DocumentOrganizerWorkflow(llm),
            "operations_consultant": OperationsConsultantWorkflow(llm),
            "health_educator": HealthEducatorWorkflow(llm),
            "rag_qa": RagQAWorkflow(llm),
        }

    def register(self, workflow_type: str, workflow) -> None:
        self._workflows[workflow_type] = workflow

    async def dispatch(
        self,
        workflow_type: str,
        messages: list[dict],
        session_context: dict,
        agent_id: str,
        user_role: str,
        rag_enabled: bool = False,
        rag_chunks: list[dict] | None = None,
    ) -> AsyncIterator[str]:
        workflow = self._workflows.get(workflow_type)
        if workflow is None:
            raise ValueError(f"Unknown workflow type: {workflow_type}")

        state: WorkflowState = {
            "messages": messages,
            "session_context": session_context,
            "agent_id": agent_id,
            "user_role": user_role,
            "rag_enabled": rag_enabled,
            "rag_chunks": rag_chunks or [],
            "response_tokens": [],
            "has_disclaimer": False,
            "refused": False,
            "refusal_reason": "",
        }
        return workflow.stream(state)
