import uuid

from src.domains.publishing.aggregates import PublishingBatchAggregate
from src.domains.publishing.entities import PublishingBatch
from src.domains.publishing.repository import IPublishingRepository


class PublishingApplicationService:
    def __init__(self, publishing_repo: IPublishingRepository) -> None:
        self._publishing_repo = publishing_repo

    async def submit_batch(
        self,
        submitted_by: uuid.UUID,
        agents: list[dict],
    ) -> PublishingBatch:
        aggregate = PublishingBatchAggregate.create(submitted_by=submitted_by)

        for agent_config in agents:
            aggregate.add_item(agent_config)

        batch = aggregate.batch
        await self._publishing_repo.save_batch(batch)

        # Dispatch Celery task after persisting
        from src.infrastructure.celery_tasks.process_publishing_batch import (
            process_publishing_batch,
        )
        process_publishing_batch.delay(str(batch.id))

        return batch

    async def get_batch_status(self, batch_id: uuid.UUID) -> PublishingBatch:
        batch = await self._publishing_repo.find_batch_by_id(batch_id)
        if batch is None:
            raise ValueError(f"PublishingBatch {batch_id} not found")
        return batch
