import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime

DISCLAIMER_TEXT = "本内容仅供辅助参考，不构成医疗诊断或治疗建议，请遵医嘱。"


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class Message:
    conversation_id: uuid.UUID
    session_id: uuid.UUID
    role: MessageRole
    content: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    agent_id: uuid.UUID | None = None
    has_disclaimer: bool = False
    metadata: dict = field(default_factory=dict)
    is_deleted: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        # Invariant: assistant messages MUST have agent_id
        if self.role == MessageRole.ASSISTANT and self.agent_id is None:
            raise ValueError("Assistant messages must have agent_id")

    def soft_delete(self) -> None:
        self.content = "[REDACTED]"
        self.is_deleted = True


@dataclass
class ConversationSession:
    conversation_id: uuid.UUID
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    active_agent_id: uuid.UUID | None = None
    context_snapshot: dict = field(default_factory=dict)
    rag_enabled: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity_at: datetime = field(default_factory=datetime.utcnow)

    def switch_agent(self, agent_id: uuid.UUID) -> None:
        self.active_agent_id = agent_id
        self.last_activity_at = datetime.utcnow()

    def touch(self) -> None:
        self.last_activity_at = datetime.utcnow()


@dataclass
class Conversation:
    user_id: uuid.UUID
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    title: str = "新对话"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
