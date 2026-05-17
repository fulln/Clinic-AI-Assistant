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
