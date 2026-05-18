import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.publishing.entities import (
    BatchStatus,
    ItemStatus,
    PublishingBatch,
    PublishingBatchItem,
)
from src.domains.publishing.repository import IPublishingRepository
from src.infrastructure.db.models import PublishingBatchModel, PublishingBatchItemModel


class PublishingRepository(IPublishingRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_batch(self, batch: PublishingBatch) -> PublishingBatch:
        model = PublishingBatchModel(
            id=batch.id,
            submitted_by=batch.submitted_by,
            submitted_at=batch.submitted_at,
            status=batch.status.value,
            total_count=batch.total_count,
            success_count=batch.success_count,
            failure_count=batch.failure_count,
        )
        self._session.add(model)

        for item in batch.items:
            item_model = PublishingBatchItemModel(
                id=item.id,
                batch_id=batch.id,
                agent_config=item.agent_config,
                status=item.status.value,
                error_message=item.error_message,
                agent_id=item.agent_id,
            )
            self._session.add(item_model)

        await self._session.flush()
        return batch

    async def find_batch_by_id(self, batch_id: uuid.UUID) -> PublishingBatch | None:
        result = await self._session.execute(
            select(PublishingBatchModel)
            .options(selectinload(PublishingBatchModel.items))
            .where(PublishingBatchModel.id == batch_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._to_domain(row)

    async def update_batch(self, batch: PublishingBatch) -> PublishingBatch:
        result = await self._session.execute(
            select(PublishingBatchModel)
            .options(selectinload(PublishingBatchModel.items))
            .where(PublishingBatchModel.id == batch.id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise ValueError(f"PublishingBatch {batch.id} not found")

        row.status = batch.status.value
        row.total_count = batch.total_count
        row.success_count = batch.success_count
        row.failure_count = batch.failure_count

        # Build a map of existing item rows by id
        existing_items = {item_row.id: item_row for item_row in row.items}

        for item in batch.items:
            if item.id in existing_items:
                item_row = existing_items[item.id]
                item_row.status = item.status.value
                item_row.error_message = item.error_message
                item_row.agent_id = item.agent_id
            else:
                new_item = PublishingBatchItemModel(
                    id=item.id,
                    batch_id=batch.id,
                    agent_config=item.agent_config,
                    status=item.status.value,
                    error_message=item.error_message,
                    agent_id=item.agent_id,
                )
                self._session.add(new_item)

        await self._session.flush()
        return batch

    @staticmethod
    def _to_domain(row: PublishingBatchModel) -> PublishingBatch:
        items = [
            PublishingBatchItem(
                id=item.id,
                batch_id=item.batch_id,
                agent_config=item.agent_config or {},
                status=ItemStatus(item.status),
                error_message=item.error_message,
                agent_id=item.agent_id,
            )
            for item in (row.items or [])
        ]
        return PublishingBatch(
            id=row.id,
            submitted_by=row.submitted_by,
            submitted_at=row.submitted_at,
            status=BatchStatus(row.status),
            total_count=row.total_count,
            success_count=row.success_count,
            failure_count=row.failure_count,
            items=items,
        )
