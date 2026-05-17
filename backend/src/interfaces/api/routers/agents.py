import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.publishing_service import PublishingApplicationService
from src.domains.agent.entities import Agent, AgentStatus, AgentType
from src.infrastructure.db.models import UserRole
from src.infrastructure.db.repositories.agent_repo import AgentRepository
from src.infrastructure.db.repositories.publishing_repo import PublishingRepository
from src.interfaces.api.dependencies import get_current_user, get_db, require_role
from src.interfaces.api.schemas.agent_schemas import (
    AgentResponse,
    BatchPublishRequest,
    BatchPublishResponse,
    BatchStatusItem,
    BatchStatusResponse,
    CreateAgentRequest,
)

router = APIRouter()


def _build_publishing_service(db: AsyncSession) -> PublishingApplicationService:
    return PublishingApplicationService(
        publishing_repo=PublishingRepository(db),
    )


def _agent_to_response(agent: Agent) -> AgentResponse:
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        slug=agent.slug,
        description=agent.description,
        agent_type=agent.agent_type.value,
        capabilities=agent.capabilities,
        allowed_roles=agent.allowed_roles,
        status=agent.status.value,
        version=agent.version,
    )


# ---------------------------------------------------------------------------
# GET /agents — list published agents, filtered by caller role
# ---------------------------------------------------------------------------

@router.get("", response_model=list[AgentResponse])
async def list_agents(
    agent_type: str | None = None,
    status_filter: str | None = None,
    include_all: bool = False,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = AgentRepository(db)
    if include_all:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
        resolved_status = AgentStatus(status_filter) if status_filter else None
        agents = await repo.find_all(status=resolved_status)
        if agent_type:
            agents = [agent for agent in agents if agent.agent_type.value == agent_type]
        return [_agent_to_response(agent) for agent in agents]

    agents = await repo.find_published(agent_type=agent_type)
    role_value = current_user.role.value
    filtered = [a for a in agents if not a.allowed_roles or role_value in a.allowed_roles]
    return [_agent_to_response(a) for a in filtered]


# ---------------------------------------------------------------------------
# POST /agents/batch-publish — admin only, async 202
# Must be declared BEFORE the /{id} routes to avoid path-param capture
# ---------------------------------------------------------------------------

@router.post(
    "/batch-publish",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=BatchPublishResponse,
)
async def batch_publish_agents(
    body: BatchPublishRequest,
    current_user=Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    svc = _build_publishing_service(db)
    agents_dicts = [a.model_dump() for a in body.agents]
    batch = await svc.submit_batch(
        submitted_by=current_user.id,
        agents=agents_dicts,
    )
    return BatchPublishResponse(
        batch_id=batch.id,
        status=batch.status.value,
        total_count=batch.total_count,
        submitted_at=batch.submitted_at,
    )


# ---------------------------------------------------------------------------
# GET /agents/batches/{batch_id} — admin only
# ---------------------------------------------------------------------------

@router.get(
    "/batches/{batch_id}",
    response_model=BatchStatusResponse,
)
async def get_batch_status(
    batch_id: uuid.UUID,
    current_user=Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    svc = _build_publishing_service(db)
    try:
        batch = await svc.get_batch_status(batch_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    items = [
        BatchStatusItem(
            index=idx,
            status=item.status.value,
            agent_id=item.agent_id,
            error=item.error_message,
        )
        for idx, item in enumerate(batch.items)
    ]
    return BatchStatusResponse(
        batch_id=batch.id,
        status=batch.status.value,
        total_count=batch.total_count,
        success_count=batch.success_count,
        failure_count=batch.failure_count,
        items=items,
    )


# ---------------------------------------------------------------------------
# GET /agents/{id}
# ---------------------------------------------------------------------------

@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: uuid.UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = AgentRepository(db)
    agent = await repo.find_by_id(agent_id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return _agent_to_response(agent)


# ---------------------------------------------------------------------------
# POST /agents — admin only, create draft agent
# ---------------------------------------------------------------------------

@router.post("", status_code=status.HTTP_201_CREATED, response_model=AgentResponse)
async def create_agent(
    body: CreateAgentRequest,
    current_user=Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    repo = AgentRepository(db)

    # Validate slug uniqueness
    existing = await repo.find_by_slug(body.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Agent with slug '{body.slug}' already exists",
        )

    agent = Agent(
        name=body.name,
        slug=body.slug,
        description=body.description,
        agent_type=AgentType(body.agent_type),
        workflow_config=body.workflow_config,
        capabilities=body.capabilities,
        allowed_roles=body.allowed_roles,
        created_by=current_user.id,
    )
    saved = await repo.save(agent)
    return _agent_to_response(saved)


# ---------------------------------------------------------------------------
# PATCH /agents/{id} — admin only
# ---------------------------------------------------------------------------

@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: uuid.UUID,
    body: CreateAgentRequest,
    current_user=Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    repo = AgentRepository(db)
    agent = await repo.find_by_id(agent_id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    agent.name = body.name
    agent.description = body.description
    agent.agent_type = AgentType(body.agent_type)
    agent.workflow_config = body.workflow_config
    agent.capabilities = body.capabilities
    agent.allowed_roles = body.allowed_roles

    saved = await repo.save(agent)
    return _agent_to_response(saved)


# ---------------------------------------------------------------------------
# POST /agents/{id}/publish — admin only
# ---------------------------------------------------------------------------

@router.post("/{agent_id}/publish", response_model=AgentResponse)
async def publish_agent(
    agent_id: uuid.UUID,
    current_user=Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    repo = AgentRepository(db)
    agent = await repo.find_by_id(agent_id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    try:
        agent.publish(version=agent.version or "1.0.0")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    saved = await repo.save(agent)
    return _agent_to_response(saved)


# ---------------------------------------------------------------------------
# POST /agents/{id}/archive — admin only
# ---------------------------------------------------------------------------

@router.post("/{agent_id}/archive", response_model=AgentResponse)
async def archive_agent(
    agent_id: uuid.UUID,
    current_user=Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    repo = AgentRepository(db)
    agent = await repo.find_by_id(agent_id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    agent.archive()
    saved = await repo.save(agent)
    return _agent_to_response(saved)
