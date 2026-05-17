"""T083 — RAG domain entities."""
import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime


class DocumentStatus(str, enum.Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


@dataclass
class KnowledgeBase:
    """Aggregate root for a doctor's knowledge base.

    Invariant: owner_id MUST belong to a doctor; enforced at application layer.
    """
    name: str
    owner_id: uuid.UUID
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    description: str | None = None
    document_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("KnowledgeBase name must not be empty")


@dataclass
class Document:
    kb_id: uuid.UUID
    filename: str
    file_size_bytes: int
    mime_type: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    status: DocumentStatus = DocumentStatus.UPLOADING
    chunk_count: int = 0
    error_message: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: datetime | None = None


@dataclass
class DocumentChunk:
    document_id: uuid.UUID
    chunk_index: int
    content: str
    embedding: list[float]
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    token_count: int = 0
    metadata: dict = field(default_factory=dict)
