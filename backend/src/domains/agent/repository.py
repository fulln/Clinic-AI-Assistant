import uuid
from abc import ABC, abstractmethod

from src.domains.agent.entities import Agent, AgentStatus


class IAgentRepository(ABC):
    @abstractmethod
    async def find_by_id(self, agent_id: uuid.UUID) -> Agent | None: ...

    @abstractmethod
    async def find_by_slug(self, slug: str) -> Agent | None: ...

    @abstractmethod
    async def find_published(self, agent_type: str | None = None) -> list[Agent]: ...

    @abstractmethod
    async def find_all(self, status: AgentStatus | None = None) -> list[Agent]: ...

    @abstractmethod
    async def save(self, agent: Agent) -> Agent: ...
