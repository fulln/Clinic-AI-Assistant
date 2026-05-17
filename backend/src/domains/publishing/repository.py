import uuid
from abc import ABC, abstractmethod

from src.domains.publishing.entities import PublishingBatch


class IPublishingRepository(ABC):
    @abstractmethod
    async def save_batch(self, batch: PublishingBatch) -> PublishingBatch: ...

    @abstractmethod
    async def find_batch_by_id(self, batch_id: uuid.UUID) -> PublishingBatch | None: ...

    @abstractmethod
    async def update_batch(self, batch: PublishingBatch) -> PublishingBatch: ...
