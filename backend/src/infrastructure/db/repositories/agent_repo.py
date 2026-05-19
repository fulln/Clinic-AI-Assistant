import json
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.agent.entities import Agent, AgentStatus, AgentType
from src.domains.agent.repository import IAgentRepository
from src.infrastructure.cache import redis_client
from src.infrastructure.db.models import AgentModel

_CATALOG_TTL = 300  # 5 minutes


class AgentRepository(IAgentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, agent_id: uuid.UUID) -> Agent | None:
        result = await self._session.execute(
            select(AgentModel).where(AgentModel.id == agent_id)
        )
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def find_by_slug(self, slug: str) -> Agent | None:
        result = await self._session.execute(
            select(AgentModel).where(AgentModel.slug == slug)
        )
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def find_published(self, agent_type: str | None = None) -> list[Agent]:
        cached = await redis_client.get_json(redis_client.agent_catalog_key())
        if cached and not agent_type:
            return [self._dict_to_domain(a) for a in cached]

        query = select(AgentModel).where(AgentModel.status == AgentStatus.PUBLISHED.value)
        if agent_type:
            query = query.where(AgentModel.agent_type == agent_type)
        result = await self._session.execute(query)
        agents = [self._to_domain(r) for r in result.scalars().all()]

        if not agent_type:
            await redis_client.set_json(
                redis_client.agent_catalog_key(),
                [self._domain_to_dict(a) for a in agents],
                ex=_CATALOG_TTL,
            )
        return agents

    async def find_all(self, status: AgentStatus | None = None) -> list[Agent]:
        query = select(AgentModel)
        if status:
            query = query.where(AgentModel.status == status.value)
        result = await self._session.execute(query)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def save(self, agent: Agent) -> Agent:
        result = await self._session.execute(
            select(AgentModel).where(AgentModel.id == agent.id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = AgentModel(
                id=agent.id, name=agent.name, slug=agent.slug,
                description=agent.description, agent_type=agent.agent_type.value,
                capabilities=agent.capabilities, workflow_config=agent.workflow_config,
                allowed_roles=agent.allowed_roles, status=agent.status.value,
                version=agent.version, created_by=agent.created_by,
                created_at=agent.created_at, updated_at=agent.updated_at,
                system_prompt_en=agent.system_prompt_en,
                system_prompt_zh=agent.system_prompt_zh,
                tools=agent.tools,
                max_tool_turns=agent.max_tool_turns,
                llm_model=agent.llm_model,
                llm_temperature=agent.llm_temperature,
                llm_max_tokens=agent.llm_max_tokens,
            )
            self._session.add(row)
        else:
            row.name = agent.name
            row.description = agent.description
            row.capabilities = agent.capabilities
            row.workflow_config = agent.workflow_config
            row.allowed_roles = agent.allowed_roles
            row.status = agent.status.value
            row.version = agent.version
            row.system_prompt_en = agent.system_prompt_en
            row.system_prompt_zh = agent.system_prompt_zh
            row.tools = agent.tools
            row.max_tool_turns = agent.max_tool_turns
            row.llm_model = agent.llm_model
            row.llm_temperature = agent.llm_temperature
            row.llm_max_tokens = agent.llm_max_tokens
            row.updated_at = datetime.utcnow()
        await self._session.flush()
        # Invalidate catalog cache when status changes
        await redis_client.delete(redis_client.agent_catalog_key())
        return agent

    @staticmethod
    def _to_domain(row: AgentModel) -> Agent:
        return Agent(
            id=row.id, name=row.name, slug=row.slug, description=row.description,
            agent_type=AgentType(row.agent_type), workflow_config=row.workflow_config or {},
            capabilities=row.capabilities or [], allowed_roles=row.allowed_roles or [],
            status=AgentStatus(row.status), version=row.version, created_by=row.created_by,
            created_at=row.created_at, updated_at=row.updated_at,
            system_prompt_en=row.system_prompt_en,
            system_prompt_zh=row.system_prompt_zh,
            tools=list(row.tools or []),
            max_tool_turns=int(row.max_tool_turns or 3),
            llm_model=row.llm_model,
            llm_temperature=row.llm_temperature,
            llm_max_tokens=row.llm_max_tokens,
        )

    @staticmethod
    def _domain_to_dict(agent: Agent) -> dict:
        return {
            "id": str(agent.id), "name": agent.name, "slug": agent.slug,
            "description": agent.description, "agent_type": agent.agent_type.value,
            "capabilities": agent.capabilities, "allowed_roles": agent.allowed_roles,
            "status": agent.status.value, "version": agent.version,
            "system_prompt_en": agent.system_prompt_en,
            "system_prompt_zh": agent.system_prompt_zh,
            "tools": agent.tools,
            "max_tool_turns": agent.max_tool_turns,
            "llm_model": agent.llm_model,
            "llm_temperature": agent.llm_temperature,
            "llm_max_tokens": agent.llm_max_tokens,
        }

    @staticmethod
    def _dict_to_domain(d: dict) -> Agent:
        return Agent(
            id=uuid.UUID(d["id"]), name=d["name"], slug=d["slug"],
            description=d["description"], agent_type=AgentType(d["agent_type"]),
            workflow_config={}, capabilities=d.get("capabilities", []),
            allowed_roles=d.get("allowed_roles", []),
            status=AgentStatus(d["status"]), version=d.get("version"),
            system_prompt_en=d.get("system_prompt_en"),
            system_prompt_zh=d.get("system_prompt_zh"),
            tools=list(d.get("tools") or []),
            max_tool_turns=int(d.get("max_tool_turns") or 3),
            llm_model=d.get("llm_model"),
            llm_temperature=d.get("llm_temperature"),
            llm_max_tokens=d.get("llm_max_tokens"),
        )
