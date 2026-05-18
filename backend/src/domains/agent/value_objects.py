from dataclasses import dataclass
from src.domains.agent.entities import AgentStatus, AgentType


@dataclass(frozen=True)
class AgentConfig:
    workflow_type: str
    parameters: dict

    def is_valid(self) -> bool:
        return bool(self.workflow_type)


@dataclass(frozen=True)
class AgentPublication:
    agent_id: str
    version: str
    published_by: str
    version_snapshot: dict
