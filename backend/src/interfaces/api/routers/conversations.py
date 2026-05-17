import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.conversation_service import ConversationApplicationService
from src.domains.audit.services import AuditService
from src.infrastructure.db.repositories.audit_repo import AuditRepository
from src.infrastructure.db.repositories.agent_repo import AgentRepository
from src.infrastructure.db.repositories.conversation_repo import ConversationRepository
from src.infrastructure.db.repositories.rag_repo import KnowledgeBaseRepository
from src.interfaces.api.dependencies import get_current_user, get_db
from src.interfaces.api.schemas.conversation_schemas import (
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationListItem,
    ConversationResponse,
    CreateConversationRequest,
    MessageResponse,
    SendMessageRequest,
    SessionInfo,
    SessionUpdateRequest,
)
from src.domains.conversation.entities import Locale

router = APIRouter()


def _build_service(db: AsyncSession) -> ConversationApplicationService:
    return ConversationApplicationService(
        conv_repo=ConversationRepository(db),
        agent_repo=AgentRepository(db),
        rag_repo=KnowledgeBaseRepository(db),
        audit=AuditService(AuditRepository(db)),
    )


@router.post("", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    body: CreateConversationRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = _build_service(db)
    conv, session = await svc.create_conversation(
        current_user.id,
        body.title,
        body.agent_id,
        body.locale,
    )
    return ConversationResponse(
        id=conv.id, title=conv.title, user_id=conv.user_id,
        session_id=session.id, active_agent_id=session.active_agent_id,
        rag_enabled=session.rag_enabled, locale=session.locale, created_at=conv.created_at,
    )


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = _build_service(db)
    convs, total = await svc.get_conversations(current_user.id, page, page_size)
    return ConversationListResponse(
        items=[ConversationListItem(id=c.id, title=c.title, created_at=c.created_at) for c in convs],
        total=total,
    )


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200),
    before_id: Optional[uuid.UUID] = None,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = _build_service(db)
    conv, session, messages = await svc.get_conversation_detail(
        conversation_id, current_user.id, limit, before_id
    )
    return ConversationDetailResponse(
        id=conv.id,
        title=conv.title,
        session=SessionInfo(
            id=session.id if session else uuid.uuid4(),
            active_agent_id=session.active_agent_id if session else None,
            rag_enabled=session.rag_enabled if session else False,
            locale=session.locale if session else Locale.ZH_CN,
        ),
        messages=[
            MessageResponse(
                id=m.id, role=m.role.value, content=m.content,
                agent_id=m.agent_id,
                has_disclaimer=m.has_disclaimer,
                metadata=m.metadata,
                created_at=m.created_at,
            )
            for m in messages if not m.is_deleted
        ],
    )


@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: uuid.UUID,
    body: SendMessageRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = _build_service(db)
    return StreamingResponse(
        svc.stream_message(
            conversation_id=conversation_id,
            user_id=current_user.id,
            content=body.content,
            agent_id=body.agent_id,
            rag_enabled=body.rag_enabled,
            locale=body.locale,
            user_role=current_user.role.value,
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.patch("/{conversation_id}/session", response_model=SessionInfo)
async def update_session(
    conversation_id: uuid.UUID,
    body: SessionUpdateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = _build_service(db)
    session = await svc.update_session(
        conversation_id, current_user.id,
        body.active_agent_id, body.rag_enabled, body.locale, current_user.role.value,
    )
    return SessionInfo(
        id=session.id,
        active_agent_id=session.active_agent_id,
        rag_enabled=session.rag_enabled,
        locale=session.locale,
    )


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = _build_service(db)
    await svc.delete_conversation(conversation_id, current_user.id)
