import uuid
from datetime import datetime

from src.domains.conversation.entities import (
    Conversation,
    ConversationSession,
    Locale,
    Message,
    MessageRole,
)
from src.domains.conversation.i18n import get_disclaimer, get_new_conversation_title


class ConversationDomainService:
    @staticmethod
    def create_conversation(
        user_id: uuid.UUID,
        title: str | None = None,
        locale: Locale = Locale.ZH_CN,
    ) -> Conversation:
        return Conversation(user_id=user_id, title=title or get_new_conversation_title(locale))

    @staticmethod
    def create_session(
        conversation_id: uuid.UUID,
        agent_id: uuid.UUID | None = None,
        locale: Locale = Locale.ZH_CN,
    ) -> ConversationSession:
        return ConversationSession(
            conversation_id=conversation_id,
            active_agent_id=agent_id,
            locale=locale,
        )

    @staticmethod
    def build_user_message(
        conversation_id: uuid.UUID,
        session_id: uuid.UUID,
        content: str,
        locale: Locale,
    ) -> Message:
        return Message(
            conversation_id=conversation_id,
            session_id=session_id,
            role=MessageRole.USER,
            content=content,
            metadata={"locale": locale.value},
        )

    @staticmethod
    def build_assistant_message(
        conversation_id: uuid.UUID,
        session_id: uuid.UUID,
        agent_id: uuid.UUID,
        content: str,
        locale: Locale,
        metadata: dict | None = None,
    ) -> Message:
        disclaimer = get_disclaimer(locale)
        merged_metadata = {"locale": locale.value, "disclaimer_locale": locale.value}
        if metadata:
            merged_metadata.update(metadata)
        has_disclaimer = disclaimer in content
        return Message(
            conversation_id=conversation_id,
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=content,
            agent_id=agent_id,
            has_disclaimer=has_disclaimer,
            metadata=merged_metadata,
        )

    @staticmethod
    def soft_delete_conversation_messages(messages: list[Message]) -> list[Message]:
        for msg in messages:
            msg.soft_delete()
        return messages
