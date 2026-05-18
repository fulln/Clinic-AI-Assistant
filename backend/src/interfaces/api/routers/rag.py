"""T093 — FastAPI router for RAG endpoints (doctor role only)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.rag_service import RAGApplicationService
from src.domains.audit.services import AuditService
from src.infrastructure.db.repositories.audit_repo import AuditRepository
from src.infrastructure.db.repositories.rag_repo import KnowledgeBaseRepository
from src.infrastructure.db.models import UserModel, UserRole
from src.interfaces.api.dependencies import get_db, require_role
from src.interfaces.api.schemas.rag_schemas import (
    CreateKnowledgeBaseRequest,
    DocumentListItem,
    DocumentUploadResponse,
    KnowledgeBaseResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    RAGQueryResult,
)

router = APIRouter()

_doctor_guard = require_role(UserRole.DOCTOR)


def _build_service(db: AsyncSession) -> RAGApplicationService:
    return RAGApplicationService(
        kb_repo=KnowledgeBaseRepository(db),
        audit=AuditService(AuditRepository(db)),
        session=db,
    )


# ---------------------------------------------------------------------------
# Knowledge Base endpoints
# ---------------------------------------------------------------------------

@router.post("/knowledge-bases", response_model=KnowledgeBaseResponse, status_code=201)
async def create_knowledge_base(
    body: CreateKnowledgeBaseRequest,
    current_user: UserModel = Depends(_doctor_guard),
    db: AsyncSession = Depends(get_db),
):
    svc = _build_service(db)
    kb = await svc.create_kb(
        owner_id=current_user.id,
        name=body.name,
        description=body.description,
        user_role=current_user.role.value,
    )
    return KnowledgeBaseResponse(
        id=kb.id,
        owner_id=kb.owner_id,
        name=kb.name,
        description=kb.description,
        document_count=kb.document_count,
        created_at=kb.created_at,
        updated_at=kb.updated_at,
    )


@router.get("/knowledge-bases", response_model=list[KnowledgeBaseResponse])
async def list_knowledge_bases(
    current_user: UserModel = Depends(_doctor_guard),
    db: AsyncSession = Depends(get_db),
):
    svc = _build_service(db)
    kbs = await svc.list_kbs(current_user.id)
    return [
        KnowledgeBaseResponse(
            id=kb.id,
            owner_id=kb.owner_id,
            name=kb.name,
            description=kb.description,
            document_count=kb.document_count,
            created_at=kb.created_at,
            updated_at=kb.updated_at,
        )
        for kb in kbs
    ]


@router.delete("/knowledge-bases/{kb_id}", status_code=204)
async def delete_knowledge_base(
    kb_id: uuid.UUID,
    current_user: UserModel = Depends(_doctor_guard),
    db: AsyncSession = Depends(get_db),
):
    svc = _build_service(db)
    await svc.delete_kb(kb_id, current_user.id, current_user.role.value)


# ---------------------------------------------------------------------------
# Document endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/knowledge-bases/{kb_id}/documents",
    response_model=DocumentUploadResponse,
    status_code=201,
)
async def upload_document(
    kb_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: UserModel = Depends(_doctor_guard),
    db: AsyncSession = Depends(get_db),
):
    file_bytes = await file.read()
    mime_type = file.content_type or "application/octet-stream"
    svc = _build_service(db)
    document = await svc.upload_document(
        kb_id=kb_id,
        owner_id=current_user.id,
        filename=file.filename or "unknown",
        file_bytes=file_bytes,
        mime_type=mime_type,
        user_role=current_user.role.value,
    )
    return DocumentUploadResponse(
        document_id=document.id,
        filename=document.filename,
        file_size_bytes=document.file_size_bytes,
        status=document.status.value,
        created_at=document.created_at,
    )


@router.get(
    "/knowledge-bases/{kb_id}/documents",
    response_model=list[DocumentListItem],
)
async def list_documents(
    kb_id: uuid.UUID,
    current_user: UserModel = Depends(_doctor_guard),
    db: AsyncSession = Depends(get_db),
):
    svc = _build_service(db)
    docs = await svc.list_documents(kb_id, current_user.id)
    return [
        DocumentListItem(
            id=d.id,
            filename=d.filename,
            file_size_bytes=d.file_size_bytes,
            status=d.status.value,
            chunk_count=d.chunk_count,
            # Don't expose internal file path stored in error_message
            error_message=(
                d.error_message
                if d.status.value == "failed"
                else None
            ),
            created_at=d.created_at,
            processed_at=d.processed_at,
        )
        for d in docs
    ]


@router.delete("/knowledge-bases/{kb_id}/documents/{doc_id}", status_code=204)
async def delete_document(
    kb_id: uuid.UUID,
    doc_id: uuid.UUID,
    current_user: UserModel = Depends(_doctor_guard),
    db: AsyncSession = Depends(get_db),
):
    svc = _build_service(db)
    await svc.delete_document(doc_id, kb_id, current_user.id, current_user.role.value)


# ---------------------------------------------------------------------------
# RAG Query endpoint
# ---------------------------------------------------------------------------

@router.post("/query", response_model=RAGQueryResponse)
async def rag_query(
    body: RAGQueryRequest,
    current_user: UserModel = Depends(_doctor_guard),
    db: AsyncSession = Depends(get_db),
):
    svc = _build_service(db)
    results = await svc.rag_query(
        kb_id=body.knowledge_base_id,
        owner_id=current_user.id,
        query=body.query,
        top_k=body.top_k,
        user_role=current_user.role.value,
    )
    return RAGQueryResponse(
        results=[RAGQueryResult(**r) for r in results],
        query_embedding_tokens=len(body.query) // 4,
    )
