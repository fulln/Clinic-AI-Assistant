"""T090 — Celery task: vectorize an uploaded document."""
from __future__ import annotations

import asyncio
import os
import uuid
from datetime import datetime

import structlog

from src.infrastructure.celery_app import celery_app

log = structlog.get_logger(__name__)


def _run_async(coro):
    """Run an async coroutine from a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, name="vectorize_document", max_retries=3)
def vectorize_document(self, document_id: str) -> None:
    """Vectorize a document and persist chunks to the database."""
    _run_async(_vectorize(self, document_id))


async def _vectorize(task, document_id: str) -> None:
    import openai
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from src.domains.rag.entities import DocumentChunk, DocumentStatus
    from src.domains.rag.services import ChunkingService
    from src.infrastructure.db.repositories.rag_repo import KnowledgeBaseRepository

    DATABASE_URL = (
        f"postgresql+asyncpg://"
        f"{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
        f"@{os.environ.get('POSTGRES_HOST', 'localhost')}:{os.environ.get('POSTGRES_PORT', '5432')}"
        f"/{os.environ['POSTGRES_DB']}"
    )

    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    doc_uuid = uuid.UUID(document_id)

    async with SessionLocal() as session:
        repo = KnowledgeBaseRepository(session)
        document = await repo.find_document_by_id(doc_uuid)
        if not document:
            log.error("vectorize_document: document not found", document_id=document_id)
            return

        # Mark as processing
        await repo.update_document_status(doc_uuid, DocumentStatus.PROCESSING)
        await session.commit()

        try:
            # ---- Read file bytes ----
            # RAGApplicationService stores the file path in error_message temporarily.
            # Re-fetch to get the current DB value.
            from sqlalchemy import select
            from src.infrastructure.db.models import DocumentModel
            result = await session.execute(
                select(DocumentModel).where(DocumentModel.id == doc_uuid)
            )
            doc_row = result.scalar_one_or_none()
            if not doc_row:
                raise RuntimeError("DocumentModel row missing")

            file_path: str = doc_row.error_message or ""
            if not file_path or not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found at path: {file_path!r}")

            with open(file_path, "rb") as fh:
                file_bytes = fh.read()

            # ---- Extract text ----
            text = _extract_text(file_bytes, document.mime_type, document.filename)

            # ---- Chunk ----
            chunker = ChunkingService()
            chunks_text = chunker.chunk_text(text)

            if not chunks_text:
                raise ValueError("Document produced no text chunks")

            # ---- Embed ----
            openai_client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
            doc_chunks: list[DocumentChunk] = []

            for i, chunk_text in enumerate(chunks_text):
                response = openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=chunk_text,
                )
                embedding = response.data[0].embedding
                token_count = len(chunk_text) // 4  # approx

                doc_chunks.append(
                    DocumentChunk(
                        document_id=doc_uuid,
                        chunk_index=i,
                        content=chunk_text,
                        embedding=embedding,
                        token_count=token_count,
                        metadata={"chunk_index": i},
                    )
                )

            # ---- Persist chunks ----
            await repo.save_chunks(doc_chunks)

            # ---- Update document status → ready ----
            await repo.update_document_status(
                doc_uuid,
                DocumentStatus.READY,
                chunk_count=len(doc_chunks),
                error_message=None,
                processed_at=datetime.utcnow(),
            )
            await session.commit()
            log.info(
                "vectorize_document: complete",
                document_id=document_id,
                chunks=len(doc_chunks),
            )

        except Exception as exc:
            log.error(
                "vectorize_document: failed",
                document_id=document_id,
                error=str(exc),
            )
            async with SessionLocal() as err_session:
                err_repo = KnowledgeBaseRepository(err_session)
                await err_repo.update_document_status(
                    doc_uuid,
                    DocumentStatus.FAILED,
                    error_message=str(exc),
                )
                await err_session.commit()
            raise

    await engine.dispose()


def _extract_text(file_bytes: bytes, mime_type: str, filename: str) -> str:
    """Extract plain text from PDF, DOCX, TXT, or MD."""
    lower = filename.lower()

    if mime_type == "application/pdf" or lower.endswith(".pdf"):
        import io
        import pypdf

        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)

    if (
        mime_type
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        or lower.endswith(".docx")
    ):
        import io
        import docx

        doc = docx.Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs)

    # Plain text / Markdown
    return file_bytes.decode("utf-8", errors="replace")
