import uuid

from src.domains.publishing.entities import (
    BatchStatus,
    ItemStatus,
    PublishingBatch,
    PublishingBatchItem,
)


class PublishingBatchAggregate:
    """Aggregate root for a publishing batch."""

    def __init__(self, batch: PublishingBatch) -> None:
        self._batch = batch

    @classmethod
    def create(cls, submitted_by: uuid.UUID) -> "PublishingBatchAggregate":
        batch = PublishingBatch(submitted_by=submitted_by)
        return cls(batch)

    @property
    def batch(self) -> PublishingBatch:
        return self._batch

    def add_item(self, agent_config: dict) -> PublishingBatchItem:
        item = PublishingBatchItem(
            agent_config=agent_config,
            batch_id=self._batch.id,
        )
        self._batch.items.append(item)
        self._batch.total_count = len(self._batch.items)
        return item

    def mark_item_success(self, index: int, agent_id: uuid.UUID) -> None:
        item = self._batch.items[index]
        item.status = ItemStatus.SUCCESS
        item.agent_id = agent_id
        self._batch.success_count = sum(
            1 for i in self._batch.items if i.status == ItemStatus.SUCCESS
        )

    def mark_item_failed(self, index: int, error_msg: str) -> None:
        item = self._batch.items[index]
        item.status = ItemStatus.FAILED
        item.error_message = error_msg
        self._batch.failure_count = sum(
            1 for i in self._batch.items if i.status == ItemStatus.FAILED
        )

    def finalize(self) -> PublishingBatch:
        if self._batch.failure_count == 0:
            self._batch.status = BatchStatus.COMPLETED
        else:
            self._batch.status = BatchStatus.PARTIAL_FAILURE
        return self._batch
