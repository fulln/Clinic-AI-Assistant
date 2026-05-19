import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime


class AgentType(str, enum.Enum):
    FORMAL = "formal"
    DEMO = "demo"


class AgentStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


@dataclass
class Agent:
    name: str
    slug: str
    description: str
    agent_type: AgentType
    workflow_config: dict
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    capabilities: list[str] = field(default_factory=list)
    allowed_roles: list[str] = field(default_factory=list)
    status: AgentStatus = AgentStatus.DRAFT
    version: str | None = None
    system_prompt_en: str | None = None
    system_prompt_zh: str | None = None
    tools: list[str] = field(default_factory=list)
    max_tool_turns: int = 3
    llm_model: str | None = None
    llm_temperature: float | None = None
    llm_max_tokens: int | None = None
    created_by: uuid.UUID | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def publish(self, version: str) -> None:
        if self.status == AgentStatus.ARCHIVED:
            raise ValueError("Cannot publish an archived agent")
        self.status = AgentStatus.PUBLISHED
        self.version = version
        self.updated_at = datetime.utcnow()

    def archive(self) -> None:
        self.status = AgentStatus.ARCHIVED
        self.updated_at = datetime.utcnow()

    def restore_to_draft(self) -> None:
        if self.status != AgentStatus.ARCHIVED:
            raise ValueError("Only archived agents can be restored to draft")
        self.status = AgentStatus.DRAFT
        self.updated_at = datetime.utcnow()
