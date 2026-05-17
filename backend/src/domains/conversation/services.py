import uuid
from datetime import datetime

from src.domains.conversation.entities import (
    Conversation, ConversationSession, Message, MessageRole, DISCLAIMER_TEXT
)


class ConversationDomainService:
    @staticmethod
    def create_conversation(user_id: uuid.UUID, title: str = "新对话") -> Conversation:
        return Conversation(user_id=user_id, title=title)

    @staticmethod
    def create_session(conversation_id: uuid.UUID, agent_id: uuid.UUID | None = None) -> ConversationSession:
        return ConversationSession(conversation_id=conversation_id, active_agent_id=agent_id)

    @staticmethod
    def build_user_message(
        conversation_id: uuid.UUID, session_id: uuid.UUID, content: str
    ) -> Message:
        return Message(
            conversation_id=conversation_id,
            session_id=session_id,
            role=MessageRole.USER,
            content=content,
        )

    @staticmethod
    def build_assistant_message(
        conversation_id: uuid.UUID,
        session_id: uuid.UUID,
        agent_id: uuid.UUID,
        content: str,
        metadata: dict | None = None,
    ) -> Message:
        has_disclaimer = DISCLAIMER_TEXT in content
        return Message(
            conversation_id=conversation_id,
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=content,
            agent_id=agent_id,
            has_disclaimer=has_disclaimer,
            metadata=metadata or {},
        )

    @staticmethod
    def soft_delete_conversation_messages(messages: list[Message]) -> list[Message]:
        for msg in messages:
            msg.soft_delete()
        return messages
