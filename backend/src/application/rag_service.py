"""T091 — RAG application service."""
from __future__ import annotations

import os
import uuid

from fastapi import HTTPException, status

from src.domains.audit.entities import AuditAction, AuditOutcome
from src.domains.audit.services import AuditService
from src.domains.rag.entities import Document, DocumentStatus, KnowledgeBase
from src.domains.rag.repository import IKnowledgeBaseRepository
from src.infrastructure.storage.file_storage import FileStorage
from src.infrastructure.vector_store.pgvector_adapter import PgVectorAdapter


class RAGApplicationService:
    def __init__(
        self,
        kb_repo: IKnowledgeBaseRepository,
        audit: AuditService,
        file_storage: FileStorage | None = None,
        vector_adapter: PgVectorAdapter | None = None,
        session=None,
    ) -> None:
        self._repo = kb_repo
        self._audit = audit
        self._storage = file_storage or FileStorage()
        self._adapter = vector_adapter or PgVectorAdapter()
        self._session = session

    # ------------------------------------------------------------------
    # Knowledge Base
    # ------------------------------------------------------------------

    async def create_kb(
        self,
        owner_id: uuid.UUID,
        name: str,
        description: str | None,
        user_role: str,
    ) -> KnowledgeBase:
        kb = KnowledgeBase(owner_id=owner_id, name=name, description=description)
        await self._repo.save_kb(kb)
        await self._audit.log(
            action=AuditAction.KNOWLEDGE_BASE_CREATED,
            resource_type="KnowledgeBase",
            outcome=AuditOutcome.SUCCESS,
            actor_id=owner_id,
            actor_role=user_role,
            resource_id=kb.id,
            detail={"name": name},
        )
        return kb

    async def list_kbs(self, owner_id: uuid.UUID) -> list[KnowledgeBase]:
        return await self._repo.find_by_owner(owner_id)

    async def delete_kb(
        self,
        kb_id: uuid.UUID,
        owner_id: uuid.UUID,
        user_role: str,
    ) -> None:
        kb = await self._repo.find_by_id(kb_id)
        if not kb:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在")
        if kb.owner_id != owner_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作此知识库")
        await self._repo.delete_kb(kb_id)
        self._storage.delete_kb_dir(str(kb_id))
        await self._audit.log(
            action=AuditAction.KNOWLEDGE_BASE_DELETED,
            resource_type="KnowledgeBase",
            outcome=AuditOutcome.SUCCESS,
            actor_id=owner_id,
            actor_role=user_role,
            resource_id=kb_id,
        )

    # ------------------------------------------------------------------
    # Documents
    # ------------------------------------------------------------------

    async def upload_document(
        self,
        kb_id: uuid.UUID,
        owner_id: uuid.UUID,
        filename: str,
        file_bytes: bytes,
        mime_type: str,
        user_role: str,
    ) -> Document:
        kb = await self._repo.find_by_id(kb_id)
        if not kb:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在")
        if kb.owner_id != owner_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作此知识库")

        # Persist the file
        file_path = self._storage.save_file(file_bytes, filename, str(kb_id))

        # Create Document entity — temporarily use error_message to carry the
        # file path so the Celery worker can locate the file without a dedicated
        # column (the worker will clear it on success).
        document = Document(
            kb_id=kb_id,
            filename=filename,
            file_size_bytes=len(file_bytes),
            mime_type=mime_type,
            status=DocumentStatus.UPLOADING,
            error_message=file_path,  # path stashed here until processed
        )
        await self._repo.save_document(document)

        # Audit
        await self._audit.log(
            action=AuditAction.DOCUMENT_UPLOADED,
            resource_type="Document",
            outcome=AuditOutcome.SUCCESS,
            actor_id=owner_id,
            actor_role=user_role,
            resource_id=document.id,
            detail={"filename": filename, "kb_id": str(kb_id)},
        )

        # Dispatch Celery task
        from src.infrastructure.celery_tasks.vectorize_document import vectorize_document
        vectorize_document.delay(str(document.id))

        return document

    async def list_documents(
        self,
        kb_id: uuid.UUID,
        owner_id: uuid.UUID,
    ) -> list[Document]:
        kb = await self._repo.find_by_id(kb_id)
        if not kb:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在")
        if kb.owner_id != owner_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作此知识库")
        return await self._repo.find_documents_by_kb(kb_id)

    async def delete_document(
        self,
        doc_id: uuid.UUID,
        kb_id: uuid.UUID,
        owner_id: uuid.UUID,
        user_role: str,
    ) -> None:
        kb = await self._repo.find_by_id(kb_id)
        if not kb:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在")
        if kb.owner_id != owner_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作此知识库")

        document = await self._repo.find_document_by_id(doc_id)
        if not document or document.kb_id != kb_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在")

        # Remove physical file if path is stored
        if document.error_message and os.path.exists(document.error_message):
            self._storage.delete_file(document.error_message)

        await self._repo.delete_document(doc_id)
        await self._audit.log(
            action=AuditAction.DOCUMENT_DELETED,
            resource_type="Document",
            outcome=AuditOutcome.SUCCESS,
            actor_id=owner_id,
            actor_role=user_role,
            resource_id=doc_id,
            detail={"kb_id": str(kb_id)},
        )

    # ------------------------------------------------------------------
    # RAG Query
    # ------------------------------------------------------------------

    async def rag_query(
        self,
        kb_id: uuid.UUID,
        owner_id: uuid.UUID,
        query: str,
        top_k: int,
        user_role: str,
    ) -> list[dict]:
        import openai

        kb = await self._repo.find_by_id(kb_id)
        if not kb:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在")
        if kb.owner_id != owner_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作此知识库")

        embedding_api_key = os.environ.get("EMBEDDING_API_KEY") or os.environ["OPENAI_API_KEY"]
        embedding_base_url = os.environ.get("EMBEDDING_BASE_URL") or os.environ.get("OPENAI_BASE_URL")
        embedding_model = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
        embedding_dimensions = os.environ.get("EMBEDDING_DIMENSIONS")
        openai_client = openai.OpenAI(api_key=embedding_api_key, base_url=embedding_base_url)
        embedding_request = {
            "model": embedding_model,
            "input": query,
        }
        if embedding_dimensions:
            embedding_request["dimensions"] = int(embedding_dimensions)
        response = openai_client.embeddings.create(
            **embedding_request,
        )
        query_embedding: list[float] = response.data[0].embedding

        results = await self._repo.similarity_search(query_embedding, kb_id, top_k)

        await self._audit.log(
            action=AuditAction.KB_QUERIED,
            resource_type="KnowledgeBase",
            outcome=AuditOutcome.SUCCESS,
            actor_id=owner_id,
            actor_role=user_role,
            resource_id=kb_id,
            detail={"query": query[:200], "top_k": top_k, "results": len(results)},
        )
        return results
