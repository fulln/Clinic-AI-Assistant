import uuid
from abc import ABC, abstractmethod

from src.domains.conversation.entities import Conversation, ConversationSession, Message


class IConversationRepository(ABC):
    @abstractmethod
    async def find_conversation_by_id(self, conversation_id: uuid.UUID) -> Conversation | None: ...

    @abstractmethod
    async def find_by_user_id(self, user_id: uuid.UUID, page: int, page_size: int) -> tuple[list[Conversation], int]: ...

    @abstractmethod
    async def save_conversation(self, conversation: Conversation) -> Conversation: ...

    @abstractmethod
    async def save_session(self, session: ConversationSession) -> ConversationSession: ...

    @abstractmethod
    async def find_session(self, conversation_id: uuid.UUID) -> ConversationSession | None: ...

    @abstractmethod
    async def save_message(self, message: Message) -> Message: ...

    @abstractmethod
    async def get_messages(self, conversation_id: uuid.UUID, limit: int, before_id: uuid.UUID | None) -> list[Message]: ...

    @abstractmethod
    async def soft_delete_conversation(self, conversation_id: uuid.UUID) -> None: ...
