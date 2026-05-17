"""ConversationApplicationService: orchestrates message flow with SSE streaming."""
import json
import time
import uuid
from typing import AsyncIterator

from fastapi import HTTPException, status

from src.domains.agent.repository import IAgentRepository
from src.domains.agent.services import AgentDispatcher
from src.domains.audit.entities import AuditAction, AuditOutcome
from src.domains.audit.services import AuditService
from src.domains.conversation.entities import Conversation, ConversationSession
from src.domains.conversation.repository import IConversationRepository
from src.domains.conversation.services import ConversationDomainService
from src.infrastructure.llm.langchain_adapter import LLMAdapter


class ConversationApplicationService:
    def __init__(
        self,
        conv_repo: IConversationRepository,
        agent_repo: IAgentRepository,
        audit: AuditService,
    ) -> None:
        self._conv_repo = conv_repo
        self._agent_repo = agent_repo
        self._audit = audit
        self._llm = LLMAdapter()
        self._dispatcher = AgentDispatcher(self._llm)
        self._domain = ConversationDomainService()

    async def create_conversation(
        self, user_id: uuid.UUID, title: str | None, agent_id: uuid.UUID | None
    ) -> tuple[Conversation, ConversationSession]:
        conv = self._domain.create_conversation(user_id, title or "新对话")
        session = self._domain.create_session(conv.id, agent_id)
        await self._conv_repo.save_conversation(conv)
        await self._conv_repo.save_session(session)
        return conv, session

    async def get_conversations(
        self, user_id: uuid.UUID, page: int, page_size: int
    ) -> tuple[list[Conversation], int]:
        return await self._conv_repo.find_by_user_id(user_id, page, page_size)

    async def get_conversation_detail(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID, limit: int, before_id: uuid.UUID | None
    ):
        conv = await self._conv_repo.find_conversation_by_id(conversation_id)
        if not conv or conv.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        session = await self._conv_repo.find_session(conversation_id)
        messages = await self._conv_repo.get_messages(conversation_id, limit, before_id)
        return conv, session, messages

    async def stream_message(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
        agent_id: uuid.UUID | None,
        rag_enabled: bool | None,
        user_role: str,
    ) -> AsyncIterator[str]:
        conv = await self._conv_repo.find_conversation_by_id(conversation_id)
        if not conv or conv.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

        session = await self._conv_repo.find_session(conversation_id)
        if not session:
            session = self._domain.create_session(conv.id)
            await self._conv_repo.save_session(session)

        effective_agent_id = agent_id or session.active_agent_id
        agent = None
        if effective_agent_id:
            agent = await self._agent_repo.find_by_id(effective_agent_id)
            if agent and user_role not in agent.allowed_roles and user_role != "admin":
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="您的角色无权使用此智能体")

        if rag_enabled is not None and user_role == "doctor":
            session.rag_enabled = rag_enabled

        # Save user message
        user_msg = self._domain.build_user_message(conv.id, session.id, content)
        await self._conv_repo.save_message(user_msg)

        # Build message history for LLM
        history = await self._conv_repo.get_messages(conv.id, 20, None)
        messages_for_llm = [{"role": m.role.value, "content": m.content} for m in history]

        workflow_type = agent.workflow_config.get("workflow_type", "medical_auxiliary") if agent else "medical_auxiliary"

        message_id = str(uuid.uuid4())
        start_ts = time.monotonic()

        # SSE: start event
        yield f"event: start\ndata: {json.dumps({'message_id': message_id, 'agent_id': str(effective_agent_id) if effective_agent_id else None, 'session_id': str(session.id)})}\n\n"

        full_response = []
        refused = False
        try:
            stream = await self._dispatcher.dispatch(
                workflow_type=workflow_type,
                messages=messages_for_llm,
                session_context=session.context_snapshot,
                agent_id=str(effective_agent_id) if effective_agent_id else "",
                user_role=user_role,
                rag_enabled=session.rag_enabled,
            )
            async for token in stream:
                full_response.append(token)
                yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"
        except Exception as e:
            refused = True
            yield f"event: error\ndata: {json.dumps({'code': 'agent_error', 'message': str(e)})}\n\n"

        if not refused:
            from src.domains.conversation.entities import DISCLAIMER_TEXT
            response_text = "".join(full_response)
            if DISCLAIMER_TEXT in response_text:
                yield f"event: disclaimer\ndata: {json.dumps({'text': DISCLAIMER_TEXT})}\n\n"

            latency_ms = round((time.monotonic() - start_ts) * 1000)
            yield f"event: end\ndata: {json.dumps({'message_id': message_id, 'latency_ms': latency_ms})}\n\n"

            # Save assistant message
            if effective_agent_id:
                assistant_msg = self._domain.build_assistant_message(
                    conv.id, session.id, effective_agent_id, response_text,
                    metadata={"latency_ms": latency_ms}
                )
                await self._conv_repo.save_message(assistant_msg)

        session.touch()
        await self._conv_repo.save_session(session)

        await self._audit.log(
            action=AuditAction.MESSAGE_SENT if not refused else AuditAction.MESSAGE_REFUSED,
            resource_type="Message",
            outcome=AuditOutcome.SUCCESS if not refused else AuditOutcome.REFUSED,
            actor_id=user_id,
            actor_role=user_role,
            session_id=session.id,
        )

    async def update_session(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID,
        active_agent_id: uuid.UUID | None, rag_enabled: bool | None, user_role: str
    ) -> ConversationSession:
        conv = await self._conv_repo.find_conversation_by_id(conversation_id)
        if not conv or conv.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        session = await self._conv_repo.find_session(conversation_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        if active_agent_id is not None:
            session.switch_agent(active_agent_id)
        if rag_enabled is not None and user_role == "doctor":
            session.rag_enabled = rag_enabled
        await self._conv_repo.save_session(session)
        return session

    async def delete_conversation(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> None:
        conv = await self._conv_repo.find_conversation_by_id(conversation_id)
        if not conv or conv.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        await self._conv_repo.soft_delete_conversation(conversation_id)
