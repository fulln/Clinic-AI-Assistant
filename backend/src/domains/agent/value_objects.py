from dataclasses import dataclass


@dataclass(frozen=True)
class AgentPublication:
    agent_id: str
    version: str
    published_by: str
    version_snapshot: dict
