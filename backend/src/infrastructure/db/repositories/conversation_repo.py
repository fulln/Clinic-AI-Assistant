import json
import uuid
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.conversation.entities import (
    Conversation, ConversationSession, Locale, Message, MessageRole
)
from src.domains.conversation.repository import IConversationRepository
from src.infrastructure.db.models import (
    ConversationModel, ConversationSessionModel, MessageModel
)
from src.infrastructure.cache import redis_client


class ConversationRepository(IConversationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def commit(self) -> None:
        """Force-commit the underlying session.

        Needed inside SSE generators: FastAPI's `Depends(get_db)` runs its
        commit *after* the endpoint returns, but the generator keeps writing
        rows long after that. Persistent state must be committed by hand at
        each safe checkpoint.
        """
        await self._session.commit()

    async def find_conversation_by_id(self, conversation_id: uuid.UUID) -> Conversation | None:
        result = await self._session.execute(
            select(ConversationModel).where(ConversationModel.id == conversation_id)
        )
        row = result.scalar_one_or_none()
        return self._conv_to_domain(row) if row else None

    async def find_by_user_id(
        self, user_id: uuid.UUID, page: int, page_size: int
    ) -> tuple[list[Conversation], int]:
        total_result = await self._session.execute(
            select(func.count()).select_from(ConversationModel).where(
                ConversationModel.user_id == user_id
            )
        )
        total = total_result.scalar_one()
        result = await self._session.execute(
            select(ConversationModel)
            .where(ConversationModel.user_id == user_id)
            .order_by(ConversationModel.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = result.scalars().all()
        return [self._conv_to_domain(r) for r in rows], total

    async def save_conversation(self, conversation: Conversation) -> Conversation:
        result = await self._session.execute(
            select(ConversationModel).where(ConversationModel.id == conversation.id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = ConversationModel(
                id=conversation.id,
                user_id=conversation.user_id,
                title=conversation.title,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
            )
            self._session.add(row)
        else:
            row.title = conversation.title
            row.updated_at = datetime.utcnow()
        await self._session.flush()
        return conversation

    async def save_session(self, session: ConversationSession) -> ConversationSession:
        result = await self._session.execute(
            select(ConversationSessionModel).where(ConversationSessionModel.id == session.id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = ConversationSessionModel(
                id=session.id,
                conversation_id=session.conversation_id,
                active_agent_id=session.active_agent_id,
                context_snapshot=session.context_snapshot,
                rag_enabled=session.rag_enabled,
                locale=session.locale.value,
                created_at=session.created_at,
                last_activity_at=session.last_activity_at,
            )
            self._session.add(row)
        else:
            row.active_agent_id = session.active_agent_id
            row.context_snapshot = session.context_snapshot
            row.rag_enabled = session.rag_enabled
            row.locale = session.locale.value
            row.last_activity_at = session.last_activity_at
        await self._session.flush()
        # Also write to Redis cache (24h TTL)
        await redis_client.set_json(
            redis_client.session_context_key(str(session.id)),
            session.context_snapshot,
            ex=86400,
        )
        return session

    async def find_session(self, conversation_id: uuid.UUID) -> ConversationSession | None:
        result = await self._session.execute(
            select(ConversationSessionModel)
            .where(ConversationSessionModel.conversation_id == conversation_id)
            .order_by(ConversationSessionModel.created_at.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return self._session_to_domain(row) if row else None

    async def save_message(self, message: Message) -> Message:
        row = MessageModel(
            id=message.id,
            conversation_id=message.conversation_id,
            session_id=message.session_id,
            agent_id=message.agent_id,
            role=message.role.value,
            content=message.content,
            has_disclaimer=message.has_disclaimer,
            metadata_=message.metadata,
            is_deleted=message.is_deleted,
            created_at=message.created_at,
        )
        self._session.add(row)
        await self._session.flush()
        return message

    async def get_messages(
        self, conversation_id: uuid.UUID, limit: int, before_id: uuid.UUID | None
    ) -> list[Message]:
        query = (
            select(MessageModel)
            .where(MessageModel.conversation_id == conversation_id)
            .order_by(MessageModel.created_at.asc())
            .limit(limit)
        )
        if before_id:
            ref = await self._session.execute(
                select(MessageModel.created_at).where(MessageModel.id == before_id)
            )
            ref_time = ref.scalar_one_or_none()
            if ref_time:
                query = query.where(MessageModel.created_at < ref_time)
        result = await self._session.execute(query)
        return [self._msg_to_domain(r) for r in result.scalars().all()]

    async def soft_delete_conversation(self, conversation_id: uuid.UUID) -> None:
        result = await self._session.execute(
            select(MessageModel).where(MessageModel.conversation_id == conversation_id)
        )
        for row in result.scalars().all():
            row.content = "[REDACTED]"
            row.is_deleted = True
        await self._session.flush()

    @staticmethod
    def _conv_to_domain(row: ConversationModel) -> Conversation:
        return Conversation(
            id=row.id, user_id=row.user_id, title=row.title,
            created_at=row.created_at, updated_at=row.updated_at,
        )

    @staticmethod
    def _session_to_domain(row: ConversationSessionModel) -> ConversationSession:
        return ConversationSession(
            id=row.id, conversation_id=row.conversation_id,
            active_agent_id=row.active_agent_id, context_snapshot=row.context_snapshot or {},
            rag_enabled=row.rag_enabled, locale=Locale(row.locale), created_at=row.created_at,
            last_activity_at=row.last_activity_at,
        )

    @staticmethod
    def _msg_to_domain(row: MessageModel) -> Message:
        return Message(
            id=row.id, conversation_id=row.conversation_id, session_id=row.session_id,
            role=MessageRole(row.role), content=row.content, agent_id=row.agent_id,
            has_disclaimer=row.has_disclaimer, metadata=row.metadata_ or {},
            is_deleted=row.is_deleted, created_at=row.created_at,
        )
