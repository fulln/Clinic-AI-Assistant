import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime


class BatchStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIAL_FAILURE = "partial_failure"


class ItemStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class PublishingBatchItem:
    agent_config: dict
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    batch_id: uuid.UUID | None = None
    status: ItemStatus = ItemStatus.PENDING
    error_message: str | None = None
    agent_id: uuid.UUID | None = None


@dataclass
class PublishingBatch:
    submitted_by: uuid.UUID
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    submitted_at: datetime = field(default_factory=datetime.utcnow)
    status: BatchStatus = BatchStatus.PENDING
    total_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    items: list[PublishingBatchItem] = field(default_factory=list)
